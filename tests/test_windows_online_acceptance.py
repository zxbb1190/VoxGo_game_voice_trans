"""Native loopback protocol tests. No GUI, live key or origin network calls."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
import http.client
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts/windows_acceptance'
MODEL = 'tencent/Hunyuan-MT-7B'
TOKEN = 'local-acceptance-' + 'a' * 32
PRIVATE = 'PRIVATE-FIXTURE-CONTENT-MUST-NOT-BE-LOGGED'

FAKE_UPSTREAM = r'''
using System;
using System.IO;
using System.Text;
using System.Threading;
using VoxGoAcceptance;
public class FixtureUpstream : ITranslationUpstream {
    readonly string folder;
    public FixtureUpstream(string path) { folder = path; }
    public UpstreamReply Send(byte[] body) {
        File.AppendAllText(Path.Combine(folder, "fixture-count"), "1\n");
        File.WriteAllBytes(Path.Combine(folder, "fixture-last-request"), body);
        while (File.Exists(Path.Combine(folder, "fixture-block"))) Thread.Sleep(10);
        if (File.Exists(Path.Combine(folder, "fixture-throw"))) throw new Exception("FIXTURE-SECRET-DO-NOT-LOG");
        int status = File.Exists(Path.Combine(folder, "fixture-429")) ? 429 : 200;
        return new UpstreamReply(status, Encoding.UTF8.GetBytes("{\"choices\":[{\"message\":{\"content\":\"fixture-only\"}}],\"usage\":{\"prompt_tokens\":3,\"completion_tokens\":2,\"total_tokens\":5,\"unexpected\":\"PRIVATE-FIXTURE-CONTENT-MUST-NOT-BE-LOGGED\"}}"));
    }
}
'''


def payload(**changes):
    return {'model': MODEL, 'messages': [{'role': 'system', 'content': 'fixture'},
            {'role': 'user', 'content': PRIVATE}], 'max_tokens': 80,
            'temperature': 0, 'stream': False, **changes}


@unittest.skipUnless(os.name == 'nt', 'Windows PowerShell acceptance tools')
class OnlineRelayTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            self.port = sock.getsockname()[1]
        self.url = f'http://127.0.0.1:{self.port}'
        # C# using directives in the fixture must precede all namespace bodies.
        combined = (SCRIPTS / 'SiliconFlowRelay.cs').read_text(encoding='utf-8-sig') + '\n' + FAKE_UPSTREAM
        directives = sorted({line for line in combined.splitlines() if line.startswith('using ')})
        source = '\n'.join(directives) + '\n'
        source += '\n'.join(line for line in combined.splitlines() if not line.startswith('using '))
        (self.folder / 'Fixture.cs').write_text(source, encoding='utf-8-sig')
        script = self.folder / 'server.ps1'
        script.write_text('''param([int]$Port,[string]$Folder)
$ErrorActionPreference='Stop'
Add-Type -Path (Join-Path $Folder 'Fixture.cs') -ReferencedAssemblies 'System.Web.Extensions'
$upstream=[FixtureUpstream]::new($Folder)
$relay=[VoxGoAcceptance.OnlineRelay]::new($Port, 'TOKEN', 'fixture', $Folder, $upstream)
$relay.Run((Join-Path $Folder 'stop'))
'''.replace('TOKEN', TOKEN), encoding='utf-8-sig')
        self.server = subprocess.Popen(['powershell.exe', '-NoProfile', '-File', str(script),
                                       '-Port', str(self.port), '-Folder', str(self.folder)],
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.direct = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        for _ in range(100):
            try:
                self.health()
                return
            except OSError:
                if self.server.poll() is not None:
                    output = self.server.communicate(timeout=2)
                    self.temp.cleanup()
                    self.fail('Fixture relay did not compile/start: ' + repr(output))
                time.sleep(.05)
        self.tearDown()
        self.fail('Fixture relay startup timeout')

    def tearDown(self):
        (self.folder / 'stop').touch()
        (self.folder / 'fixture-block').unlink(missing_ok=True)
        try:
            self.server.communicate(timeout=4)
        except subprocess.TimeoutExpired:
            self.server.kill()
            self.server.communicate()
        self.temp.cleanup()

    def health(self):
        with self.direct.open(self.url + '/_acceptance/health', timeout=1) as response:
            return json.load(response)

    def send(self, body=None, path='/v1/chat/completions', token=TOKEN):
        data = json.dumps(payload() if body is None else body, ensure_ascii=False).encode('utf-8')
        request = urllib.request.Request(self.url + path, data=data,
                headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
        try:
            with self.direct.open(request, timeout=4) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as error:
            try:
                return error.code, error.read()
            except (ConnectionResetError, http.client.IncompleteRead):
                # Windows may reset a connection rejected before its request
                # body is consumed. The received HTTP status still proves the
                # gate rejected it; valid 200 responses must remain complete.
                return error.code, b''

    def count(self):
        path = self.folder / 'fixture-count'
        return len(path.read_text().splitlines()) if path.exists() else 0

    def test_telemetry_and_arbitrary_proxy_requests_never_reach_upstream(self):
        from voxgo.analytics.uploader import HTTPTransport
        connect = socket.create_connection
        def loopback_only(address, *args, **kwargs):
            if address[0] not in {'127.0.0.1', 'localhost'}:
                raise AssertionError('Origin network is forbidden')
            return connect(address, *args, **kwargs)
        with patch.dict(os.environ, {'HTTPS_PROXY': self.url, 'HTTP_PROXY': self.url,
                                    'NO_PROXY': '127.0.0.1,localhost'}), patch('socket.create_connection', loopback_only):
            with self.assertRaises(OSError):
                HTTPTransport()('POST', '/v1/telemetry/sync',
                    {'schema_version': 2, 'metrics': {f'fixture_{i}': 0 for i in range(63)}})
        self.assertEqual(self.send({'metrics': {'fixture_62': 0}}, '/v1/telemetry/sync')[0], 403)
        connection = http.client.HTTPConnection('127.0.0.1', self.port, timeout=2)
        connection.request('POST', 'http://example.invalid/v1/chat/completions', body=b'{}')
        self.assertEqual(connection.getresponse().status, 502)
        connection.close()
        self.assertEqual(self.count(), 0)
        self.assertEqual(self.health()['upstream_attempts'], 0)
        log = (self.folder / 'online-relay.jsonl').read_text()
        self.assertNotIn('fixture_62', log)
        self.assertNotIn(TOKEN, log)
        self.assertTrue(all(row['request_bytes'] == 0 for row in map(json.loads, log.splitlines())))

    def test_model_session_route_and_payload_validation_fail_closed(self):
        for body, path, token, status in (
            (payload(model='paid/other'), '/v1/chat/completions', TOKEN, 400),
            (payload(), '/v1/chat/completions', 'wrong', 401),
            (payload(), '/v1/chat/completions?url=https://example.invalid', TOKEN, 403),
            ({'schema_version': 2, 'metrics': {'fixture_62': 1}}, '/v1/chat/completions', TOKEN, 400),
            (payload(stream=True), '/v1/chat/completions', TOKEN, 400),
            (payload(tools=[]), '/v1/chat/completions', TOKEN, 400),
        ):
            with self.subTest(path=path, expected=status):
                self.assertEqual(self.send(body, path, token)[0], status)
        self.assertEqual(self.count(), 0)
        self.assertEqual(self.health()['upstream_attempts'], 0)

    def test_formal_provider_round_trip_preserves_prompt_and_language_without_real_key(self):
        from voxgo.translation import GameTranslator, TranslationConfig
        async def run():
            config = TranslationConfig(provider='openai_compatible', model=MODEL,
                endpoint=self.url + '/v1', api_key=TOKEN, source_lang='ja', target_lang='zh')
            client = GameTranslator(config)
            try:
                result = await client.translate_result('まだ入らないで、あと三秒。', detected_language='ja')
                self.assertEqual(result.translated, 'fixture-only')
            finally:
                await client.close()
        asyncio.run(run())
        actual = json.loads((self.folder / 'fixture-last-request').read_bytes())
        self.assertEqual(actual['model'], MODEL)
        self.assertIn('日文翻译成中文', actual['messages'][-1]['content'])
        self.assertIn('まだ入らないで、あと三秒。', actual['messages'][-1]['content'])
        self.assertEqual(actual['max_tokens'], 80)
        self.assertEqual(self.count(), 1)
        rows = [json.loads(line) for line in (self.folder / 'online-relay.jsonl').read_text().splitlines()]
        self.assertEqual([r['kind'] for r in rows], ['attempt_reserved', 'attempt_completed'])
        self.assertEqual(rows[-1]['total_tokens'], 5)
        self.assertNotIn('unexpected', rows[-1])

    def test_no_legacy_sixty_call_cap_and_no_content_or_credentials_in_journal(self):
        for _ in range(65):
            self.assertEqual(self.send()[0], 200)
        self.assertEqual(self.count(), 65)
        self.assertEqual(self.health()['upstream_attempts'], 65)
        self.assertIsNone(self.health()['budget_limit'])
        log = (self.folder / 'online-relay.jsonl').read_text()
        self.assertNotIn(PRIVATE, log)
        self.assertNotIn(TOKEN, log)
        self.assertEqual(len(log.splitlines()), 130)

    def test_busy_failure_and_http_error_are_not_retried(self):
        (self.folder / 'fixture-block').touch()
        with ThreadPoolExecutor(max_workers=1) as pool:
            first = pool.submit(self.send)
            for _ in range(100):
                if self.count() == 1:
                    break
                time.sleep(.01)
            self.assertEqual(self.count(), 1)
            self.assertEqual(self.send()[0], 429)
            self.assertEqual(self.count(), 1)
            (self.folder / 'fixture-block').unlink()
            self.assertEqual(first.result()[0], 200)
        (self.folder / 'fixture-429').touch()
        self.assertEqual(self.send()[0], 429)
        (self.folder / 'fixture-429').unlink()
        (self.folder / 'fixture-throw').touch()
        status, body = self.send()
        self.assertEqual(status, 502)
        self.assertNotIn(b'FIXTURE-SECRET', body)
        self.assertEqual(self.count(), 3)
        self.assertEqual(self.health()['upstream_attempts'], 3)

    def test_failed_reservation_prevents_any_upstream_call(self):
        # A directory at the journal path makes the pre-HTTP append fail.
        (self.folder / 'online-relay.jsonl').mkdir()
        with self.assertRaises(OSError):
            self.send()
        self.assertEqual(self.count(), 0)
        self.assertTrue(self.health()['journal_failed'])

    def test_browser_origin_duplicate_headers_and_unbounded_bodies_are_blocked(self):
        for extra, expected in (
            ('Origin: http://example.invalid\r\nContent-Length: 2\r\n', 403),
            ('Transfer-Encoding: chunked\r\n', 403),
            ('Authorization: Bearer duplicate\r\nContent-Length: 2\r\n', 400),
            ('Content-Length: 65537\r\n', 400),
            ('Content-Length: 2\r\nContent-Length: 2\r\n', 400),
        ):
            with self.subTest(headers=extra):
                request = (f'POST /v1/chat/completions HTTP/1.1\r\nHost: 127.0.0.1:{self.port}\r\n'
                    f'Authorization: Bearer {TOKEN}\r\nContent-Type: application/json\r\n' + extra + '\r\n')
                with socket.create_connection(('127.0.0.1', self.port), timeout=2) as connection:
                    connection.sendall(request.encode('ascii'))
                    response = connection.recv(1024)
                    self.assertEqual(int(response.split(b' ')[1]), expected)
        self.assertEqual(self.count(), 0)
        self.assertEqual(self.health()['upstream_attempts'], 0)


@unittest.skipUnless(os.name == 'nt', 'Windows PowerShell acceptance tools')
class OnlineLauncherPreflightTest(unittest.TestCase):
    def test_token_write_rotate_clear_preserves_settings_and_cleans_temporary_files(self):
        with tempfile.TemporaryDirectory(prefix='VoxGo token regression ') as folder:
            root = Path(folder) / '候选 目录'
            root.mkdir()
            original = {'app': {'telemetry_consent': 'denied', 'telemetry_epoch': ''},
                'translation': {'api_key': '', 'model': MODEL, 'source_lang': 'ja', 'target_lang': 'zh'},
                'whisper': {'model_size': 'base', 'beam_size': 1},
                'unknown_future_setting': {'label': '日/韩/俄 → 中文', 'values': [1, 2]}}
            settings = root / 'user_settings.json'
            settings.write_text(json.dumps(original, ensure_ascii=False), encoding='utf-8')
            common = str(SCRIPTS / 'OnlineAcceptance.Common.ps1').replace("'", "''")
            script = Path(folder) / 'token.ps1'
            script.write_text(f"""param([string]$Candidate)
