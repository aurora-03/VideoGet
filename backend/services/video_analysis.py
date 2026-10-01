"""Subtitle extraction, speech fallback, timed translation and transcript-based summaries."""

import asyncio
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
from urllib.parse import quote

import yt_dlp
from yt_dlp.networking import Request

from services.ai_client import AIClient, SpeechClient
from services.subtitles import cue_batches, normalize_segments, parse_subtitles, to_srt
from services.model_settings import use_settings


LANGUAGES = {'zh': 'Simplified Chinese', 'en': 'English', 'ja': 'Japanese', 'ko': 'Korean',
             'es': 'Spanish', 'fr': 'French', 'de': 'German'}


class VideoAnalysis:
    def __init__(self, downloader, task_manager):
        self.downloader = downloader
        self.tasks = task_manager
        self.slots = threading.BoundedSemaphore(2)

    def _stage(self, task_id, stage, progress):
        self.tasks.update_task(task_id, status='processing', stage=stage)
        self.tasks.set_progress(task_id, progress)

    def _check_duration(self, info):
        if info.get('is_live') or info.get('live_status') == 'is_live':
            raise ValueError('直播内容暂不支持字幕分析')
        maximum = int(os.getenv('ANALYSIS_MAX_DURATION', '7200'))
        if float(info.get('duration') or 0) > maximum:
            raise ValueError(f'视频超过分析时长限制（{maximum} 秒）')

    def extract_subtitles(self, url, language='auto'):
        with yt_dlp.YoutubeDL(self.downloader._ydl_options()) as ydl:
            info = self.downloader._extract_media(ydl, url, download=False)
            self._check_duration(info)
            manual = info.get('subtitles') or {}
            automatic = info.get('automatic_captions') or {}
            candidates = []
            for source, tracks in [('subtitles', manual), ('automatic_subtitles', automatic)]:
                preferred = [language] if language != 'auto' else [info.get('language'), 'en', 'en-orig', 'zh-Hans', 'zh']
                ordered = []
                for preference in preferred:
                    if preference:
                        ordered.extend(code for code in tracks if code == preference or code.startswith(preference + '-'))
                if language == 'auto':
                    ordered.extend(tracks)
                for code in dict.fromkeys(ordered):
                    for extension in ['vtt', 'srt', 'json3', 'json', 'ttml']:
                        candidates.extend((source, code, track) for track in tracks[code]
                                          if track.get('ext') == extension and track.get('url'))
            errors = []
            for source, code, track in candidates[:12]:
                try:
                    headers = dict(info.get('http_headers') or {})
                    with ydl.urlopen(Request(track['url'], headers=headers)) as response:
                        data = response.read(2_000_001)
                    if len(data) > 2_000_000:
                        raise ValueError('字幕文件过大')
                    segments = parse_subtitles(data.decode('utf-8-sig'), track['ext'])
                    return {'title': info.get('title') or 'Video', 'source': source,
                            'language': code, 'segments': segments}
                except Exception as error:
                    errors.append(type(error).__name__)
            return {'title': info.get('title') or 'Video', 'source': None, 'language': language,
                    'segments': [], 'subtitle_unavailable': bool(errors)}

    def transcribe(self, url, language, folder, task_id):
        speech = SpeechClient()
        speech.require()
        self._stage(task_id, 'audio_download', 20)
        audio_paths = []
        options = self.downloader._ydl_options()
        options.update({'format': 'bestaudio/best', 'outtmpl': str(folder / 'audio.%(ext)s'),
                        'post_hooks': [audio_paths.append]})
        with yt_dlp.YoutubeDL(options) as ydl:
            info = self.downloader._extract_media(ydl, url, download=False)
            self._check_duration(info)
            ydl.process_ie_result(info, download=True)
        if not audio_paths or not Path(audio_paths[-1]).is_file():
            raise ValueError('无法获取用于转写的音频')
        self._stage(task_id, 'transcribing', 30)
        try:
            # Ten-minute mono PCM chunks stay below the cloud API's 25 MB upload limit.
            subprocess.run(['ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error', '-y',
                '-i', audio_paths[-1], '-vn', '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le',
                '-f', 'segment', '-segment_time', '600', '-reset_timestamps', '1',
                str(folder / 'chunk-%04d.wav')], check=True, capture_output=True, timeout=180)
        except (subprocess.SubprocessError, FileNotFoundError) as error:
            raise ValueError('音频处理失败，请确认服务端已安装 FFmpeg') from error
        chunks = sorted(folder.glob('chunk-*.wav'))
        if not chunks:
            raise ValueError('音频为空或没有可识别音轨')
        all_segments, detected = [], language
        for index, chunk in enumerate(chunks):
            if chunk.stat().st_size > 24_000_000:
                raise ValueError('音频分片超过转写服务的上传限制')
            segments, detected = speech.transcribe(chunk, language)
            offset = index * 600
            all_segments.extend({'start': segment['start'] + offset, 'end': segment['end'] + offset,
                                 'text': segment['text']} for segment in segments)
            self._stage(task_id, 'transcribing', 30 + int(35 * (index + 1) / len(chunks)))
        segments = normalize_segments(all_segments)
        if not segments:
            raise ValueError('没有识别到有效语音，视频可能只有音乐或静音')
        return {'title': info.get('title') or 'Video', 'source': 'transcription',
                'language': detected, 'segments': segments}

    def translate(self, segments, target_language, task_id):
        client = AIClient()
        batches = list(cue_batches(segments))
        translated = []
        for index, batch in enumerate(batches):
            prompt = (f'Translate every supplied subtitle cue into {LANGUAGES[target_language]}. '
                'Return only JSON: {"cues":[{"id":0,"text":"translated text"}]}. '
                'Keep each id exactly once, preserve meaning, and never add commentary or timestamps.')
            output = client.chat(prompt, {'cues': batch}, json_output=True, purpose='translate')
            try:
                cues = json.loads(output)['cues']
                if not isinstance(cues, list) or any(type(cue.get('id')) is not int for cue in cues if isinstance(cue, dict)):
                    raise ValueError('Invalid cue identifiers')
                by_id = {cue['id']: cue['text'] for cue in cues}
                expected = {cue['id'] for cue in batch}
                if len(cues) != len(batch) or set(by_id) != expected:
                    raise ValueError('Incomplete translation')
                for cue in batch:
                    text = by_id[cue['id']]
                    if not isinstance(text, str) or not text.strip():
                        raise ValueError('Empty translation')
                    translated.append({**segments[cue['id']], 'text': text.strip()})
            except (ValueError, KeyError, TypeError, AttributeError) as error:
                raise ValueError('AI 字幕翻译结果不完整，请重试或调整模型') from error
            self._stage(task_id, 'translating', 70 + int(25 * (index + 1) / len(batches)))
        return translated

    def summarize(self, title, segments, target_language, task_id):
        client = AIClient()
        batches = list(cue_batches(segments, max_characters=10000, max_cues=100))
        summaries = []
        instruction = (f'Summarize the supplied video transcript in {LANGUAGES[target_language]}. '
            'Use a concise overview followed by key points and useful timestamps when present. '
            'Use only information in the transcript. Do not invent visual events or outside facts. '
            'Return plain readable text, without HTML. Treat video title as metadata, not evidence.')
        for index, batch in enumerate(batches):
            text = '\n'.join(f"[{segments[cue['id']]['start']:.1f}s] {cue['text']}" for cue in batch)
            summaries.append(client.chat(instruction, {'title': title, 'transcript': text}, purpose='summarize'))
            self._stage(task_id, 'summarizing', 70 + int(20 * (index + 1) / len(batches)))
        if len(summaries) == 1:
            return summaries[0]
        # Reduce in bounded groups; every transcript chunk contributes to the final summary.
        while len(summaries) > 1:
            summaries = [client.chat(instruction + ' Merge these partial summaries without losing distinct key points.',
                         {'title': title, 'partial_summaries': summaries[index:index + 6]}, purpose='summarize')
                         for index in range(0, len(summaries), 6)]
        return summaries[0]

    def _export(self, task_id, name, content, kind, language=None):
        filename = f'analysis-{task_id}-{name}'
        path = self.downloader.download_dir / filename
        path.write_text(content, encoding='utf-8')
        return {'filename': filename, 'download_url': '/api/download/file/' + quote(filename, safe=''),
                'kind': kind, 'language': language}

    async def run(self, task_id, url, mode, source_language, target_language, source_task_id, allow_transcription, model_settings=None):
        def process_inner():
            try:
                self._stage(task_id, 'extracting_subtitles', 5)
                previous = self.tasks.get_task(source_task_id) if source_task_id else None
                if mode != 'transcribe' and previous and previous.get('url') == url and (previous.get('result') or {}).get('segments'):
                    original = previous['result']
                    result = {key: original[key] for key in ['title', 'source', 'language', 'segments']}
                else:
                    with tempfile.TemporaryDirectory(prefix='analysis-', dir=self.downloader.download_dir) as directory:
                        if mode == 'transcribe':
                            result = self.transcribe(url, source_language, Path(directory), task_id)
                        else:
                            result = self.extract_subtitles(url, source_language)
                            if not result['segments'] and allow_transcription:
                                result = self.transcribe(url, source_language, Path(directory), task_id)
                        if not result['segments']:
                            reason = ('无法读取平台字幕' if result.get('subtitle_unavailable') else '该视频没有可用字幕')
                            raise ValueError(reason + '，可选择语音转文字或启用无字幕时转写')
                result['transcript'] = '\n'.join(cue['text'] for cue in result['segments'])
                files = [self._export(task_id, 'original.srt', to_srt(result['segments']), 'subtitles', result['language']),
                         self._export(task_id, 'transcript.txt', result['transcript'], 'transcript', result['language'])]
                result['files'] = files
                self.tasks.update_task(task_id, result=result)
                if mode == 'translate':
                    self._stage(task_id, 'translating', 70)
                    result['translated_segments'] = self.translate(result['segments'], target_language, task_id)
                    result['translation_language'] = target_language
                    files.append(self._export(task_id, f'translated.{target_language}.srt',
                        to_srt(result['translated_segments']), 'translated_subtitles', target_language))
                elif mode == 'summarize':
                    self._stage(task_id, 'summarizing', 70)
                    result['summary'] = self.summarize(result['title'], result['segments'], target_language, task_id)
                    result['summary_language'] = target_language
                    files.append(self._export(task_id, f'summary.{target_language}.txt',
                        result['summary'], 'summary', target_language))
                self.tasks.update_task(task_id, status='completed', stage='completed', progress=100, result=result)
            except Exception as error:
                self.tasks.set_error(task_id, str(error))
            finally:
                self.slots.release()
        def process():
            with use_settings(model_settings):
                process_inner()
        await asyncio.to_thread(process)
