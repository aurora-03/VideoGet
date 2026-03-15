#!/bin/bash

echo "========================================"
echo "VideoGet - 万能视频下载器"
echo "========================================"
echo ""

echo "[1/3] 检查 Python..."
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python，请先安装 Python 3.11+"
    exit 1
fi
echo "Python 检查通过"
echo ""

echo "[2/3] 安装后端依赖..."
cd backend
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
cd ..
echo "后端依赖安装完成"
echo ""

echo "[3/3] 检查 Node.js..."
if ! command -v node &> /dev/null; then
    echo "警告: 未找到 Node.js，前端将无法启动"
    echo "如需启动前端，请先安装 Node.js"
else
    echo "Node.js 检查通过"
    echo "安装前端依赖..."
    cd frontend
    npm install
    cd ..
    echo "前端依赖安装完成"
fi
echo ""

echo "========================================"
echo "安装完成！"
echo ""
echo "启动方式:"
echo "1. 启动后端: cd backend && source venv/bin/activate && python main.py"
echo "2. 启动前端: cd frontend && npm run dev"
echo ""
echo "或者使用 Docker: docker-compose up -d"
echo "========================================"
