import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from scripts.archive_portable import archive_directory


class PortableArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'VoxGo-v0.6.0-full'
        self.source.mkdir()
        self.destination = self.root / 'package.zip'

    def test_root_layout_unicode_empty_directory_and_binary_crc(self):
        (self.source / '_internal').mkdir()
        (self.source / 'empty').mkdir()
        binary = self.source / '_internal' / '模型.bin'
        with binary.open('wb') as stream:
            for i in range(64):
                stream.write(bytes(range(256)) * 256)
        (self.source / 'VoxGo.exe').write_bytes(b'fixture executable')
        archive_directory(self.source, self.destination)
        with zipfile.ZipFile(self.destination) as archive:
            self.assertIsNone(archive.testzip())
            self.assertIn(self.source.name + '/empty/', archive.namelist())
            self.assertEqual(hashlib.sha256(archive.read(self.source.name + '/_internal/模型.bin')).digest(),
                             hashlib.sha256(binary.read_bytes()).digest())
            self.assertEqual(archive.read(self.source.name + '/VoxGo.exe'), b'fixture executable')

    def test_existing_archive_is_never_replaced(self):
        self.destination.write_bytes(b'existing valid release')
        with self.assertRaises(FileExistsError):
            archive_directory(self.source, self.destination)
        self.assertEqual(self.destination.read_bytes(), b'existing valid release')

    def test_destination_inside_payload_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'outside'):
            archive_directory(self.source, self.source / 'recursive.zip')
        self.assertEqual(list(self.source.iterdir()), [])

    def test_disk_write_failure_keeps_source_and_cleans_partial_archive(self):
        original = self.source / 'VoxGo.exe'
        original.write_bytes(b'keep me')
        with patch('scripts.archive_portable.zipfile.ZipFile.write', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                archive_directory(self.source, self.destination)
        self.assertEqual(original.read_bytes(), b'keep me')
        self.assertFalse(self.destination.exists())
        self.assertEqual(list(self.root.glob('*.partial')), [])

    def test_link_cannot_include_external_private_files(self):
        external = self.root / 'private.txt'
        external.write_text('private fixture', encoding='utf-8')
        try:
            (self.source / 'link.txt').symlink_to(external)
        except OSError as exc:
            self.skipTest('Symlink permission unavailable: ' + type(exc).__name__)
        with self.assertRaisesRegex(ValueError, 'link or reparse'):
            archive_directory(self.source, self.destination)
        self.assertFalse(self.destination.exists())
