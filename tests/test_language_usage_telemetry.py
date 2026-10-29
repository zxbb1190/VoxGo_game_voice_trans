"""Language classification is additive to the original 63 cumulative counters."""
import asyncio
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import os
import queue
from pathlib import Path
import subprocess
import tempfile
import threading
from types import SimpleNamespace
import unittest
import uuid

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from voxgo.analytics import DailyMetrics, DailySnapshotStore
from voxgo.analytics.aggregation import AggregateStore
from voxgo.analytics.consent import CONSENT_VERSION
from voxgo.analytics.daily_metrics import METRICS
from voxgo.analytics.language_usage import direction_key, language_usage_allowed, usage_map, validate_totals
from voxgo.analytics.uploader import RemoteUploader
from voxgo.languages import ONLINE_DIRECTIONS
from voxgo.runtime.events import EventBus
from voxgo.translation.base import TranslationConfig, TranslationResult
from voxgo.translation.runtime import TranslationRuntime


def row(source='ja', target='zh', mode='api', success=1, failed=0):
    return dict(source_lang=source, target_lang=target, mode=mode, success=success, failed=failed)


class LanguageCountersTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.day = date(2026, 10, 29)

    def test_all_twenty_codes_and_strict_wire_whitelist(self):
        self.assertEqual(len(ONLINE_DIRECTIONS), 20)
        for source, target in ONLINE_DIRECTIONS:
            self.assertIsNotNone(direction_key(source, target, 'api'))
        self.assertEqual(direction_key('zh_CN', 'en', 'offline'), 'zh>en/offline')
        for bad in [row('zh_CN'), row('ja (Beta)'), row('ja', 'ja'), row(mode='offline'),
                    row(success=True), row(success=-1), row(success=0), row(success=10000001),
                    dict(row(), text='private'), dict(row(), provider='private')]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                usage_map([bad])
        with self.assertRaises(ValueError):
            usage_map([row(), row()])

    def test_daily_atomic_totals_modes_rollover_and_consent(self):
        disk = DailySnapshotStore(self.root, today=lambda: self.day)
        enabled = [False]
        metrics = DailyMetrics(disk, '0.6.0', language_usage_allowed=lambda: enabled[0])
        metrics.translation_result(True, 5, 'api', source_lang='ja', target_lang='zh')
        self.assertNotIn('language_usage', metrics.snapshot_copy())
        enabled[0] = True
        for source, target in sorted(ONLINE_DIRECTIONS):
            metrics.translation_result(True, 5, 'api', source_lang=source, target_lang=target)
        metrics.translation_result(False, 5, 'api', 'timeout', 'google', 'ru', 'ja')
        metrics.translation_result(True, 5, None, source_lang='en', target_lang='zh', usage_mode='cache')
        metrics.translation_result(True, 5, 'offline', source_lang='zh', target_lang='en')
        metrics.translation_result(True, 5, 'api', source_lang='ja', target_lang='ru', usage_mode='cache')
        snap = metrics.snapshot_copy()
        self.assertEqual(len(METRICS), 63)
        self.assertFalse(set(snap['metrics']) - METRICS)
        self.assertEqual(snap['metrics']['translation_success'], 24)
        self.assertEqual(snap['metrics']['api_translation_failed_timeout'], 1)
        self.assertEqual(len(snap['language_usage']), 22)
        validate_totals(snap['language_usage'], snap['metrics'])
        metrics.flush()
        self.assertEqual(DailyMetrics(disk, '0.6.0').snapshot_copy()['language_usage'], snap['language_usage'])
        self.day += timedelta(days=1)
        metrics.translation_result(True, source_lang='ru', target_lang='zh')
        self.assertEqual(metrics.snapshot_copy()['language_usage'], [row('ru', 'zh', 'unknown')])
        self.assertEqual(disk.load('2026-10-29')['language_usage'], snap['language_usage'])

    def write(self, success=2, language=None):
        path = self.root / 'shards' / getattr(self, 'shard', str(uuid.uuid4())) / f'{self.day}.json'
        self.shard = path.parent.name
        path.parent.mkdir(parents=True, exist_ok=True)
        value = dict(schema_version=2, date=str(self.day), metrics={
            'translation_success': success, 'api_translation_success': success})
        if language is not None:
            value['language_usage'] = language
        path.write_text(json.dumps(value))
        return path

    def test_aggregate_highwatermark_ack_retry_and_capability_rollback(self):
        path = self.write(language=[row()])
        store = AggregateStore(self.root, '0.6.0', today=lambda: self.day, language_usage=True)
        first = store.snapshots()[0]
        self.assertEqual(first['schema_version'], 3)
        self.assertEqual(first['language_usage'], [row()])
        self.assertEqual(store.snapshots(), [first])
        self.assertEqual(AggregateStore(self.root, '0.6.0', today=lambda: self.day,
                                        language_usage=True).snapshots(), [first])
        self.assertTrue(store.acknowledge(first))
        path.unlink()
        self.write(language=[row()])
        self.assertEqual(store.snapshots(), [])
        self.write(success=3, language=[row(success=2)])
        newer = store.snapshots()[0]
        self.assertFalse(store.acknowledge(first))
        self.assertEqual(newer['metrics']['translation_success'], 3)
        self.assertEqual(newer['language_usage'], [row(success=2)])
        store.language_usage = False
        fallback = store.snapshots()[0]
        self.assertEqual(fallback['schema_version'], 2)
        self.assertEqual(len(fallback['metrics']), 63)
        self.assertNotIn('language_usage', fallback)
        self.assertTrue(store.acknowledge(fallback))
        self.write(success=3, language=[])  # old writer may omit the extension
        store.language_usage = True
        restored = store.snapshots()[0]
        self.assertEqual(restored['language_usage'], [row(success=2)])
        self.assertEqual(restored['install_id'], first['install_id'])
        unsigned = {k: v for k, v in restored.items() if k != 'snapshot_id'}
        self.assertEqual(restored['snapshot_id'], hashlib.sha256(json.dumps(
            unsigned, sort_keys=True, separators=(',', ':')).encode()).hexdigest())

    def test_actual_previous_binary_cannot_post_schema3_and_does_not_erase_watermarks(self):
        self.write(language=[row()])
        store = AggregateStore(self.root, '0.6.0', today=lambda: self.day, language_usage=True)
        original = store.snapshots()[0]
        # Load the actual pre-change implementation without changing the checkout.
        previous = subprocess.run(['git', 'show', 'fa5f6054:voxgo/analytics/aggregation.py'],
                                  capture_output=True, text=True, check=True).stdout
        namespace = dict(__name__='voxgo.analytics._previous_aggregate', __package__='voxgo.analytics')
        exec(compile(previous, '<previous-aggregate>', 'exec'), namespace)
        old_store = namespace['AggregateStore'](self.root, '0.6.0', today=lambda: self.day)
        self.assertEqual(old_store.snapshots(), [])  # language_pending is invisible to old code
        self.write(success=4, language=[row()])
        fallback = old_store.snapshots()[0]
        self.assertEqual(fallback['schema_version'], 2)
        self.assertEqual(fallback['install_id'], original['install_id'])
        self.assertTrue(old_store.acknowledge(fallback))
        current = store.snapshots()[0]
        self.assertGreater(current['revision'], fallback['revision'])
        self.assertEqual(current['language_usage'], [row()])
        self.assertEqual(current['metrics']['translation_success'], 4)
        self.assertTrue(store.acknowledge(current))
        self.assertEqual(store.snapshots(), [])

    def test_late_extension_after_old_aggregation_counts_only_new_classification(self):
        self.write()
        old = AggregateStore(self.root, '0.6.0', today=lambda: self.day)
        old.acknowledge(old.snapshots()[0])
        self.write(language=[row(success=2)])
        new = AggregateStore(self.root, '0.6.0', today=lambda: self.day, language_usage=True)
        snap = new.snapshots()[0]
        self.assertEqual(snap['metrics']['translation_success'], 2)
        self.assertEqual(snap['language_usage'], [row(success=2)])
        self.assertTrue(new.acknowledge(snap))
        self.write(success=1, language=[row()])
        self.assertEqual(new.snapshots(), [])


