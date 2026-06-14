#!/usr/bin/env python3
"""
Jira 问题数据获取脚本
用于从 Jira 获取指定用户的 issues 并生成本地数据文件

使用方式：
1. 通过 Claude MCP 工具获取数据
2. 或通过 Jira API 直接获取
"""

import json
import os
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
BOARDS_DIR = PROJECT_ROOT / "boards"

def create_sample_data():
    """创建示例数据结构"""
    sample = {
        "lastUpdate": datetime.now().strftime('%Y-%m-%d'),
        "issues": [
            {
                "key": "EXAMPLE-123",
                "summary": "示例问题标题",
                "assignee": "负责人",
                "priority": "Major",
                "status": "OPEN",
                "labels": [],
                "category": "未分类",
                "created": "2026-01-01",
                "updated": "2026-01-01"
            }
        ]
    }
    return sample

def main():
    print("=" * 50)
    print("📋 Jira 问题数据获取工具")
    print("=" * 50)

    print("\n⚠️  此脚本需要配合 Claude MCP 使用")
    print("\n请在 Claude 中运行以下命令来获取数据：")
    print("\n  请帮我从 Jira 拉取我的 issues 并生成 boards/all-issues-data.json")
    print("\n或者指定具体条件：")
    print("  请帮我从 Jira 拉取 [用户名] 的 issues，状态为 OPEN/In Progress/Verify")

    # 检查现有数据
    data_file = BOARDS_DIR / "all-issues-data.json"
    if data_file.exists():
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"\n📊 当前数据:")
        print(f"   文件: {data_file}")
        print(f"   更新时间: {data.get('lastUpdate', '未知')}")
        print(f"   问题数量: {len(data.get('issues', []))}")

        # 显示负责人列表
        assignees = set(i.get('assignee', '') for i in data.get('issues', []))
        print(f"   负责人: {', '.join(assignees)}")
    else:
        print(f"\n❌ 数据文件不存在: {data_file}")

if __name__ == "__main__":
    main()
