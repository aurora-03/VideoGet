"""Extract media exposed by public Douyin and Kuaishou mobile share pages."""

import json
import base64
import hashlib
import os
import re
import time
from http.cookiejar import MozillaCookieJar
from urllib.parse import parse_qs, urlparse

import requests


MOBILE_UA = (
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) '
    'AppleWebKit/605.1.15 Version/16.0 Mobile/15E148 Safari/604.1'
)


def matches_host(url, domains):
    host = (urlparse(url).hostname or '').lower()
    return any(host == domain or host.endswith('.' + domain) for domain in domains)


def extract_page_state(html, name):
    """Decode a JSON assignment without executing webpage JavaScript."""
    match = re.search(r'window\.' + re.escape(name) + r'\s*=\s*', html)
    if not match:
        return {}
    source = html[match.end():].lstrip()
    try:
        if source.startswith('JSON.parse('):
            source = source[len('JSON.parse('):].lstrip()
        value, _ = json.JSONDecoder().raw_decode(source)
        if isinstance(value, str):
            value = json.loads(value)
        return value if isinstance(value, dict) else {}
    except (ValueError, TypeError):
        return {}


def _http_urls(values):
    for value in values or []:
        url = value.get('url') if isinstance(value, dict) else value
        if isinstance(url, str) and urlparse(url).scheme in {'http', 'https'}:
            yield url


def solve_page_challenge(html):
    """Handle the bounded SHA-256 guest-session challenge returned by share pages."""
    match = re.search(r'wci="([^"]+)"\s*,\s*cs="([^"]+)"', html)
    if not match:
        return None

    def decode(value):
        return base64.urlsafe_b64decode(value + '=' * (-len(value) % 4))

    try:
        name, blob = match.groups()
        payload = json.loads(decode(blob))
        prefix = decode(payload['v']['a'])
        expected = decode(payload['v']['c'])
        deadline = time.monotonic() + 1
        for candidate in range(1_000_001):
            if candidate % 1000 == 0 and time.monotonic() > deadline:
                break
            if hashlib.sha256(prefix + str(candidate).encode()).digest() == expected:
                payload['d'] = base64.b64encode(str(candidate).encode()).decode()
                value = base64.b64encode(json.dumps(payload, separators=(',', ':')).encode()).decode()
                return name, value
    except (ValueError, TypeError, KeyError):
        pass
    return None


