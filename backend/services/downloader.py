import asyncio
import os
import yt_dlp
from pathlib import Path
from typing import Dict, Any, List, Optional
import uuid
import re
import json
from urllib.parse import quote, quote_plus
from urllib.request import Request, urlopen
from urllib.parse import urlparse, parse_qs, urlencode

from services.share_parser import SharePageParser


class VideoDownloader:
    """视频下载服务 - 封装 yt-dlp"""

    def __init__(self):
        self.download_dir = Path(os.getenv("DOWNLOAD_DIR", "./downloads"))
        self.download_dir.mkdir(parents=True, exist_ok=True)

    class _YDLLogger:
        def debug(self, msg):
            return None
        def warning(self, msg):
            return None
        def error(self, msg):
            return None

    async def get_video_info(self, url: str) -> Dict[str, Any]:
        """获取视频信息"""
        def _get_info():
            with yt_dlp.YoutubeDL(self._ydl_options()) as ydl:
                info = self._extract_media(ydl, url, download=False)
                return self._format_video_info(info, url)

        return await asyncio.to_thread(_get_info)

    def _ydl_options(self):
        options = {
            'quiet': True, 'no_warnings': True, 'extract_flat': False,
            'noplaylist': True, 'socket_timeout': 20, 'retries': 2,
            'extractor_retries': 2, 'logger': self._YDLLogger(),
        }
        cookie_file = os.getenv('YTDLP_COOKIE_FILE')
        if cookie_file:
            if not Path(cookie_file).is_file():
                raise ValueError('YTDLP_COOKIE_FILE 指向的 Cookie 文件不存在')
            options['cookiefile'] = cookie_file
        password = os.getenv('YTDLP_VIDEO_PASSWORD')
        if password:
            options['videopassword'] = password
        return options

    @staticmethod
    def _vimeo_player_url(url):
        parsed = urlparse(url)
        if parsed.hostname not in {'vimeo.com', 'www.vimeo.com'}:
            return None
        match = re.fullmatch(r'/(\d+)(?:/([a-zA-Z0-9]+))?/?', parsed.path)
        if not match:
            return None
        player = f'https://player.vimeo.com/video/{match.group(1)}'
        unlisted_hash = match.group(2) or parse_qs(parsed.query).get('h', [''])[0]
        return player + ('?' + urlencode({'h': unlisted_hash}) if unlisted_hash else '')

    def _extract_media(self, ydl, url, download):
        if SharePageParser.supports(url):
            media = SharePageParser().extract(url)
            return ydl.process_ie_result(media, download=download)
        try:
            return ydl.extract_info(url, download=download)
        except yt_dlp.utils.DownloadError:
            player_url = self._vimeo_player_url(url)
            if not player_url:
                raise
            return ydl.extract_info(player_url, download=download)

    @staticmethod
    def _format_selector(quality):
        height = {'4K': 2160, '2K': 1440, '8K': 4320}.get(quality)
        match = re.fullmatch(r'(\d+)p', quality)
        if match:
            height = int(match.group(1))
        limit = f'[height<=?{height}]' if height else ''
        # Unknown dimensions occur on Facebook; video-only formats occur on Instagram.
        return f'bestvideo{limit}+bestaudio/best{limit}/bestvideo{limit}'

    def _format_video_info(self, info: Dict[str, Any], url: str) -> Dict[str, Any]:
        """格式化视频信息"""
        title = info.get('title') or 'Unknown Title'
        author = info.get('uploader') or info.get('channel') or 'Unknown'
        thumbnails = info.get('thumbnails', [])
        thumbnail = ''
        if info.get('thumbnail'):
            thumbnail = info['thumbnail']
        if thumbnails:
            sorted_thumbs = sorted(thumbnails, key=lambda t: t.get('width', 0) or 0, reverse=True)
            for thumb in sorted_thumbs:
                if int(thumb.get('width', 0) or 0) >= 320:
                    thumbnail = thumb.get('url', '')
                    break
            if not thumbnail and sorted_thumbs:
                thumbnail = sorted_thumbs[0].get('url', '')
        thumbnail = self._resolve_thumbnail(url, thumbnail)
        duration = info.get('duration', 0)
        duration_str = self._format_duration(duration)
        views = info.get('view_count', 0)
        views_str = self._format_views(views)
        formats = self._get_available_formats(info)

        return {
            'url': url,
            'title': title,
            'author': author,
            'thumbnail': thumbnail,
            'duration': duration_str,
            'views': views_str,
            'formats': formats
        }

    def _resolve_thumbnail(self, url: str, thumbnail: str) -> str:
        normalized = self._normalize_url(thumbnail)
        if normalized and 'transparent.png' not in normalized.lower():
            return normalized
        if 'bilibili.com/video/' not in url:
            return normalized
        bvid = self._extract_bvid(url)
        if not bvid:
            return normalized
        api = f"https://api.bilibili.com/x/web-interface/view?bvid={quote_plus(bvid)}"
        try:
            req = Request(api, headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen(req, timeout=10) as resp:
                payload = json.loads(resp.read().decode('utf-8'))
                pic = payload.get('data', {}).get('pic', '')
                fallback = self._normalize_url(pic)
                if fallback:
                    return fallback
        except Exception:
            pass
        return normalized

    def _extract_bvid(self, url: str) -> Optional[str]:
        match = re.search(r'(BV[0-9A-Za-z]+)', url)
        if not match:
            return None
        return match.group(1)

    def _normalize_url(self, value: str) -> str:
        if not value:
            return ''
        if value.startswith('//'):
            return f'https:{value}'
        return value

    def _format_duration(self, seconds: Any) -> str:
        """格式化时长"""
        seconds = int(float(seconds or 0))
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours:d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:d}:{secs:02d}"

    def _format_views(self, views: Any) -> str:
        """格式化观看次数"""
        views = int(float(views or 0))
        if views >= 100000000:
            return f"{views / 100000000:.1f}亿次观看"
        elif views >= 10000:
            return f"{views / 10000:.1f}万次观看"
        else:
            return f"{views:d}次观看"

    def _get_available_formats(self, info: Dict[str, Any]) -> List[Dict[str, str]]:
        """获取可用的格式列表"""
        formats = []
        quality_buckets: Dict[str, Dict[str, str]] = {}
        quality_labels = {
            '2160': '4K',
            '1440': '2K',
            '1080': '1080p',
            '720': '720p',
            '480': '480p',
            '360': '360p'
        }
        duration = float(info.get('duration') or 0)
        audio_size = self._estimate_best_audio_size(info.get('formats', []), duration)
        for fmt in info.get('formats', []):
            if fmt.get('vcodec') == 'none' or fmt.get('ext') == 'mhtml':
                continue
            height = int(float(fmt.get('height', 0) or 0))
            if not height:
                continue
            quality_str = str(height)
            label = quality_labels.get(quality_str, f"{height:d}p")
            video_size = self._estimate_format_size(fmt, duration)
            if fmt.get('acodec') == 'none':
                if video_size > 0:
                    total_size = video_size + audio_size
                else:
                    total_size = self._estimate_profile_size(height, duration)
            else:
                total_size = video_size if video_size > 0 else self._estimate_profile_size(height, duration)
            existing = quality_buckets.get(label)
            if not existing or int(existing['size_bytes']) < total_size:
                quality_buckets[label] = {
                    'quality': label,
                    'height': str(height),
                    'size': self._format_filesize(total_size) if total_size > 0 else '未知',
                    'size_bytes': str(total_size)
                }
        formats = list(quality_buckets.values())
        formats.sort(key=lambda fmt: int(fmt['height']), reverse=True)
        if not formats:
            formats = [{'quality': 'best', 'label': '最佳画质', 'size': '未知'}]
        else:
            formats = [{'quality': f['quality'], 'height': f['height'], 'size': f['size']} for f in formats]

        return formats

    def _estimate_best_audio_size(self, formats: List[Dict[str, Any]], duration: float) -> int:
        best = 0
        for fmt in formats:
            if fmt.get('vcodec') != 'none':
                continue
            size = self._estimate_format_size(fmt, duration)
            if size > best:
                best = size
        if best <= 0 and duration > 0:
            best = int(160 * 1000 / 8 * duration)
        return best

    def _estimate_format_size(self, fmt: Dict[str, Any], duration: float) -> int:
        filesize = fmt.get('filesize') or fmt.get('filesize_approx') or 0
        if filesize:
            return int(float(filesize))
        if duration <= 0:
            return 0
        bitrate_kbps = fmt.get('tbr') or fmt.get('vbr') or fmt.get('abr') or 0
        if not bitrate_kbps:
            return 0
        return int(float(bitrate_kbps) * 1000 / 8 * duration)

    def _format_filesize(self, bytesize: Any) -> str:
        """格式化文件大小"""
        bytesize = int(float(bytesize or 0))
        if bytesize >= 1024 * 1024 * 1024:
            return f"{bytesize / (1024 * 1024 * 1024):.1f}GB"
        elif bytesize >= 1024 * 1024:
            return f"{bytesize / (1024 * 1024):.0f}MB"
        else:
            return f"{bytesize / 1024:.0f}KB"

    def _estimate_profile_size(self, height: int, duration: float) -> int:
        bitrate_by_height = {
            2160: 22000,
            1440: 12000,
            1080: 7000,
            720: 4000,
            480: 2200,
            360: 1200
        }
        candidates = sorted(bitrate_by_height.keys())
        mapped = min(candidates, key=lambda x: abs(x - height))
        if duration > 0:
            bitrate = bitrate_by_height[mapped]
            return int(float(bitrate) * 1000 / 8 * duration)
        return 0

    async def download_video(
        self,
        task_id: str,
        url: str,
        quality: str = "best",
        only_audio: bool = False,
        download_subtitle: bool = False,
        task_manager=None
    ):
        """下载视频"""
        def _download():
            try:
                if task_manager:
                    task_manager.set_status(task_id, "downloading")

                # 生成唯一文件名
                unique_id = str(uuid.uuid4())[:8]

                final_paths = []
                ydl_opts = self._ydl_options()
                ydl_opts.update({
                    'outtmpl': str(self.download_dir / f'%(title)s-{unique_id}.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True,
                    'logger': self._YDLLogger(),
                    'progress_hooks': [lambda d: self._progress_hook(d, task_id, task_manager)],
                    'post_hooks': [final_paths.append],
                })

                # 仅下载音频
                if only_audio:
                    ydl_opts.update({
                        'format': 'bestaudio/best',
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }],
                    })
                else:
                    # 根据质量选择格式
                    ydl_opts['format'] = self._format_selector(quality)

                # 下载字幕
                if download_subtitle:
                    ydl_opts.update({
                        'writesubtitles': True,
                        'writeautomaticsub': True,
                        'subtitleslangs': ['zh-Hans', 'zh', 'en'],
                    })

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = self._extract_media(ydl, url, download=True)

                    # 获取下载的文件名
                    filename = final_paths[-1] if final_paths else info.get('filepath')
                    if not filename or not Path(filename).is_file() or Path(filename).stat().st_size == 0:
                        raise ValueError('下载未生成有效文件，请重试')

                    actual_filename = Path(filename).name
                    download_url = f"/api/download/file/{quote(actual_filename, safe='')}"

                    if task_manager:
                        task_manager.set_complete(task_id, actual_filename, download_url)

            except Exception as e:
                if task_manager:
                    task_manager.set_error(task_id, str(e))
                    return
                raise

        return await asyncio.to_thread(_download)

    def _progress_hook(self, d: Dict[str, Any], task_id: str, task_manager):
        """下载进度回调"""
        if d['status'] == 'downloading' and task_manager:
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded_bytes = d.get('downloaded_bytes', 0)
            if total_bytes > 0:
                progress = int(float(downloaded_bytes) / float(total_bytes) * 95)
                task_manager.set_progress(task_id, progress)
        elif d['status'] == 'finished' and task_manager:
            task_manager.set_progress(task_id, 95)
