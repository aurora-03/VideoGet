@echo off
chcp 65001 >nul
echo ========================================
echo VideoGet - 推送到 GitHub
echo ========================================
echo.

REM 检查是否已初始化 git
if not exist ".git" (
    echo [1/6] 初始化 Git 仓库...
    git init
    if errorlevel 1 (
        echo 错误: Git 初始化失败！
        pause
        exit /b 1
    )
    echo 完成！
    echo.
)

echo [2/6] 添加文件到暂存区...
git add .
echo 完成！
echo.

echo [3/6] 提交更改...
git commit -m "Initial commit: VideoGet - 万能视频下载器"
if errorlevel 1 (
    echo 提示: 没有新文件需要提交，或已经提交过
)
echo.

echo [4/6] 切换到 main 分支...
git branch -M main
echo 完成！
echo.

echo ========================================
echo 下一步操作：
echo.
echo 1. 在 GitHub 创建新仓库: https://github.com/new
echo    - 仓库名: VideoGet
echo    - 不要勾选 "Initialize this repository"
echo.
echo 2. 然后运行以下命令（替换 YOUR_USERNAME）:
echo.
echo    git remote add origin https://github.com/YOUR_USERNAME/VideoGet.git
echo    git push -u origin main
echo.
echo 或者安装 GitHub CLI 后运行:
echo.
echo    gh repo create VideoGet --public --source=. --remote=origin --push
echo.
echo ========================================
echo.
echo 按任意键打开 GitHub 新建仓库页面...
pause >nul
start https://github.com/new
echo.
echo 完成！
pause