class SharePageParser:
    @staticmethod
    def supports(url):
        return matches_host(url, ('douyin.com', 'iesdouyin.com', 'kuaishou.com',
                                  'kuaishou.cn', 'gifshow.com', 'chenzhongtech.com'))

    def extract(self, url):
        with requests.Session() as session:
            session.headers.update({'User-Agent': MOBILE_UA, 'Accept-Language': 'zh-CN,zh;q=0.9'})
            cookie_file = os.getenv('YTDLP_COOKIE_FILE')
            if cookie_file:
                jar = MozillaCookieJar(cookie_file)
                jar.load(ignore_discard=True)
                session.cookies.update(jar)
            if matches_host(url, ('douyin.com', 'iesdouyin.com')):
                return self._douyin(session, url)
            return self._kuaishou(session, url)

    @staticmethod
    def _get(session, url):
        response = session.get(url, timeout=(10, 20))
        response.raise_for_status()
        challenge = solve_page_challenge(response.text)
        if challenge:
            name, value = challenge
            session.cookies.set(name, value, domain=urlparse(response.url).hostname, path='/')
            response = session.get(url, timeout=(10, 20))
            response.raise_for_status()
        return response

    def _douyin(self, session, url):
        session.headers['Referer'] = 'https://www.douyin.com/'
        video_id = self._douyin_id(url)
        if not video_id:
            video_id = self._douyin_id(self._get(session, url).url)
        if not video_id:
            raise ValueError('无法识别抖音视频，请粘贴抖音App的视频分享链接')
        share_url = f'https://www.iesdouyin.com/share/video/{video_id}/?from_ssr=1'
        # First response supplies the guest ttwid cookie; reuse it on subsequent requests.
        for attempt in range(6):
            if attempt:
                time.sleep(0.2 * attempt)
            state = extract_page_state(self._get(session, share_url).text, '_ROUTER_DATA')
            for node in (state.get('loaderData') or {}).values():
                if not isinstance(node, dict):
                    continue
                result = node.get('videoInfoRes') or {}
                if result.get('filter_list'):
                    raise ValueError('该抖音视频已删除、设为私密或当前不可访问')
                for item in result.get('item_list') or []:
                    if str(item.get('aweme_id')) == video_id:
                        return self._douyin_media(item, url)
        raise ValueError('抖音分享页未返回视频数据，请稍后重试；如需登录，可配置 YTDLP_COOKIE_FILE')

    @staticmethod
    def _douyin_id(url):
        parsed = urlparse(url)
        match = re.search(r'/(?:video|note)/(\d{8,24})(?:/|$)', parsed.path)
        if match:
            return match.group(1)
        for key in ('modal_id', 'aweme_id', 'item_ids', 'group_id'):
            value = parse_qs(parsed.query).get(key, [''])[0]
            if re.fullmatch(r'\d{8,24}', value):
                return value
        return None

    @staticmethod
    def _douyin_media(item, url):
        video = item.get('video') or {}
        sources = [video.get('play_addr') or {}]
        sources.extend(rate.get('play_addr') or {} for rate in video.get('bit_rate') or [])
        formats, seen = [], set()
        for source in sources:
            for media_url in _http_urls(source.get('url_list')):
                if media_url in seen:
                    continue
                seen.add(media_url)
                formats.append({
                    'format_id': f'share-{len(formats)}', 'url': media_url, 'ext': 'mp4',
                    # The share endpoint can return a lower resolution than advertised.
                    # Offer best rather than promising unverified dimensions.
                    'filesize': source.get('data_size') or None,
                })
        if not formats:
            raise ValueError('该抖音作品没有公开的视频播放地址（图文作品暂不支持）')
        covers = list(_http_urls((video.get('cover') or {}).get('url_list')))
        return {
            'id': str(item['aweme_id']), 'title': item.get('desc') or f"抖音视频_{item['aweme_id']}",
            'uploader': (item.get('author') or {}).get('nickname') or 'Douyin',
            'duration': float(video.get('duration') or item.get('duration') or 0) / 1000,
            'view_count': (item.get('statistics') or {}).get('play_count'),
            'thumbnail': covers[0] if covers else None,
            'formats': formats, 'webpage_url': url,
            'http_headers': {'User-Agent': MOBILE_UA, 'Referer': 'https://www.douyin.com/'},
        }

    def _kuaishou(self, session, url):
        session.headers['Referer'] = 'https://www.kuaishou.com/'
        response = self._get(session, url)
        state = extract_page_state(response.text, 'INIT_STATE')
        photos = [node['photo'] for node in state.values()
                  if isinstance(node, dict) and isinstance(node.get('photo'), dict)]
        if not photos:
            raise ValueError('快手分享页未返回视频数据，链接可能已失效或需要登录；可配置 YTDLP_COOKIE_FILE')
        return self._kuaishou_media(photos[0], url)

    @staticmethod
    def _kuaishou_media(photo, url):
        formats, seen = [], set()

        def add(media_url, source, preference=0):
            if media_url in seen:
                return
            seen.add(media_url)
            formats.append({
                'format_id': f'share-{len(formats)}', 'url': media_url, 'ext': 'mp4',
                'height': source.get('height') or photo.get('height'),
                'width': source.get('width') or photo.get('width'),
                'filesize': source.get('fileSize') or None, 'preference': preference,
            })

        for media_url in _http_urls(photo.get('mainMvUrls')):
            add(media_url, photo, 1)
        manifest = photo.get('manifest') or {}
        if isinstance(manifest, str):
            try:
                manifest = json.loads(manifest)
            except ValueError:
                manifest = {}
        for group in manifest.get('adaptationSet') or []:
            for source in group.get('representation') or []:
                for media_url in _http_urls([source.get('url')] + (source.get('backupUrl') or [])):
                    add(media_url, source)
        if not formats:
            raise ValueError('该快手作品没有公开的视频播放地址（图文作品暂不支持）')
        covers = list(_http_urls(photo.get('coverUrls')))
        return {
            'id': str(photo['photoId']), 'title': photo.get('caption') or f"快手视频_{photo['photoId']}",
            'uploader': photo.get('userName') or 'Kuaishou',
            'duration': float(photo.get('duration') or 0) / 1000,
            'view_count': photo.get('viewCount'), 'thumbnail': covers[0] if covers else None,
            'formats': formats, 'webpage_url': url,
            'http_headers': {'User-Agent': MOBILE_UA, 'Referer': 'https://www.kuaishou.com/'},
        }