class LanguageRuntimeTests(unittest.TestCase):
    def run_case(self, provider='openai_compatible', error=None, translated='fixture', stale=False):
        calls = []
        class Collector:
            def translation_result_with_language(self, *args):
                calls.append(args)
        class Translator:
            config = TranslationConfig(source_lang='ja', target_lang='ru', provider=provider)
            async def translate_result_with_config(self, text, detected_language, config):
                self.config = TranslationConfig(source_lang='en', target_lang='zh')
                if error:
                    raise error
                return TranslationResult(translated, 'en', 'zh',
                    'local_cache' if provider == 'cache' else provider)
        runtime = TranslationRuntime(EventBus(), {'errors': 0}, {}, lambda: None)
        runtime.analytics, runtime.client = Collector(), Translator()
        if stale:
            runtime.set_language_revision_getter(lambda: 2)
        asyncio.run(runtime._translate_and_publish('fixture', 'nonprivate fixture', 'ja',
                                                  language_revision=1 if stale else 0))
        return calls

    def test_success_and_failure_use_task_snapshot_never_final_setting_or_result_codes(self):
        for error in (None, TimeoutError('not uploaded')):
            calls = self.run_case(error=error)
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][5:7], ('ja', 'ru'))
            self.assertEqual(calls[0][2], 'api')
            self.assertNotIn('nonprivate fixture', str(calls))

    def test_cache_not_api_and_stale_or_unsupported_never_counted(self):
        calls = self.run_case(provider='cache')
        self.assertIsNone(calls[0][2])
        self.assertEqual(calls[0][-1], 'cache')
        self.assertEqual(self.run_case(stale=True), [])
        self.assertEqual(self.run_case(translated='[未翻译] unsupported'), [])


