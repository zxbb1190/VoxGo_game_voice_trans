"""Opt-in cross-repository acceptance against the actual Worker and SQLite.

VOXGO_API_ROOT selects a local voxgo-api checkout; no production requests occur.
"""
import hashlib
import json
import os
import subprocess
import tempfile
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path

from voxgo.analytics.aggregation import AggregateStore
from voxgo.analytics.client import LocalAnalytics
from voxgo.analytics.daily_metrics import CLASSIFIED_COUNTERS, METRICS


NODE_ACCEPTANCE = r"""
import assert from 'node:assert/strict';
import { DatabaseSync } from 'node:sqlite';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
const apiRoot = process.argv[1];
const load = name => import(pathToFileURL(join(apiRoot, name)));
const [{ default: worker }, { canonical, digest, validate }, { getDashboardStats }] =
  await Promise.all([load('src/index.js'), load('lib/validation.js'), load('lib/admin-stats.js')]);
const { legacy, current, now, classifiedKeys } = JSON.parse(readFileSync(0, 'utf8'));
class D1 {
  sqlite = new DatabaseSync(':memory:');
  prepare(sql) {
    const db = this.sqlite;
    const stmt = (args = []) => ({
      bind: (...values) => {
        assert.ok(values.length <= 100, 'D1 bind limit');
        return stmt(values);
      },
      all: async () => ({ success: true, results: db.prepare(sql).all(...args) }),
      run: async () => ({ success: true, meta: db.prepare(sql).run(...args) }),
      execute: () => sql.trimStart().startsWith('SELECT')
        ? { success: true, results: db.prepare(sql).all(...args) }
        : { success: true, meta: db.prepare(sql).run(...args) },
    });
    return stmt();
  }
  async batch(statements) {
    this.sqlite.exec('BEGIN');
    try {
      const result = statements.map(stmt => stmt.execute());
      this.sqlite.exec('COMMIT');
      return result;
    } catch (error) { this.sqlite.exec('ROLLBACK'); throw error; }
  }
}
const db = new D1();
const migrate = name => db.sqlite.exec(readFileSync(join(apiRoot, 'migrations', name), 'utf8'));
for (const name of ['0001_telemetry.sql', '0002_telemetry_lifecycle.sql',
  '0003_telemetry_v2.sql', '0004_dashboard_auth.sql', '0005_asr_daily_counters.sql']) migrate(name);
const before = Object.fromEntries(Object.entries(legacy).filter(([key]) => key !== 'metrics'));
Object.assign(before, legacy.metrics, { created_at: new Date(now).toISOString(), updated_at: new Date(now).toISOString() });
db.sqlite.prepare(`INSERT INTO telemetry_daily (${Object.keys(before).join(',')})
  VALUES (${Object.keys(before).map(() => '?').join(',')})`).run(...Object.values(before));
migrate('0006_classified_diagnostics.sql');
const migrated = db.sqlite.prepare('SELECT * FROM telemetry_daily').get();
for (const [key, value] of Object.entries(legacy.metrics)) assert.equal(migrated[key], value);
for (const key of classifiedKeys) assert.equal(migrated[key], 0);
assert.equal(migrated.diagnostics_classification_reported, 0);
assert.equal(await validate(legacy, now), true);
assert.equal(await validate(current, now), true);
const allow = { limit: async () => ({ success: true }) };
const env = { DB: db, TELEMETRY_ENABLED: 'true', IP_LIMITER: allow, INSTALL_LIMITER: allow };
const post = async value => {
  const response = await worker.fetch(new Request('https://api.voxgo.cn/v1/telemetry/sync', {
    method: 'POST', headers: { 'Content-Type': 'application/json', 'CF-Connecting-IP': '192.0.2.1' },
    body: JSON.stringify(value),
  }), env);
  return { status: response.status, body: await response.json() };
};
const ack = await post(current);
assert.equal(ack.status, 200);
assert.equal(ack.body.snapshot_id, current.snapshot_id);
assert.equal(ack.body.revision, current.revision);
assert.equal((await post(current)).status, 200);
assert.equal((await post(legacy)).status, 200);
const after = db.sqlite.prepare('SELECT * FROM telemetry_daily').get();
assert.equal(after.revision, current.revision);
assert.equal(after.diagnostics_classification_reported, 1);
for (const [key, value] of Object.entries(current.metrics)) assert.equal(after[key], value);
const resign = async payload => {
  const { snapshot_id, ...unsigned } = payload;
  return { ...unsigned, snapshot_id: await digest(canonical(unsigned)) };
};
const conflict = structuredClone(current);
conflict.metrics.session_seconds += 1;
assert.equal((await post(await resign(conflict))).status, 400);
const regression = structuredClone(current);
regression.revision += 1;
regression.metrics.asr_fast_segments -= 1;
assert.equal((await post(await resign(regression))).status, 400);
// Later old-format writers retain new counters and reporting metadata.
const olderWriter = structuredClone(current);
olderWriter.revision += 1;
for (const key of classifiedKeys) delete olderWriter.metrics[key];
assert.equal((await post(await resign(olderWriter))).status, 200);
const preserved = db.sqlite.prepare('SELECT * FROM telemetry_daily').get();
for (const key of classifiedKeys) assert.equal(preserved[key], current.metrics[key]);
assert.equal(preserved.diagnostics_classification_reported, 1);
const dashboard = await getDashboardStats(db, 7, now + 86400000);
const output = JSON.stringify(dashboard);
for (const forbidden of ['install_id', 'daily_id', 'snapshot_id', current.install_id]) {
  assert.equal(output.includes(forbidden), false);
}
assert.equal(db.sqlite.prepare('SELECT COUNT(*) n FROM telemetry_daily').get().n, 1);
process.stdout.write(JSON.stringify({ ack: ack.body, dashboard: dashboard.breakdowns,
  checks: ['populated_0005_to_0006', 'client_63_fields', 'worker_exact_ack', 'duplicate',
    'reversed', 'conflict', 'regression', 'old_writer_preserves', 'aggregate_privacy', 'binds_le_100'] }));
"""


