from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import uuid
from pathlib import Path

from services.downloader import VideoDownloader
from services.task_manager import TaskManager

router = APIRouter()

# 初始化服务
downloader = VideoDownloader()
task_manager = TaskManager()


class VideoURLRequest(BaseModel):
    url: str = Field(..., description="视频 URL")


class VideoInfoResponse(BaseModel):
    title: str
    author: str
    thumbnail: str
    duration: str
    views: str
    formats: List[Dict[str, str]]


class DownloadRequest(BaseModel):
    url: str
    quality: str = "best"
    only_audio: bool = False
    download_subtitle: bool = False


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: int
    filename: Optional[str] = None
    download_url: Optional[str] = None
    error: Optional[str] = None


@router.post("/video/info", response_model=VideoInfoResponse)
async def get_video_info(request: VideoURLRequest):
    """获取视频信息"""
    try:
        info = await downloader.get_video_info(request.url)
        return VideoInfoResponse(**info)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/download")
async def start_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    """开始下载任务"""
    try:
        task_id = str(uuid.uuid4())
        task_manager.create_task(task_id, request.url)

        # 在后台启动下载
        background_tasks.add_task(
            downloader.download_video,
            task_id,
            request.url,
            request.quality,
            request.only_audio,
            request.download_subtitle,
            task_manager
        )

        return {"task_id": task_id, "status": "started"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """获取任务状态"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskStatusResponse(
        task_id=task_id,
        status=task.get("status", "unknown"),
        progress=task.get("progress", 0),
        filename=task.get("filename"),
        download_url=task.get("download_url"),
        error=task.get("error")
    )


@router.get("/download/file/{filename}")
async def download_file(filename: str):
    """下载已完成的文件"""
    download_dir = Path(os.getenv("DOWNLOAD_DIR", "./downloads"))
    file_path = download_dir / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream"
    )


@router.get("/supported-platforms")
async def get_supported_platforms():
    """获取支持的平台列表"""
    return {
        "platforms": [
            "YouTube",
            "Bilibili",
            "抖音",
            "快手",
            "TikTok",
            "Instagram",
            "Twitter/X",
            "Facebook",
            "Vimeo",
            "Twitch",
            "还有 1000+ 平台..."
        ]
    }
