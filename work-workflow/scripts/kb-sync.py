#!/usr/bin/env python3
"""
知识库事件驱动同步
- 扫描 Jira 操作记录（解决、评论、状态变更）
- 与知识库比对，找出需要更新的内容
- 生成待处理列表供用户确认
"""

import json
import re
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_DIR = os.path.join(BASE_DIR, "knowledge-base")
BOARDS_DIR = os.path.join(BASE_DIR, "boards")
SOLUTIONS_FILE = os.path.join(KB_DIR, "solutions.md")
OUTPUT_FILE = os.path.join(BOARDS_DIR, "kb-pending.json")


def parse_solutions_md():
    """解析 solutions.md 中的表格数据"""
    entries = {}
    if not os.path.exists(SOLUTIONS_FILE):
        return entries

    with open(SOLUTIONS_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r'\|\s*([A-Z]+-\d+)\s*\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|'
    for m in re.finditer(pattern, content):
        key = m.group(1).strip()
        if key == "Jira":
            continue
        entries[key] = {
            "key": key,
            "summary": m.group(2).strip(),
            "category": m.group(3).strip(),
            "solution": m.group(4).strip(),
            "location": m.group(5).strip(),
            "status": m.group(6).strip(),
            "date": m.group(7).strip(),
            "related": m.group(8).strip(),
        }
    return entries


def load_jira_issues():
    """加载 Jira 问题数据"""
    all_file = os.path.join(BOARDS_DIR, "all-issues-data.json")
    if not os.path.exists(all_file):
        return []
    with open(all_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("issues", [])


def load_activities():
    """加载操作记录"""
    act_file = os.path.join(BOARDS_DIR, "activity-data.json")
    if not os.path.exists(act_file):
        return []
    with open(act_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("activities", [])


def load_existing_pending():
    """加载已有的待处理记录（避免重复）"""
    if not os.path.exists(OUTPUT_FILE):
        return []
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("pending", [])


def find_pending_updates(kb_entries, jira_issues, activities, existing_pending):
    """找出需要更新知识库的内容"""
    pending = []
    existing_keys = {p["key"] for p in existing_pending}

    # 1. 扫描最近的解决/状态变更操作
    for act in activities:
        key = act["key"]
        if not key or key in existing_keys:
            continue

        issue = next((i for i in jira_issues if i["key"] == key), None)

        if act["type"] == "resolve":
            # 已解决但知识库没有记录
            if key not in kb_entries:
                pending.append({
                    "key": key,
                    "type": "new_resolution",
                    "trigger": f"已解决: {act.get('detail', '')}",
                    "summary": act.get("summary", issue.get("summary", "") if issue else ""),
                    "category": issue.get("category", "") if issue else "",
                    "current_status": issue.get("status", "") if issue else "",
                    "action": "需要录入知识库：解决方案、解决位置、关联Jira",
                    "time": act["time"],
                    "done": False,
                })

        elif act["type"] == "status_change":
            # 状态变更，检查知识库是否需要同步
            if key in kb_entries:
                kb_status = kb_entries[key].get("status", "")
                detail = act.get("detail", "")
                if "Resolved" in detail or "Closed" in detail:
                    if kb_status not in ["已解决", "已关闭"]:
                        pending.append({
                            "key": key,
                            "type": "status_update",
                            "trigger": f"状态变更: {detail}",
                            "summary": kb_entries[key].get("summary", ""),
                            "kb_status": kb_status,
                            "new_status": "已解决",
                            "action": "更新知识库状态",
                            "time": act["time"],
                            "done": False,
                        })

        elif act["type"] == "comment":
            # 有新评论，检查是否包含解决方案信息
            detail = act.get("detail", "")
            solution_keywords = ["解决", "修复", "方案", "原因", "根因", "workaround", "临时方案"]
            if any(kw in detail for kw in solution_keywords):
                if key not in kb_entries:
                    pending.append({
                        "key": key,
                        "type": "solution_in_comment",
                        "trigger": f"评论中发现解决方案: {detail[:80]}",
                        "summary": act.get("summary", issue.get("summary", "") if issue else ""),
                        "category": issue.get("category", "") if issue else "",
                        "action": "提取评论中的解决方案，录入知识库",
                        "time": act["time"],
                        "done": False,
                    })

    # 2. 扫描知识库中状态过时的记录
    for key, entry in kb_entries.items():
        if key in existing_keys:
            continue
        issue = next((i for i in jira_issues if i["key"] == key), None)
        if issue:
            jira_status = issue.get("status", "")
            kb_status = entry.get("status", "")
            if jira_status in ["Resolved", "Closed"] and kb_status not in ["已解决", "已关闭"]:
                pending.append({
                    "key": key,
                    "type": "stale_kb_entry",
                    "trigger": f"Jira 已{jira_status}，知识库仍为{kb_status}",
                    "summary": entry.get("summary", ""),
                    "kb_status": kb_status,
                    "jira_status": jira_status,
                    "action": "同步知识库状态",
                    "time": datetime.now().strftime("%Y-%m-%dT%H:%M"),
                    "done": False,
                })

    return pending


def main():
    print("知识库事件同步检查...")

    kb_entries = parse_solutions_md()
    jira_issues = load_jira_issues()
    activities = load_activities()
    existing_pending = load_existing_pending()

    print(f"  知识库: {len(kb_entries)} 条")
    print(f"  Jira: {len(jira_issues)} 个")
    print(f"  操作记录: {len(activities)} 条")
    print(f"  已有待处理: {len(existing_pending)} 条")

    new_pending = find_pending_updates(kb_entries, jira_issues, activities, existing_pending)
    print(f"  新增待处理: {len(new_pending)} 条")

    # 合并（保留已有的，新增的放前面）
    all_pending = new_pending + existing_pending

    result = {
        "lastUpdate": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total": len(all_pending),
        "pending": all_pending,
    }

    os.makedirs(BOARDS_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n结果: {OUTPUT_FILE}")

    if new_pending:
        print("\n新增待处理:")
        for p in new_pending:
            print(f"  [{p['type']}] {p['key']}: {p['trigger']}")
    else:
        print("\n无需更新。")


if __name__ == "__main__":
    main()