. '{common}'
$path=Join-Path $Candidate 'user_settings.json'
$first='local-acceptance-' + ('a' * 32)
$second='local-acceptance-' + ('b' * 32)
Set-LocalAcceptanceToken $Candidate $first
if ((Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json).translation.api_key -cne $first) {{ throw 'First token was not written' }}
Set-LocalAcceptanceToken $Candidate $second
if ((Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json).translation.api_key -cne $second) {{ throw 'Token rotation failed' }}
Set-LocalAcceptanceToken $Candidate ''
'TOKEN_LIFECYCLE_OK'
""", encoding='utf-8-sig')
            result = subprocess.run(['powershell.exe', '-NoProfile', '-File', str(script), '-Candidate', str(root)],
                                    capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(b'TOKEN_LIFECYCLE_OK', result.stdout)
            self.assertEqual(json.loads(settings.read_text(encoding='utf-8')), original)
            self.assertEqual(list(root.glob('relay-settings-*')), [])

    def test_locked_settings_failure_preserves_original_and_cleans_temporary_file(self):
        with tempfile.TemporaryDirectory(prefix='VoxGo failed token regression ') as folder:
            root = Path(folder)
            settings = root / 'user_settings.json'
            original = b'{"translation":{"api_key":""},"app":{"telemetry_consent":"denied"}}'
            settings.write_bytes(original)
            common = str(SCRIPTS / 'OnlineAcceptance.Common.ps1').replace("'", "''")
            script = root / 'locked.ps1'
            script.write_text(f"""param([string]$Candidate)
