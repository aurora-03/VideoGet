# 上传到 GitHub 指南

## 方式一：使用 GitHub CLI（最简单）

### 1. 安装 GitHub CLI

访问 https://cli.github.com/ 下载并安装

### 2. 登录 GitHub

```bash
gh auth login
```

### 3. 创建仓库并推送

```bash
cd E:\project_bymyself\video-get

# 初始化 git
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: VideoGet - 万能视频下载器"

# 创建仓库并推送
gh repo create VideoGet --public --source=. --remote=origin --push
```

---

## 方式二：手动步骤

### 步骤 1：在 GitHub 创建仓库

1. 访问 https://github.com/new
2. 仓库名称：`VideoGet`
3. 描述：`万能视频下载器 - 支持 1800+ 平台，一键保存视频`
4. 选择 **Public** 或 **Private**
5. **不要**勾选 "Initialize this repository"
6. 点击 **Create repository**

### 步骤 2：本地提交并推送

在 `E:\project_bymyself\video-get` 目录下执行：

```bash
# 1. 初始化 Git
git init

# 2. 添加所有文件
git add .

# 3. 首次提交
git commit -m "Initial commit: VideoGet - 万能视频下载器"

# 4. 重命名分支为 main
git branch -M main

# 5. 添加远程仓库（替换 YOUR_USERNAME）
git remote add origin https://github.com/YOUR_USERNAME/VideoGet.git

# 6. 推送到 GitHub
git push -u origin main
```

---

## 方式三：使用 GitHub Desktop

1. 下载 GitHub Desktop：https://desktop.github.com/
2. 打开 GitHub Desktop
3. File -> Add Local Repository
4. 选择 `E:\project_bymyself\video-get`
5. 点击 "Publish repository"

---

## 项目包含的内容

✅ 前端（Vue 3 + Tailwind CSS）
- 按设计图布局的 SaveAny 界面
- 蓝白配色风格
- 响应式设计
- 完整的组件：导航、Hero、下载、功能、定价、页脚

✅ 后端（Python FastAPI + yt-dlp）
- FastAPI 框架
- yt-dlp 完整封装
- 任务管理系统
- RESTful API

✅ 部署配置
- Dockerfile
- docker-compose.yml
- 启动脚本

---

## .gitignore 已配置

已自动排除：
- `node_modules/`
- `venv/`
- `.env`
- `backend/downloads/*`（视频文件）
- `analyze_website.py`（临时文件）
- `website_screenshot.png`（临时文件）
- `website_info.json`（临时文件）
