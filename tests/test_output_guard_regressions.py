"""Captured-output regression in everyday CI; real inference has a separate CLI."""
from collections import defaultdict
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

import numpy as np

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from voxgo.asr.runaway_repetition import analyze_repetition, is_runaway_repetition
from voxgo.asr.whisper_engine import SpeechRecognizer, WhisperConfig, should_drop_transcription_result
from voxgo.translation.base import TranslationConfig, TranslationResult, guard_translation_result
from voxgo.translation.client import GameTranslator
from voxgo.translation.local import LocalTranslationProvider

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / 'tests/assets/output_guard/captured.json').read_text(encoding='utf-8'))


class CapturedASRRegressionTests(unittest.TestCase):
    def test_audio_and_synthetic_callout_fixtures_match_their_hashes(self):
        self.assertEqual(hashlib.sha256((ROOT / FIXTURE['audio']).read_bytes()).hexdigest(),
                         FIXTURE['audio_sha256'])
        for case in FIXTURE['callouts']:
            with self.subTest(case=case['id']):
                self.assertEqual(hashlib.sha256((ROOT / case['audio']).read_bytes()).hexdigest(),
                                 case['sha256'])

    def test_actual_slow_repetition_is_blocked(self):
        case = FIXTURE['cases'][0]
        text = case['asr']['raw_text']
        analysis = analyze_repetition(text)
        self.assertEqual((analysis.word_count, analysis.max_repeat_count), (38, 35))
        self.assertLess(analysis.word_count / 6, 8)
        self.assertTrue(is_runaway_repetition(text, duration_seconds=6))

    def test_recorded_decoder_outputs_pass_through_the_real_recognizer_guard(self):
        # Only the model decoder is replayed. Aggregation, filtering and result
        # construction execute production code; this is not fresh inference.
        for case in FIXTURE['cases']:
            with self.subTest(case=case['id']):
                row = case['asr']
                recognizer = SpeechRecognizer(WhisperConfig())
                recognizer._model = SimpleNamespace(transcribe=lambda *_args, **_kwargs: (
                    [SimpleNamespace(text=row['raw_text'], avg_logprob=row['avg_logprob'],
                                     no_speech_prob=row['no_speech_prob'], compression_ratio=row['compression_ratio'])],
                    SimpleNamespace(language=row['language'], language_probability=row['language_probability'])))
                result = recognizer._transcribe_audio_array(np.zeros(96000, dtype=np.float32), None, None)
                self.assertEqual(result.runaway_guarded, case['expected_blocked'])
                if case['expected_blocked']:
                    self.assertEqual(result.text, '')
                    self.assertEqual(should_drop_transcription_result(result), 'global_asr_runaway_repetition')
                else:
                    self.assertEqual(result.text, row['raw_text'])
                    self.assertEqual(should_drop_transcription_result(result), '')


class TranslationOutputGuardTests(unittest.TestCase):
    def test_actual_garbled_translation_and_decoder_markers_are_failures(self):
        for text in (FIXTURE['invalid_translation'], '⁇ , ⁇ , ⁇', '���',
                     '<unk> <unk> <unk>', '<target_text>⁇,⁇,⁇</target_text>', '敌⁇⁇⁇'):
            with self.subTest(text=text[:40]):
                original = TranslationResult(text, 'en', 'zh', 'local', .2)
                result = guard_translation_result(original)
                self.assertTrue(result.translated.startswith('[翻译失败]'))
                self.assertEqual(result.failure_reason, 'other')
                self.assertNotIn('⁇', result.translated)
                self.assertNotIn('�', result.translated)
                self.assertEqual(result.elapsed_seconds, .2)
                self.assertEqual(original.translated, text)

    def test_readable_multilingual_text_and_normal_symbols_are_preserved(self):
        for text in ('???', 'B2 → A1!', 'Go! Go! Go!', '进攻！', '行け！', '가자!', 'Вперёд!',
                     'Unknown name ⁇ is on the roof.', '敌人在⁇旁边', '<target_text>你好</target_text>'):
            with self.subTest(text=text):
                result = TranslationResult(text, 'en', 'zh', 'local')
                self.assertIs(guard_translation_result(result), result)

    def test_existing_errors_and_empty_result_keep_their_original_contract(self):
        for text, reason in (('[翻译超时] 服务暂不可用', 'timeout'), ('', 'empty_result'), ('[未翻译] 未配置', '')):
            result = TranslationResult(text, 'en', 'zh', 'local', failure_reason=reason)
            self.assertIs(guard_translation_result(result), result)
        self.assertIsNone(guard_translation_result(None))


