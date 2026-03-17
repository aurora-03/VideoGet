from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import uuid
import re
from pathlib import Path
from urllib.parse import quote, urlparse
from urllib.request import Request as UrlRequest, urlopen

from services.downloader import VideoDownloader
from services.task_manager import TaskManager

router = APIRouter()

# 初始化服务
downloader = VideoDownloader()
task_manager = TaskManager()


def _format_error_message(err: Any) -> str:
    raw = str(err or "").strip()
    message = re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', raw).strip()
    message = re.sub(r'^ERROR:\s*', '', message, flags=re.IGNORECASE).strip()
    message = re.sub(r'\s*\(caused by <[^>]+>\)\s*$', '', message, flags=re.IGNORECASE).strip()
    lowered = message.lower()
    if "unable to download webpage" in lowered and "http error 404" in lowered:
        return "链接不存在或已失效，请检查视频地址后重试"
    if "unsupported url" in lowered:
        return "暂不支持该链接格式，请确认是可访问的视频地址"
    if "invalid url" in lowered or "not a valid url" in lowered:
        return "地址无效，请输入正确的视频链接"
    if "fresh cookies" in lowered or "抖音视频解析失败" in lowered:
        return "该抖音链接当前受风控，请使用抖音App分享链接后重试"
    if "抖音视频当前受限" in message:
        return "该抖音视频当前受限，无法下载，请在抖音App打开并重新分享后重试"
    return message or "解析失败，请检查链接是否正确"


def _extract_input_url(raw: str) -> str:
    text = str(raw or "").strip()
    if not text:
        return ""
    matched = re.search(r'https?://[^\s<>"\'`]+', text, flags=re.IGNORECASE)
    candidate = matched.group(0) if matched else text
    return re.sub(r"[)\]}>，。！？、；：'\"`]+$", "", candidate)


class VideoURLRequest(BaseModel):
    url: str = Field(..., description="视频 URL")


class VideoInfoResponse(BaseModel):
    url: str
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
async def get_video_info(payload: VideoURLRequest, request: Request):
    """获取视频信息"""
    try:
        cleaned_url = _extract_input_url(payload.url)
        if not cleaned_url:
            raise HTTPException(status_code=400, detail="地址无效，请输入正确的视频链接")
        if not re.match(r'^https?://', cleaned_url, flags=re.IGNORECASE):
            raise HTTPException(status_code=400, detail="地址无效，请输入正确的视频链接")
        info = await downloader.get_video_info(cleaned_url)
        thumbnail = info.get("thumbnail", "")
        if thumbnail.startswith("http://") or thumbnail.startswith("https://"):
            encoded = quote(thumbnail, safe="")
            info["thumbnail"] = f"{str(request.base_url).rstrip('/')}/api/video/thumbnail?url={encoded}"
        return VideoInfoResponse(**info)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=_format_error_message(e))


@router.get("/video/thumbnail")
async def get_video_thumbnail(url: str):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise HTTPException(status_code=400, detail="Invalid thumbnail URL")
        headers = {'User-Agent': 'Mozilla/5.0'}
        if 'hdslb.com' in parsed.netloc:
            headers['Referer'] = 'https://www.bilibili.com/'
        req = UrlRequest(url, headers=headers)
        with urlopen(req, timeout=10) as resp:
            content = resp.read()
            media_type = resp.headers.get_content_type() or "image/jpeg"
            return Response(content=content, media_type=media_type)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=_format_error_message(e))


@router.post("/download")
async def start_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    """开始下载任务"""
    try:
        cleaned_url = _extract_input_url(request.url)
        if not cleaned_url:
            raise HTTPException(status_code=400, detail="地址无效，请输入正确的视频链接")
        if not re.match(r'^https?://', cleaned_url, flags=re.IGNORECASE):
            raise HTTPException(status_code=400, detail="地址无效，请输入正确的视频链接")
        task_id = str(uuid.uuid4())
        task_manager.create_task(task_id, cleaned_url)

        # 在后台启动下载
        background_tasks.add_task(
            downloader.download_video,
            task_id,
            cleaned_url,
            request.quality,
            request.only_audio,
            request.download_subtitle,
            task_manager
        )

        return {"task_id": task_id, "status": "started"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=_format_error_message(e))


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
        error=_format_error_message(task.get("error")) if task.get("error") else None
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
