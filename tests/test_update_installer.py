import hashlib
import io
import json
import os
import subprocess
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from voxgo.update import installer
from voxgo.update.checker import UpdateInfo


class FakeResponse(io.BytesIO):
    headers = {}

    def geturl(self):
        return 'https://release-assets.githubusercontent.com/download'


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def archive(self, additional=()):
        path = self.root / 'package.zip'
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('VoxGo-v0.4.2-lite/VoxGo.exe', b'program')
            archive.writestr('VoxGo-v0.4.2-lite/_internal/library.dll', b'library')
            for name, content in additional:
                archive.writestr(name, content)
        return path

    def test_portable_package_extracts_without_touching_installed_config(self):
        (self.root / 'config.json').write_text('secret')
        payload = installer.extract_package(self.archive(), self.root / 'extracted')
        self.assertEqual((payload / 'VoxGo.exe').read_bytes(), b'program')
        self.assertEqual((self.root / 'config.json').read_text(), 'secret')

    def test_windows_unsafe_paths_rejected_and_partial_payload_removed(self):
        for name in ('../escape', '/escape', 'C:/escape', 'root/../escape',
                     'root\\..\\escape', 'root/CON.txt', 'root/a:stream',
                     'root/space ', 'root/dot.', 'root//file'):
            with self.subTest(name=name):
                with self.assertRaises(installer.UpdateInstallError):
                    installer.extract_package(self.archive([(name, b'bad')]), self.root / 'out')
                self.assertFalse((self.root / 'out').exists())

    def test_symlink_rejected(self):
        link = zipfile.ZipInfo('root/link')
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        with self.assertRaises(installer.UpdateInstallError):
            installer.extract_package(self.archive([(link, '../outside')]), self.root / 'out')

    def test_case_collision_rejected(self):
        with self.assertRaises(installer.UpdateInstallError):
            installer.extract_package(self.archive([
                ('VoxGo-v0.4.2-lite/voxgo.exe', b'other')]), self.root / 'out')

    def test_extraction_limits_checked_before_writing_files(self):
        with patch.object(installer, 'MAX_EXTRACTED_BYTES', 1):
            with self.assertRaises(installer.UpdateInstallError):
                installer.extract_package(self.archive(), self.root / 'out')
        self.assertFalse((self.root / 'out').exists())

    def test_non_application_rejected(self):
        archive = self.root / 'bad.zip'
        with zipfile.ZipFile(archive, 'w') as package:
            package.writestr('something.txt', b'not an app')
        with self.assertRaises(installer.UpdateInstallError):
            installer.extract_package(archive, self.root / 'out')

    def test_mismatch_deletes_download(self):
        dest = self.root / 'download.zip'
        with patch.object(installer.urllib.request, 'build_opener') as opener:
            opener.return_value.open.return_value = FakeResponse(b'corrupt')
            with self.assertRaisesRegex(installer.UpdateInstallError, 'checksum mismatch'):
                installer.download_package('https://github.com/zxbb1190/VoxGo_game_voice_trans/releases/download/v1/a.zip',
                                           '0' * 64, dest)
        self.assertFalse(dest.exists())

    def test_verified_download_and_progress(self):
        data = b'verified'
        updates = []
        with patch.object(installer.urllib.request, 'build_opener') as opener:
            opener.return_value.open.return_value = FakeResponse(data)
            installer.download_package('https://github.com/zxbb1190/VoxGo_game_voice_trans/releases/download/v1/a.zip',
                                       hashlib.sha256(data).hexdigest(), self.root / 'ok.zip',
                                       lambda current, total: updates.append(current))
        self.assertEqual((self.root / 'ok.zip').read_bytes(), data)
        self.assertEqual(updates, [len(data)])

    def test_untrusted_urls_rejected(self):
        for url in ('http://github.com/zxbb1190/VoxGo_game_voice_trans/releases/download/v1/a.zip',
                    'https://github.com/attacker/repo/releases/download/v1/a.zip',
                    'https://github.com.evil.test/zxbb1190/VoxGo_game_voice_trans/releases/download/v1/a.zip'):
            with self.subTest(url=url), self.assertRaises(installer.UpdateInstallError):
                installer._validate_download_url(url)
        with self.assertRaises(installer.UpdateInstallError):
            installer._validate_download_url('https://evil.test/a.zip', redirected=True)

    def test_source_mode_does_not_download(self):
        with patch.object(installer, 'auto_update_supported', return_value=False), \
                patch.object(installer, 'download_package') as download:
            with self.assertRaises(installer.UpdateInstallError):
                installer.prepare_update(UpdateInfo(latest='0.4.2'))
            download.assert_not_called()

    def test_edition_detection(self):
        self.assertEqual(installer.detect_edition(self.root), 'lite')
        (self.root / '_internal/.models').mkdir(parents=True)
        self.assertEqual(installer.detect_edition(self.root), 'full')
        (self.root / 'runtime/cuda').mkdir(parents=True)
        self.assertEqual(installer.detect_edition(self.root), 'full-cuda')

    def test_preparation_failure_cleans_staging(self):
        stage = self.root / 'stage'
        stage.mkdir()
        with patch.object(installer, 'auto_update_supported', return_value=True), \
                patch.object(installer.tempfile, 'mkdtemp', return_value=str(stage)), \
                patch.object(installer, 'download_package', side_effect=OSError('offline')):
            with self.assertRaises(OSError):
                installer.prepare_update(UpdateInfo(latest='0.4.2'), edition='lite')
        self.assertFalse(stage.exists())


    @unittest.skipUnless(os.name == 'nt', 'Requires Windows PowerShell and process handles')
    def test_windows_transaction_preserves_data_and_rolls_back_bad_executable(self):
        powershell = str(Path(os.environ.get('SystemRoot', r'C:\Windows')) /
                         'System32/WindowsPowerShell/v1.0/powershell.exe')
        old = self.root / 'old.exe'
        source = self.root / 'dummy.cs'
        source.write_text('public class Program { public static void Main() { '
                          'System.Threading.Thread.Sleep(1800); } }')
        compile_script = self.root / 'compile.ps1'
        compile_script.write_text('param($Source,$Output)\nAdd-Type -Path $Source '
                                  '-OutputAssembly $Output -OutputType ConsoleApplication')
        subprocess.run([powershell, '-NoProfile', '-File', str(compile_script),
                        str(source), str(old)], check=True, capture_output=True)
        for valid in (True, False, 'cache-link', 'escaped-link'):
            with self.subTest(valid=valid):
                case = self.root / str(valid)
                app, payload, stage = case / 'app', case / 'payload', case / 'stage'
                for folder in (app, payload / '_internal', stage):
                    folder.mkdir(parents=True)
                (app / 'VoxGo.exe').write_bytes(old.read_bytes())
                (payload / 'VoxGo.exe').write_bytes(old.read_bytes() if valid is not False else b'invalid executable')
                (payload / 'new.txt').write_text('new')
                (app / 'old.txt').write_text('old')
                for relative in ('config.json', 'user_settings.json', '.models/model.bin',
                                 '.translation-models/model.bin', 'runtime/cuda/cuda.dll',
                                 '_internal/.models/whisper.bin'):
                    target = app / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text('user data')
                expected_success = valid in (True, 'cache-link')
                if valid in ('cache-link', 'escaped-link'):
                    link = app / '.models/snapshot.bin'
                    external = case / 'external.bin'
                    external.write_text('outside')
                    try:
                        link.symlink_to(app / '.models/model.bin' if valid == 'cache-link' else external)
                    except OSError as exc:
                        self.skipTest('Windows account cannot create model cache symlinks: ' + str(exc))
                plan = stage / 'plan.json'
                running = subprocess.Popen([str(app / 'VoxGo.exe')],
                                           creationflags=subprocess.CREATE_NO_WINDOW)
                plan.write_text(json.dumps({'pid': running.pid, 'app': str(app),
                                            'payload': str(payload),
                                            'preserve': installer.PRESERVE_PATHS}), encoding='utf-8')
                helper = stage / 'helper.ps1'
                helper.write_text(installer._HELPER, encoding='utf-8-sig')
                result = subprocess.run([powershell, '-NoProfile', '-ExecutionPolicy', 'Bypass',
                                         '-File', str(helper), '-PlanPath', str(plan)],
                                        capture_output=True, timeout=30)
                running.wait(timeout=10)
                self.assertTrue((stage / 'ready').exists(), result.stderr)
                self.assertEqual((app / 'config.json').read_text(), 'user data')
                self.assertEqual((app / '.translation-models/model.bin').read_text(), 'user data')
                self.assertEqual((app / 'runtime/cuda/cuda.dll').read_text(), 'user data')
                self.assertEqual((app / 'VoxGo.exe').read_bytes(), old.read_bytes())
                self.assertTrue((stage / ('success' if expected_success else 'failed')).exists(), result.stderr)
                self.assertEqual((app / 'new.txt').exists(), expected_success)
                self.assertEqual((app / 'old.txt').exists(), not expected_success)
                if valid == 'cache-link':
                    self.assertEqual((app / '.models/snapshot.bin').read_text(), 'user data')
                    self.assertFalse((app / '.models/snapshot.bin').is_symlink())
                # The relaunched fixture exits by itself; wait before TemporaryDirectory cleanup.
                waiter = stage / 'wait.ps1'
                waiter.write_text('param($Exe)\nGet-Process VoxGo -ErrorAction SilentlyContinue | '
                                  'Where-Object { $_.Path -eq $Exe } | '
                                  'Wait-Process -Timeout 20 -ErrorAction SilentlyContinue')
                subprocess.run([powershell, '-NoProfile', '-File', str(waiter),
                                str(app / 'VoxGo.exe')], capture_output=True, timeout=25)


if __name__ == '__main__':
    unittest.main()
