import asyncio
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from services.ai_client import AIClient, ConfigurationError, SpeechClient, capabilities
from services.downloader import VideoDownloader
from services.subtitles import cue_batches, parse_subtitles, to_srt
from services.task_manager import TaskManager
from services.video_analysis import VideoAnalysis


CUES = [{'start': 0.1, 'end': 2.5, 'text': 'Hello world.'}, {'start': 3.0, 'end': 4.0, 'text': 'Second line.'}]


class SubtitleTests(unittest.TestCase):
    def test_vtt_markup_and_settings_preserve_timing(self):
        result = parse_subtitles('WEBVTT\n\n00:00.100 --> 00:02.500 align:start\n<v Speaker>Hello &amp; <b>world</b>.</v>\n', 'vtt')
        self.assertEqual(result, [{'start': 0.1, 'end': 2.5, 'text': 'Hello & world.'}])

    def test_srt_roundtrip(self):
        self.assertEqual(parse_subtitles(to_srt(CUES), 'srt'), CUES)

    def test_youtube_json_and_bilibili_json(self):
        self.assertEqual(parse_subtitles(json.dumps({'events': [{'tStartMs': 100, 'dDurationMs': 2400,
            'segs': [{'utf8': 'Hello '}, {'utf8': 'world.'}]}]}), 'json3'), [CUES[0]])
        self.assertEqual(parse_subtitles(json.dumps({'body': [{'from': 0.1, 'to': 2.5, 'content': 'Hello world.'}]}), 'json'), [CUES[0]])

    def test_ttml(self):
        result = parse_subtitles('<tt xmlns="http://www.w3.org/ns/ttml"><body><p begin="00:00:00.100" end="00:00:02.500">Hello world.</p></body></tt>', 'ttml')
        self.assertEqual(result, [CUES[0]])

    def test_ttml_second_offsets_and_real_repetitions(self):
        result = parse_subtitles('<tt><p begin="100ms" end="2.5s">Hello world.</p></tt>', 'ttml')
        self.assertEqual(result, [CUES[0]])
        repeated = [{'start': 0, 'end': 1, 'text': 'Hello'}, {'start': 1, 'end': 2, 'text': 'Hello'}]
        self.assertEqual(len(parse_subtitles(to_srt(repeated), 'srt')), 2)

    def test_empty_captions_are_not_success(self):
        with self.assertRaisesRegex(ValueError, 'No readable'):
            parse_subtitles('WEBVTT\n\n', 'vtt')

    def test_batches_cover_every_cue_without_truncation(self):
        cues = [{'start': i, 'end': i + 1, 'text': '长文本' * 20} for i in range(120)]
        batches = list(cue_batches(cues, max_characters=200))
        self.assertEqual([cue['id'] for batch in batches for cue in batch], list(range(120)))
        self.assertTrue(all(sum(len(cue['text']) for cue in batch) <= 200 for batch in batches))


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {'AI_PROVIDER': 'openai', 'AI_API_KEY': '',
            'OPENAI_API_KEY': '', 'ASR_API_KEY': '', 'ASR_BACKEND': 'api', 'AI_MODEL': 'test-model'})
        self.environment.start()

    def tearDown(self):
        self.environment.stop()

    def test_missing_credentials_are_explicit(self):
        with self.assertRaises(ConfigurationError):
            AIClient().require_text()
        state = capabilities()
        self.assertFalse(state['text_ready'])
        self.assertFalse(state['speech_ready'])
        self.assertNotIn('key', state)

    def test_ollama_does_not_require_a_key(self):
        with patch.dict(os.environ, {'AI_PROVIDER': 'ollama', 'AI_MODEL': 'local-model'}):
            AIClient().require_text()

    def test_local_text_service_does_not_receive_inherited_cloud_credentials(self):
        with patch.dict(os.environ, {'AI_PROVIDER': 'ollama', 'AI_MODEL': 'local-model', 'OPENAI_API_KEY': 'cloud-secret'}):
            self.assertEqual(AIClient().key, '')

    def test_chat_protocol_json_and_secret_not_returned(self):
        response = Mock(status_code=200)
        response.json.return_value = {'choices': [{'finish_reason': 'stop', 'message': {'content': '{"cues":[]}'}}]}
        with patch.dict(os.environ, {'AI_API_KEY': 'test-secret'}), patch('services.ai_client.requests.post', return_value=response) as post:
            self.assertEqual(AIClient().chat('Return JSON', {'text': 'source'}, True), '{"cues":[]}')
            self.assertEqual(post.call_args.kwargs['json']['response_format'], {'type': 'json_object'})
            self.assertEqual(post.call_args.kwargs['headers']['Authorization'], 'Bearer test-secret')

    def test_authentication_errors_do_not_echo_provider_secrets(self):
        response = Mock(status_code=401)
        response.json.return_value = {'error': 'secret internal data'}
        with patch.dict(os.environ, {'AI_API_KEY': 'test-secret'}), patch('services.ai_client.requests.post', return_value=response):
            with self.assertRaisesRegex(ValueError, '鉴权失败') as error:
                AIClient().chat('Summarize', 'text')
            self.assertNotIn('secret', str(error.exception))

    def test_truncated_model_outputs_are_rejected(self):
        response = Mock(status_code=200)
        response.json.return_value = {'choices': [{'finish_reason': 'length', 'message': {'content': '{'}}]}
        with patch.dict(os.environ, {'AI_API_KEY': 'test-secret'}), patch('services.ai_client.requests.post', return_value=response):
            with self.assertRaisesRegex(ValueError, '截断'):
                AIClient().chat('Return JSON', {}, True)

    def test_cloud_transcription_uses_timestamped_response(self):
        response = Mock(status_code=200)
        response.json.return_value = {'language': 'en', 'segments': CUES}
        with tempfile.TemporaryDirectory() as directory:
            audio = Path(directory) / 'audio.wav'
            audio.write_bytes(b'RIFF-test')
            with patch.dict(os.environ, {'ASR_API_KEY': 'test-secret', 'ASR_MODEL': 'whisper-1'}), patch('services.ai_client.requests.post', return_value=response) as post:
                segments, language = SpeechClient().transcribe(audio)
                self.assertEqual(segments, CUES)
                self.assertEqual(language, 'en')
                self.assertEqual(post.call_args.kwargs['data']['response_format'], 'verbose_json')
                self.assertEqual(post.call_args.kwargs['data']['timestamp_granularities[]'], 'segment')

    def test_all_three_cloud_operations_share_address_key_and_select_their_models(self):
        config = {'AI_PROVIDER': 'custom', 'CLOUD_BASE_URL': 'https://cloud.example.test/v1/',
            'CLOUD_API_KEY': 'shared-test-key', 'CLOUD_ASR_MODEL': 'speech-model',
            'CLOUD_TRANSLATION_MODEL': 'translation-model', 'CLOUD_SUMMARY_MODEL': 'summary-model',
            'AI_BASE_URL': '', 'ASR_BASE_URL': '', 'AI_API_KEY': '', 'ASR_API_KEY': '', 'ASR_MODEL': ''}
        response = Mock(status_code=200)
        response.json.return_value = {'choices': [{'finish_reason': 'stop', 'message': {'content': 'OK'}}]}
        with patch.dict(os.environ, config), patch('services.ai_client.requests.post', return_value=response) as post:
            client = AIClient()
            client.chat('Translate', {}, purpose='translate')
            self.assertEqual(post.call_args.args[0], 'https://cloud.example.test/v1/chat/completions')
            self.assertEqual(post.call_args.kwargs['json']['model'], 'translation-model')
            self.assertEqual(post.call_args.kwargs['headers']['Authorization'], 'Bearer shared-test-key')
            client.chat('Summarize', {}, purpose='summarize')
            self.assertEqual(post.call_args.kwargs['json']['model'], 'summary-model')
            response.json.return_value = {'language': 'en', 'segments': CUES}
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'audio.wav'
                path.write_bytes(b'RIFF-test')
                SpeechClient().transcribe(path)
            self.assertEqual(post.call_args.args[0], 'https://cloud.example.test/v1/audio/transcriptions')
            self.assertEqual(post.call_args.kwargs['data']['model'], 'speech-model')
            self.assertEqual(post.call_args.kwargs['headers']['Authorization'], 'Bearer shared-test-key')

    def test_blank_override_settings_inherit_shared_cloud_config(self):
        with patch.dict(os.environ, {'AI_PROVIDER': 'custom', 'CLOUD_BASE_URL': 'https://cloud.example.test/v1',
            'CLOUD_API_KEY': 'shared-key', 'AI_API_KEY': '', 'ASR_API_KEY': '', 'AI_BASE_URL': '', 'ASR_BASE_URL': ''}):
            self.assertEqual(AIClient().key, 'shared-key')
            self.assertEqual(SpeechClient().key, 'shared-key')
            self.assertEqual(SpeechClient().base_url, 'https://cloud.example.test/v1')

    def test_speech_can_use_an_independent_provider(self):
        with patch.dict(os.environ, {'CLOUD_BASE_URL': 'https://text.example.test/v1', 'CLOUD_API_KEY': 'text-key',
            'ASR_BASE_URL': 'https://speech.example.test/v1', 'ASR_API_KEY': 'speech-key', 'ASR_MODEL': 'speech-model'}):
            speech = SpeechClient()
            self.assertEqual(speech.key, 'speech-key')
            self.assertEqual(speech.base_url, 'https://speech.example.test/v1')
            self.assertEqual(speech.model, 'speech-model')

    def test_custom_provider_never_uses_ambient_openai_credentials_or_address(self):
        with patch.dict(os.environ, {'AI_PROVIDER': 'custom', 'CLOUD_API_KEY': '', 'AI_API_KEY': '',
            'ASR_API_KEY': '', 'CLOUD_BASE_URL': '', 'AI_BASE_URL': '', 'ASR_BASE_URL': '',
            'OPENAI_API_KEY': 'unrelated-openai-key', 'OPENAI_BASE_URL': 'https://api.openai.com/v1'}):
            self.assertEqual(AIClient().key, '')
            self.assertEqual(SpeechClient().key, '')
            self.assertEqual(AIClient().base_url, '')
            with self.assertRaises(ConfigurationError):
                AIClient().require_text()

    def test_translation_and_summary_readiness_are_independent(self):
        with patch.dict(os.environ, {'AI_PROVIDER': 'custom', 'CLOUD_BASE_URL': 'https://cloud.example.test/v1',
            'CLOUD_API_KEY': 'test-key', 'CLOUD_TRANSLATION_MODEL': 'translator', 'CLOUD_SUMMARY_MODEL': '',
            'AI_MODEL': '', 'AI_BASE_URL': '', 'ASR_BASE_URL': '', 'CLOUD_ASR_MODEL': 'speech-model'}):
            state = capabilities()
            self.assertTrue(state['translation_ready'])
            self.assertFalse(state['summary_ready'])
            self.assertTrue(state['speech_ready'])

    def test_local_modes_do_not_use_cloud_models_or_credentials(self):
        with patch.dict(os.environ, {'AI_PROVIDER': 'ollama', 'AI_MODEL': 'local-text', 'AI_BASE_URL': '',
            'ASR_BACKEND': 'local', 'ASR_MODEL': '', 'CLOUD_BASE_URL': 'https://cloud.example.test/v1',
            'CLOUD_API_KEY': 'cloud-key', 'CLOUD_ASR_MODEL': 'cloud-speech'}):
            self.assertEqual(AIClient().base_url, 'http://localhost:11434/v1')
            self.assertEqual(AIClient().key, '')
            self.assertEqual(AIClient().model_for('translate'), 'local-text')
            self.assertEqual(SpeechClient().model, 'base')


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {'DOWNLOAD_DIR': self.directory.name, 'AI_API_KEY': 'test-secret'})
        self.env.start()
        self.tasks = TaskManager()
        self.downloader = VideoDownloader()
        self.analysis = VideoAnalysis(self.downloader, self.tasks)
        self.tasks.create_task('test', 'https://example.com/video')

    def tearDown(self):
        self.env.stop()
        self.directory.cleanup()

    def test_translation_keeps_timestamps_and_source_unchanged(self):
        with patch.object(AIClient, 'chat', return_value=json.dumps({'cues': [{'id': 0, 'text': '你好世界。'}, {'id': 1, 'text': '第二行。'}]})):
            result = self.analysis.translate(CUES, 'zh', 'test')
        self.assertEqual([(c['start'], c['end']) for c in result], [(c['start'], c['end']) for c in CUES])
        self.assertEqual(CUES[0]['text'], 'Hello world.')

    def test_missing_or_duplicate_translations_are_rejected(self):
        for cues in [[{'id': 0, 'text': 'one'}], [{'id': 0, 'text': 'one'}, {'id': 0, 'text': 'two'}]]:
            with patch.object(AIClient, 'chat', return_value=json.dumps({'cues': cues})):
                with self.assertRaisesRegex(ValueError, '不完整'):
                    self.analysis.translate(CUES, 'zh', 'test')

    def test_summary_includes_all_chunks_and_reduces(self):
        cues = [{'start': i, 'end': i + 1, 'text': 'content ' * 600} for i in range(5)]
        with patch.object(AIClient, 'chat', return_value='A grounded summary') as chat:
            self.assertEqual(self.analysis.summarize('Title', cues, 'en', 'test'), 'A grounded summary')
            self.assertGreater(chat.call_count, 1)
            partial_calls = [call for call in chat.call_args_list if 'transcript' in call.args[1]]
            self.assertTrue(any('[4.0s]' in call.args[1]['transcript'] for call in partial_calls))

    def test_existing_transcript_is_reused_and_files_exported(self):
        self.tasks.create_task('previous', 'https://example.com/video')
        self.tasks.update_task('previous', result={'title': 'Title', 'source': 'subtitles', 'language': 'en', 'segments': CUES})
        self.analysis.slots.acquire()
        with patch.object(self.analysis, 'extract_subtitles') as extract, patch.object(AIClient, 'chat', return_value='Summary'):
            asyncio.run(self.analysis.run('test', 'https://example.com/video', 'summarize', 'auto', 'en', 'previous', False))
        extract.assert_not_called()
        task = self.tasks.get_task('test')
        self.assertEqual(task['status'], 'completed')
        self.assertEqual(task['result']['summary'], 'Summary')
        self.assertEqual(len(task['result']['files']), 3)
        self.assertTrue(all((Path(self.directory.name) / file['filename']).is_file() for file in task['result']['files']))
        self.assertTrue(self.analysis.slots.acquire(blocking=False))
        self.analysis.slots.release()

    def test_no_captions_has_clear_error_and_releases_slot(self):
        self.analysis.slots.acquire()
        with patch.object(self.analysis, 'extract_subtitles', return_value={'title': 'Title', 'source': None, 'language': 'auto', 'segments': []}):
            asyncio.run(self.analysis.run('test', 'https://example.com/video', 'subtitles', 'auto', 'en', None, False))
        self.assertEqual(self.tasks.get_task('test')['status'], 'error')
        self.assertIn('没有可用字幕', self.tasks.get_task('test')['error'])
        self.assertTrue(self.analysis.slots.acquire(blocking=False))
        self.analysis.slots.release()

    def test_task_results_are_snapshots_during_background_updates(self):
        result = {'segments': [dict(CUES[0])]}
        self.tasks.update_task('test', result=result)
        result['segments'][0]['text'] = 'Changed outside the manager'
        self.assertEqual(self.tasks.get_task('test')['result']['segments'][0]['text'], 'Hello world.')
        snapshot = self.tasks.get_task('test')
        snapshot['result']['segments'].clear()
        self.assertEqual(len(self.tasks.get_task('test')['result']['segments']), 1)

    def test_failed_translation_retains_original_text_for_retry(self):
        self.analysis.slots.acquire()
        source = {'title': 'Title', 'source': 'subtitles', 'language': 'en', 'segments': CUES}
        with patch.object(self.analysis, 'extract_subtitles', return_value=source), patch.object(AIClient, 'chat', side_effect=ValueError('provider failed')):
            asyncio.run(self.analysis.run('test', 'https://example.com/video', 'translate', 'auto', 'zh', None, False))
        task = self.tasks.get_task('test')
        self.assertEqual(task['status'], 'error')
        self.assertEqual(task['result']['segments'], CUES)
        self.assertEqual(len(task['result']['files']), 2)

    def test_speech_chunks_restore_original_timestamps(self):
        folder = Path(self.directory.name)
        audio = folder / 'audio.webm'
        audio.write_bytes(b'audio')
        ydl = Mock()
        ydl.__enter__ = Mock(return_value=ydl)
        ydl.__exit__ = Mock(return_value=False)
        def process(info, download):
            for hook in ydl_options['post_hooks']:
                hook(str(audio))
        ydl_options = {}
        def create(options):
            ydl_options.update(options)
            return ydl
        ydl.process_ie_result.side_effect = process
        def split(*args, **kwargs):
            (folder / 'chunk-0000.wav').write_bytes(b'first')
            (folder / 'chunk-0001.wav').write_bytes(b'second')
        with patch('services.video_analysis.yt_dlp.YoutubeDL', side_effect=create), \
             patch.object(self.downloader, '_extract_media', return_value={'title': 'Test', 'duration': 610}), \
             patch('services.video_analysis.subprocess.run', side_effect=split), \
             patch.object(SpeechClient, 'require'), \
             patch.object(SpeechClient, 'transcribe', return_value=([{'start': 1, 'end': 2, 'text': 'Speech'}], 'en')):
            result = self.analysis.transcribe('https://example.com/video', 'auto', folder, 'test')
        self.assertEqual([cue['start'] for cue in result['segments']], [1, 601])
        self.assertEqual([cue['end'] for cue in result['segments']], [2, 602])


