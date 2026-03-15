import asyncio
import os
import yt_dlp
from pathlib import Path
from typing import Dict, Any, List, Optional
import uuid


class VideoDownloader:
    """视频下载服务 - 封装 yt-dlp"""

    def __init__(self):
        self.download_dir = Path(os.getenv("DOWNLOAD_DIR", "./downloads"))
        self.download_dir.mkdir(exist_ok=True)

    async def get_video_info(self, url: str) -> Dict[str, Any]:
        """获取视频信息"""
        def _get_info():
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return self._format_video_info(info)

        return await asyncio.to_thread(_get_info)

    def _format_video_info(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """格式化视频信息"""
        # 获取标题
        title = info.get('title', 'Unknown Title')

        # 获取作者
        author = info.get('uploader', info.get('channel', 'Unknown'))

        # 获取缩略图
        thumbnails = info.get('thumbnails', [])
        thumbnail = ''
        if thumbnails:
            # 选择中等大小的缩略图
            sorted_thumbs = sorted(thumbnails, key=lambda t: t.get('width', 0) or 0, reverse=True)
            for thumb in sorted_thumbs:
                if thumb.get('width', 0) >= 320:
                    thumbnail = thumb.get('url', '')
                    break
            if not thumbnail and sorted_thumbs:
                thumbnail = sorted_thumbs[0].get('url', '')

        # 获取时长
        duration = info.get('duration', 0)
        duration_str = self._format_duration(duration)

        # 获取观看次数
        views = info.get('view_count', 0)
        views_str = self._format_views(views)

        # 获取可用格式
        formats = self._get_available_formats(info)

        return {
            'title': title,
            'author': author,
            'thumbnail': thumbnail,
            'duration': duration_str,
            'views': views_str,
            'formats': formats
        }

    def _format_duration(self, seconds: int) -> str:
        """格式化时长"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"

    def _format_views(self, views: int) -> str:
        """格式化观看次数"""
        if views >= 100000000:
            return f"{views / 100000000:.1f}亿次观看"
        elif views >= 10000:
            return f"{views / 10000:.1f}万次观看"
        else:
            return f"{views}次观看"

    def _get_available_formats(self, info: Dict[str, Any]) -> List[Dict[str, str]]:
        """获取可用的格式列表"""
        formats = []
        seen_qualities = set()

        # 优先顺序：4K -> 1080p -> 720p -> 480p -> 360p
        quality_order = ['2160', '1440', '1080', '720', '480', '360']
        quality_labels = {
            '2160': '4K',
            '1440': '2K',
            '1080': '1080p',
            '720': '720p',
            '480': '480p',
            '360': '360p'
        }

        # 获取所有视频格式
        for fmt in info.get('formats', []):
            height = fmt.get('height', 0)
            if not height:
                continue

            # 找到最接近的质量标签
            quality_str = str(height)
            label = quality_labels.get(quality_str, f"{height}p")

            if label not in seen_qualities:
                seen_qualities.add(label)
                # 估算文件大小
                filesize = fmt.get('filesize', fmt.get('filesize_approx', 0))
                size_str = self._format_filesize(filesize) if filesize else '~'

                formats.append({
                    'quality': label,
                    'height': str(height),
                    'size': size_str
                })

        # 按质量排序
        def get_quality_order(fmt):
            label = fmt['quality']
            for i, q in enumerate(quality_labels.values()):
                if q == label:
                    return i
            return len(quality_labels)

        formats.sort(key=get_quality_order)

        # 如果没有找到任何格式，添加默认选项
        if not formats:
            formats = [
                {'quality': '1080p', 'size': '~500MB'},
                {'quality': '720p', 'size': '~250MB'},
                {'quality': '480p', 'size': '~100MB'},
            ]

        return formats

    def _format_filesize(self, bytesize: int) -> str:
        """格式化文件大小"""
        if bytesize >= 1024 * 1024 * 1024:
            return f"~{bytesize / (1024 * 1024 * 1024):.1f}GB"
        elif bytesize >= 1024 * 1024:
            return f"~{bytesize / (1024 * 1024):.0f}MB"
        else:
            return f"~{bytesize / 1024:.0f}KB"

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

                ydl_opts = {
                    'outtmpl': str(self.download_dir / f'%(title)s-{unique_id}.%(ext)s'),
                    'quiet': False,
                    'no_warnings': False,
                    'progress_hooks': [lambda d: self._progress_hook(d, task_id, task_manager)],
                }

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
                    if quality == '4K':
                        ydl_opts['format'] = 'bestvideo[height<=2160]+bestaudio/best[height<=2160]'
                    elif quality == '2K':
                        ydl_opts['format'] = 'bestvideo[height<=1440]+bestaudio/best[height<=1440]'
                    elif quality == '1080p':
                        ydl_opts['format'] = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
                    elif quality == '720p':
                        ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
                    elif quality == '480p':
                        ydl_opts['format'] = 'bestvideo[height<=480]+bestaudio/best[height<=480]'
                    else:
                        ydl_opts['format'] = 'bestvideo+bestaudio/best'

                # 下载字幕
                if download_subtitle:
                    ydl_opts.update({
                        'writesubtitles': True,
                        'writeautomaticsub': True,
                        'subtitleslangs': ['zh-Hans', 'zh', 'en'],
                    })

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)

                    # 获取下载的文件名
                    filename = ydl.prepare_filename(info)
                    if only_audio:
                        filename = filename.rsplit('.', 1)[0] + '.mp3'

                    actual_filename = Path(filename).name
                    download_url = f"/api/download/file/{actual_filename}"

                    if task_manager:
                        task_manager.set_complete(task_id, actual_filename, download_url)

            except Exception as e:
                if task_manager:
                    task_manager.set_error(task_id, str(e))
                raise

        return await asyncio.to_thread(_download)

    def _progress_hook(self, d: Dict[str, Any], task_id: str, task_manager):
        """下载进度回调"""
        if d['status'] == 'downloading' and task_manager:
            # 计算进度
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded_bytes = d.get('downloaded_bytes', 0)

            if total_bytes > 0:
                progress = int(downloaded_bytes / total_bytes * 100)
                task_manager.set_progress(task_id, progress)

        elif d['status'] == 'finished' and task_manager:
            task_manager.set_progress(task_id, 100)
