import asyncio
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from services.downloader import VideoDownloader
from services.task_manager import TaskManager


class DownloadRegressionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {'DOWNLOAD_DIR': self.directory.name})
        self.env.start()
        self.downloader = VideoDownloader()

    def tearDown(self):
        self.env.stop()
        self.directory.cleanup()

    def test_missing_height_offers_best_instead_of_invented_resolutions(self):
        info = {'duration': 3, 'formats': [{'url': 'https://example.com/video.mp4', 'ext': 'mp4'}]}
        formats = self.downloader._get_available_formats(info)
        self.assertEqual([f['quality'] for f in formats], ['best'])
        self.assertEqual(formats[0]['size'], '未知')

    def test_storyboards_are_not_downloadable_video_qualities(self):
        info = {'duration': 7, 'formats': [
            {'height': 27, 'vcodec': 'none', 'acodec': 'none', 'ext': 'mhtml'},
            {'height': 720, 'vcodec': 'h264', 'acodec': 'aac', 'filesize': 1200000},
        ]}
        self.assertEqual([f['quality'] for f in self.downloader._get_available_formats(info)], ['720p'])

    def test_unknown_duration_does_not_invent_huge_file_sizes(self):
        formats = self.downloader._get_available_formats({'formats': [{'height': 1280, 'vcodec': 'h264'}]})
        self.assertEqual(formats[0]['size'], '未知')

    def test_all_numeric_qualities_have_a_height_limit(self):
        for quality in ['360p', '540p', '840p', '1024p', '1280p', '4320p']:
            self.assertIn('height<=?', self.downloader._format_selector(quality))
            self.assertIn(quality[:-1], self.downloader._format_selector(quality))

    def test_selector_accepts_unknown_height_and_keeps_numeric_quality_limit(self):
        import yt_dlp
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            select = ydl.build_format_selector(self.downloader._format_selector('360p'))
            formats = [
                {'format_id': 'small', 'url': 'https://example.com/small.mp4', 'height': 360,
                 'vcodec': 'h264', 'acodec': 'aac', 'ext': 'mp4'},
                {'format_id': 'large', 'url': 'https://example.com/large.mp4', 'height': 720,
                 'vcodec': 'h264', 'acodec': 'aac', 'ext': 'mp4'},
            ]
            self.assertEqual(list(select({'formats': formats, 'incomplete_formats': False}))[0]['format_id'], 'small')
            unknown = dict(formats[0], format_id='facebook')
            unknown.pop('height')
            self.assertEqual(list(select({'formats': [unknown], 'incomplete_formats': False}))[0]['format_id'], 'facebook')

    def test_vimeo_preserves_unlisted_hash_in_player_fallback(self):
        self.assertEqual(self.downloader._vimeo_player_url('https://vimeo.com/123456/abcdef1234'),
                         'https://player.vimeo.com/video/123456?h=abcdef1234')
        self.assertIsNone(self.downloader._vimeo_player_url('https://vimeo.com.evil.test/123456'))
        self.assertIsNone(self.downloader._vimeo_player_url('https://player.vimeo.com/video/123456'))

    def test_final_file_uses_postprocessing_path(self):
        target = Path(self.directory.name) / '#音频 ? converted.mp3'
        def extract(downloader, ydl, url, download):
            target.write_bytes(b'test-audio')
            for hook in ydl.params['post_hooks']:
                hook(str(target))
            return {'id': 'test', 'title': 'original', 'ext': 'webm'}
        tasks = TaskManager()
        tasks.create_task('audio', 'https://example.com/video')
        with patch.object(VideoDownloader, '_extract_media', extract):
            asyncio.run(self.downloader.download_video('audio', 'https://example.com/video', only_audio=True, task_manager=tasks))
        self.assertEqual(tasks.get_task('audio')['filename'], '#音频 ? converted.mp3')
        self.assertEqual(tasks.get_task('audio')['status'], 'completed')
        from fastapi.testclient import TestClient
        from main import app
        with TestClient(app) as client:
            response = client.get(tasks.get_task('audio')['download_url'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'test-audio')

    def test_missing_output_is_not_reported_as_completed(self):
        tasks = TaskManager()
        tasks.create_task('missing', 'https://example.com/video')
        with patch.object(VideoDownloader, '_extract_media', return_value={'id': 'test', 'title': 'test', 'ext': 'mp4'}):
            asyncio.run(self.downloader.download_video('missing', 'https://example.com/video', task_manager=tasks))
        self.assertEqual(tasks.get_task('missing')['status'], 'error')

    def test_download_exposes_subtitle_files_or_missing_caption_warning(self):
        for has_subtitles in [True, False]:
            tasks = TaskManager()
            tasks.create_task('caption-download', 'https://example.com/video')
            def extract(downloader, ydl, url, download):
                filename = ydl.prepare_filename({'title': 'test', 'id': 'test', 'ext': 'mp4'})
                media = Path(filename)
                media.write_bytes(b'video')
                if has_subtitles:
                    media.with_suffix('.en.vtt').write_text('WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nCaption\n')
                for hook in ydl.params['post_hooks']:
                    hook(str(media))
                return {'id': 'test', 'title': 'test', 'ext': 'mp4'}
            with patch.object(VideoDownloader, '_extract_media', extract):
                asyncio.run(self.downloader.download_video('caption-download', 'https://example.com/video',
                    download_subtitle=True, task_manager=tasks))
            task = tasks.get_task('caption-download')
            self.assertEqual(task['status'], 'completed', task.get('error'))
            self.assertEqual(len(task['subtitle_files']), 1 if has_subtitles else 0)
            self.assertEqual(len(task['warnings']), 0 if has_subtitles else 1)

    def test_vimeo_retries_player_for_both_info_and_download(self):
        from yt_dlp.utils import DownloadError
        for download in [False, True]:
            from unittest.mock import Mock
            ydl = Mock()
            ydl.extract_info.side_effect = [DownloadError('login required'), {'id': '123456'}]
            self.assertEqual(self.downloader._extract_media(ydl, 'https://vimeo.com/123456', download), {'id': '123456'})
            self.assertEqual(ydl.extract_info.call_args.args, ('https://player.vimeo.com/video/123456',))
            self.assertEqual(ydl.extract_info.call_args.kwargs, {'download': download})


if __name__ == '__main__':
    unittest.main()
