#!/bin/bash

# 每日自动更新脚本
# 功能：更新 lastUpdate 日期 + 提示用户手动更新数据
# 使用方式：手动运行或通过 LaunchAgent 定时执行

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_DIR/update.log"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

TODAY=$(date '+%Y-%m-%d')

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  📅 每日数据更新 - $TODAY${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 1. 更新 JSON 文件中的 lastUpdate 字段
log "更新数据文件日期..."
python3 << PYEOF
import json
import os

today = "$TODAY"
project_dir = "$PROJECT_DIR"

files = [
    'boards/category-data.json',
    'boards/all-issues-data.json',
    'boards/monthly-data.json',
    'boards/activity-data.json',
    'boards/kb-pending.json',
    'boards/kb-sync.json',
    'knowledge-base/docs-index.json',
]

updated = 0
for f in files:
    path = os.path.join(project_dir, f)
    try:
        with open(path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        if 'lastUpdate' in data:
            data['lastUpdate'] = today
            with open(path, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            updated += 1
    except Exception as e:
        print(f'  ⚠️ {f}: {e}')

print(f'  ✅ 已更新 {updated} 个文件的日期为 {today}')
PYEOF

# 2. 检查知识库是否有新文档
log "检查知识库更新..."
KB_COUNT=$(python3 -c "
import json
with open('$PROJECT_DIR/knowledge-base/docs-index.json', 'r') as f:
    data = json.load(f)
print(data.get('total', 0))
")
log "知识库当前文档数: $KB_COUNT"

# 3. 检查 Jira 数据
log "检查 Jira 数据..."
JIRA_COUNT=$(python3 -c "
import json
with open('$PROJECT_DIR/boards/all-issues-data.json', 'r') as f:
    data = json.load(f)
print(len(data.get('issues', [])))
")
log "当前 Jira 问题数: $JIRA_COUNT"

# 4. 提示用户手动更新
echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  💡 提示${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo "  数据日期已更新为 $TODAY"
echo ""
echo "  如需更新实际数据，请在 Claude 中运行："
echo ""
echo "    /kb update"
echo ""
echo "  或者告诉 Claude："
echo "    请帮我从 Jira 拉取最新数据"
echo ""
echo -e "${BLUE}========================================${NC}"
echo ""

log "每日更新完成"
