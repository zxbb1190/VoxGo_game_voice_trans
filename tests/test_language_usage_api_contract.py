"""Actual client -> actual local Worker -> SQLite; never contacts a service."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from voxgo.analytics.aggregation import AggregateStore
from voxgo.analytics.client import LocalAnalytics
from voxgo.languages import ONLINE_DIRECTIONS


NODE_ACCEPTANCE = r"""
import assert from 'node:assert/strict';
import { DatabaseSync } from 'node:sqlite';
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
const root=process.argv[1];
const load=name=>import(pathToFileURL(join(root,name)));
const [{default:worker},{validate,canonical,digest},{getDashboardStats}]=await Promise.all([
  load('src/index.js'),load('lib/validation.js'),load('lib/admin-stats.js')]);
const {legacy,current,now}=JSON.parse(readFileSync(0,'utf8'));
class D1 {
  sqlite=new DatabaseSync(':memory:');
  maxBinds=0;
  prepare(sql) {
    const db=this.sqlite,owner=this;
    const statement=(args=[])=>({
      bind(...values) { owner.maxBinds=Math.max(owner.maxBinds,values.length);assert.ok(values.length<=100);return statement(values); },
      all:async()=>({success:true,results:db.prepare(sql).all(...args)}),
      run:async()=>({success:true,meta:db.prepare(sql).run(...args)}),
      execute:()=>sql.trimStart().startsWith('SELECT')?{success:true,results:db.prepare(sql).all(...args)}
        :{success:true,meta:db.prepare(sql).run(...args)},
    });
    return statement();
  }
  async batch(statements) {
    this.sqlite.exec('BEGIN');
    try {const results=statements.map(s=>s.execute());this.sqlite.exec('COMMIT');return results;}
    catch(e) {this.sqlite.exec('ROLLBACK');throw e;}
  }
}
const db=new D1(),allow={limit:async()=>({success:true})};
const env={DB:db,TELEMETRY_ENABLED:'true',IP_LIMITER:allow,INSTALL_LIMITER:allow};
const fetch=async(path,payload)=>{
  const response=await worker.fetch(new Request('https://api.voxgo.cn'+path,payload?{
    method:'POST',headers:{'content-type':'application/json','CF-Connecting-IP':'192.0.2.1'},body:JSON.stringify(payload)}:{}),env);
  return {status:response.status,body:await response.json()};
};
const post=value=>fetch('/v1/telemetry/sync',value);
const resign=async value=>{const {snapshot_id,...unsigned}=value;return {...unsigned,snapshot_id:await digest(canonical(unsigned))};};
const migrations=readdirSync(join(root,'migrations')).filter(n=>/^000[1-6]_.*\.sql$/.test(n)).sort();
assert.equal(migrations.length,6);
for(const migration of migrations) db.sqlite.exec(readFileSync(join(root,'migrations',migration),'utf8'));
assert.equal((await post(legacy)).status,200);
env.LANGUAGE_USAGE_TELEMETRY_ENABLED='true';
assert.equal((await fetch('/v1/config?language_usage=1')).body.language_usage_schema,undefined);
db.sqlite.exec(readFileSync(join(root,'migrations','0007_language_usage.sql'),'utf8'));
assert.equal(db.sqlite.prepare('SELECT language_usage_reported FROM telemetry_daily').get().language_usage_reported,0);
assert.equal(db.sqlite.prepare('SELECT COUNT(*) n FROM telemetry_language_daily').get().n,0);
const ordinary=(await fetch('/v1/config')).body;
assert.deepEqual(Object.keys(ordinary).sort(),['schema_version','telemetry_enabled','basic_telemetry_enabled','telemetry_sample_rate','sync_interval_seconds'].sort());
assert.equal((await fetch('/v1/config?language_usage=1')).body.language_usage_schema,1);
env.LANGUAGE_USAGE_TELEMETRY_ENABLED='false';
assert.equal((await post(current)).status,503);
assert.equal((await post(legacy)).status,200);
env.LANGUAGE_USAGE_TELEMETRY_ENABLED='true';
assert.equal(await validate(current,now),true,'real Python schema3/hash validates in JS');
const ack=await post(current);
assert.equal(ack.status,200);
assert.equal(ack.body.snapshot_id,current.snapshot_id);
assert.equal((await post(current)).status,200);
assert.equal((await post(legacy)).status,200);
const before=db.sqlite.prepare('SELECT * FROM telemetry_daily').get();
assert.equal(before.language_usage_reported,1);
assert.equal(before.translation_success,current.metrics.translation_success);
const children=()=>db.sqlite.prepare('SELECT source_lang,target_lang,mode,success,failed FROM telemetry_language_daily ORDER BY source_lang,target_lang,mode').all();
assert.equal(children().length,current.language_usage.length);
const expected=JSON.stringify(children());
const omitted=structuredClone(current);omitted.revision++;omitted.language_usage=omitted.language_usage.slice(1);
assert.equal((await post(await resign(omitted))).status,400,'cannot erase a positive row');
assert.equal(db.sqlite.prepare('SELECT revision FROM telemetry_daily').get().revision,before.revision,'atomic rejection');
assert.equal(JSON.stringify(children()),expected);
const oldWriter=structuredClone(current);delete oldWriter.language_usage;oldWriter.schema_version=2;oldWriter.revision++;
oldWriter.metrics.translation_success++;oldWriter.metrics.api_translation_success++;
assert.equal((await post(await resign(oldWriter))).status,200);
assert.equal(JSON.stringify(children()),expected,'old writers preserve classification');
const restored=structuredClone(current);restored.revision+=2;restored.metrics=oldWriter.metrics;
assert.equal((await post(await resign(restored))).status,200);
const dashboard=await getDashboardStats(db,7,now+86400000);
const language=dashboard.breakdowns.language_usage;
assert.equal(language.views.all.directions.length,20);
assert.equal(language.views.all.success,current.language_usage.reduce((n,r)=>n+r.success,0));
assert.equal(language.reporter_install_days,1);
assert.equal(language.views.all.event_install_days,1);
assert.equal(language.views.all.unclassified,2,'pre-authorization and rollback events stay unclassified');
for(const forbidden of ['install_id','daily_id','snapshot_id',current.install_id]) assert.equal(JSON.stringify(dashboard).includes(forbidden),false);
process.stdout.write(JSON.stringify({ack:ack.body,max_binds:db.maxBinds,checks:[
  '0006_to_0007_no_backfill','legacy_five_config_fields','migration_readiness','default_gate',
  'python_js_hash','all_twenty_directions','exact_ack','duplicate_reversed','atomic_omission_rejection',
  'old_writer_preserves','upgrade_restore','aggregate_only_dashboard','unclassified_denominator','binds_le_100']}));
