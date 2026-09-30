import tempfile
import unittest
from pathlib import Path

from scripts.release_preflight import (
    PreflightError,
    _class_defaults,
    audit_packaging_inputs,
    check_release_notes,
    check_version_plumbing,
    parse_requirement_names,
    validate_update_manifest,
)


class ReleasePreflightTests(unittest.TestCase):
    def test_requirement_parser_normalizes_names_and_ignores_options(self):
        names = parse_requirement_names(
            "numpy==1.24.3\nPyAudioWPatch==0.2.12.8\n"
            "qrcode[pil]==7.4.2\n-r requirements-dev.txt\n# comment\n"
        )
        self.assertEqual(names, {"numpy", "pyaudiowpatch", "qrcode"})

    def test_class_default_parser_resolves_unchanged_named_preset(self):
        source = (
            'FAST = "fast"\n'
            "class AudioConfig:\n"
            "    latency_mode: str = FAST\n"
            "    silence_limit_blocks: int = 3\n"
        )
        self.assertEqual(
            _class_defaults(source, "AudioConfig"),
            {"latency_mode": "fast", "silence_limit_blocks": 3},
        )

    def test_release_version_must_match_all_packaging_positions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            files = {
                "voxgo/app_info.py": 'APP_VERSION = "0.5.2"\n',
                "scripts/build_portable.ps1": '[string]$Version = "0.5.2"\n',
                "installer/VoxGo.iss": '#define MyAppVersion "0.5.2"\n',
                ".github/workflows/publish-release.yml": (
                    'description: "Release version, for example 0.5.2"\n'
                    'default: "0.5.2"\n'
                ),
            }
            for relative, content in files.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            check_version_plumbing(root, "0.5.2")
            (root / "installer/VoxGo.iss").write_text(
                '#define MyAppVersion "0.5.1"\n', encoding="utf-8"
            )
            with self.assertRaisesRegex(PreflightError, "installer version"):
                check_version_plumbing(root, "0.5.2")

    def test_release_notes_require_both_languages_and_real_publish_commands(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            notes = root / "docs/releases/v0.5.2.md"
            notes.parent.mkdir(parents=True)
            notes.write_text(
                "# VoxGo v0.5.2\n## 更新内容\n## What's new\n"
                '.\\scripts\\build_portable.ps1 -Version "0.5.2"\n'
                "git tag v0.5.2\ngit push origin v0.5.2\n",
                encoding="utf-8",
            )
            check_release_notes(root, "0.5.2")
            notes.write_text("# VoxGo v0.5.2\n## 更新内容\n", encoding="utf-8")
            with self.assertRaisesRegex(PreflightError, "What's new"):
                check_release_notes(root, "0.5.2")

    def test_update_manifest_must_match_selected_published_baseline(self):
        published = '{"latest":"0.6.0","channel":"stable"}'
        self.assertIn(
            "0.6.0",
            validate_update_manifest(published, published, "0.6.1", "origin/main"),
        )
        with self.assertRaisesRegex(PreflightError, "changed from origin/main"):
            validate_update_manifest(
                '{"latest":"0.6.1","channel":"stable"}',
                published,
                "0.6.1",
                "origin/main",
            )
        with self.assertRaisesRegex(PreflightError, "already points to 0.6.0"):
            validate_update_manifest(published, published, "0.6.0", "origin/main")

    def test_packaging_allows_only_runtime_data_and_staged_output(self):
        spec = '''
datas = [("assets/app.ico", "assets"), ("voxgo/mobile/static", "voxgo/mobile/static")]
excludes = ["tests", "diagnostics", "scripts"]
a = Analysis(["voxgo/app.py"], datas=datas, excludes=excludes)
'''
        build = 'Copy-Item -Recurse "dist\\VoxGo" $packageDir\nCompress-DirectoryWithRetry -SourceDir $packageDir\n'
        self.assertEqual(len(audit_packaging_inputs(spec, build)), 2)
        leaked_report = spec.replace(
            '("assets/app.ico", "assets")',
            '("diagnostics/asr-benchmark/report.json", "diagnostics")',
        )
        with self.assertRaisesRegex(PreflightError, "bundled as data"):
            audit_packaging_inputs(leaked_report, build)
        with self.assertRaisesRegex(PreflightError, "dist/VoxGo"):
            audit_packaging_inputs(spec, build.replace('"dist\\VoxGo"', '"."'))


if __name__ == "__main__":
    unittest.main()
