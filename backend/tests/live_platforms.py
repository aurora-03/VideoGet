"""Opt-in real-network checks: python tests/live_platforms.py --platform Facebook 抖音."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys


BACKEND = Path(__file__).resolve().parents[1]
SAMPLES = {
    'YouTube': 'https://www.youtube.com/watch?v=x41yOUIvK2k',
    'Bilibili': 'https://www.bilibili.com/video/BV1bK411W797?p=1',
    '抖音': 'https://www.douyin.com/video/6961737553342991651',
    '快手': 'https://www.kuaishou.com/short-video/3x25msbsnncn8cs',
    'TikTok': 'https://www.tiktok.com/@patroxofficial/video/6742501081818877190',
    'Instagram': 'https://www.instagram.com/reel/Chunk8-jurw/',
    'Twitter/X': 'https://x.com/historyinmemes/status/1790637656616943991',
    'Facebook': 'https://www.facebook.com/100033620354545/videos/106560053808006/',
    # Official yt-dlp password-protected fixture; its documented password is youtube-dl.
    'Vimeo': 'https://vimeo.com/68375962',
    'Twitch': 'https://clips.twitch.tv/FaintLightGullWholeWheat',
}


def worker(platform, output, audio, url=None):
    target = output / platform.replace('/', '-')
    target.mkdir(parents=True, exist_ok=True)
    os.environ['DOWNLOAD_DIR'] = str(target)
    os.chdir(BACKEND)
    sys.path.insert(0, str(BACKEND))
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)
    url = url or SAMPLES[platform]
    result = {'platform': platform, 'url': url, 'stage': 'parse'}
    report = target / 'result.json'

    def save():
        report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')

    save()
    try:
        response = client.post('/api/video/info', json={'url': url})
        result['info_http'] = response.status_code
        if response.status_code != 200:
            result.update(outcome='parse_failed', error=response.json())
            return
        info = response.json()
        formats = info['formats']
        quality = next((f['quality'] for f in formats if f['quality'] == '1080p'), formats[0]['quality'])
        result.update(stage='download', title=info['title'], formats=formats, quality=quality)
        save()
        response = client.post('/api/download', json={
            'url': url, 'quality': quality, 'only_audio': audio})
        if response.status_code != 200:
            result.update(outcome='submit_failed', error=response.json())
            return
        task = client.get('/api/task/' + response.json()['task_id']).json()
        result['task'] = task
        if task['status'] != 'completed':
            result['outcome'] = 'download_failed'
            return
        file_path = target / task['filename']
        result['file_exists'] = file_path.is_file()
        if not file_path.is_file():
            result['outcome'] = 'file_missing'
            return
        result['file_bytes'] = file_path.stat().st_size
        result['file_http'] = client.get(task['download_url']).status_code
        probe = subprocess.run([
            'ffprobe', '-v', 'error', '-show_entries',
            'format=duration,size:stream=codec_name,codec_type,width,height',
            '-of', 'json', str(file_path),
        ], capture_output=True, text=True, timeout=15)
        result['ffprobe_exit'] = probe.returncode
        result['media'] = json.loads(probe.stdout) if probe.returncode == 0 else probe.stderr
        result['outcome'] = ('success' if result['file_http'] == 200 and
                             probe.returncode == 0 and result['file_bytes'] > 0 else 'file_failed')
    except Exception as error:
        result.update(outcome='test_error', error=str(error))
    finally:
        save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--platform', nargs='+', choices=list(SAMPLES), default=list(SAMPLES))
    parser.add_argument('--timeout', type=int, default=120)
    parser.add_argument('--audio', action='store_true')
    parser.add_argument('--url', help='Override the sample URL when testing one platform')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--worker', choices=list(SAMPLES), help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.url and not args.worker and len(args.platform) != 1:
        parser.error('--url requires exactly one --platform')
    output = (args.output or BACKEND / 'downloads' / (
        'verification-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))).resolve()
    output.mkdir(parents=True, exist_ok=True)
    if args.worker:
        worker(args.worker, output, args.audio, args.url)
        return

    def run(platform):
        command = [sys.executable, __file__, '--worker', platform, '--output', str(output)]
        if args.audio:
            command.append('--audio')
        if args.url:
            command.extend(['--url', args.url])
        timed_out = False
        try:
            process = subprocess.run(command, capture_output=True, text=True, timeout=args.timeout)
            process_error = process.stderr[-2000:] if process.returncode else None
        except subprocess.TimeoutExpired:
            timed_out, process_error = True, None
        report = output / platform.replace('/', '-') / 'result.json'
        result = json.loads(report.read_text(encoding='utf-8')) if report.is_file() else {'platform': platform}
        if timed_out:
            result['outcome'] = 'timeout'
        elif process_error:
            result.update(outcome='test_error', error=process_error)
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"{platform}: {result.get('outcome', 'unknown')}", flush=True)
        return result

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(run, args.platform))
    report = output / 'results.json'
    report.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Report: {report}', flush=True)
    sys.exit(0 if all(result.get('outcome') == 'success' for result in results) else 1)


if __name__ == '__main__':
    main()
