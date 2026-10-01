# VideoGet

[English](README.md) | **简体中文**

基于 Vue 3、FastAPI、yt-dlp 和 FFmpeg 的网页视频下载器。粘贴视频链接，查看可用画质，下载视频或提取 MP3 音频。

VideoGet 目前处于早期 MVP 阶段。下载流程已接入真实后端 API，原始项目文档中的部分功能仍处于规划阶段。

## 页面截图

当前界面为中文，使用 SaveAny 品牌名称。以下截图来自实际运行的前端，以及后端成功解析的 Bilibili 视频。

通过 `?lang=zh-CN` 访问中文界面，通过 `?lang=en` 访问英文界面；英文 README 使用英文界面的独立截图。

<p>
  <img src="docs/images/frontend-home.jpg" alt="VideoGet 首页与视频链接输入框" width="350" />
  <img src="docs/images/frontend-video-info.jpg" alt="视频解析结果、画质选择、MP3 和字幕选项" width="350" />
</p>

## 功能思维导图

蓝色分支表示已实现能力，橙色分支表示待开发功能。

![VideoGet 功能思维导图](docs/images/feature-mindmap.zh-CN.png)

[可编辑 SVG](docs/images/feature-mindmap.zh-CN.svg) · [English map](docs/images/feature-mindmap.en.png)

安装 `rsvg-convert` 后，可运行 `python3 scripts/generate-feature-maps.py` 重新生成两种语言的导图。

## 功能

- 解析视频标题、作者、封面、时长和可用画质。
- 下载含音轨的视频，或提取 MP3 音频。
- 通过进度条查看后台下载任务。
- 将可用字幕下载到服务器。
- 使用内置适配器解析抖音和快手的公开移动分享页。
- 可配置服务端 Cookie 和已知视频密码，访问已有授权的内容。
- 响应式 Vue 界面及 Docker Compose 配置。

AI 总结、字幕翻译、完整批量下载流程、账户、支付及持久化下载历史尚未实现。字幕文件会保存在服务器，但界面目前只交付媒体文件。

## 平台支持

| 平台 | 实现方式 | 样例验证结果 |
| --- | --- | --- |
| YouTube | yt-dlp | 下载及文件交付通过 |
| Bilibili（哔哩哔哩） | yt-dlp，附加封面回退 | 下载及文件交付通过 |
| 抖音 | 内置移动分享页解析 | 视频及 MP3 下载通过 |
| 快手 | 内置移动分享页解析 | 下载及文件交付通过 |
| TikTok | yt-dlp | 下载及文件交付通过 |
| Instagram | yt-dlp | 下载及文件交付通过 |
| Twitter / X | yt-dlp | 下载及文件交付通过 |
| Facebook | yt-dlp；分辨率未知时使用最佳画质 | 下载及文件交付通过 |
| Vimeo | yt-dlp，附加播放器地址回退 | 密码保护样例在提供其公开测试密码后通过 |
| Twitch | yt-dlp | 视频片段下载及文件交付通过 |

以上结果来自 `dev` 分支，测试使用 yt-dlp `2026.8.19`。成功样例均检查了文件交付，并通过 FFprobe 验证媒体有效；不代表这些平台的所有视频都能下载。其他 yt-dlp 支持的网站也可能适用。

抖音和快手适配器支持视频作品，不支持图文作品。抖音解析会保留游客会话 Cookie，并对暂时没有视频数据的响应进行有限重试。两个适配器均不再依赖此前缺失的 `backend/third_party` 目录。

Vimeo 原始测试样例需要密码；另一个公开样例返回了 DRM 保护的视频流，无法下载。私密、需要登录、密码保护、地区限制及 DRM 内容仍受原有访问条件限制；不支持 DRM 视频下载。

## 环境要求

- Python 3.11 或更高版本。
- Node.js 20 或更高版本及 npm。
- `PATH` 中可调用 FFmpeg 和 FFprobe，用于媒体合并、MP3 转换和真实下载验证。
- 使用容器时需要 Docker 和 Docker Compose，后端镜像已包含 FFmpeg。

## 快速开始

以下命令使用 Bash 或 zsh。默认版本位于 `main` 分支，后续开发使用 `dev` 分支。

```bash
git clone https://github.com/aurora-03/VideoGet.git
cd VideoGet
```

### 本地开发

在一个终端启动后端：

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python main.py
```

Windows PowerShell 中使用 `.\.venv\Scripts\Activate.ps1` 激活虚拟环境。

在另一个终端，从仓库根目录启动前端：

```bash
cd frontend
npm ci
npm run dev
```

- 前端：[http://localhost:3000](http://localhost:3000)
- 后端：[http://localhost:8000](http://localhost:8000)
- API 文档：[Swagger UI](http://localhost:8000/docs) / [ReDoc](http://localhost:8000/redoc)

### Docker Compose

从仓库根目录运行：

```bash
cp backend/.env.example backend/.env
mkdir -p backend/downloads
docker compose up --build -d
```

前后端端口与本地开发相同，下载文件持久保存在 `backend/downloads`。

前端目前直接请求 `http://localhost:8000`。部署到远程服务器、使用 HTTPS 或通过其他设备访问前，需要配置前端 API 地址及后端 CORS 来源。前端容器目前使用 Vite 预览服务，生产部署配置仍需完善。

