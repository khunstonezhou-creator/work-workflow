#!/usr/bin/env python3
"""
知识库自动更新脚本
定期检查飞书文档链接，将新增文档同步到知识库
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
KB_FILE = PROJECT_ROOT / "knowledge-base" / "docs-index.json"
TRACKER_FILE = PROJECT_ROOT / "knowledge-base" / "docs-tracker.json"

# 需要监控的飞书链接（父文档）
WATCHED_LINKS = [
    "https://mi.feishu.cn/wiki/Vw9Ywq3EQiPAhakr357cd1nvn7e",
    "https://mi.feishu.cn/wiki/Od03wEYcoiA2L6k5OfbcHK2bnBg",
    "https://mi.feishu.cn/wiki/JXZqwBiwPixe3Xkk8FjcGlarnWh",
    "https://mi.feishu.cn/wiki/W3qbwAZiZiFNS6kOJLXcgb9qn5b",
    "https://mi.feishu.cn/wiki/JFYUwn4diiVk70kYIABcpM81nng",
    "https://mi.feishu.cn/wiki/N45QwNOwciIv6jkCWsNcQqUPnle",
    "https://mi.feishu.cn/wiki/ZiGQw7vTiiNOykkfpqucjArxnpf",
    "https://mi.feishu.cn/wiki/AsSMw24YmidTiqkEUaOcyCQznXb",
    "https://mi.feishu.cn/wiki/DtPEwISk9i4IOdkBPQ8c37lnnsb",
    "https://mi.feishu.cn/wiki/Mg24wePfpiFahckJlCjcYQ4qnjd",
    "https://mi.feishu.cn/wiki/DsoQwrjStirJOKkgUsscLhQxnvb",
    "https://mi.feishu.cn/wiki/O3clwk8BDiHLU9kEqZNcuOjonRh",
]

def load_json(filepath):
    """加载 JSON 文件"""
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_json(filepath, data):
    """保存 JSON 文件"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_doc_id(url):
    """从 URL 提取文档 ID"""
    # 格式: https://xxx.feishu.cn/wiki/DOC_ID
    parts = url.rstrip('/').split('/')
    return parts[-1].split('?')[0]

def categorize_doc(title, parent_title=""):
    """根据标题和父文档标题判断分类"""
    title_lower = title.lower()
    parent_lower = parent_title.lower()

    # 分类规则
    rules = [
        (["需求", "待办", "进版", "提需"], "需求管理与待办"),
        (["4g", "4g版", "低功耗", "流量"], "4G产品需求"),
        (["c700", "双目"], "C700双目相关"),
        (["说明书", "功能说明", "开发书"], "软件功能说明书"),
        (["模板", "规范", "sop", "模版"], "模板与规范"),
        (["竞品", "统计", "对比", "列表", "清单"], "资料库与参考"),
    ]

    for keywords, category in rules:
        if any(kw in title_lower for kw in keywords):
            return category
        if any(kw in parent_lower for kw in keywords):
            return category

    return "其他参考"

def main():
    """主函数"""
    print("=" * 50)
    print("📚 知识库自动更新")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # 加载现有知识库
    kb = load_json(KB_FILE)
    if not kb:
        print("❌ 知识库文件不存在:", KB_FILE)
        sys.exit(1)

    # 加载追踪器（记录已处理的文档）
    tracker = load_json(TRACKER_FILE) or {"processed": [], "lastUpdate": None}

    # 获取所有已存在的文档 ID
    existing_ids = set()
    for cat in kb['categories'].values():
        for doc in cat['docs']:
            existing_ids.add(doc['id'])

    print(f"\n📊 当前知识库:")
    print(f"   文档总数: {kb['total']} 篇")
    print(f"   分类数: {len(kb['categories'])} 个")
    print(f"   已追踪: {len(tracker['processed'])} 个链接")

    print(f"\n⚠️  注意: 此脚本需要配合 Claude MCP 使用")
    print(f"   请在 Claude 中运行以下命令来更新知识库:")
    print(f"\n   /kb update")
    print(f"\n   或者告诉 Claude:")
    print(f"   '请帮我检查这些飞书链接是否有新增文档，并更新到知识库'")

    # 输出当前监控的链接列表
    print(f"\n📋 监控的链接 ({len(WATCHED_LINKS)} 个):")
    for i, link in enumerate(WATCHED_LINKS, 1):
        doc_id = get_doc_id(link)
        status = "✅" if doc_id in tracker['processed'] else "⏳"
        print(f"   {status} {i}. {link}")

if __name__ == "__main__":
    main()
