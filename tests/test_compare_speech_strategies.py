import asyncio
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

from scripts.compare_speech_strategies import build_schedule, Journal, ObservedClient, ENDPOINT, MODEL
from scripts.validate_multilingual_live import BudgetClient
from voxgo.translation import TranslationConfig


class PairedPlanTest(unittest.TestCase):
    def test_each_language_has_ab_then_ba_in_fresh_process_schedule(self):
        rows=build_schedule()
        self.assertEqual(len(rows),12)
        self.assertEqual(len({r['id'] for r in rows}),12)
        for language in ('ja','ko','ru'):
            pair=[r for r in rows if r['language']==language]
            self.assertEqual([(r['repeat'],r['strategy']) for r in pair],
                [(1,'legacy'),(1,'language_aware'),(2,'language_aware'),(2,'legacy')])

    def test_journal_persists_attempt_before_http_and_rejects_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'attempts.jsonl'
            journal=Journal(path);journal.reserve('fixture')
            self.assertEqual(json.loads(path.read_text())['kind'],'reserved_before_http')
            self.assertEqual(journal.count,1)
            with self.assertRaises(ValueError):Journal(path)
            before=path.read_bytes();journal.blocked=True
            with self.assertRaisesRegex(RuntimeError,'blocked'):journal.reserve('must not send')
            self.assertEqual(journal.count,1);self.assertEqual(path.read_bytes(),before)

    def test_fixed_model_origin_guard_precedes_transport(self):
        async def run():
            with tempfile.TemporaryDirectory() as directory:
                journal=Journal(Path(directory)/'attempts.jsonl')
                client=ObservedClient(TranslationConfig(api_key='fixture'),journal)
                post=Mock();session=SimpleNamespace(post=post)
                with patch.object(BudgetClient,'_get_session',AsyncMock(return_value=session)):
                    transport=await client._get_session()
                for url,model in [('https://other-host/v1',MODEL),(ENDPOINT,'other-model')]:
                    with self.assertRaises(ValueError):transport.post(url,json={'model':model})
                post.assert_not_called();self.assertEqual(journal.count,0)
        asyncio.run(run())

    def test_http_auth_error_blocks_later_attempts_without_recording_body(self):
        class Response:
            async def __aenter__(self):return SimpleNamespace(status=401)
            async def __aexit__(self,*args):return False
        async def run():
            with tempfile.TemporaryDirectory() as directory:
                journal=Journal(Path(directory)/'attempts.jsonl')
                client=ObservedClient(TranslationConfig(api_key='fixture'),journal)
                post=Mock(return_value=Response());session=SimpleNamespace(post=post)
                with patch.object(BudgetClient,'_get_session',AsyncMock(return_value=session)):
                    transport=await client._get_session()
                async with transport.post(ENDPOINT,json={'model':MODEL}):pass
                self.assertTrue(journal.blocked);self.assertEqual(journal.statuses,[401])
                self.assertFalse(post.call_args.kwargs['allow_redirects'])
                self.assertNotIn('fixture',journal.path.read_text())
                with self.assertRaises(RuntimeError):journal.reserve('no retry')
        asyncio.run(run())


if __name__=='__main__':unittest.main()
