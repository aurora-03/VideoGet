# VideoGet

**English** | [简体中文](README.zh-CN.md)

A web-based video downloader built with Vue 3, FastAPI, yt-dlp, and FFmpeg. Paste a video link, inspect its available quality options, and download the video or extract an MP3.

VideoGet is an early MVP. The download workflow uses real backend APIs; some features advertised in the original project documents are still planned.

## Features

- Parse video titles, authors, thumbnails, durations, and available quality options.
- Download videos with audio, or extract audio as MP3.
- Track background downloads with a progress indicator.
- Download available subtitles on the server.
- Parse public Douyin and Kuaishou mobile share pages with built-in adapters.
- Use optional server-side cookies and known video passwords for authorized content.
- Responsive Vue interface and Docker Compose setup.

AI summaries, subtitle translation, a complete batch-download workflow, accounts, payments, and persistent download history are not implemented. Subtitle files are saved on the server, but the interface currently delivers only the media file.

## Platform support

| Platform | Implementation | Sample verification |
| --- | --- | --- |
| YouTube | yt-dlp | Download and file delivery passed |
| Bilibili | yt-dlp with thumbnail fallback | Download and file delivery passed |
| Douyin / 抖音 | Built-in mobile share-page parser | Video and MP3 downloads passed |
| Kuaishou / 快手 | Built-in mobile share-page parser | Download and file delivery passed |
| TikTok | yt-dlp | Download and file delivery passed |
| Instagram | yt-dlp | Download and file delivery passed |
| Twitter / X | yt-dlp | Download and file delivery passed |
| Facebook | yt-dlp; best-quality option when dimensions are unknown | Download and file delivery passed |
| Vimeo | yt-dlp with player-URL fallback | Password-protected fixture passed with its documented password |
| Twitch | yt-dlp | Clip download and file delivery passed |

These results describe individual samples tested on the `dev` branch with yt-dlp `2026.8.19`. Successful samples were checked for file delivery and valid media using FFprobe. They do not guarantee that every video on a platform can be downloaded. Other websites supported by yt-dlp may also work.

Douyin and Kuaishou adapters support video posts, not image galleries. Douyin reuses guest-session cookies and retries temporary empty responses. Neither adapter requires the previously missing `backend/third_party` directory.

Vimeo's original test sample requires a password. Another public sample exposed DRM-protected streams and could not be downloaded. Private, login-required, password-protected, region-restricted, and DRM-protected content remain subject to their original restrictions; DRM downloads are not supported.

## Requirements

- Python 3.11 or newer.
- Node.js 20 or newer and npm.
- FFmpeg and FFprobe available on `PATH` for media merging, MP3 conversion, and live verification.
- Docker with Docker Compose, if using containers. The backend image includes FFmpeg.

## Quick start

The commands below use Bash or zsh. Current development changes are on `dev`.

```bash
git clone --branch dev https://github.com/aurora-03/VideoGet.git
cd VideoGet
```

### Local development

Start the backend in one terminal:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python main.py
```

On Windows PowerShell, activate the environment with `.\.venv\Scripts\Activate.ps1`.

Start the frontend in a second terminal, from the repository root:

```bash
cd frontend
npm ci
npm run dev
```

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend: [http://localhost:8000](http://localhost:8000)
- API documentation: [Swagger UI](http://localhost:8000/docs) / [ReDoc](http://localhost:8000/redoc)

### Docker Compose

From the repository root:

```bash
cp backend/.env.example backend/.env
mkdir -p backend/downloads
docker compose up --build -d
```

The frontend and backend use the same ports as local development. Downloaded files are persisted in `backend/downloads`.

The frontend currently calls `http://localhost:8000` directly. Before hosting remotely, using HTTPS, or accessing from another device, configure the frontend API address and backend CORS origins. The frontend container currently runs Vite's preview server; production deployment configuration still needs improvement.

## Configuration

Backend settings are loaded from `backend/.env` before download services are initialized.

