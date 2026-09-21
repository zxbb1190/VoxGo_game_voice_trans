import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from voxgo.package_info import package_type


class PackageInfoTests(unittest.TestCase):
    def test_source_and_all_built_editions(self):
        with patch('sys.frozen', False, create=True):
            self.assertEqual(package_type(), 'source')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch('sys.frozen', True, create=True), patch(
                    'voxgo.package_info.__file__', str(root / 'voxgo' / 'package_info.py')):
                self.assertEqual(package_type(), 'unknown')
                for edition in ('lite', 'full', 'full-cuda', 'bad', 'source'):
                    (root / 'package-info.json').write_text(json.dumps({'package_type': edition}))
                    self.assertEqual(package_type(), edition if edition in ('lite', 'full', 'full-cuda') else 'unknown')
