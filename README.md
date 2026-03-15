# VideoGet - 万能视频下载器

一个现代化的视频下载网站，支持 1000+ 平台，提供 4K 高清下载、AI 视频总结、字幕翻译等功能。

## ✨ 功能特性

- 🚀 **支持 1000+ 平台** - YouTube、Bilibili、抖音、快手、TikTok 等
- 🎬 **4K 高清画质** - 最高支持 8K 画质下载
- ⚡ **极速下载** - 多线程加速，充分利用带宽
- 📦 **批量下载** - 一键下载整个播放列表/频道
- 🤖 **AI 视频总结** - 智能生成视频摘要（Pro 功能）
- 🌐 **字幕翻译** - 自动下载并翻译字幕（Pro 功能）
- 📱 **响应式设计** - 手机电脑都能用

## 🛠️ 技术栈

### 前端
- Vue 3 - 渐进式 JavaScript 框架
- Tailwind CSS - 实用优先的 CSS 框架
- Vite - 下一代前端构建工具

### 后端
- Python 3.11+
- FastAPI - 高性能 Web 框架
- yt-dlp - 强大的视频下载库
- Uvicorn - ASGI 服务器

### 部署
- Docker + Docker Compose

## 🚀 快速开始

### 方式一：使用 Docker（推荐）

```bash
# 克隆项目
git clone <repository-url>
cd video-get

# 复制环境变量文件
cd backend
cp .env.example .env
cd ..

# 启动服务
docker-compose up -d

# 访问应用
# 前端: http://localhost:3000
# 后端 API: http://localhost:8000
```

### 方式二：本地开发

#### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

#### 后端开发

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 复制环境变量
cp .env.example .env

# 启动开发服务器
python main.py
```

## 📁 项目结构

```
video-get/
├── frontend/                 # 前端项目
│   ├── src/
│   │   ├── components/      # Vue 组件
│   │   │   ├── NavBar.vue
│   │   │   ├── HeroSection.vue
│   │   │   ├── DownloadSection.vue
│   │   │   ├── FeaturesSection.vue
│   │   │   ├── PricingSection.vue
│   │   │   └── Footer.vue
│   │   ├── App.vue
│   │   ├── main.js
│   │   └── style.css
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── Dockerfile
├── backend/                  # 后端项目
│   ├── api/                 # API 路由
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── services/            # 业务逻辑
│   │   ├── __init__.py
│   │   ├── downloader.py    # yt-dlp 封装
│   │   └── task_manager.py  # 任务管理
│   ├── downloads/           # 下载文件存储
│   ├── main.py              # 应用入口
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── docker-compose.yml
├── DESIGN_SYSTEM.md         # 设计系统文档
└── README.md
```

## 🎨 设计系统

项目采用**蓝色极简科技风格**。

主要特点：
- 蓝白配色 + 简洁卡片
- 蓝色主色调 + 柔和阴影
- 流畅的微交互动画
- 响应式设计，支持手机端

详细设计规范请参考 [DESIGN_SYSTEM.md](./DESIGN_SYSTEM.md)。

## 🔧 API 文档

启动后端服务后，访问以下地址查看 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 主要 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/video/info` | POST | 获取视频信息 |
| `/api/download` | POST | 开始下载任务 |
| `/api/task/{task_id}` | GET | 获取任务状态 |
| `/api/download/file/{filename}` | GET | 下载已完成的文件 |
| `/api/supported-platforms` | GET | 获取支持的平台列表 |

## ⚠️ 免责声明

1. 本项目仅供学习和个人使用
2. 请遵守各视频平台的服务条款
3. 用户下载的内容由用户自行负责
4. 请勿将下载的内容用于商业用途
5. 如有版权问题，请联系相关平台

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**注意**: 使用本工具下载视频时，请确保遵守相关法律法规和平台规则。
