#!/usr/bin/env python3
"""
GitLab 代码仓库索引脚本
用于将 GitLab 仓库的内容索引到知识库中
"""

import json
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# 配置
GITLAB_REPO = "https://git.n.xiaomi.com/yanqingqing/miot.camera.spec.bot.git"
PROJECT_ROOT = Path(__file__).parent.parent
CODE_INDEX_FILE = PROJECT_ROOT / "knowledge-base" / "code-index.json"
TEMP_DIR = Path("/tmp/miot-camera-spec-bot")

def clone_or_pull_repo():
    """克隆或更新仓库"""
    if TEMP_DIR.exists():
        print("📦 更新仓库...")
        subprocess.run(["git", "-C", str(TEMP_DIR), "pull"], capture_output=True)
    else:
        print("📦 克隆仓库...")
        subprocess.run(["git", "clone", "--depth", "1", GITLAB_REPO, str(TEMP_DIR)], capture_output=True)
    return TEMP_DIR

def extract_important_files(repo_path):
    """提取重要文件内容"""
    important_files = []

    # 优先索引的文件模式
    priority_patterns = [
        "*.md",           # Markdown 文档
        "*.txt",          # 文本文件
        "*.json",         # 配置文件
        "*.yaml", "*.yml", # YAML 配置
        "*.py",           # Python 文件（提取注释和函数名）
        "*.js", "*.ts",   # JavaScript/TypeScript
        "README*",        # README 文件
        "CHANGELOG*",     # 变更日志
        "docs/*",         # 文档目录
        "spec/*",         # 规格目录
    ]

    # 排除的目录
    exclude_dirs = {
        '.git', 'node_modules', '__pycache__', 'venv', '.venv',
        'dist', 'build', '.idea', '.vscode'
    }

    print("🔍 扫描文件...")
    for root, dirs, files in os.walk(repo_path):
        # 排除不需要的目录
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            file_path = Path(root) / file
            relative_path = file_path.relative_to(repo_path)

            # 检查是否是重要文件
            is_important = False
            for pattern in priority_patterns:
                if file_path.match(pattern):
                    is_important = True
                    break

            if is_important:
                try:
                    # 读取文件内容
                    content = file_path.read_text(encoding='utf-8', errors='ignore')

                    # 对于代码文件，只提取注释和函数定义
                    if file.endswith(('.py', '.js', '.ts')):
                        content = extract_code_summary(content, file)

                    # 限制内容长度
                    if len(content) > 5000:
                        content = content[:5000] + "\n... (内容截断)"

                    important_files.append({
                        "path": str(relative_path),
                        "name": file,
                        "content": content,
                        "type": get_file_type(file),
                        "size": file_path.stat().st_size
                    })
                except Exception as e:
                    print(f"  ⚠️ 跳过 {relative_path}: {e}")

    return important_files

def extract_code_summary(content, filename):
    """从代码文件中提取摘要（注释和函数定义）"""
    lines = content.split('\n')
    summary_lines = []
    in_comment = False

    for line in lines:
        stripped = line.strip()

        # Python 注释
        if filename.endswith('.py'):
            if stripped.startswith('#'):
                summary_lines.append(stripped)
            elif stripped.startswith('def ') or stripped.startswith('class '):
                summary_lines.append(stripped)
            elif stripped.startswith('"""') or stripped.startswith("'''"):
                in_comment = not in_comment
                summary_lines.append(stripped)
            elif in_comment:
                summary_lines.append(stripped)

        # JavaScript/TypeScript 注释
        elif filename.endswith(('.js', '.ts')):
            if stripped.startswith('//'):
                summary_lines.append(stripped)
            elif stripped.startswith('/*'):
                in_comment = True
                summary_lines.append(stripped)
            elif in_comment:
                summary_lines.append(stripped)
                if stripped.endswith('*/'):
                    in_comment = False
            elif 'function ' in stripped or 'const ' in stripped and '=>' in stripped:
                summary_lines.append(stripped)

    return '\n'.join(summary_lines[:50])  # 最多50行

def get_file_type(filename):
    """获取文件类型"""
    ext = Path(filename).suffix.lower()
    type_map = {
        '.md': 'markdown',
        '.txt': 'text',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.html': 'html',
        '.css': 'css',
    }
    return type_map.get(ext, 'other')

def build_search_index(files):
    """构建搜索索引"""
    index = {
        "lastUpdate": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "repo": GITLAB_REPO,
        "totalFiles": len(files),
        "files": []
    }

    for file_info in files:
        # 提取关键词
        content = file_info["content"].lower()
        keywords = set()

        # 提取有意义的词
        words = content.split()
        for word in words:
            # 清理词
            word = word.strip('.,;:!?()[]{}"\'-')
            if len(word) >= 3 and not word.startswith(('http', 'www', '//')):
                keywords.add(word)

        index["files"].append({
            "path": file_info["path"],
            "name": file_info["name"],
            "type": file_info["type"],
            "size": file_info["size"],
            "keywords": list(keywords)[:100],  # 最多100个关键词
            "summary": file_info["content"][:500]  # 摘要
        })

    return index

def main():
    """主函数"""
    print("=" * 50)
    print("🔧 GitLab 代码仓库索引工具")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # 克隆或更新仓库
    repo_path = clone_or_pull_repo()
    if not repo_path.exists():
        print("❌ 无法访问仓库，请检查权限或网络")
        sys.exit(1)

    # 提取重要文件
    files = extract_important_files(repo_path)
    print(f"📄 找到 {len(files)} 个重要文件")

    # 构建索引
    index = build_search_index(files)

    # 保存索引
    with open(CODE_INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 索引完成!")
    print(f"   索引文件: {CODE_INDEX_FILE}")
    print(f"   文件数量: {index['totalFiles']}")
    print(f"   更新时间: {index['lastUpdate']}")

    # 清理临时目录
    # import shutil
    # shutil.rmtree(TEMP_DIR, ignore_errors=True)

if __name__ == "__main__":
    main()
