"""Real v0.5.2 module upgrade/downgrade evidence, with synthetic local state."""
from contextlib import contextmanager
from datetime import date
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid

from voxgo.analytics.aggregation import AggregateStore
from voxgo.analytics.daily_metrics import CLASSIFIED_COUNTERS, METRICS
from voxgo.app_info import APP_VERSION

ROOT=Path(__file__).resolve().parents[1]
LEGACY_REF='52d77cbf'


@contextmanager
def legacy_aggregate():
    """Load actual published-baseline sources under a private package name."""
    name='_rc_053_legacy_analytics'
    with tempfile.TemporaryDirectory() as folder:
        package=Path(folder)/name
        package.mkdir()
        (package/'__init__.py').write_text('',encoding='utf-8')
        for module in ('aggregation','daily_metrics'):
            source=subprocess.check_output(['git','show',f'{LEGACY_REF}:voxgo/analytics/{module}.py'],cwd=ROOT)
            (package/(module+'.py')).write_bytes(source)
        sys.path.insert(0,folder)
        try:
            yield importlib.import_module(name+'.aggregation').AggregateStore
        finally:
            sys.path.remove(folder)
            for module in tuple(sys.modules):
                if module==name or module.startswith(name+'.'):
                    del sys.modules[module]


def shard(root,day,values):
    path=Path(root)/'shards'/str(uuid.uuid4())/(str(day)+'.json')
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(dict(schema_version=2,date=str(day),metrics=values)),encoding='utf-8')
    return path


class Release053CompatibilityTests(unittest.TestCase):
    def test_real_052_pending_upgrade_keeps_identity_hash_revision_and_adds_only_event_delta(self):
        with legacy_aggregate() as Legacy, tempfile.TemporaryDirectory() as folder:
            day=date(2026,10,14)
            shard(folder,day,dict(asr_segments=3,asr_segment_duration_samples=3,asr_segment_duration_sum_ms=6000))
            old=Legacy(folder,'0.5.2',today=lambda:day)
            pending=old.snapshots()[0]
            self.assertEqual(len(pending['metrics']),35)
            current=AggregateStore(folder,APP_VERSION,today=lambda:day)
            self.assertEqual(current.snapshots(),[pending])
            self.assertEqual(current.snapshots(),[pending])
            shard(folder,day,dict(asr_segments=1,asr_segment_duration_samples=1,
                asr_segment_duration_sum_ms=1500,asr_custom_segments=1,
                asr_custom_segment_duration_samples=1,asr_custom_segment_duration_sum_ms=1500))
            upgraded=current.snapshots()[0]
            self.assertEqual(upgraded['install_id'],pending['install_id'])
            self.assertEqual(upgraded['revision'],pending['revision']+1)
            self.assertEqual(set(upgraded['metrics']),METRICS)
            self.assertEqual(upgraded['app_version'],APP_VERSION)
            self.assertEqual(upgraded['metrics']['asr_segments'],4)
            self.assertEqual(upgraded['metrics']['asr_custom_segments'],1)
            self.assertFalse(current.acknowledge(pending))
            self.assertTrue(current.acknowledge(upgraded))

    def test_real_052_downgrade_pauses_full_without_rewriting_state_then_053_resumes(self):
        with legacy_aggregate() as Legacy, tempfile.TemporaryDirectory() as folder:
            day=date(2026,10,14)
            shard(folder,day,dict(asr_segments=1,asr_fast_segments=1,
                asr_segment_duration_samples=1,asr_segment_duration_sum_ms=1000,
                asr_fast_segment_duration_samples=1,asr_fast_segment_duration_sum_ms=1000))
            current=AggregateStore(folder,APP_VERSION,today=lambda:day)
            pending=current.snapshots()[0]
            tracked={p.name:p.read_bytes() for p in (Path(folder)/'aggregate.json',Path(folder)/'identity.json')}
            old=Legacy(folder,'0.5.2',today=lambda:day)
            with self.assertRaisesRegex(ValueError,'invalid metrics'):
                old.snapshots()
            self.assertEqual(tracked,{p.name:p.read_bytes() for p in (Path(folder)/'aggregate.json',Path(folder)/'identity.json')})
            # A separate old-process shard is unclassified, never inferred fast.
            shard(folder,day,dict(asr_segments=2,asr_segment_duration_samples=2,asr_segment_duration_sum_ms=4000))
            resumed=current.snapshots()[0]
            self.assertEqual(resumed['install_id'],pending['install_id'])
            self.assertEqual(resumed['revision'],pending['revision']+1)
            self.assertEqual(resumed['metrics']['asr_segments'],3)
            self.assertEqual(resumed['metrics']['asr_fast_segments'],1)
            self.assertEqual(current.snapshots(),[resumed])
            self.assertFalse(current.acknowledge(pending))
            self.assertTrue(current.acknowledge(resumed))
            self.assertEqual(current.snapshots(),[])

    def test_real_052_downgrade_also_preserves_acked_63_field_watermarks(self):
        with legacy_aggregate() as Legacy, tempfile.TemporaryDirectory() as folder:
            day=date(2026,10,14)
            shard(folder,day,dict(api_translation_failed=1,translation_failed=1,
                api_translation_failed_network=1,api_translation_failed_google=1))
            current=AggregateStore(folder,APP_VERSION,today=lambda:day)
            payload=current.snapshots()[0]
            self.assertTrue(current.acknowledge(payload))
            before=(Path(folder)/'aggregate.json').read_bytes()
            with self.assertRaisesRegex(ValueError,'invalid metrics'):
                Legacy(folder,'0.5.2',today=lambda:day).snapshots()
            self.assertEqual((Path(folder)/'aggregate.json').read_bytes(),before)
            self.assertEqual(current.snapshots(),[])
            state=current._load()['days'][str(day)]
            self.assertEqual(state['totals']['api_translation_failed_network'],1)
            self.assertEqual(state['totals']['api_translation_failed_google'],1)
            self.assertEqual(set(state['totals']),METRICS)
            self.assertEqual(len(CLASSIFIED_COUNTERS),28)


if __name__=='__main__':
    unittest.main()
