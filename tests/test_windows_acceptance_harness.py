"""No GUI automation: reject unsafe test configs and verify local-only fencing."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
import urllib.request
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts/windows_acceptance"


@unittest.skipUnless(os.name == "nt", "Windows PowerShell acceptance harness")
class WindowsAcceptanceHarnessTest(unittest.TestCase):
    def test_unsafe_settings_stop_before_any_candidate_or_server_start(self):
        for label, extra, consent, reason in (
            ("consent", {}, "allowed", b"Full telemetry must remain denied"),
            ("google_key", {"provider": "google", "api_key": "fixture"}, "denied", b"API Key must be empty"),
            ("external_endpoint", {"endpoint": "https://api.siliconflow.cn/v1"}, "denied", b"Only the local acceptance endpoint"),
        ):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as folder:
                base = Path(folder)
                (base/"control").mkdir()
                (base/"candidate").mkdir()
                shutil.copyfile(SCRIPTS/"Start-Acceptance.ps1", base/"control/Start-Acceptance.ps1")
                app = {"telemetry_consent":consent, "telemetry_epoch":""}
                translation = {"provider":"openai_compatible", "api_key":"", "endpoint":"http://127.0.0.1:17853/v1", **extra}
                (base/"candidate/user_settings.json").write_text(json.dumps({"app":app,"translation":translation}))
                (base/"candidate/telemetry_consent.json").write_text(json.dumps(app))
                result = subprocess.run(["powershell.exe", "-NoProfile", "-File", str(base/"control/Start-Acceptance.ps1")], capture_output=True, timeout=15)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(reason, result.stderr)
                self.assertFalse((base/"evidence/session.json").exists())

    def test_https_transport_cannot_forward_a_full_snapshot(self):
        from voxgo.analytics.uploader import HTTPTransport
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            with socket.socket() as probe:
                probe.bind(("127.0.0.1", 0))
                port = probe.getsockname()[1]
            stop = base/"stop"
            server = subprocess.Popen(["powershell.exe", "-NoProfile", "-File", str(SCRIPTS/"LocalOnlyServer.ps1"), "-Port", str(port), "-Evidence", str(base), "-StopFile", str(stop)], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            direct = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            url = f"http://127.0.0.1:{port}"
            try:
                for _ in range(100):
                    try:
                        health = json.load(direct.open(url+"/_acceptance/health", timeout=.5))
                        break
                    except OSError:
                        if server.poll() is not None:
                            self.fail("local rejection server failed to start")
                        time.sleep(.1)
                else:
                    self.fail("local rejection server never became healthy")
                self.assertEqual(health["external_forwarded"], 0)
                real_connect = socket.create_connection
                def local_only(address, *args, **kwargs):
                    if address[0] not in {"127.0.0.1", "localhost"}:
                        raise AssertionError("origin network connection prohibited")
                    return real_connect(address, *args, **kwargs)
                with patch.dict(os.environ, {"HTTPS_PROXY":url, "HTTP_PROXY":url, "NO_PROXY":"127.0.0.1,localhost"}), patch("socket.create_connection", local_only):
                    with self.assertRaises(OSError):
                        HTTPTransport()("POST", "/v1/telemetry/sync", {"schema_version":2,"metrics":{f"test_{i}":0 for i in range(63)}})
                health = json.load(direct.open(url+"/_acceptance/health", timeout=1))
                self.assertEqual(health["external_forwarded"], 0)
                self.assertEqual(health["blocked"], 1)
                log = (base/"local-only-server.jsonl").read_text(encoding="utf-8")
                self.assertIn('"body_bytes":0', log)  # CONNECT refused before TLS/body.
                self.assertNotIn("test_62", log)
            finally:
                stop.touch()
                try:
                    server.communicate(timeout=3)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.communicate()
