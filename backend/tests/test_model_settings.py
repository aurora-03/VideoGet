import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from main import app
from services.ai_client import AIClient, SpeechClient
from services.model_settings import COOKIE, store, use_settings


class ModelSettingsTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'AI_PROVIDER': 'custom', 'CLOUD_PROTOCOL': 'openai',
            'CLOUD_BASE_URL': 'https://default.example/v1', 'CLOUD_API_KEY': 'server-test-secret',
            'CLOUD_TRANSLATION_MODEL': 'translate-default', 'CLOUD_SUMMARY_MODEL': 'summary-default',
            'ASR_BACKEND': 'api', 'ASR_MODEL': 'whisper-1', 'ASR_BASE_URL': '', 'ASR_API_KEY': '',
            'AI_API_KEY': '', 'AI_BASE_URL': '', 'AI_MODEL': '', 'ALLOWED_ORIGINS': 'http://localhost:3000'})
        self.env.start()
        self.client = TestClient(app)
        self.defaults = self.client.get('/api/ai/settings').json()

    def tearDown(self):
        self.env.stop()

    def payload(self, **changes):
        fields = {key: value for key, value in self.defaults.items() if key not in {'api_key_configured', 'asr_api_key_configured'}}
        return {**fields, **changes}

    def test_settings_never_return_secrets_and_cookie_is_httponly(self):
        response = self.client.get('/api/ai/settings')
        self.assertNotIn('server-test-secret', response.text)
        self.assertTrue(response.json()['api_key_configured'])
        self.assertIn('HttpOnly', response.headers['set-cookie'])
        self.assertIn('SameSite=strict', response.headers['set-cookie'])
        self.assertEqual(response.headers['cache-control'], 'no-store')

    def test_save_is_effective_only_in_own_session(self):
        other = TestClient(app)
        other.get('/api/ai/settings')
        response = self.client.post('/api/ai/settings', json=self.payload(
            base_url='https://session.example/v1', api_key='session-test-secret', summary_model='session-summary'))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('session-test-secret', response.text)
        profile = store.get(self.client.cookies.get(COOKIE))
        with use_settings(profile):
            self.assertEqual(AIClient().key, 'session-test-secret')
            self.assertEqual(AIClient().base_url, 'https://session.example/v1')
            self.assertEqual(AIClient().model_for('summarize'), 'session-summary')
        self.assertEqual(other.get('/api/ai/settings').json()['base_url'], 'https://default.example/v1')
        self.assertEqual(AIClient().key, 'server-test-secret')

    def test_changed_address_without_new_key_cannot_forward_server_secret(self):
        response = self.client.post('/api/ai/settings', json=self.payload(base_url='https://another.example/v1', api_key=''))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['settings']['api_key_configured'])
        self.assertFalse(response.json()['capabilities']['summary_ready'])

    def test_blank_key_retains_same_service_and_explicit_clear_removes_it(self):
        response = self.client.post('/api/ai/settings', json=self.payload(api_key='', summary_model='new-model'))
        self.assertTrue(response.json()['settings']['api_key_configured'])
        response = self.client.post('/api/ai/settings', json=self.payload(clear_api_key=True))
        self.assertFalse(response.json()['settings']['api_key_configured'])

    def test_foreign_speech_service_does_not_inherit_text_key(self):
        response = self.client.post('/api/ai/settings', json=self.payload(asr_base_url='https://speech.example/v1'))
        self.assertFalse(response.json()['capabilities']['speech_ready'])
        with use_settings(store.get(self.client.cookies.get(COOKIE))):
            self.assertEqual(SpeechClient().key, '')

    def test_validation_errors_do_not_echo_secret_input(self):
        response = self.client.post('/api/ai/settings', json=self.payload(api_key={'secret': 'sensitive-test-key'}))
        self.assertEqual(response.status_code, 422)
        self.assertNotIn('sensitive-test-key', response.text)

    def test_foreign_origin_cannot_change_configuration(self):
        response = self.client.post('/api/ai/settings', json=self.payload(), headers={'origin': 'https://foreign.example'})
        self.assertEqual(response.status_code, 403)

    def test_urls_with_embedded_credentials_are_rejected_without_echo(self):
        response = self.client.post('/api/ai/settings', json=self.payload(base_url='https://user:secret-value@example.com/v1'))
        self.assertEqual(response.status_code, 400)
        self.assertNotIn('secret-value', response.text)

    def test_local_text_and_independent_cloud_speech_defaults_are_preserved(self):
        with patch.dict(os.environ, {'AI_PROVIDER': 'ollama', 'AI_BASE_URL': 'http://localhost:11434/v1',
            'AI_MODEL': 'local', 'ASR_BASE_URL': 'https://speech.example/v1', 'ASR_API_KEY': 'speech-secret'}):
            client = TestClient(app)
            data = client.get('/api/ai/settings').json()
            with use_settings(store.get(client.cookies.get(COOKIE))):
                self.assertEqual(SpeechClient().base_url, 'https://speech.example/v1')
                self.assertEqual(SpeechClient().key, 'speech-secret')
            self.assertTrue(data['asr_api_key_configured'])

    def test_expired_or_missing_browser_session_does_not_fall_back(self):
        client = TestClient(app)
        response = client.get('/api/ai/capabilities', headers={'X-Model-Session': 'required'})
        self.assertEqual(response.status_code, 409)
        client.cookies.set(COOKIE, 'expired-token')
        self.assertEqual(client.post('/api/video/analyze', json={'url': 'https://example.com', 'mode': 'summarize'}).status_code, 409)

    def test_background_job_uses_saved_profile_not_process_environment(self):
        from api import routes
        import tempfile
        from pathlib import Path
        self.client.post('/api/ai/settings', json=self.payload(summary_model='session-model'))
        source = {'title': 'Test', 'source': 'subtitles', 'language': 'en',
                  'segments': [{'start': 0, 'end': 2, 'text': 'Test transcript.'}]}
        seen = []
        def chat(client, instruction, data, **kwargs):
            seen.append(client.model_for(kwargs.get('purpose')))
            return 'Test summary'
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'DOWNLOAD_DIR': directory}), \
             patch.object(routes.downloader, 'download_dir', Path(directory)), \
             patch.object(routes.video_analysis, 'extract_subtitles', return_value=source), \
             patch.object(AIClient, 'chat', chat):
            response = self.client.post('/api/video/analyze', json={'url': 'https://example.com/video', 'mode': 'summarize'})
            self.assertEqual(response.status_code, 200)
            task = self.client.get('/api/task/' + response.json()['task_id']).json()
        self.assertEqual(task['status'], 'completed')
        self.assertEqual(seen, ['session-model'])
        self.assertNotIn('server-test-secret', str(task))

    def test_openai_compatible_output_limit_uses_the_session_setting(self):
        from unittest.mock import Mock
        response = Mock(status_code=200)
        response.json.return_value = {'choices': [{'message': {'content': 'OK'}, 'finish_reason': 'stop'}]}
        self.client.post('/api/ai/settings', json=self.payload(max_output_tokens=3072))
        with use_settings(store.get(self.client.cookies.get(COOKIE))), patch('services.ai_client.requests.post', return_value=response) as post:
            AIClient().chat('Test', {}, purpose='summarize')
            self.assertEqual(post.call_args.kwargs['json']['max_tokens'], 3072)

    def test_default_output_limit_is_high_for_new_sessions_and_requests(self):
        from api.routes import ModelConfigRequest
        with patch.dict(os.environ, {'AI_MAX_OUTPUT_TOKENS': ''}):
            defaults = TestClient(app).get('/api/ai/settings').json()
            self.assertEqual(defaults['max_output_tokens'], 16384)
            self.assertEqual(ModelConfigRequest().max_output_tokens, 16384)

    def test_both_cloud_protocols_send_the_high_default_limit(self):
        from unittest.mock import Mock
        for protocol in ['openai', 'anthropic']:
            with self.subTest(protocol=protocol):
                response = Mock(status_code=200)
                response.json.return_value = ({'stop_reason': 'end_turn', 'content': [{'type': 'text', 'text': 'OK'}]}
                    if protocol == 'anthropic' else {'choices': [{'message': {'content': 'OK'}, 'finish_reason': 'stop'}]})
                with patch.dict(os.environ, {'AI_MAX_OUTPUT_TOKENS': '', 'CLOUD_PROTOCOL': protocol}), \
                     patch('services.ai_client.requests.post', return_value=response) as post:
                    AIClient().chat('Test', {}, purpose='summarize')
                    self.assertEqual(post.call_args.kwargs['json']['max_tokens'], 16384)


if __name__ == '__main__':
    unittest.main()
