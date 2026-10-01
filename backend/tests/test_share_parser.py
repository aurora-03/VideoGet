import json
import base64
import hashlib
import unittest
from unittest.mock import Mock, patch

from services.share_parser import SharePageParser, extract_page_state, solve_page_challenge


class ShareParserRegressionTests(unittest.TestCase):
    def setUp(self):
        self.parser = SharePageParser()

    def test_state_json_with_compact_assignment_and_escaped_braces(self):
        state = {'caption': 'A } and "quoted" title', 'photo': {'duration': 10}}
        html = '<script>window.INIT_STATE=' + json.dumps(state) + ';window.OTHER=1;</script>'
        self.assertEqual(extract_page_state(html, 'INIT_STATE'), state)

    def test_state_json_parse_wrapper(self):
        state = {'photo': {'caption': '测试'}}
        html = 'window.INIT_STATE = JSON.parse(' + json.dumps(json.dumps(state)) + ');'
        self.assertEqual(extract_page_state(html, 'INIT_STATE'), state)

    def test_state_does_not_execute_javascript(self):
        self.assertEqual(extract_page_state('window.INIT_STATE = alert("x")', 'INIT_STATE'), {})

    def test_guest_challenge_cookie_and_bounded_failure(self):
        encode = lambda value: base64.urlsafe_b64encode(value).decode().rstrip('=')
        data = {'v': {'a': encode(b'test-prefix'), 'c': encode(hashlib.sha256(b'test-prefix3').digest())}}
        page = 'var wci="guest_test",cs="' + encode(json.dumps(data).encode()) + '";'
        name, value = solve_page_challenge(page)
        self.assertEqual(name, 'guest_test')
        solved = json.loads(base64.b64decode(value))
        self.assertEqual(base64.b64decode(solved['d']), b'3')
        self.assertIsNone(solve_page_challenge('var wci="x",cs="invalid";'))

    def test_guest_challenge_cookie_is_set_on_the_response_host(self):
        session = Mock()
        session.get.side_effect = [Mock(text='challenge', url='https://www.iesdouyin.com/share/video/123'),
                                   Mock(text='video', url='https://www.iesdouyin.com/share/video/123')]
        with patch('services.share_parser.solve_page_challenge', return_value=('guest_test', 'value')):
            response = self.parser._get(session, 'https://www.iesdouyin.com/share/video/123')
        self.assertEqual(response.text, 'video')
        session.cookies.set.assert_called_once_with('guest_test', 'value', domain='www.iesdouyin.com', path='/')

    def test_domain_matching_rejects_lookalikes(self):
        for url in ['https://douyin.com.evil.test/video/12345678', 'https://notdouyin.com/video/12345678']:
            self.assertFalse(self.parser.supports(url))
        for url in ['https://v.douyin.com/abc/', 'https://v.kuaishou.com/abc/', 'https://m.gifshow.com/fw/photo/abc']:
            self.assertTrue(self.parser.supports(url))

    def test_douyin_guest_session_is_reused_after_empty_first_response(self):
        item = {'aweme_id': '6961737553342991651', 'desc': 'Test', 'video': {
            'duration': 19000, 'play_addr': {'url_list': ['https://video.example.com/playwm/1'], 'height': 720}}}
        first = 'window._ROUTER_DATA={"loaderData":{"video_(id)/page":{}}};'
        second = 'window._ROUTER_DATA=' + json.dumps({'loaderData': {
            'video_(id)/page': {'videoInfoRes': {'item_list': [item]}}}}) + ';'
        session = Mock()
        session.headers = {}
        with patch.object(self.parser, '_get', side_effect=[Mock(text=first), Mock(text=second)]) as get:
            info = self.parser._douyin(session, 'https://www.douyin.com/video/6961737553342991651')
        self.assertEqual(get.call_count, 2)
        self.assertTrue(all(call.args[0] is session for call in get.call_args_list))
        self.assertEqual(info['duration'], 19)
        self.assertEqual(info['formats'][0]['url'], 'https://video.example.com/playwm/1')

    def test_douyin_retries_temporary_shell_responses_within_a_bound(self):
        session = Mock()
        session.headers = {}
        item = {'aweme_id': '6961737553342991651', 'video': {'play_addr': {
            'url_list': ['https://video.example.com/a.mp4']}}}
        ready = 'window._ROUTER_DATA=' + json.dumps({'loaderData': {
            'page': {'videoInfoRes': {'item_list': [item]}}}})
        with patch('services.share_parser.time.sleep'), patch.object(
                self.parser, '_get', side_effect=[Mock(text='shell')] * 4 + [Mock(text=ready)]) as get:
            self.parser._douyin(session, 'https://www.douyin.com/video/6961737553342991651')
        self.assertEqual(get.call_count, 5)
        with patch('services.share_parser.time.sleep'), patch.object(
                self.parser, '_get', return_value=Mock(text='shell')) as get:
            with self.assertRaisesRegex(ValueError, '未返回视频数据'):
                self.parser._douyin(session, 'https://www.douyin.com/video/6961737553342991651')
        self.assertEqual(get.call_count, 6)

    def test_douyin_restricted_items_fail_instead_of_returning_fake_formats(self):
        html = 'window._ROUTER_DATA=' + json.dumps({'loaderData': {
            'video_(id)/page': {'videoInfoRes': {'filter_list': [{'filter_reason': 'PRIVATE'}]}}}})
        session = Mock()
        session.headers = {}
        with patch.object(self.parser, '_get', return_value=Mock(text=html)):
            with self.assertRaisesRegex(ValueError, '不可访问'):
                self.parser._douyin(session, 'https://www.douyin.com/video/6961737553342991651')

    def test_kuaishou_mobile_state_produces_real_formats_and_metadata(self):
        photo = {'photoId': '123', 'caption': '#测试', 'userName': '作者', 'duration': 33000,
                 'height': 720, 'width': 720, 'viewCount': 100, 'coverUrls': [{'url': 'https://img.example.com/a.jpg'}],
                 'mainMvUrls': [{'url': 'https://video.example.com/a.mp4'}], 'manifest': {
                     'adaptationSet': [{'representation': [{'url': 'https://video.example.com/b.mp4',
                                                           'height': 1080, 'fileSize': 5000}]}]}}
        html = 'window.INIT_STATE=' + json.dumps({'opaque-key': {'photo': photo}}) + ';'
        with patch.object(self.parser, '_get', return_value=Mock(text=html)):
            session = Mock()
            session.headers = {}
            info = self.parser._kuaishou(session, 'https://www.kuaishou.com/short-video/abc')
        self.assertEqual(info['duration'], 33)
        self.assertEqual(info['uploader'], '作者')
        self.assertEqual([f['height'] for f in info['formats']], [720, 1080])
        self.assertEqual(info['formats'][1]['filesize'], 5000)

    def test_images_without_video_addresses_are_not_reported_as_downloadable(self):
        with self.assertRaisesRegex(ValueError, '图文'):
            self.parser._douyin_media({'aweme_id': '123', 'video': {}}, 'https://www.douyin.com/note/123')
        with self.assertRaisesRegex(ValueError, '图文'):
            self.parser._kuaishou_media({'photoId': '123'}, 'https://www.kuaishou.com/short-video/abc')


if __name__ == '__main__':
    unittest.main()