class AnalysisAPITests(unittest.TestCase):
    def setUp(self):
        from main import app
        from api import routes
        from fastapi.testclient import TestClient
        self.directory = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {'DOWNLOAD_DIR': self.directory.name, 'AI_PROVIDER': 'openai',
            'AI_API_KEY': 'test-key', 'ASR_API_KEY': '', 'ASR_BACKEND': 'api'})
        self.env.start()
        self.path = patch.object(routes.downloader, 'download_dir', Path(self.directory.name))
        self.path.start()
        self.client = TestClient(app)
        self.url = 'https://example.com/video'

    def tearDown(self):
        self.path.stop()
        self.env.stop()
        self.directory.cleanup()

    def job(self, **arguments):
        response = self.client.post('/api/video/analyze', json={'url': self.url, **arguments})
        self.assertEqual(response.status_code, 200, response.text)
        task_id = response.json()['task_id']
        return task_id, self.client.get('/api/task/' + task_id).json()

    def test_caption_translate_summary_api_and_file_delivery(self):
        from api import routes
        source = {'title': 'Test', 'source': 'subtitles', 'language': 'en', 'segments': CUES}
        with patch.object(routes.video_analysis, 'extract_subtitles', return_value=source) as extract:
            original_id, original = self.job(mode='subtitles')
            self.assertEqual(original['status'], 'completed')
            with patch.object(AIClient, 'chat', return_value=json.dumps({'cues': [{'id': 0, 'text': '你好。'}, {'id': 1, 'text': '第二行。'}]})):
                translated_id, translated = self.job(mode='translate', target_language='zh', source_task_id=original_id)
            with patch.object(AIClient, 'chat', return_value='A transcript-based summary'):
                _, summary = self.job(mode='summarize', target_language='en', source_task_id=translated_id)
        self.assertEqual(extract.call_count, 1)
        self.assertEqual(translated['status'], 'completed')
        self.assertEqual(summary['status'], 'completed')
        self.assertEqual(summary['result']['summary'], 'A transcript-based summary')
        for task in [original, translated, summary]:
            for file in task['result']['files']:
                response = self.client.get(file['download_url'])
                self.assertEqual(response.status_code, 200)
                self.assertGreater(len(response.content), 0)
        file = next(f for f in translated['result']['files'] if f['kind'] == 'translated_subtitles')
        text = self.client.get(file['download_url']).content.decode('utf-8')
        self.assertIn('00:00:00,100 --> 00:00:02,500', text)
        self.assertIn('你好。', text)

    def test_missing_key_is_503_before_fetching_media(self):
        from api import routes
        with patch.dict(os.environ, {'AI_API_KEY': '', 'OPENAI_API_KEY': ''}), patch.object(routes.video_analysis, 'extract_subtitles') as extract:
            response = self.client.post('/api/video/analyze', json={'url': self.url, 'mode': 'summarize'})
        self.assertEqual(response.status_code, 503)
        extract.assert_not_called()

    def test_speech_fallback_does_not_require_service_when_captions_exist(self):
        from api import routes
        source = {'title': 'Test', 'source': 'subtitles', 'language': 'en', 'segments': CUES}
        with patch.dict(os.environ, {'AI_API_KEY': '', 'OPENAI_API_KEY': '', 'ASR_API_KEY': ''}), \
             patch.object(routes.video_analysis, 'extract_subtitles', return_value=source), \
             patch.object(routes.video_analysis, 'transcribe') as transcribe:
            _, task = self.job(mode='subtitles', allow_transcription=True)
        self.assertEqual(task['status'], 'completed')
        transcribe.assert_not_called()

    def test_invalid_modes_languages_and_foreign_transcripts_are_rejected(self):
        for arguments in [{'mode': 'unknown'}, {'mode': 'translate', 'target_language': 'unknown'}]:
            response = self.client.post('/api/video/analyze', json={'url': self.url, **arguments})
            self.assertEqual(response.status_code, 422)
        import uuid
        response = self.client.post('/api/video/analyze', json={'url': self.url, 'source_task_id': str(uuid.uuid4())})
        self.assertEqual(response.status_code, 400)

    def test_no_captions_is_reported_in_task(self):
        from api import routes
        with patch.object(routes.video_analysis, 'extract_subtitles', return_value={'title': 'Test', 'source': None, 'language': 'auto', 'segments': []}):
            _, task = self.job(mode='subtitles')
        self.assertEqual(task['status'], 'error')
        self.assertIn('没有可用字幕', task['error'])
        self.assertIsNone(task['result'])

    def test_busy_analysis_service_returns_429(self):
        from api import routes
        routes.video_analysis.slots.acquire()
        routes.video_analysis.slots.acquire()
        try:
            response = self.client.post('/api/video/analyze', json={'url': self.url})
            self.assertEqual(response.status_code, 429)
        finally:
            routes.video_analysis.slots.release()
            routes.video_analysis.slots.release()


if __name__ == '__main__':
    unittest.main()
