from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import uuid
from pathlib import Path
from dotenv import load_dotenv

from api.routes import router as api_router

# 加载环境变量
load_dotenv()

app = FastAPI(
    title="VideoGet API",
    description="万能视频下载器 API",
    version="1.0.0"
)

# CORS 配置
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建下载目录
download_dir = Path(os.getenv("DOWNLOAD_DIR", "./downloads"))
download_dir.mkdir(exist_ok=True)

# 挂载静态文件目录用于下载
if not download_dir.exists():
    download_dir.mkdir(parents=True)
app.mount("/downloads", StaticFiles(directory=str(download_dir)), name="downloads")

# 包含 API 路由
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": "VideoGet API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host=host, port=port, reload=True)