@unittest.skipUnless(os.environ.get('VOXGO_API_ROOT'), 'set VOXGO_API_ROOT for local joint acceptance')
class TelemetryApiContractTests(unittest.TestCase):
    def test_real_client_upgrade_worker_migration_and_ack(self):
        api_root = Path(os.environ['VOXGO_API_ROOT']).resolve()
        with tempfile.TemporaryDirectory() as root:
            day = datetime.now(timezone.utc).date()
            store = AggregateStore(root, '0.5.3-dev', today=lambda: day)
            historical = Path(root) / 'shards' / str(uuid.uuid4()) / (str(day) + '.json')
            historical.parent.mkdir(parents=True)
            old_metrics = dict.fromkeys(sorted(METRICS - CLASSIFIED_COUNTERS), 0)
            old_metrics.update(asr_segments=3, asr_segment_duration_samples=3,
                               asr_segment_duration_sum_ms=6000,
                               translation_failed=4, api_translation_failed=4)
            historical.write_text(json.dumps(dict(schema_version=2, date=str(day), metrics=old_metrics)))
            store.snapshots()
            state = store._load()
            entry = state['days'][str(day)]
            for values in [entry['totals'], entry['pending']['metrics'], *entry['seen'].values()]:
                for key in CLASSIFIED_COUNTERS:
                    values.pop(key, None)
            legacy = entry['pending']
            legacy.pop('snapshot_id')
            legacy['snapshot_id'] = hashlib.sha256(json.dumps(
                legacy, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            store._save(state)
            self.assertEqual(store.snapshots(), [legacy])
            collector = LocalAnalytics(root, '0.5.3-dev', storage_root=Path(root) / 'shards', count_start=False)
            for mode in ('fast', 'balanced', 'accurate', 'custom'):
                collector.asr_segment(2500, True, False, mode)
            for provider in ('google', 'openai_compatible'):
                collector.translation_result(False, 1000, 'api', 'timeout', provider)
            collector.stop()
            collector._thread.join(3)
            self.assertFalse(collector._thread.is_alive())
            current = store.snapshots()[0]
            self.assertEqual(current['revision'], legacy['revision'] + 1)
            self.assertEqual(current['metrics']['asr_segments'], 7)
            self.assertEqual(current['metrics']['api_translation_failed'], 6)
            self.assertEqual(current['metrics']['api_translation_failed_timeout'], 2)
            result = subprocess.run(['node', '--input-type=module', '-e', NODE_ACCEPTANCE, str(api_root)],
                input=json.dumps(dict(legacy=legacy, current=current,
                    classifiedKeys=sorted(CLASSIFIED_COUNTERS),
                    now=int(datetime.now(timezone.utc).timestamp() * 1000))),
                text=True, encoding='utf-8', capture_output=True, timeout=30, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            response = json.loads(result.stdout)
            self.assertEqual(response['ack']['snapshot_id'], current['snapshot_id'])
            self.assertFalse(store.acknowledge(legacy))
            self.assertTrue(store.acknowledge(current))
            self.assertEqual(store.snapshots(), [])
            self.assertEqual(len(response['checks']), 10)