class LanguageUploaderTests(unittest.TestCase):
    def test_capability_and_authorization_gate_preserve_legacy63(self):
        for marker, capability in [(0, 1), (1, None), (1, False), (1, True), (1, 1)]:
            with self.subTest(marker=marker, capability=capability), tempfile.TemporaryDirectory() as root:
                consent = SimpleNamespace(telemetry_consent='allowed', telemetry_consent_version=CONSENT_VERSION,
                    telemetry_language_usage_consent_version=marker)
                day = str(datetime.now(timezone.utc).date())
                shard = Path(root) / 'shards' / str(uuid.uuid4()) / f'{day}.json'
                shard.parent.mkdir(parents=True)
                shard.write_text(json.dumps(dict(schema_version=2, date=day,
                    metrics={'translation_success': 1, 'api_translation_success': 1}, language_usage=[row()])))
                calls = []
                def transport(method, path, payload=None):
                    calls.append((method, path, payload))
                    if method == 'GET':
                        config = dict(schema_version=1, telemetry_enabled=True,
                                      telemetry_sample_rate=1.0, sync_interval_seconds=900)
                        if capability is not None:
                            config['language_usage_schema'] = capability
                        return 200, {}, config
                    return 200, {}, dict(success=True, snapshot_id=payload['snapshot_id'], revision=payload['revision'])
                RemoteUploader(root, lambda: consent, transport=transport, start=False).sync_once()
                self.assertEqual(len(calls), 2)
                self.assertEqual(calls[0][1], '/v1/config?language_usage=1' if marker else '/v1/config')
                expected = 3 if marker and type(capability) is int and capability == 1 else 2
                self.assertEqual(calls[1][2]['schema_version'], expected)
                self.assertEqual(len(calls[1][2]['metrics']), 63)
                self.assertEqual('language_usage' in calls[1][2], expected == 3)


class LanguageConsentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PyQt5.QtWidgets import QApplication
        cls.qt = QApplication.instance() or QApplication([])

    def test_old_grant_requires_explicit_enable_and_full_off_revokes(self):
        from voxgo.config.loader import default_app_config, save_user_settings, load_user_settings
        from voxgo.ui.settings_dialog import SettingsDialog
        config = default_app_config()
        config.app.telemetry_consent = 'allowed'
        config.app.telemetry_consent_version = CONSENT_VERSION
        config.app.telemetry_epoch = str(uuid.uuid4())
        with tempfile.TemporaryDirectory() as folder:
            save_user_settings(config, Path(folder))
            self.assertFalse(language_usage_allowed(config.app))
            dialog = SettingsDialog(config.overlay, config.hotkeys, app_config=config.app)
            try:
                self.assertFalse(dialog.language_usage_consent_button.isHidden())
                epoch = dialog.app_config.telemetry_epoch
                dialog._enable_language_usage_consent()
                self.assertEqual(dialog.app_config.telemetry_epoch, epoch)
                config.app = dialog.app_config
                save_user_settings(config, Path(folder))
                loaded = default_app_config()
                load_user_settings(loaded, Path(folder))
                self.assertTrue(language_usage_allowed(loaded.app))
                dialog._change_telemetry_consent(False)
                self.assertFalse(language_usage_allowed(dialog.app_config))
                self.assertEqual(dialog.app_config.telemetry_language_usage_consent_version, 0)
            finally:
                dialog.close()

    def test_new_full_optin_includes_category_but_unchanged_historical_setup_does_not(self):
        from voxgo.config.loader import default_app_config
        from voxgo.ui.dialogs import FirstRunWizard
        for origin in ('new_install', 'historical_install'):
            cfg = default_app_config()
            cfg.app.telemetry_install_origin = origin
            cfg.app.telemetry_consent = 'allowed'
            cfg.app.telemetry_consent_version = CONSENT_VERSION
            cfg.app.telemetry_epoch = str(uuid.uuid4())
            wizard = FirstRunWizard(None, translation_config=cfg.translation, app_config=cfg.app)
            try:
                wizard._mark_completed()
                self.assertEqual(language_usage_allowed(wizard.app_config), origin == 'new_install')
            finally:
                wizard.close()

    def test_durable_authority_beats_stale_settings_and_invalid_scope(self):
        from voxgo.analytics.migration import read_consent_authority, validated_consent
        state = dict(telemetry_consent='allowed', telemetry_consent_version=CONSENT_VERSION,
                     telemetry_epoch=str(uuid.uuid4()))
        self.assertEqual(validated_consent(state)['telemetry_language_usage_consent_version'], 0)
        for bad in (True, '1', 2, -1):
            self.assertEqual(validated_consent(dict(state, telemetry_language_usage_consent_version=bad))[
                'telemetry_language_usage_consent_version'], 0)
        with tempfile.TemporaryDirectory() as root:
            (Path(root) / 'telemetry_consent.json').write_text(json.dumps(state))
            result = read_consent_authority(root, dict(state, telemetry_language_usage_consent_version=1))
            self.assertEqual(result['telemetry_language_usage_consent_version'], 0)

    def test_grant_cannot_classify_queued_pregrant_events_and_revoke_stops_writer(self):
        from voxgo.analytics.client import AuthorizedAnalytics, LocalAnalytics
        def collector():
            result = LocalAnalytics.__new__(LocalAnalytics)
            result._stopped = threading.Event()
            result._queue = queue.Queue(maxsize=10)
            return result
        analytics = AuthorizedAnalytics.__new__(AuthorizedAnalytics)
        analytics._lock, analytics._stopping = threading.RLock(), False
        analytics._epoch = str(uuid.uuid4())
        analytics.local, analytics.remote = collector(), collector()
        analytics.refresh_consent = lambda: None
        allowed = [False]
        analytics._language_usage_allowed = lambda epoch: allowed[0]
        analytics.translation_result_with_language(True, 20, 'api', None, None, 'ja', 'ru', 'api')
        allowed[0] = True
        with tempfile.TemporaryDirectory() as root:
            metrics = DailyMetrics(DailySnapshotStore(root), '0.6.0', language_usage_allowed=lambda: allowed[0])
            before = analytics.remote._queue.get_nowait()
            self.assertEqual(len(before), 6)  # event has no category, even consumed after grant
            getattr(metrics, before[0])(*before[1:])
            self.assertNotIn('language_usage', metrics.snapshot_copy())
            analytics.translation_result_with_language(True, 20, 'api', None, None, 'ja', 'ru', 'api')
            after = analytics.remote._queue.get_nowait()
            self.assertEqual(len(after), 9)
            allowed[0] = False  # revoke before the writer consumes it
            getattr(metrics, after[0])(*after[1:])
            self.assertNotIn('language_usage', metrics.snapshot_copy())
            self.assertEqual(metrics.snapshot_copy()['metrics']['translation_success'], 2)
