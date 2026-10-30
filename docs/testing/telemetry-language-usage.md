# 语言使用统计 / Language usage telemetry

Initial implementation accepted on2026-10-29; current activation/package status is below.

Update2026-10-30: the user authorized production compatibility rollout and a new local Lite;
both completed. See [current release/test handoff](v0.6.0-language-usage-release-2026-10-30.md).
The earlier separate category opt-in was superseded by the original Full switch.

## 范围与口径 / Counting contract

沿用现有 Full 日累计统计，增加源语言、目标语言、翻译方式和成功/失败计数。
统计一次实际完成的翻译任务；失败表示技术失败，成功不表示语义正确。
按照任务配置快照归属，不按当天最后一次语言设置或 Provider 返回的语言推断。

- 固定语言代码 `zh/en/ja/ko/ru`，仅20个不同语言的有向组合。
- `api`：在线任务结果；`offline`：原有英中本地任务结果；`cache`：本地缓存命中；`unknown`：方式不明。
- 缓存不增加原 API 成功计数；失败分类仍沿用原来的固定原因/服务商口径。
- 设置切换、接口测试、语言门控、取消、过期任务和不支持方向不增加完成任务数。
- 没有可靠方向的旧调用只增加原总数，保持未分类；不根据历史设置回填。
- 不上报语音、原文、译文、Prompt、Key、地址、路径或新增硬件/安装标识。

Counts represent completed runtime translation outcomes, not language-selector clicks, HTTP attempts,
semantic accuracy, or people. Attribution uses the immutable task configuration. Legacy calls remain
unclassified. Cache is separate from API and offline outcomes.

## 协议与存储 / Wire and storage

Original `metrics` remains exactly **63 numeric fields**, with unchanged meanings.
New wire schema **3** adds only `language_usage` beside `metrics`. Each array row contains:

```json
{"source_lang":"ja","target_lang":"zh","mode":"api","success":4,"failed":1}
```

The array is sorted, bounded (<=80), strictly allowlisted, and included in the canonical hash.
Duplicate direction/mode rows, same-language pairs, noncanonical codes, extra text fields,
invalid counts and non-English/Chinese offline pairs are rejected. Empty array is a valid
classification reporter. Direction totals fit the old coarse totals; cache/unknown fit the
remainder. Earlier events stay unclassified. Local shard schema2 stores the optional array
beside the original metrics, atomically with each result, within the old retention/size limits.

The aggregate keeps independent direction high watermarks and a separate `language_pending`
outbox. Old executables cannot POST schema3 from their legacy `pending` slot. Restart,
replay, shard resurrection, old-writer updates and capability downgrade/upgrade preserve
the installation identity and cumulative baseline.

Migration **0007** adds a parent reporting marker and a child direction table, avoiding
column/binding growth beyond D1's 100 bind limit. Parent/child changes share one transaction.
Higher legacy revisions preserve classifications. Decreasing counts or omitting positive
rows in schema3 cannot erase history. Historical rows stay unclassified. Retention cascades
from the parent to its child rows.

## 授权与协商 / Authorization and negotiation

As of2026-10-30, language counts follow the **original Full privacy switch**, with no separate
button, category grant or stored consent marker. Existing allowed/version3 grants include
language counts without another click. New-install setup keeps its original checked default,
and Full starts only after setup completes. Existing denied/unknown choices are preserved.

- The updated five-locale privacy notice includes fixed language codes/mode/outcome counts.
- Remote admission and the background writer both check Full permission; revocation stops
  queued collection. An obsolete per-language marker in older settings is ignored.
- Full off stops all Full dimensions. Re-enable uses the existing new-epoch rule without
  disabled-period backfill. Ordinary saves cannot restore a revoked grant from another process.
- Local-only statistics remain separate from the consent-authorized remote buffer.

Only Full-authorized clients request `GET /v1/config?language_usage=1`. Schema3 requires the exact
integer capability `language_usage_schema:1`. Ordinary config retains its original five fields.
Old Worker, disabled flag, missing migration or invalid capability yields the original
schema2/63-field payload. Consent is checked again before a schema3 POST.

## Dashboard

源/目标语言排行、20方向矩阵、成功失败数、模式筛选、UTC每日趋势、去重使用安装日、
上报覆盖率及未分类量；完整 UTC7/14/30日与原报表口径一致。
各方向安装日不能相加当用户人数；缓存/未知方式没有可靠的独立旧指标分母。
无上报显示“尚无语言分类上报”，不解释为无人使用。接口仅返回聚合结果。

## 本地验证 / Local acceptance

```powershell
$env:QT_QPA_PLATFORM='offscreen'
$env:VOXGO_API_ROOT='E:/my/my/voxgo-api'
.venv-win/Scripts/python.exe -B -X utf8 -m unittest tests.test_language_usage_telemetry tests.test_language_usage_api_contract -v
.venv-win/Scripts/python.exe -B -X utf8 -m unittest discover -s tests -v
.venv-win/Scripts/python.exe scripts/release_preflight.py --version 0.6.0 --base-ref afc33a67
.venv-win/Scripts/python.exe scripts/verify_english_chinese_compatibility.py --base-ref afc33a67
# In the API checkout:
npm test
npm run build
node scripts/check-language-usage-workerd.mjs
```

Joint tests use actual Python collectors and the JavaScript Worker against isolated SQLite;
the API's script separately verifies real local workerd/D1. Rollback tests load the actual
pre-change aggregate source from `fa5f6054` without changing the checkout. Offscreen UI
screenshots are component evidence, not Full EXE acceptance. Browser fixtures contain
synthetic aggregate data only. See [acceptance results](language-usage-2026-10-29.md).

## 发布与回退 / Rollout and rollback

No production operation is authorized or executed here. Future release must:

1. Verify/backup the actual target schema. Accept existing 0006 and additive0007 in order;
   this task does not establish the production migration state.
2. Deploy the compatible Worker **with the language flag false**. Check health, the old
   five config fields, old payloads, authorization, cleanup and aggregate Dashboard.
3. After 0007 is verified, explicitly enable `LANGUAGE_USAGE_TELEMETRY_ENABLED=true` and
   check opt-in capability, controlled exact ACK, duplicate/reversed idempotency and coverage.
4. Separately build/test/distribute the updated client. This source change does not replace
   the already-built v0.6.0 Lite ZIP. One Full switch controls both old and new numeric dimensions.

Rollback: disable the language flag first so new clients use the original 63 fields. Keep 0007
and cumulative state. A compatible Worker can remain deployed with the flag off; client
rollback preserves coarse counts and classification watermarks. A rejected snapshot is not
a successful report. Do not roll back to a Worker that cannot accept 63 fields while
distributing a 63-field Full client.