. '{common}'
$lock=[IO.File]::OpenRead((Join-Path $Candidate 'user_settings.json'))
$failed=$false
try {{
    try {{ Set-LocalAcceptanceToken $Candidate ('local-acceptance-' + ('c' * 32)) }}
    catch {{ $failed=$true }}
}} finally {{ $lock.Dispose() }}
if (-not $failed) {{ throw 'The locked-file replacement unexpectedly succeeded' }}
'FAILED_WRITE_PRESERVED_ORIGINAL'
""", encoding='utf-8-sig')
            result = subprocess.run(['powershell.exe', '-NoProfile', '-File', str(script), '-Candidate', str(root)],
                                    capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(b'FAILED_WRITE_PRESERVED_ORIGINAL', result.stdout)
            self.assertEqual(settings.read_bytes(), original)
            self.assertEqual(list(root.glob('relay-settings-*')), [])

    def test_production_helper_with_fake_credential_exposes_only_health_and_gate(self):
        # Unlike a live-key process smoke, this uses only a synthetic credential.
        # No valid chat request is sent; the production upstream stays unused.
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            credential = root / 'fixture-settings.json'
            credential.write_text(json.dumps({'translation': {'provider': 'openai_compatible',
                'model': MODEL, 'endpoint': 'https://api.siliconflow.cn/v1/chat/completions',
                'api_key': 'fixture-credential-not-a-real-service-key'}}))
            with socket.socket() as probe:
                probe.bind(('127.0.0.1', 0))
                port = probe.getsockname()[1]
            environment = os.environ.copy()
            environment.update(VOXGO_ONLINE_SESSION_TOKEN=TOKEN, VOXGO_ONLINE_INSTANCE='a' * 32)
            server = subprocess.Popen(['powershell.exe', '-NoProfile', '-File', str(SCRIPTS / 'OnlineRelay.ps1'),
                '-Port', str(port), '-Evidence', str(root), '-StopFile', str(root / 'stop'),
                '-CredentialSettings', str(credential)], env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            direct = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            try:
                for _ in range(100):
                    try:
                        with direct.open(f'http://127.0.0.1:{port}/_acceptance/health', timeout=.5) as response:
                            health = json.load(response)
                        break
                    except OSError:
                        if server.poll() is not None:
                            self.fail('Production helper with fixture failed: ' + repr(server.communicate(timeout=2)))
                        time.sleep(.05)
                else:
                    self.fail('Production helper with fixture startup timeout')
                self.assertEqual(health['upstream_attempts'], 0)
                self.assertEqual(health['instance'], 'a' * 32)
                connection = http.client.HTTPConnection('127.0.0.1', port, timeout=2)
                connection.request('CONNECT', 'telemetry-fixture.invalid:443')
                self.assertEqual(connection.getresponse().status, 502)
                connection.close()
                with direct.open(f'http://127.0.0.1:{port}/_acceptance/health', timeout=1) as response:
                    health = json.load(response)
                self.assertEqual(health['upstream_attempts'], 0)
                self.assertEqual(health['blocked'], 1)
                log = (root / 'online-relay.jsonl').read_text()
                self.assertNotIn('fixture-credential', log)
                self.assertNotIn(TOKEN, log)
            finally:
                (root / 'stop').touch()
                try:
                    server.communicate(timeout=4)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.communicate()

    def test_saved_settings_inherit_baseline_but_cannot_override_network_guards(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            base = {'app': {'setup_completed': True, 'telemetry_consent': 'denied', 'telemetry_epoch': '', 'telemetry_consent_version': 3},
                    'translation': {'provider': 'openai_compatible', 'model': MODEL, 'endpoint': 'http://127.0.0.1:17854/v1', 'api_key': ''},
                    'whisper': {'local_files_only': True}, 'update': {'enabled': False}, 'websocket': {'host': '127.0.0.1'}}
            (root / 'acceptance.config.json').write_text(json.dumps(base))
            (root / 'telemetry_consent.json').write_text(json.dumps(base['app']))
            script = root / 'check.ps1'
            common = str(SCRIPTS / 'OnlineAcceptance.Common.ps1').replace("'", "''")
            script.write_text(f"param([string]$Candidate)\n. '{common}'\nTest-OnlineAcceptanceProfile $Candidate 17854\n'PROFILE_OK'\n", encoding='utf-8-sig')
            # Normal shipped whitelist excludes local_files_only/websocket.
            saved = {'app': base['app'], 'translation': base['translation'], 'whisper': {'model_size': 'small'}, 'update': {'enabled': False}}
            (root / 'user_settings.json').write_text(json.dumps(saved))
            command = ['powershell.exe', '-NoProfile', '-File', str(script), '-Candidate', str(root)]
            result = subprocess.run(command, capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(b'PROFILE_OK', result.stdout)
            saved['whisper']['local_files_only'] = False
            (root / 'user_settings.json').write_text(json.dumps(saved))
            result = subprocess.run(command, capture_output=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)

    def test_unsafe_profiles_and_credentials_stop_without_processes_or_network(self):
        for case in ('full', 'real_key', 'external_endpoint', 'other_model', 'wrong_credential', 'updates'):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                (root / 'control').mkdir()
                (root / 'candidate').mkdir()
                for name in ('Start-OnlineAcceptance.ps1', 'OnlineAcceptance.Common.ps1'):
                    shutil.copyfile(SCRIPTS / name, root / 'control' / name)
                config = {'app': {'setup_completed': True, 'telemetry_consent': 'denied', 'telemetry_epoch': '', 'telemetry_consent_version': 3},
                          'translation': {'provider': 'openai_compatible', 'model': MODEL, 'endpoint': 'http://127.0.0.1:17854/v1', 'api_key': ''},
                          'update': {'enabled': False}, 'whisper': {'local_files_only': True}, 'websocket': {'host': '127.0.0.1'}}
                source = {'translation': {'provider': 'openai_compatible', 'model': MODEL,
                          'endpoint': 'https://api.siliconflow.cn/v1/chat/completions', 'api_key': 'FIXTURE-REAL-KEY-NOT-TO-PRINT'}}
                if case == 'full': config['app']['telemetry_consent'] = 'allowed'
                if case == 'real_key': config['translation']['api_key'] = 'FIXTURE-REAL-KEY-NOT-TO-PRINT'
                if case == 'external_endpoint': config['translation']['endpoint'] = source['translation']['endpoint']
                if case == 'other_model': config['translation']['model'] = 'other'
                if case == 'wrong_credential': source['translation']['endpoint'] = 'https://another.invalid/v1'
                if case == 'updates': config['update']['enabled'] = True
                for name in ('user_settings.json', 'acceptance.config.json'):
                    (root / 'candidate' / name).write_text(json.dumps(config))
                (root / 'candidate' / 'telemetry_consent.json').write_text(json.dumps(config['app']))
                credential = root / 'source.json'
                credential.write_text(json.dumps(source))
                before = hashlib.sha256(credential.read_bytes()).digest()
                result = subprocess.run(['powershell.exe', '-NoProfile', '-File',
                    str(root / 'control' / 'Start-OnlineAcceptance.ps1'), '-CredentialSettings', str(credential)],
                    capture_output=True, timeout=10)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn(b'FIXTURE-REAL-KEY-NOT-TO-PRINT', result.stdout + result.stderr)
                self.assertEqual(hashlib.sha256(credential.read_bytes()).digest(), before)
                self.assertFalse((root / 'evidence').exists())


if __name__ == '__main__':
    unittest.main()