"""


@unittest.skipUnless(os.environ.get('VOXGO_API_ROOT'), 'set VOXGO_API_ROOT for local joint acceptance')
class LanguageUsageApiContractTests(unittest.TestCase):
    def test_real_client_schema3_and_legacy_worker_storage_contract(self):
        with tempfile.TemporaryDirectory() as root:
            day = datetime.now(timezone.utc).date()
            allowed = [False]
            collector = LocalAnalytics(root, '0.6.0', storage_root=Path(root) / 'shards',
                                       count_start=False, language_usage_allowed=lambda: allowed[0])
            collector.translation_result_with_language(True, 10, 'api', None, None, 'ja', 'zh', 'api')
            collector.stop()
            collector._thread.join(3)
            self.assertFalse(collector._thread.is_alive())
            store = AggregateStore(root, '0.6.0', today=lambda: day)
            legacy = store.snapshots()[0]
            allowed[0] = True
            collector = LocalAnalytics(root, '0.6.0', storage_root=Path(root) / 'shards', count_start=False,
                                       language_usage_allowed=lambda: allowed[0])
            for source, target in sorted(ONLINE_DIRECTIONS):
                collector.translation_result_with_language(True, 10, 'api', None, None, source, target, 'api')
            collector.translation_result_with_language(False, 10, 'api', 'timeout', 'google', 'ko', 'ru', 'api')
            collector.translation_result_with_language(True, 10, 'offline', None, None, 'en', 'zh', 'offline')
            collector.translation_result_with_language(True, 10, None, None, None, 'zh', 'en', 'cache')
            collector.stop()
            collector._thread.join(3)
            self.assertFalse(collector._thread.is_alive())
            store.language_usage = True
            current = store.snapshots()[0]
            self.assertEqual(len(current['metrics']), 63)
            response = subprocess.run(['node', '--input-type=module', '-e', NODE_ACCEPTANCE, os.environ['VOXGO_API_ROOT']],
                input=json.dumps(dict(legacy=legacy, current=current,
                    now=int(datetime.now(timezone.utc).timestamp() * 1000))),
                text=True, encoding='utf-8', capture_output=True, timeout=30)
            self.assertEqual(response.returncode, 0, response.stderr)
            result = json.loads(response.stdout)
            self.assertEqual(len(result['checks']), 14)
            self.assertEqual(result['ack']['snapshot_id'], current['snapshot_id'])
            self.assertLessEqual(result['max_binds'], 100)
            self.assertFalse(store.acknowledge(legacy))
            self.assertTrue(store.acknowledge(current))
            self.assertEqual(store.snapshots(), [])
