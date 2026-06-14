#!/bin/bash

# 个人工作台 - 初始化脚本
# 用法: bash setup.sh

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  🚀 个人工作台 - 初始化配置${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查依赖
echo -e "${GREEN}[1/5] 检查依赖...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}⚠️  Python3 未安装，请先安装${NC}"
    exit 1
fi
echo "  ✅ Python3: $(python3 --version)"

if command -v node &> /dev/null; then
    echo "  ✅ Node.js: $(node --version)"
else
    echo -e "${YELLOW}  ⚠️  Node.js 未安装（每日更新脚本需要）${NC}"
fi

# 创建目录结构
echo ""
echo -e "${GREEN}[2/5] 创建目录结构...${NC}"
mkdir -p boards knowledge-base scripts
echo "  ✅ boards/"
echo "  ✅ knowledge-base/"
echo "  ✅ scripts/"

# 检查配置文件
echo ""
echo -e "${GREEN}[3/5] 检查配置文件...${NC}"
if [ ! -f "config.json" ]; then
    echo -e "${YELLOW}  ⚠️  config.json 不存在，请手动创建或从模板复制${NC}"
else
    echo "  ✅ config.json 已存在"
fi

# 检查数据文件
echo ""
echo -e "${GREEN}[4/5] 检查数据文件...${NC}"
if [ ! -f "boards/all-issues-data.json" ]; then
    echo -e "${YELLOW}  ⚠️  boards/ 数据文件不存在${NC}"
    echo "  请先运行 Claude 生成数据："
    echo "    请帮我从 Jira 拉取数据并生成 boards/ 下的 JSON 文件"
else
    echo "  ✅ boards/ 数据文件已存在"
fi

if [ ! -f "knowledge-base/docs-index.json" ]; then
    echo -e "${YELLOW}  ⚠️  knowledge-base/docs-index.json 不存在${NC}"
    echo "  请先运行 Claude 导入知识库："
    echo "    请帮我把这些飞书文档添加到知识库："
    echo "    https://mi.feishu.cn/docx/xxx"
else
    local count=$(python3 -c "import json; print(json.load(open('knowledge-base/docs-index.json'))['total'])" 2>/dev/null || echo "0")
    echo "  ✅ knowledge-base/docs-index.json ($count 篇文档)"
fi

# 启动服务
echo ""
echo -e "${GREEN}[5/5] 启动服务...${NC}"
PORT=${1:-9000}
echo "  启动 HTTP 服务在端口 $PORT..."
echo "  访问: http://localhost:$PORT"
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  配置完成！${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "下一步："
echo "  1. 编辑 config.json 配置你的团队信息"
echo "  2. 在 Claude 中配置 Jira 和飞书 MCP"
echo "  3. 运行 python3 -m http.server $PORT 启动服务"
echo ""

# 启动服务
python3 -m http.server $PORT