## 配置

后端在初始化下载服务前加载 `backend/.env`。

| 变量 | 默认值 | 用途 |
| --- | --- | --- |
| `HOST` | `0.0.0.0` | 后端监听地址 |
| `PORT` | `8000` | 后端端口 |
| `DOWNLOAD_DIR` | `./downloads` | 媒体存储目录，相对于后端工作目录 |
| `ALLOWED_ORIGINS` | `.env.example` 中为 `http://localhost:3000,http://127.0.0.1:3000` | 逗号分隔的 CORS 来源 |
| `YTDLP_COOKIE_FILE` | 未设置 | 已有授权的 Netscape 格式 Cookie 文件路径 |
| `YTDLP_VIDEO_PASSWORD` | 未设置 | 密码保护视频的已知密码 |

`.env.example` 中的 `MAX_FILE_SIZE` 目前尚未执行限制。任务状态保存在内存中，后端重启后丢失；限流和自动文件清理尚未实现。

Cookie 文件需要后端可读。Docker 中须使用容器内的路径，并以只读卷挂载文件。请勿将 Cookie 文件或密码提交到 Git。

## API

| 方法 | 接口 | 用途 |
| --- | --- | --- |
| `POST` | `/api/video/info` | 解析视频链接，返回信息及画质选项 |
| `GET` | `/api/video/thumbnail?url=...` | 代理获取封面图片 |
| `POST` | `/api/download` | 创建后台下载任务 |
| `GET` | `/api/task/{task_id}` | 获取任务状态、进度和完成后的文件地址 |
| `GET` | `/api/download/file/{filename}` | 获取已下载的文件 |
| `GET` | `/api/supported-platforms` | 返回项目声明的平台列表 |
| `GET` | `/health` | 基础后端健康检查 |

文件先下载到服务器，再交付到浏览器。画质选择以请求的分辨率为上限；分辨率未知的视频提供“最佳画质”选项。

## 测试与构建

激活后端虚拟环境后，从仓库根目录安装开发依赖并运行回归测试：

```bash
python -m pip install -r backend/requirements-dev.txt
PYTHONPATH=backend python -m unittest discover -s backend/tests -v
```

按需运行连接真实后端和平台链接的网络测试：

```bash
python backend/tests/live_platforms.py --platform Facebook 抖音 快手
YTDLP_VIDEO_PASSWORD=youtube-dl python backend/tests/live_platforms.py --platform Vimeo
python backend/tests/live_platforms.py --platform YouTube --audio
python backend/tests/live_platforms.py --platform Vimeo --url https://vimeo.com/VIDEO_ID
```

默认 Vimeo 样例是 yt-dlp 官方的密码保护测试视频，公开测试密码为 `youtube-dl`。这是测试样例的密码，并非其他视频的默认密码。

真实测试会下载视频、验证文件交付，并使用 FFprobe 检查媒体。报告及下载文件保存在 `backend/downloads/verification-*`；样例可能随时间失效。脚本还支持 `--timeout` 和 `--output` 参数。

构建前端：

```bash
cd frontend
npm run build
```

## 项目结构

```text
VideoGet/
├── frontend/
│   ├── src/App.vue              # 下载流程及任务轮询
│   ├── src/components/          # Vue 界面组件
│   └── package.json
├── backend/
│   ├── api/routes.py            # FastAPI 接口
│   ├── services/downloader.py   # yt-dlp 集成及媒体交付
│   ├── services/share_parser.py # 抖音和快手适配器
│   ├── services/task_manager.py # 内存任务状态
│   ├── tests/                   # 回归测试及按需运行的真实测试
│   ├── downloads/               # 生成的媒体及测试报告，Git 忽略
│   ├── main.py
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── .env.example
├── docker-compose.yml
├── docs/images/                 # 页面截图与双语功能导图
├── scripts/generate-feature-maps.py # 重新生成 SVG 和 PNG 功能导图
├── README.md                    # 默认英文文档
└── README.zh-CN.md               # 简体中文文档
```

[PRD.md](PRD.md)、[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) 和 [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) 为原始规划和设计资料，部分内容早于当前实现；现有能力以代码和本 README 为准。

## 文档语言

`README.md` 默认使用英文，`README.zh-CN.md` 提供简体中文。修改能力、配置或启动说明时，请同步两份文档。新增译文可使用 `README.<语言代码>.md` 命名，并在各 README 顶部的语言切换链接中列出。

## 贡献与使用

欢迎提交 Issue 和 Pull Request。当前开发使用 `dev` 分支，修改时请附上相关回归验证。

仅下载已有权限保存的内容，并遵守平台条款及版权要求。原始项目文档声明使用 MIT 许可证，但当前仓库尚未包含独立的 `LICENSE` 文件。
