#!/bin/bash
# 内网服务器部署脚本
# 用法: bash deploy-server.sh [服务器地址] [端口]

SERVER=${1:-"your-server.internal"}
PORT=${2:-"9000"}
REMOTE_DIR="/opt/work-workflow"

echo "========================================="
echo "  🚀 部署工作台到内网服务器"
echo "========================================="
echo ""
echo "目标服务器: $SERVER"
echo "端口: $PORT"
echo "目录: $REMOTE_DIR"
echo ""

# 1. 打包
echo "[1/4] 打包项目..."
cd /Users/stonekhun/Desktop/mi-work/work-workflow
tar -czf /tmp/work-workflow.tar.gz \
  --exclude='data-sql' \
  --exclude='.DS_Store' \
  --exclude='*.log' \
  --exclude='venv' \
  --exclude='__pycache__' \
  .
echo "  ✅ 打包完成: /tmp/work-workflow.tar.gz"

# 2. 上传
echo "[2/4] 上传到服务器..."
scp /tmp/work-workflow.tar.gz $SERVER:/tmp/
echo "  ✅ 上传完成"

# 3. 部署
echo "[3/4] 部署..."
ssh $SERVER << EOF
  sudo mkdir -p $REMOTE_DIR
  sudo tar -xzf /tmp/work-workflow.tar.gz -C $REMOTE_DIR
  sudo chmod +x $REMOTE_DIR/setup.sh
  sudo chmod +x $REMOTE_DIR/update.sh
  echo "  ✅ 文件解压完成"
EOF

# 4. 启动服务
echo "[4/4] 启动服务..."
ssh $SERVER << EOF
  # 检查是否有旧服务
  OLD_PID=\$(lsof -ti:$PORT 2>/dev/null)
  if [ ! -z "\$OLD_PID" ]; then
    echo "  停止旧服务 (PID: \$OLD_PID)..."
    kill \$OLD_PID 2>/dev/null
  fi

  # 启动新服务
  cd $REMOTE_DIR
  nohup python3 -m http.server $PORT > /tmp/work-workflow.log 2>&1 &
  echo "  ✅ 服务已启动 (PID: \$!)"
EOF

echo ""
echo "========================================="
echo "  ✅ 部署完成！"
echo "========================================="
echo ""
echo "访问地址: http://$SERVER:$PORT"
echo ""
echo "管理命令："
echo "  查看日志: ssh $SERVER 'tail -f /tmp/work-workflow.log'"
echo "  重启服务: ssh $SERVER 'cd $REMOTE_DIR && python3 -m http.server $PORT &'"
echo "  更新数据: ssh $SERVER 'cd $REMOTE_DIR && bash update.sh'"
echo ""
