#!/bin/bash
# Git 部署脚本
# 用法: bash deploy.sh

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  🚀 Git 部署工作台${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 初始化 Git
if [ ! -d ".git" ]; then
    echo -e "${GREEN}[1/4] 初始化 Git 仓库...${NC}"
    git init
    git add -A
    git commit -m "Initial commit: 个人工作台"
    echo "  ✅ Git 仓库已初始化"
else
    echo -e "${GREEN}[1/4] Git 仓库已存在${NC}"
fi

# 创建部署目录
echo -e "${GREEN}[2/4] 准备部署文件...${NC}"
DEPLOY_DIR="/opt/work-workflow"
mkdir -p $DEPLOY_DIR

# 复制文件（排除开发文件）
rsync -av --exclude='data-sql' --exclude='.DS_Store' --exclude='*.log' \
  --exclude='venv' --exclude='__pycache__' --exclude='.git' \
  ./ $DEPLOY_DIR/

echo "  ✅ 文件已复制到 $DEPLOY_DIR"

# 设置权限
echo -e "${GREEN}[3/4] 设置权限...${NC}"
chmod +x $DEPLOY_DIR/setup.sh
chmod +x $DEPLOY_DIR/update.sh
chmod +x $DEPLOY_DIR/deploy.sh

# 初始化用户配置
if [ ! -f "$DEPLOY_DIR/users.json" ]; then
    echo '{"admin":{"password_hash":"'$(echo -n "admin123" | shasum -a 256 | cut -d' ' -f1)'","status":"approved","role":"admin","created":"'$(date -u +%Y-%m-%dT%H:%M:%S)'"}}' > $DEPLOY_DIR/users.json
    echo "  ✅ 已创建默认管理员账号 (admin / admin123)"
fi

echo -e "${GREEN}[4/4] 部署完成！${NC}"
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  部署信息${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "项目目录: $DEPLOY_DIR"
echo ""
echo "启动服务:"
echo "  cd $DEPLOY_DIR"
echo "  python3 auth_server.py 9000"
echo ""
echo "或使用 systemd:"
echo "  sudo cp $DEPLOY_DIR/work-workflow.service /etc/systemd/system/"
echo "  sudo systemctl enable work-workflow"
echo "  sudo systemctl start work-workflow"
echo ""
echo "访问地址: http://$(hostname -I | awk '{print $1}'):9000"
echo ""
echo "管理员登录: admin / admin123"
echo "管理后台: http://$(hostname -I | awk '{print $1}'):9000/admin"
echo ""
echo "用户注册流程:"
echo "  1. 用户访问工作台，点击「注册」"
echo "  2. 输入用户名和密码，提交注册"
echo "  3. 管理员在后台审批通过"
echo "  4. 用户登录即可使用"
echo ""
