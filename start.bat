@echo off
echo ========================================
echo VideoGet - 万能视频下载器
echo ========================================
echo.

echo [1/3] 检查 Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.11+
    pause
    exit /b 1
)
echo Python 检查通过
echo.

echo [2/3] 安装后端依赖...
cd backend
if not exist venv (
    echo 创建虚拟环境...
    python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt
cd ..
echo 后端依赖安装完成
echo.

echo [3/3] 检查 Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo 警告: 未找到 Node.js，前端将无法启动
    echo 如需启动前端，请先安装 Node.js
) else (
    echo Node.js 检查通过
    echo 安装前端依赖...
    cd frontend
    call npm install
    cd ..
    echo 前端依赖安装完成
)
echo.

echo ========================================
echo 安装完成！
echo.
echo 启动方式:
echo 1. 启动后端: cd backend ^&^& venv\Scripts\activate ^&^& python main.py
echo 2. 启动前端: cd frontend ^&^& npm run dev
echo.
echo 或者使用 Docker: docker-compose up -d
echo ========================================
pause