| Variable | Default | Purpose |
| --- | --- | --- |
| `HOST` | `0.0.0.0` | Backend bind address |
| `PORT` | `8000` | Backend port |
| `DOWNLOAD_DIR` | `./downloads` | Media storage, relative to the backend working directory |
| `ALLOWED_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` in `.env.example` | Comma-separated CORS origins |
| `YTDLP_COOKIE_FILE` | Unset | Path to an authorized Netscape-format cookie file |
| `YTDLP_VIDEO_PASSWORD` | Unset | Known password for password-protected videos |

`MAX_FILE_SIZE` appears in `.env.example`, but is not currently enforced. Task state is held in memory and is lost when the backend restarts. Rate limiting and automatic file cleanup are not implemented.

Cookie files must be readable by the backend. In Docker, use a container-visible path and mount the file read-only. Keep cookie files and passwords out of Git.

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/video/info` | Parse a video URL and return metadata and quality options |
| `GET` | `/api/video/thumbnail?url=...` | Proxy a thumbnail image |
| `POST` | `/api/download` | Create a background download task |
| `GET` | `/api/task/{task_id}` | Retrieve task status, progress, and the completed file URL |
| `GET` | `/api/download/file/{filename}` | Retrieve a downloaded file |
| `GET` | `/api/supported-platforms` | Return the project's declared platform list |
| `GET` | `/health` | Basic backend health check |

Files are first downloaded to the server, then delivered to the browser. Quality selection uses the requested resolution as an upper bound; videos without known dimensions offer a “best quality” option.

## Tests and builds

Install development dependencies and run regression tests from the repository root, with your backend virtual environment active:

```bash
python -m pip install -r backend/requirements-dev.txt
PYTHONPATH=backend python -m unittest discover -s backend/tests -v
```

Run opt-in live tests against the actual backend and platform URLs:

```bash
python backend/tests/live_platforms.py --platform Facebook 抖音 快手
YTDLP_VIDEO_PASSWORD=youtube-dl python backend/tests/live_platforms.py --platform Vimeo
python backend/tests/live_platforms.py --platform YouTube --audio
python backend/tests/live_platforms.py --platform Vimeo --url https://vimeo.com/VIDEO_ID
```

The default Vimeo fixture is yt-dlp's password-protected test video, whose documented test password is `youtube-dl`. This is a test fixture password, not a default password for other videos.

Live tests perform real downloads, verify file delivery, and inspect media with FFprobe. Reports and downloaded files are saved under `backend/downloads/verification-*`. Samples may become unavailable over time. The script also accepts `--timeout` and `--output`.

Build the frontend:

```bash
cd frontend
npm run build
```

## Project layout

```text
VideoGet/
├── frontend/
│   ├── src/App.vue              # Download workflow and task polling
│   ├── src/components/          # Vue interface components
│   └── package.json
├── backend/
│   ├── api/routes.py            # FastAPI endpoints
│   ├── services/downloader.py   # yt-dlp integration and media delivery
│   ├── services/share_parser.py # Douyin and Kuaishou adapters
│   ├── services/task_manager.py # In-memory task state
│   ├── tests/                   # Regression and opt-in live tests
│   ├── downloads/               # Generated media and reports; ignored by Git
│   ├── main.py
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── .env.example
├── docker-compose.yml
├── README.md                    # English documentation, default
└── README.zh-CN.md               # Simplified Chinese documentation
```

[PRD.md](PRD.md), [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md), and [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) contain original planning and design material. Some descriptions predate the current implementation; use the code and this README for current capabilities.

## Documentation languages

English is the default in `README.md`; Simplified Chinese is maintained in `README.zh-CN.md`. Keep both versions aligned when changing capabilities, configuration, or setup instructions. Additional translations can follow the `README.<language-code>.md` naming convention and be linked in each README's language selector.

## Contributing and usage

Issues and pull requests are welcome. Use the `dev` branch for current development and include relevant regression checks with changes.

Download only content you are authorized to save, and comply with the relevant platform terms and copyright requirements. The original project documentation states an MIT license, but this checkout does not yet include a standalone `LICENSE` file.
