import unittest
from unittest.mock import patch

from voxgo.app import _parse_args


class WindowedCliTests(unittest.TestCase):
    def test_help_without_console_streams_exits_cleanly(self):
        with patch('sys.stdout', None), patch('sys.stderr', None):
            with self.assertRaises(SystemExit) as result:
                _parse_args(['--help'])
        self.assertEqual(result.exception.code, 0)

    def test_arguments_without_console_streams_keep_normal_defaults(self):
        with patch('sys.stdout', None), patch('sys.stderr', None):
            args, remaining = _parse_args([])
        self.assertEqual(args.benchmark_audio, '')
        self.assertFalse(args.benchmark_game_mode)
        self.assertEqual(remaining, [])


if __name__ == '__main__':
    unittest.main()
