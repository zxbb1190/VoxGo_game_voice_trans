import copy
from dataclasses import asdict, replace
import threading
import unittest
from collections import defaultdict
from types import SimpleNamespace
from unittest.mock import patch, Mock

from voxgo.config.loader import default_app_config, migrate_runtime_defaults, sync_language_flow, apply_language_runtime_policy, serialize_user_settings
from voxgo.asr.language_profiles import effective_speech_config, audio_runtime_signature
from voxgo.asr.pipeline import SpeechPipeline
from voxgo.asr.whisper_engine import SpeechRecognizer, WhisperConfig, TranscriptionResult
from voxgo.audio.capture import SystemAudioCapture, SpeechSegment
from voxgo.runtime.events import EventBus
from voxgo.runtime.work_items import SpeechWorkItem, LatencyTrace
from voxgo.languages import ONLINE_DIRECTIONS, LOCAL_DIRECTIONS


def configured(source='en',target='zh',pure=False):
    config=default_app_config()
    config.translation.source_lang=source;config.translation.target_lang=target
    config.whisper.pure_english_environment=pure
    migrate_runtime_defaults(config,preserve_existing_audio_tuning=False)
    sync_language_flow(config);apply_language_runtime_policy(config)
    return config


class SpeechLanguageProfilesTest(unittest.TestCase):
    def test_exact_twenty_requested_directions_and_no_new_offline_pairs(self):
        expected={(s,t) for s in ('en','zh','ja','ko','ru') for t in ('en','zh','ja','ko','ru') if s!=t}
        self.assertEqual(ONLINE_DIRECTIONS,expected)
        self.assertEqual(LOCAL_DIRECTIONS,{('en','zh'),('zh','en')})

    def test_english_and_chinese_configs_are_not_overridden_for_any_target(self):
        for pure in (False,True):
            for source in ('en','zh'):
                legacy=configured(source,'zh' if source=='en' else 'en',pure)
                for target in ('en','zh','ja','ko','ru'):
                    if target==source:continue
                    with self.subTest(source=source,target=target,pure=pure):
                        config=configured(source,target,pure)
                        before=copy.deepcopy(asdict(config))
                        self.assertIs(effective_speech_config(config),config)
                        self.assertEqual(asdict(config),before)
                        self.assertEqual(asdict(config.audio),asdict(legacy.audio))
                        self.assertEqual(asdict(config.whisper),asdict(legacy.whisper))

    def test_new_profiles_do_not_mutate_saved_settings_and_legacy_roundtrip(self):
        legacy=configured('en','zh',True)
        original_audio=asdict(legacy.audio);original_whisper=asdict(legacy.whisper)
        for source in ('ja','ko','ru'):
            for target in ('en','zh','ja','ko','ru'):
                if source==target:continue
                config=configured(source,target)
                before=serialize_user_settings(config)
                config.whisper.multilingual_asr_strategy='language_aware'
                effective=effective_speech_config(config,experimental=True)
                self.assertIsNot(effective,config)
                self.assertEqual(serialize_user_settings(config),before)
                self.assertEqual(effective.audio.diagnostics_latency_mode,'custom')
                self.assertEqual(effective.audio.max_speech_seconds,4.5)
                self.assertFalse(effective.whisper.active_model_size.endswith('.en'))
                effective.whisper.vad_parameters['max_speech_duration_s']=99
                self.assertNotEqual((config.whisper.vad_parameters or {}).get('max_speech_duration_s'),99)
                config.translation.source_lang='en';config.translation.target_lang='zh'
                config.whisper.pure_english_environment=True
                config.whisper.multilingual_asr_strategy='legacy'
                migrate_runtime_defaults(config,preserve_existing_audio_tuning=False)
                sync_language_flow(config);apply_language_runtime_policy(config)
                self.assertIs(effective_speech_config(config),config)
                self.assertEqual(asdict(config.audio),original_audio)
                self.assertEqual(asdict(config.whisper),original_whisper)

    def test_compatibility_switch_and_explicit_custom_modes_preserve_selection(self):
        config=configured('ja','zh')
        config.whisper.multilingual_asr_strategy='legacy'
        self.assertIs(effective_speech_config(config),config)
        self.assertEqual(serialize_user_settings(config)['whisper']['multilingual_asr_strategy'],'legacy')
        config.whisper.multilingual_asr_strategy='language_aware'
        for mode in ('custom','balanced','accurate'):
            config.audio.latency_mode=mode
            self.assertIs(effective_speech_config(config,experimental=True),config)
        config.audio.latency_mode='fast';config.whisper.asr_impact_mode='ultra_low'
        self.assertIs(effective_speech_config(config,experimental=True),config)

    def test_segment_events_and_work_items_capture_custom_mode_and_profile(self):
        config=configured('ja','en')
        config.whisper.multilingual_asr_strategy='language_aware'
        config=effective_speech_config(config,experimental=True)
        diagnostics=[]
        pipeline=SpeechPipeline(lambda:config,lambda:None,EventBus(),defaultdict(int),
            lambda:True,lambda:False,lambda:'fixture',{},lambda *a:None,
            lambda:1,lambda *args:diagnostics.append(args))
        segment=SpeechSegment(audio_data=b'\x01\x00'*16000,sample_rate=16000,
            duration_seconds=1,voice_duration_seconds=.9,block_count=8,voice_blocks=8,
            peak_rms_dbfs=-18,noise_floor_dbfs=-60,energy_threshold_dbfs=-40,reason='test')
        pipeline.on_speech_detected(segment)
        self.assertTrue(diagnostics)
        self.assertEqual(diagnostics[0][-1],'custom')
        item=pipeline._queue.get_nowait()
        self.assertEqual(item.trace.latency_mode,'custom')
        self.assertEqual(item.target_lang,'en')
        beam=item.whisper_config_snapshot.beam_size
        config.whisper.beam_size=1
        self.assertEqual(item.whisper_config_snapshot.beam_size,beam)
        # A device recovery copy must retain the event-time diagnostic label.
        self.assertEqual(replace(config.audio).diagnostics_latency_mode,'custom')

    def test_config_change_waits_until_current_inference_finishes(self):
        old=WhisperConfig(model_size='base',active_model_size='base',language='auto',source_language='ja',beam_size=1)
        recognizer=SpeechRecognizer(old)
        recognizer._initialized=True
        entered=threading.Event();release=threading.Event();used=[]
        def transcribe(*args):
            used.append((recognizer.config.source_language,recognizer.config.beam_size))
            if len(used)==1:
                entered.set();self.assertTrue(release.wait(3))
            return TranscriptionResult(text='fixture',language=recognizer.config.source_language)
        new=replace(old,source_language='ko',beam_size=3)
        errors=[]
        def first():
            try:recognizer.transcribe_audio_bytes_with_language(b'\0\0'*1600,16000)
            except Exception as exc:errors.append(exc)
        with patch.object(recognizer,'_validate_native_model_language'),patch.object(recognizer,'_transcribe_audio_array',side_effect=transcribe):
            thread=threading.Thread(target=first);thread.start()
            self.assertTrue(entered.wait(3))
            recognizer.request_config(new)
            self.assertEqual(recognizer.config.source_language,'ja')
            release.set();thread.join(3)
            self.assertFalse(thread.is_alive());self.assertEqual(errors,[])
            recognizer.transcribe_audio_bytes_with_language(b'\0\0'*1600,16000)
        self.assertEqual(used,[('ja',1),('ko',3)])

    def test_task_snapshot_takes_precedence_over_later_gui_settings(self):
        old=WhisperConfig(model_size='base',active_model_size='base',source_language='ja',beam_size=3)
        recognizer=SpeechRecognizer(old)
        recognizer.request_config(replace(old,source_language='en',beam_size=1))
        recognizer._apply_pending_config(old)
        self.assertEqual(recognizer.config.source_language,'ja')
        self.assertEqual(recognizer.config.beam_size,3)

    def test_queued_vad_config_retains_legacy_defaults_and_is_not_shared(self):
        from voxgo.asr.whisper_engine import DEFAULT_VAD_PARAMS
        old=WhisperConfig()
        recognizer=SpeechRecognizer(old)
        incoming=WhisperConfig(vad_parameters=None)
        recognizer.request_config(incoming)
        recognizer._apply_pending_config()
        self.assertEqual(recognizer.config.vad_parameters,DEFAULT_VAD_PARAMS)
        self.assertIsNone(incoming.vad_parameters)

    def test_model_switch_does_not_cleanup_on_gui_thread(self):
        recognizer=SpeechRecognizer(WhisperConfig(active_model_size='base'))
        recognizer._initialized=True
        with patch.object(recognizer,'cleanup') as cleanup:
            recognizer.request_config(WhisperConfig(active_model_size='small'))
            cleanup.assert_not_called()
            recognizer._apply_pending_config()
            cleanup.assert_called_once()
        self.assertEqual(recognizer.config.active_model_size,'small')

    def test_settings_switch_restarts_effective_capture_and_restores_english(self):
        from voxgo.app import VoxGoApp
        from voxgo.runtime.settings_controller import OverlaySettingsController
        app=VoxGoApp.__new__(VoxGoApp)
        app.config=configured('en','zh')
        app._running=True;app._overlay=None;app._language_flow_revision=1
        app._speech_recognizer=SpeechRecognizer(copy.deepcopy(app.config.whisper))
        app._audio=Mock();app._audio.clear_pending_audio.return_value=0
        app._speech_pipeline=Mock();app._translation=Mock()
        for name in ('_setup_hotkeys','_save_user_settings','_analytics_call','_notify_user','_sync_tray_state'):
            setattr(app,name,Mock())
        captures=[]
        app._restart_audio_capture=lambda **kw:captures.append(audio_runtime_signature(app.config))
        app._refresh_cached_settings()
        controller=OverlaySettingsController(app)
        def change(source,target):
            # Overlay selection mutates the shared translation dataclass before
            # applying settings, so old values must come from cached state.
            app.config.translation.source_lang=source;app.config.translation.target_lang=target
            controller.apply(app.config.overlay,app.config.hotkeys,app.config.audio,
                app.config.translation,copy.deepcopy(app.config.whisper),app.config.app,app.config.update)
        legacy_audio=asdict(app.config.audio)
        change('ko','en')
        self.assertEqual(app._speech_recognizer._pending_config.active_model_size,'base')
        self.assertEqual(app._speech_recognizer.config.source_language,'en')
        self.assertEqual(len(captures),1)
        change('en','zh')
        self.assertEqual(asdict(app.config.audio),legacy_audio)
        self.assertEqual(app._speech_recognizer._pending_config.cpu_threads,1)
        self.assertEqual(app._speech_recognizer._pending_config.active_model_size,'base')
        self.assertEqual(app._speech_recognizer._pending_config.source_language,'en')
        self.assertEqual(len(captures),2)
        self.assertEqual(app._language_flow_revision,3)


if __name__=='__main__':unittest.main()
