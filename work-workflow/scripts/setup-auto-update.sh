#!/bin/bash

# 设置自动更新定时任务
# 功能：安装 LaunchAgent，每天早上 9:00 自动更新数据日期

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PLIST_NAME="com.xiaomi.workbench-update"
PLIST_SOURCE="$PROJECT_DIR/$PLIST_NAME.plist"
PLIST_TARGET="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  ⏰ 设置自动更新定时任务${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查是否已安装
if [ -f "$PLIST_TARGET" ]; then
    echo -e "${YELLOW}⚠️  检测到已存在的定时任务${NC}"
    echo ""
    read -p "是否重新安装？(y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "已取消"
        exit 0
    fi
    # 卸载旧任务
    launchctl unload "$PLIST_TARGET" 2>/dev/null || true
fi

# 复制 plist 文件
echo -e "${BLUE}📋 安装定时任务...${NC}"
cp "$PLIST_SOURCE" "$PLIST_TARGET"

# 加载任务
launchctl load "$PLIST_TARGET"

echo ""
echo -e "${GREEN}✅ 自动更新已设置！${NC}"
echo ""
echo -e "${BLUE}📋 任务详情：${NC}"
echo "  • 执行时间：每天早上 9:00"
echo "  • 执行内容：更新数据文件日期"
echo "  • 日志位置：$PROJECT_DIR/update.log"
echo ""
echo -e "${YELLOW}💡 提示：${NC}"
echo "  • 数据日期会自动更新"
echo "  • 实际数据需要手动运行 /kb update 更新"
echo "  • 如需取消自动更新，运行："
echo "    launchctl unload ~/Library/LaunchAgents/$PLIST_NAME.plist"
echo ""
