import asyncio
import os
import yt_dlp
from pathlib import Path
from typing import Dict, Any, List, Optional
import uuid
import re
import json
import base64
import hashlib
import importlib.util
import logging
import sys
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
from urllib.parse import urlparse, parse_qs


class VideoDownloader:
    """视频下载服务 - 封装 yt-dlp"""

    def __init__(self):
        self.download_dir = Path(os.getenv("DOWNLOAD_DIR", "./downloads"))
        self.download_dir.mkdir(exist_ok=True)
        self._douyin_cache: Dict[str, Dict[str, Any]] = {}
        self._douyin_vendor_downloader_cls = None
        self._douyin_vendor_utils_module = None

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
            try:
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': False,
                    'logger': self._YDLLogger(),
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    return self._format_video_info(info, url)
            except Exception:
                if self._is_douyin_url(url):
                    item_info, resolved_url = self._fetch_douyin_item_info(url)
                    self._douyin_cache[item_info.get('aweme_id', resolved_url)] = item_info
                    return self._format_douyin_video_info(item_info, resolved_url)
                raise

        return await asyncio.to_thread(_get_info)

    def _format_video_info(self, info: Dict[str, Any], url: str) -> Dict[str, Any]:
        """格式化视频信息"""
        title = info.get('title', 'Unknown Title')
        author = info.get('uploader', info.get('channel', 'Unknown'))
        thumbnails = info.get('thumbnails', [])
        thumbnail = ''
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

    def _load_douyin_vendor(self):
        if self._douyin_vendor_downloader_cls and self._douyin_vendor_utils_module:
            return self._douyin_vendor_downloader_cls, self._douyin_vendor_utils_module
        vendor_root = Path(__file__).resolve().parents[1] / 'third_party' / 'douyin_video_downloader'
        utils_path = vendor_root / 'utils.py'
        downloader_path = vendor_root / 'downloader.py'
        if not utils_path.exists() or not downloader_path.exists():
            raise ValueError('抖音解析组件未安装，请稍后重试')
        utils_spec = importlib.util.spec_from_file_location('douyin_vendor_utils', str(utils_path))
        if not utils_spec or not utils_spec.loader:
            raise ValueError('抖音解析组件加载失败')
        utils_module = importlib.util.module_from_spec(utils_spec)
        sys.modules['douyin_vendor_utils'] = utils_module
        utils_spec.loader.exec_module(utils_module)
        previous_utils = sys.modules.get('utils')
        sys.modules['utils'] = utils_module
        try:
            downloader_spec = importlib.util.spec_from_file_location('douyin_vendor_downloader', str(downloader_path))
            if not downloader_spec or not downloader_spec.loader:
                raise ValueError('抖音解析组件加载失败')
            downloader_module = importlib.util.module_from_spec(downloader_spec)
            sys.modules['douyin_vendor_downloader'] = downloader_module
            downloader_spec.loader.exec_module(downloader_module)
        finally:
            if previous_utils is not None:
                sys.modules['utils'] = previous_utils
            else:
                sys.modules.pop('utils', None)
        self._douyin_vendor_downloader_cls = downloader_module.DouyinDownloader
        self._douyin_vendor_utils_module = utils_module
        return self._douyin_vendor_downloader_cls, self._douyin_vendor_utils_module

    def _create_douyin_vendor_client(self):
        downloader_cls, _ = self._load_douyin_vendor()
        return downloader_cls(output_dir=self.download_dir, logger=logging.getLogger('douyin_vendor_bridge'))

    def _is_douyin_url(self, url: str) -> bool:
        lowered = str(url or '').lower()
        return 'douyin.com' in lowered or 'iesdouyin.com' in lowered

    def _extract_first_url(self, raw: str) -> str:
        text = str(raw or '').strip()
        match = re.search(r'https?://[^\s<>"\'`]+', text, flags=re.IGNORECASE)
        candidate = match.group(0) if match else text
        return re.sub(r"[)\]}>，。！？、；：'\"`]+$", "", candidate)

    def _resolve_redirect_url(self, share_url: str) -> str:
        req = Request(
            share_url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.douyin.com/'
            },
        )
        with urlopen(req, timeout=15) as resp:
            return resp.geturl()

    def _extract_douyin_video_id(self, resolved_url: str) -> str:
        parsed = urlparse(resolved_url)
        query = parse_qs(parsed.query)
        for key in ('modal_id', 'item_ids', 'group_id', 'aweme_id'):
            values = query.get(key)
            if values:
                match = re.search(r'(\d{8,24})', values[0])
                if match:
                    return match.group(1)
        for pattern in (r'/video/(\d{8,24})', r'/note/(\d{8,24})', r'/(\d{8,24})(?:/|$)'):
            match = re.search(pattern, parsed.path)
            if match:
                return match.group(1)
        fallback = re.search(r'(?<!\d)(\d{8,24})(?!\d)', resolved_url)
        if fallback:
            return fallback.group(1)
        raise ValueError('地址无效，请输入正确的视频链接')

    def _fetch_douyin_item_info(self, raw_url: str) -> tuple[Dict[str, Any], str]:
        _, utils_module = self._load_douyin_vendor()
        client = self._create_douyin_vendor_client()
        try:
            share_url = utils_module.extract_first_url(raw_url)
            resolved_url = utils_module.resolve_redirect_url(
                session=client.session,
                share_url=share_url,
                timeout=client.timeout,
                max_retries=client.max_retries,
                backoff_factor=client.backoff_factor,
                logger=client.logger,
            )
            video_id = utils_module.extract_video_id(resolved_url)
            item_info = client._fetch_item_info(video_id=video_id, resolved_url=resolved_url)
            return item_info, resolved_url
        except Exception as e:
            raise ValueError('该抖音链接当前受风控，请使用抖音App分享链接后重试') from e
        finally:
            client.close()

    def _fetch_douyin_item_info_from_share_page(self, video_id: str, resolved_url: str) -> Dict[str, Any]:
        candidates = []
        ies_url = f"https://www.iesdouyin.com/share/video/{video_id}/"
        candidates.append(ies_url)
        if resolved_url and resolved_url not in candidates:
            candidates.append(resolved_url)
        for page_url in candidates:
            try:
                html = self._get_share_page_html(page_url)
            except Exception:
                continue
            router_data = self._extract_router_data_json(html)
            item_info = self._extract_item_info_from_router_data(router_data)
            if item_info:
                return item_info
            item_info = self._build_douyin_item_from_meta(video_id, html)
            if item_info:
                return item_info
        return {
            'aweme_id': video_id,
            'desc': f'抖音视频_{video_id}',
            'duration': 0,
            'video': {
                'cover': {'url_list': []},
                'play_addr': {'url_list': []},
                'bit_rate': []
            },
            'author': {'nickname': 'Douyin'},
            'statistics': {'play_count': 0}
        }

    def _build_douyin_item_from_meta(self, video_id: str, html: str) -> Dict[str, Any]:
        title = self._extract_meta_content(html, 'og:title') or self._extract_title_tag(html)
        cover = self._extract_meta_content(html, 'og:image')
        if not title and not cover:
            return {}
        return {
            'aweme_id': video_id,
            'desc': title or f'douyin_{video_id}',
            'duration': 0,
            'video': {
                'cover': {'url_list': [cover] if cover else []},
                'play_addr': {'url_list': []},
                'bit_rate': []
            },
            'author': {'nickname': 'Douyin'},
            'statistics': {'play_count': 0}
        }

    def _extract_meta_content(self, html: str, prop: str) -> str:
        pattern = rf'<meta[^>]+(?:property|name)=["\']{re.escape(prop)}["\'][^>]+content=["\']([^"\']+)["\']'
        match = re.search(pattern, html, flags=re.IGNORECASE)
        if not match:
            return ''
        return self._normalize_url(match.group(1).strip())

    def _extract_title_tag(self, html: str) -> str:
        match = re.search(r'<title>(.*?)</title>', html, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            return ''
        return re.sub(r'\s+', ' ', match.group(1)).strip()

    def _get_share_page_html(self, share_url: str) -> str:
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.douyin.com/'
        }
        req = Request(share_url, headers=headers)
        with urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        if ('wci="' in html and 'cs="' in html) or ('wci=' in html and 'cs=' in html):
            solved = self._solve_waf_cookie(html, share_url)
            if solved:
                req = Request(share_url, headers={**headers, 'Cookie': solved})
                with urlopen(req, timeout=15) as resp:
                    return resp.read().decode('utf-8', errors='ignore')
        return html

    def _solve_waf_cookie(self, html: str, page_url: str) -> str:
        match = re.search(r'wci="([^"]+)"\s*,\s*cs="([^"]+)"', html)
        if not match:
            return ''
        cookie_name, challenge_blob = match.groups()
        try:
            challenge_data = json.loads(self._decode_urlsafe_b64(challenge_blob).decode('utf-8'))
            prefix = self._decode_urlsafe_b64(challenge_data['v']['a'])
            expected_digest = self._decode_urlsafe_b64(challenge_data['v']['c']).hex()
        except Exception:
            return ''
        solved_value = None
        for candidate in range(1_000_001):
            digest = hashlib.sha256(prefix + str(candidate).encode('utf-8')).hexdigest()
            if digest == expected_digest:
                solved_value = candidate
                break
        if solved_value is None:
            return ''
        challenge_data['d'] = base64.b64encode(str(solved_value).encode('utf-8')).decode('utf-8')
        cookie_value = base64.b64encode(
            json.dumps(challenge_data, separators=(',', ':')).encode('utf-8')
        ).decode('utf-8')
        domain = urlparse(page_url).hostname or 'www.iesdouyin.com'
        return f"{cookie_name}={cookie_value}"

    def _decode_urlsafe_b64(self, value: str) -> bytes:
        normalized = value.replace('-', '+').replace('_', '/')
        normalized += '=' * (-len(normalized) % 4)
        return base64.b64decode(normalized)

    def _extract_router_data_json(self, html: str) -> Dict[str, Any]:
        marker = "window._ROUTER_DATA = "
        start = html.find(marker)
        if start < 0:
            return {}
        index = start + len(marker)
        while index < len(html) and html[index].isspace():
            index += 1
        if index >= len(html) or html[index] != "{":
            return {}
        depth = 0
        in_string = False
        escaped = False
        for cursor in range(index, len(html)):
            char = html[cursor]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    payload = html[index: cursor + 1]
                    try:
                        return json.loads(payload)
                    except Exception:
                        return {}
        return {}

    def _extract_item_info_from_router_data(self, router_data: Dict[str, Any]) -> Dict[str, Any]:
        loader_data = router_data.get('loaderData', {})
        if not isinstance(loader_data, dict):
            return {}
        for node in loader_data.values():
            if not isinstance(node, dict):
                continue
            video_info_res = node.get('videoInfoRes', {})
            if not isinstance(video_info_res, dict):
                continue
            item_list = video_info_res.get('item_list', [])
            if item_list and isinstance(item_list[0], dict):
                return item_list[0]
            filter_list = video_info_res.get('filter_list', [])
            if filter_list and isinstance(filter_list[0], dict):
                filter_reason = filter_list[0].get('filter_reason', '')
                aweme_id = filter_list[0].get('aweme_id', '')
                return {
                    'aweme_id': aweme_id,
                    'desc': f'抖音视频_{aweme_id}' if aweme_id else '抖音视频',
                    'duration': 0,
                    'video': {'cover': {'url_list': []}, 'play_addr': {'url_list': []}, 'bit_rate': []},
                    'author': {'nickname': 'Douyin'},
                    'statistics': {'play_count': 0},
                    '_unavailable_reason': filter_reason or 'RESTRICTED'
                }
        return {}

    def _format_douyin_video_info(self, item: Dict[str, Any], resolved_url: str) -> Dict[str, Any]:
        author = item.get('author', {}) if isinstance(item.get('author', {}), dict) else {}
        title = item.get('desc') or f"douyin_{item.get('aweme_id', '')}"
        thumbnail = self._extract_douyin_thumbnail(item)
        duration_ms = item.get('duration') or 0
        duration_str = self._format_duration(float(duration_ms) / 1000 if duration_ms else 0)
        stats = item.get('statistics', {}) if isinstance(item.get('statistics', {}), dict) else {}
        views_str = self._format_views(stats.get('play_count', 0))
        formats = self._extract_douyin_formats(item)
        return {
            'url': resolved_url,
            'title': title,
            'author': author.get('nickname', 'Douyin'),
            'thumbnail': thumbnail,
            'duration': duration_str,
            'views': views_str,
            'formats': formats
        }

    def _extract_douyin_thumbnail(self, item: Dict[str, Any]) -> str:
        video = item.get('video', {}) if isinstance(item.get('video', {}), dict) else {}
        for key in ('cover', 'origin_cover', 'dynamic_cover'):
            urls = video.get(key, {}).get('url_list', [])
            if urls:
                return self._normalize_url(urls[0])
        return ''

    def _extract_douyin_formats(self, item: Dict[str, Any]) -> List[Dict[str, str]]:
        formats: List[Dict[str, str]] = []
        if item.get('_unavailable_reason'):
            return [{'quality': '不可下载', 'size': '受限'}]
        video = item.get('video', {}) if isinstance(item.get('video', {}), dict) else {}
        duration = float(item.get('duration') or 0) / 1000 if item.get('duration') else 0
        bit_rates = video.get('bit_rate', []) if isinstance(video.get('bit_rate', []), list) else []
        for br in bit_rates:
            if not isinstance(br, dict):
                continue
            quality_label = br.get('gear_name') or br.get('quality_type') or '标清'
            bit_rate = br.get('bit_rate') or 0
            size = self._format_filesize(int(float(bit_rate) / 8 * duration)) if bit_rate and duration else '未知'
            formats.append({'quality': str(quality_label), 'size': size})
        if not formats:
            play_addr = video.get('play_addr', {}) if isinstance(video.get('play_addr', {}), dict) else {}
            url_list = play_addr.get('url_list', []) if isinstance(play_addr.get('url_list', []), list) else []
            if url_list:
                formats = [{'quality': '默认', 'size': '未知'}]
        return formats or [{'quality': '默认', 'size': '未知'}]

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
        def get_quality_order(fmt):
            label = fmt['quality']
            for i, q in enumerate(quality_labels.values()):
                if q == label:
                    return i
            return len(quality_labels)
        formats = list(quality_buckets.values())
        formats.sort(key=get_quality_order)
        if not formats:
            formats = [
                {'quality': '1080p', 'size': '500MB'},
                {'quality': '720p', 'size': '250MB'},
                {'quality': '480p', 'size': '100MB'},
            ]
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
        default_by_height = {
            2160: 2.5 * 1024 * 1024 * 1024,
            1440: 1.4 * 1024 * 1024 * 1024,
            1080: 650 * 1024 * 1024,
            720: 320 * 1024 * 1024,
            480: 180 * 1024 * 1024,
            360: 120 * 1024 * 1024
        }
        candidates = sorted(bitrate_by_height.keys())
        mapped = min(candidates, key=lambda x: abs(x - height))
        if duration > 0:
            bitrate = bitrate_by_height[mapped]
            return int(float(bitrate) * 1000 / 8 * duration)
        return int(default_by_height[mapped])

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
                    'quiet': True,
                    'no_warnings': True,
                    'logger': self._YDLLogger(),
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
                if self._is_douyin_url(url):
                    try:
                        return self._download_douyin_direct(task_id, url, only_audio, task_manager)
                    except Exception as fallback_error:
                        if task_manager:
                            task_manager.set_error(task_id, str(fallback_error))
                            return
                        raise fallback_error
                if task_manager:
                    task_manager.set_error(task_id, str(e))
                    return
                raise

        return await asyncio.to_thread(_download)

    def _download_douyin_direct(self, task_id: str, raw_url: str, only_audio: bool, task_manager=None):
        client = self._create_douyin_vendor_client()
        try:
            mode = 'audio' if only_audio else 'video'
            result = client.download_from_share_url(raw_url, mode=mode, show_progress=False)
            output_path = Path(result.file_path)
            if task_manager:
                task_manager.set_progress(task_id, 95)
                task_manager.set_complete(task_id, output_path.name, f"/api/download/file/{output_path.name}")
        except Exception as e:
            raise ValueError('该抖音视频当前受限，无法下载，请在抖音App打开并重新分享后重试') from e
        finally:
            client.close()

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
