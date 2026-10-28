"""Released compatibility policy; isolated settings, no audio/model/API calls."""
import ast
import copy
from dataclasses import asdict
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import release_preflight
from voxgo.app import VoxGoApp
from voxgo.asr.language_profiles import effective_speech_config, normalize_multilingual_strategy
from voxgo.asr.whisper_engine import WhisperConfig
from voxgo.config.loader import default_app_config, load_config, save_user_settings, serialize_user_settings
from voxgo.languages import ONLINE_DIRECTIONS
from voxgo.ui.config_models import WhisperDeviceConfig

ROOT = Path(__file__).resolve().parents[1]


class ReleaseSpeechPolicyTests(unittest.TestCase):
    def test_defaults_and_unknown_values_choose_compatibility(self):
        for config in (WhisperConfig(), WhisperDeviceConfig(), default_app_config().whisper):
            self.assertEqual(config.multilingual_asr_strategy, 'legacy')
        for value in (None, '', 'unknown', 'legacy'):
            self.assertEqual(normalize_multilingual_strategy(value), 'legacy')

    def test_client_cannot_enable_candidate_via_an_old_in_memory_setting(self):
        for source, target in sorted(ONLINE_DIRECTIONS):
            for mode in ('fast', 'balanced', 'accurate', 'custom'):
                for strategy in ('legacy', 'language_aware', 'unknown'):
                    with self.subTest(source=source, target=target, mode=mode, strategy=strategy):
                        config=default_app_config()
                        config.translation.source_lang,config.translation.target_lang=source,target
                        config.whisper.multilingual_asr_strategy=strategy
                        config.audio.latency_mode=mode
                        before=copy.deepcopy(asdict(config))
                        owner=VoxGoApp.__new__(VoxGoApp);owner.config=config
                        self.assertIs(effective_speech_config(config),config)
                        self.assertIs(owner._speech_runtime_config(),config)
                        self.assertEqual(asdict(config),before)

    def test_omitted_and_old_candidate_files_load_save_and_restart_as_legacy(self):
        for strategy in (None, 'legacy', 'language_aware', 'unknown'):
            with self.subTest(strategy=strategy),tempfile.TemporaryDirectory() as tmp:
                directory=Path(tmp)
                whisper={} if strategy is None else {'multilingual_asr_strategy':strategy}
                data={'whisper':whisper,'translation':{'source_lang':'ko','target_lang':'ja'},
                      'audio':{'latency_mode':'custom','pre_roll_ms':321,'max_speech_seconds':6.2}}
                settings=directory/'user_settings.json'
                settings.write_text(json.dumps(data),'utf-8')
                original=settings.read_bytes()
                # Isolate this read check from the pre-existing telemetry migration,
                # which may persist its own consent metadata on first load.
                with patch('voxgo.analytics.migration.initialize_telemetry_v2'):
                    loaded=load_config(runtime_dir=directory)
                self.assertEqual(settings.read_bytes(),original)  # Reading never rewrites user settings.
                self.assertEqual(loaded.whisper.multilingual_asr_strategy,'legacy')
                self.assertIs(effective_speech_config(loaded),loaded)
                self.assertEqual(loaded.audio.pre_roll_ms,321)
                self.assertEqual(loaded.audio.max_speech_seconds,6.2)
                self.assertEqual((loaded.translation.source_lang,loaded.translation.target_lang),('ko','ja'))
                loaded.whisper.multilingual_asr_strategy='language_aware'
                self.assertEqual(serialize_user_settings(loaded)['whisper']['multilingual_asr_strategy'],'legacy')
                save_user_settings(loaded,runtime_dir=directory)
                restarted=load_config(runtime_dir=directory)
                self.assertEqual(restarted.whisper.multilingual_asr_strategy,'legacy')
                self.assertEqual(restarted.audio.pre_roll_ms,321)

    def test_bundled_config_candidate_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'config.json'
            path.write_text(json.dumps({'whisper':{'multilingual_asr_strategy':'language_aware'}}),'utf-8')
            config=load_config(config_path=str(path))
            self.assertEqual(config.whisper.multilingual_asr_strategy,'legacy')

    def test_experimental_opt_in_is_absent_from_product_call_sites(self):
        for path in (ROOT/'voxgo').rglob('*.py'):
            for node in ast.walk(ast.parse(path.read_text('utf-8-sig'))):
                if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='effective_speech_config':
                    self.assertFalse(node.keywords,str(path))

    def test_preflight_rejects_candidate_defaults_instead_of_weakening_guard(self):
        original=release_preflight._read
        def candidate(root,relative):
            source=original(root,relative)
            if relative=='voxgo/asr/whisper_engine.py':
                source=source.replace('multilingual_asr_strategy: str = "legacy"',
                                      'multilingual_asr_strategy: str = "language_aware"')
            return source
        with patch.object(release_preflight,'_read',side_effect=candidate):
            with self.assertRaisesRegex(release_preflight.PreflightError,'default to compatibility'):
                release_preflight.check_product_defaults(ROOT,'afc33a67')
