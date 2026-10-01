"""Browser-session model profiles; never expose or persist entered API keys."""

from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
import secrets
import threading
import time


overrides = ContextVar('model_settings', default=None)
COOKIE = 'videoget_model_session'
LIFETIME = 7200


@contextmanager
def use_settings(profile):
    token = overrides.set(profile)
    try:
        yield
    finally:
        overrides.reset(token)


class ModelSettingsStore:
    def __init__(self):
        self._profiles = {}
        self._lock = threading.Lock()

    def _prune(self):
        now = time.monotonic()
        self._profiles = {key: value for key, value in self._profiles.items() if value[0] > now}

    def get(self, token):
        with self._lock:
            self._prune()
            value = self._profiles.get(token)
            return deepcopy(value[1]) if value else None

    def save(self, token, profile):
        with self._lock:
            self._prune()
            if token not in self._profiles:
                if len(self._profiles) >= 256:
                    raise ValueError('模型配置会话过多，请稍后重试')
                token = secrets.token_urlsafe(32)
            self._profiles[token] = (time.monotonic() + LIFETIME, deepcopy(profile))
            return token


store = ModelSettingsStore()


def initial_profile():
    from services.ai_client import AIClient, SpeechClient, setting
    text, speech = AIClient(), SpeechClient()
    speech_address = setting('ASR_BASE_URL')
    speech_key = setting('ASR_API_KEY')
    if speech.backend == 'api' and speech.base_url != text.base_url:
        speech_address, speech_key = speech.base_url, speech.key
    return {'AI_PROVIDER': text.provider, 'CLOUD_BASE_URL': text.base_url,
        'CLOUD_PROTOCOL': text.protocol, 'CLOUD_API_KEY': text.key,
        'CLOUD_TRANSLATION_MODEL': text.model_for('translate'),
        'CLOUD_SUMMARY_MODEL': text.model_for('summarize'),
        'AI_MAX_OUTPUT_TOKENS': setting('AI_MAX_OUTPUT_TOKENS', default='16384'),
        'AI_BASE_URL': '', 'AI_API_KEY': '', 'AI_MODEL': text.model if text.provider == 'ollama' else '',
        'ASR_BACKEND': speech.backend, 'ASR_MODEL': speech.model, 'CLOUD_ASR_MODEL': '',
        'ASR_BASE_URL': speech_address, 'ASR_API_KEY': speech_key,
        'OPENAI_API_KEY': '', 'OPENAI_BASE_URL': ''}


def public_profile(profile):
    return {'provider': profile['AI_PROVIDER'], 'base_url': profile['CLOUD_BASE_URL'],
        'protocol': profile['CLOUD_PROTOCOL'], 'translation_model': profile['CLOUD_TRANSLATION_MODEL'],
        'summary_model': profile['CLOUD_SUMMARY_MODEL'], 'max_output_tokens': int(profile['AI_MAX_OUTPUT_TOKENS']),
        'api_key_configured': bool(profile['CLOUD_API_KEY']), 'asr_backend': profile['ASR_BACKEND'],
        'asr_base_url': profile['ASR_BASE_URL'], 'asr_model': profile['ASR_MODEL'],
        'asr_api_key_configured': bool(profile['ASR_API_KEY'])}