class TranslationBoundaryTests(unittest.IsolatedAsyncioTestCase):
    async def test_current_and_snapshot_requests_do_not_count_invalid_output_as_success(self):
        translator = GameTranslator(TranslationConfig(provider='local', enable_local_phrase_cache=False))
        provider = Mock(name='provider')
        provider.name = 'local'
        provider.requires_api_key.return_value = False
        provider.translate = AsyncMock(return_value=TranslationResult(FIXTURE['invalid_translation'], 'en', 'zh', 'local'))
        with patch.object(translator, '_current_provider', return_value=provider), \
             patch('voxgo.translation.client.create_provider', return_value=provider):
            try:
                for config in (translator.config, replace(translator.config)):
                    result = await translator.translate_result_with_config('ordinary speech', 'en', config)
                    self.assertEqual(result.failure_reason, 'other')
                    self.assertEqual(translator.get_stats()['total_translations'], 0)
            finally:
                await translator.close()

    async def test_custom_phrase_cache_cannot_bypass_output_guard(self):
        translator = GameTranslator(TranslationConfig(local_phrase_cache={'en:zh': {'hello': '⁇ ⁇ ⁇'}}))
        result = await translator.translate_result('hello', 'en')
        self.assertEqual(result.failure_reason, 'other')
        self.assertEqual(translator.get_stats()['total_translations'], 0)

    async def test_local_provider_connection_test_reports_invalid_output_as_failure(self):
        provider = LocalTranslationProvider(TranslationConfig())
        with patch.object(provider, '_translate_sync', return_value=FIXTURE['invalid_translation']):
            result = await provider.test()
        self.assertFalse(result.ok)
        self.assertTrue(result.message.startswith('[翻译失败]'))

    async def test_invalid_output_reaches_qt_and_mobile_as_failure_only(self):
        from PyQt5.QtWidgets import QApplication
        from voxgo.app import VoxGoApp
        from voxgo.runtime.events import EventBus, TranslationReady
        from voxgo.translation.runtime import TranslationRuntime
        from voxgo.ui.overlay_window import GameOverlay

        qt = QApplication.instance() or QApplication([])
        overlay = GameOverlay()
        overlay.add_translation_with_id('bad', 'ordinary speech', 'pending')
        owner = VoxGoApp.__new__(VoxGoApp)
        owner._stopping, owner._language_flow_revision = False, 1
        owner._stats, owner._latency_traces = defaultdict(int), {}
        owner._overlay, owner._mobile = overlay, SimpleNamespace(server=object())
        owner._broadcast_to_mobile = Mock()
        bus = EventBus()
        bus.subscribe(TranslationReady, owner._handle_translation_ready)
        runtime = TranslationRuntime(bus, owner._stats, {}, lambda: overlay)
        runtime.client = SimpleNamespace(config=TranslationConfig(provider='local'),
            translate_result_with_config=AsyncMock(return_value=TranslationResult(
                FIXTURE['invalid_translation'], 'en', 'zh', 'local')))
        runtime.analytics = Mock()
        try:
            await runtime._translate_and_publish('bad', 'ordinary speech', 'en')
            qt.processEvents()
            item = next(item for item in overlay._translations if item.item_id == 'bad')
            self.assertFalse(item.copyable)
            self.assertTrue(item.translated.startswith('[翻译失败]'))
            self.assertEqual(owner._stats['translations'], 0)
            self.assertEqual(owner._stats['errors'], 1)
            self.assertFalse(runtime.analytics.translation_result.call_args.args[0])
            owner._broadcast_to_mobile.assert_called_once_with('ordinary speech', item.translated)
            self.assertNotIn('⁇', item.translated)
        finally:
            overlay._allow_close = True
            overlay.close()
            overlay.deleteLater()
            qt.processEvents()
