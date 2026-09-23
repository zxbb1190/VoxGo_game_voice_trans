import unittest
from io import BytesIO
from unittest.mock import patch
from voxgo.analytics.uploader import HTTPTransport, NoRedirect

class Response(BytesIO):
    status = 403
    headers = {'Retry-After': '3600'}

class TransportTests(unittest.TestCase):
    def test_post_and_config_request_timeouts(self):
        with patch('urllib.request.build_opener') as opener:
            for method, path, timeout in [('GET', '/v1/config', 5),
                                          ('POST', '/v1/telemetry/sync', 15),
                                          ('POST', '/v1/telemetry/basic', 15)]:
                opener.return_value.open.return_value = Response(b'{}')
                HTTPTransport()(method, path, {'schema_version': 1} if method == 'POST' else None)
                self.assertEqual(opener.return_value.open.call_args.kwargs['timeout'], timeout)

    def test_https_origin_and_path_only(self):
        for origin in ['http://example.com', 'https://user:pass@example.com',
                       'https://example.com/x', 'https://example.com?secret=1']:
            with self.assertRaises(ValueError):
                HTTPTransport(origin)
        with self.assertRaises(ValueError):
            HTTPTransport()('GET', 'https://other.example/v1/config')

    def test_no_redirect_including_cross_origin(self):
        handler = NoRedirect()
        for status in [301, 302, 303, 307, 308]:
            self.assertIsNone(handler.redirect_request(None, None, status, '', {},
                                                       'https://other.example/collect'))

    def test_non_json_failure_preserves_status_for_backoff(self):
        with patch('urllib.request.build_opener') as opener:
            opener.return_value.open.return_value = Response(b'<html>Denied</html>')
            status, headers, data = HTTPTransport()('GET', '/v1/config')
            self.assertEqual(status, 403)
            self.assertIsNone(data)
            self.assertEqual(headers['Retry-After'], '3600')

    def test_response_byte_cap(self):
        with patch('urllib.request.build_opener') as opener:
            opener.return_value.open.return_value = Response(b'x' * 32769)
            with self.assertRaises(ValueError):
                HTTPTransport()('GET', '/v1/config')

    def test_exact_urls_and_host_survive_trailing_slash(self):
        with patch('urllib.request.build_opener') as opener:
            for method, path in [('GET', '/v1/config'), ('POST', '/v1/telemetry/sync')]:
                opener.return_value.open.return_value = Response(b'{}')
                HTTPTransport('https://api.voxgo.cn/')(method, path, {'schema_version': 1})
                request = opener.return_value.open.call_args.args[0]
                self.assertEqual(request.full_url, 'https://api.voxgo.cn' + path)
                self.assertEqual(request.host, 'api.voxgo.cn')

    def test_request_metadata_does_not_persist_body_or_private_url(self):
        import json
        import tempfile
        from pathlib import Path
        from voxgo.analytics.debug import AnalyticsDebug
        with tempfile.TemporaryDirectory() as folder:
            debug = AnalyticsDebug(folder)
            debug.update(config_request_url='https://api.voxgo.cn/v1/config',
                         config_http_status=200, config_server_header='cloudflare',
                         config_cf_ray='abc123-HKG', config_raw_enabled=True,
                         config_effective_enabled=True, config_attempt_at=123,
                         response_body='secret')
            debug.update(config_request_url='https://private.example/path?token=secret')
            data = json.loads((Path(folder) / 'debug-state.json').read_text())
            self.assertEqual(data['config_request_url'], 'https://api.voxgo.cn/v1/config')
            self.assertEqual(data['config_cf_ray'], 'abc123-HKG')
            self.assertNotIn('secret', json.dumps(data))
