from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field, SecretStr, ValidationError
from typing import Optional, List, Dict, Any, Literal
import os
import uuid
import re
from pathlib import Path
from urllib.parse import quote, urlparse
from urllib.request import Request as UrlRequest, urlopen

from services.downloader import VideoDownloader
from services.task_manager import TaskManager
from services.video_analysis import VideoAnalysis
from services.ai_client import AIClient, SpeechClient, ConfigurationError, capabilities
from services.ai_client import require_address
from services.model_settings import COOKIE, LIFETIME, store as model_store, initial_profile, public_profile, use_settings

router = APIRouter()

# 初始化服务
downloader = VideoDownloader()
task_manager = TaskManager()
video_analysis = VideoAnalysis(downloader, task_manager)


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
    if "protected by a password" in lowered or "wrong video password" in lowered:
        return "该视频受密码保护，请在服务端配置 YTDLP_VIDEO_PASSWORD 后重试"
    if "only works when logged-in" in lowered or "login required" in lowered:
        return "该视频需要登录，请在服务端配置 YTDLP_COOKIE_FILE 后重试"
    if "requested format is not available" in lowered:
        return "所选画质当前不可用，请重新解析并选择其他画质"
    if "drm protected" in lowered:
        return "该视频没有可下载的非 DRM 格式"
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
    stage: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    subtitle_files: List[Dict[str, str]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class AnalysisRequest(BaseModel):
    url: str
    mode: Literal['subtitles', 'transcribe', 'translate', 'summarize'] = 'subtitles'
    source_language: Literal['auto', 'zh', 'en', 'ja', 'ko', 'es', 'fr', 'de'] = 'auto'
    target_language: Literal['zh', 'en', 'ja', 'ko', 'es', 'fr', 'de'] = 'zh'
    source_task_id: Optional[uuid.UUID] = None
    allow_transcription: bool = False


class ModelConfigRequest(BaseModel):
    model_config = {'extra': 'forbid'}
    provider: Literal['openai', 'custom', 'ollama'] = 'custom'
    protocol: Literal['openai', 'anthropic'] = 'openai'
    base_url: str = Field(default='', max_length=2048)
    api_key: Optional[SecretStr] = None
    clear_api_key: bool = False
    translation_model: str = Field(default='', max_length=200)
    summary_model: str = Field(default='', max_length=200)
    max_output_tokens: int = Field(default=16384, ge=256, le=32768)
    asr_backend: Literal['api', 'local'] = 'api'
    asr_base_url: str = Field(default='', max_length=2048)
    asr_api_key: Optional[SecretStr] = None
    clear_asr_api_key: bool = False
    asr_model: str = Field(default='', max_length=200)


def session_profile(request):
    token = request.cookies.get(COOKIE)
    profile = model_store.get(token) if token else None
    if (token or request.headers.get('x-model-session') == 'required') and profile is None:
        raise HTTPException(status_code=409, detail='模型配置会话已过期，请刷新页面重新配置')
    return profile


def set_model_cookie(response, request, token):
    response.set_cookie(COOKIE, token, max_age=LIFETIME, httponly=True,
                        secure=request.url.scheme == 'https', samesite='strict', path='/api')
    response.headers['Cache-Control'] = 'no-store'


@router.get('/ai/settings')
async def get_model_settings(request: Request, response: Response):
    token = request.cookies.get(COOKIE)
    profile = model_store.get(token) if token else None
    if profile is None:
        profile = initial_profile()
        token = model_store.save(None, profile)
    set_model_cookie(response, request, token)
    return public_profile(profile)


@router.post('/ai/settings')
async def save_model_settings(request: Request, response: Response):
    origin = request.headers.get('origin')
    allowed = {value.strip() for value in os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')}
    allowed.add(str(request.base_url).rstrip('/'))
    if origin and origin not in allowed:
        raise HTTPException(status_code=403, detail='不允许从此页面保存模型配置')
    try:
        payload = ModelConfigRequest.model_validate(await request.json())
    except (ValidationError, ValueError):
        raise HTTPException(status_code=422, detail='模型配置参数无效，请检查地址、模型和 Token 上限')
    old = session_profile(request) or initial_profile()
    base_url, asr_base_url = payload.base_url.strip().rstrip('/'), payload.asr_base_url.strip().rstrip('/')
    try:
        if base_url:
            require_address(base_url)
        if asr_base_url:
            require_address(asr_base_url)
    except ConfigurationError as error:
        raise HTTPException(status_code=400, detail=str(error))
    same_service = base_url == old['CLOUD_BASE_URL'].rstrip('/') and payload.protocol == old['CLOUD_PROTOCOL'] and payload.provider == old['AI_PROVIDER']
    entered_key = payload.api_key.get_secret_value().strip() if payload.api_key else ''
    key = entered_key or (old['CLOUD_API_KEY'] if same_service else '')
    if payload.clear_api_key or payload.provider == 'ollama':
        key = ''
    entered_asr_key = payload.asr_api_key.get_secret_value().strip() if payload.asr_api_key else ''
    same_asr_service = (asr_base_url or base_url) == (old['ASR_BASE_URL'].rstrip('/') or old['CLOUD_BASE_URL'].rstrip('/'))
    asr_key = entered_asr_key or (old['ASR_API_KEY'] if same_asr_service else '')
    if payload.clear_asr_api_key:
        asr_key = ''
    if len(key) > 8192 or len(asr_key) > 8192:
        raise HTTPException(status_code=400, detail='API Key 长度无效')
    profile = {**old, 'AI_PROVIDER': payload.provider, 'CLOUD_PROTOCOL': payload.protocol,
        'CLOUD_BASE_URL': base_url, 'CLOUD_API_KEY': key,
        'CLOUD_TRANSLATION_MODEL': payload.translation_model.strip(),
        'CLOUD_SUMMARY_MODEL': payload.summary_model.strip(),
        'AI_BASE_URL': base_url if payload.provider == 'ollama' else '',
        'AI_API_KEY': '', 'AI_MODEL': payload.summary_model.strip() if payload.provider == 'ollama' else '',
        'OPENAI_API_KEY': '', 'OPENAI_BASE_URL': '',
        'AI_MAX_OUTPUT_TOKENS': str(payload.max_output_tokens), 'ASR_BACKEND': payload.asr_backend,
        'ASR_BASE_URL': asr_base_url, 'ASR_API_KEY': asr_key, 'ASR_MODEL': payload.asr_model.strip(), 'CLOUD_ASR_MODEL': ''}
    token = model_store.save(request.cookies.get(COOKIE), profile)
    set_model_cookie(response, request, token)
    with use_settings(profile):
        state = capabilities()
    return {'settings': public_profile(profile), 'capabilities': state}


@router.get('/ai/capabilities')
async def get_ai_capabilities(request: Request):
    with use_settings(session_profile(request)):
        return capabilities()


@router.post('/video/analyze')
async def start_analysis(payload: AnalysisRequest, background_tasks: BackgroundTasks, request: Request):
    url = _extract_input_url(payload.url)
    if not re.match(r'^https?://', url, flags=re.IGNORECASE):
        raise HTTPException(status_code=400, detail='地址无效，请输入正确的视频链接')
    source_id = str(payload.source_task_id) if payload.source_task_id else None
    if source_id:
        source = task_manager.get_task(source_id)
        if not source or source.get('url') != url or not (source.get('result') or {}).get('segments'):
            raise HTTPException(status_code=400, detail='已有文本任务不可用，请重新提取字幕')
    try:
        profile = session_profile(request)
        with use_settings(profile):
            if payload.mode in {'translate', 'summarize'}:
                AIClient().require_text(payload.mode)
            if payload.mode == 'transcribe':
                SpeechClient().require()
    except ConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error))
    if not video_analysis.slots.acquire(blocking=False):
        raise HTTPException(status_code=429, detail='分析任务繁忙，请稍后重试')
    task_id = str(uuid.uuid4())
    task_manager.create_task(task_id, url)
    background_tasks.add_task(video_analysis.run, task_id, url, payload.mode, payload.source_language,
                              payload.target_language, source_id, payload.allow_transcription, profile)
    return {'task_id': task_id, 'status': 'started'}


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
        error=_format_error_message(task.get("error")) if task.get("error") else None,
        stage=task.get('stage'),
        result=task.get('result'),
        subtitle_files=task.get('subtitle_files', []),
        warnings=task.get('warnings', [])
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
