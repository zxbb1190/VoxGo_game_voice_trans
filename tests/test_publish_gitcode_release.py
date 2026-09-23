"""Local validation of GitCode's idempotent Lite mirror path."""

import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import publish_gitcode_release as module


class _Response:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        pass


class GitCodeReleaseTest(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.package = Path(self.temp.name) / "VoxGo-v0.5.1-lite.zip"
        self.package.write_bytes(b"official github zip")
        self.digest = hashlib.sha256(self.package.read_bytes()).hexdigest()
        self.url = (
            "https://gitcode.com/zxbb1190/VoxGo/releases/download/"
            "v0.5.1/VoxGo-v0.5.1-lite.zip"
        )

    def publish(self, **overrides):
        args = dict(tag="v0.5.1", package=self.package, notes="release notes",
                    token="secret-token", target_commitish=None,
                    expected_sha256=self.digest)
        args.update(overrides)
        return module.publish(**args)

    def test_existing_matching_attachment_is_idempotent(self):
        release = {"tag_name": "v0.5.1", "assets": [
            {"name": self.package.name, "browser_download_url": self.url}]}
        with patch.object(module, "_api_json", return_value=release) as api, \
                patch.object(module, "_remote_sha256", return_value=(self.digest, self.package.stat().st_size)):
            self.assertEqual(self.publish(), (self.url, self.digest, self.package.stat().st_size))
        api.assert_called_once()

    def test_existing_different_attachment_fails_without_upload(self):
        release = {"tag_name": "v0.5.1", "assets": [
            {"name": self.package.name, "browser_download_url": self.url}]}
        with patch.object(module, "_api_json", return_value=release) as api, \
                patch.object(module, "_remote_sha256", return_value=("0" * 64, self.package.stat().st_size)):
            with self.assertRaisesRegex(module.PublishError, "does not match"):
                self.publish()
        api.assert_called_once()

    def test_wrong_expected_hash_fails_before_network(self):
        with patch.object(module, "_api_json") as api:
            with self.assertRaisesRegex(module.PublishError, "expected GitHub SHA256"):
                self.publish(expected_sha256="0" * 64)
        api.assert_not_called()

    def test_missing_release_requires_exact_gitcode_commit(self):
        with patch.object(module, "_api_json", side_effect=module.PublishError("GitCode GET returned HTTP 404")):
            with self.assertRaisesRegex(module.PublishError, "target-commitish"):
                self.publish()

    def test_create_upload_and_verify(self):
        release = {"tag_name": "v0.5.1", "assets": []}
        completed = {"tag_name": "v0.5.1", "assets": [
            {"name": self.package.name, "browser_download_url": self.url}]}

        def api(path, token, **kwargs):
            self.assertEqual(token, "secret-token")
            if path == "/tags/v0.5.1" and not hasattr(api, "created"):
                raise module.PublishError("GitCode GET returned HTTP 404")
            if kwargs.get("method") == "POST":
                self.assertEqual(kwargs["payload"]["target_commitish"], "a" * 40)
                api.created = True
                return release
            if path.endswith("/upload_url"):
                return {"url": "https://upload.example.test/once", "headers": {"Content-Type": "application/zip"}}
            return completed

        with patch.object(module, "_api_json", side_effect=api), \
                patch.object(module, "_request", return_value=_Response()) as request, \
                patch.object(module, "_remote_sha256", return_value=(self.digest, self.package.stat().st_size)):
            self.assertEqual(self.publish(target_commitish="a" * 40)[0], self.url)
        self.assertEqual(request.call_count, 1)
        self.assertEqual(request.call_args.kwargs["method"], "PUT")
        self.assertEqual(request.call_args.kwargs["headers"]["Content-Length"], str(self.package.stat().st_size))


if __name__ == "__main__":
    unittest.main()
