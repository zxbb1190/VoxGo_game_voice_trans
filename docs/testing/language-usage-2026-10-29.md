# v0.6.0 language usage — local acceptance, 2026-10-29

## Result

Implemented and locally validated. **No production migration, deployment, translation API
request, push, tag or release. Existing release ZIPs were not rebuilt or replaced.**

Client branch: `codex/release-0.6.0`, starting at `fa5f6054`; this commit contains the client
implementation and evidence. API branch: `codex/telemetry-classified-diagnostics`, implementation
commit `9fd68125e928bc1ba25b5ae7d80f350133f66de3` (based on `e369e505`). Production migration
state was not queried. See [protocol and rollout checklist](telemetry-language-usage.md).

## Delivered behavior

- Per task: fixed source/target codes, `api/offline/cache/unknown`, technical success/failure.
  All 20 directions are representable; offline remains English–Chinese only.
- Attribution uses the task's configuration snapshot. Changing settings, stale/cancelled work,
  unsupported/filtered input and API configuration tests do not manufacture usage events.
- Original63 metrics retain their meaning. Schema3 adds a bounded allowlisted array, includes
  it in the snapshot hash, and is negotiated only with a ready server capability.
- Direction cumulative watermarks and the dedicated outbox survive restart, duplicates,
  shard resurrection, old executable rollback and re-upgrade without identity reset.
- Existing Full users retain their old authorization scope. A Privacy action enables this
  new category; new Full opt-ins include it after disclosure. No pre-grant or disabled-period
  backfill. Full off stops language collection. Basic contains no language classification.
- Dashboard adds source/target ranking, a 20-direction matrix, modes, daily trends, dimension-
  deduplicated install-days, reporting/event coverage and unclassified counts. No installation
  identifiers or private content are returned. Success is not semantic accuracy.

## Verification

| Check | Actual result |
| --- | --- |
| Client complete suite, final run | **732/732 passed**, 58.054s, with local API contract enabled |
| Dedicated language tests | **13/13 passed**, including actual pre-change aggregate rollback |
| Existing and new joint contracts | Actual Python collector/aggregate → actual Worker → isolated SQLite; both passed |
| API unit tests | **79/79 passed** in the API implementation run |
| API build | Passed |
| Real local workerd/D1 | 0001–0007, config capability, atomic parent/child JSON batch, replay, omitted-row conflict, legacy writer and FK cascade passed |
| EN/ZH runtime comparison | **48/48 equal** to `afc33a67`: audio, decoding/model selection, scheduling |
| v0.6.0 release preflight | Passed; published update metadata stays 0.5.2 |
| Privacy UI | Five locales, ungranted and granted states, offscreen Qt components checked |
| Dashboard browser | Actual HTML with synthetic SQLite-derived aggregates, desktop 1440px/mobile 390px; all/API/offline/cache/unknown and 7/14/30-day controls checked |
| Browser errors | 0 console errors; requests stayed on 127.0.0.1 |
| Diff check | Passed |

One intermediate full run hit the pre-existing local relay preflight flake
`test_production_helper_with_fake_credential_exposes_only_health_and_gate` (`blocked=2`, expected 1).
The isolated case then passed, followed by the complete 732-test pass after closing parallel browser
fixtures. Both logs are retained; no relay, translation or ASR code was altered to mask it.

The new joint test verifies migration 0006→0007 without historical backfill, unchanged ordinary
config fields, missing-schema/disabled capability gates, Python/JS array hashes, all 20 directions,
exact ACK/replay, atomic omitted-row rejection, old-writer preservation, aggregate-only output,
unclassified denominators and <=100 SQL binds.

Independent review identified one authorization race: a pre-grant event could be queued with
language data and consumed after enabling the category. Admission now strips language fields
before queueing unless authorized, while the writer rechecks revocation. A deterministic queue
regression and an independent reviewer rerun passed. No remaining reviewed blockers were found.

## Implementation map

| Area | Files/functions |
| --- | --- |
| Capture task direction | `voxgo/translation/runtime.py`: `_translate_current`, `_record_analytics`, `_handle_error` |
| Fixed vocabulary and bounds | `voxgo/analytics/language_usage.py`: `direction_key`, `usage_map`, `validate_totals` |
| Atomic outcome and queue authorization | `daily_metrics.py::translation_result`; `client.py::AuthorizedAnalytics._call` |
| High watermarks / rollback-safe outbox | `aggregation.py::AggregateStore.snapshots`, `_load`, `acknowledge` |
| Capability / per-POST consent | `uploader.py::RemoteUploader.sync_once` |
| Durable category grant | `migration.py::validated_consent`, existing authority persistence; config schema/loader and UI copies |
| Disclosure / explicit opt-in | `settings_dialog.py::_enable_language_usage_consent`; `dialogs.py::FirstRunWizard._mark_completed`; five-locale messages |
| API / schema / Dashboard | API commit above: `language-usage.js`, `d1-store.js`, migration 0007, `language-stats.js`, `dashboard-page.js` |

No ASR presets, models, recognition filters, Provider prompts or OPUS semantics changed.

## Evidence and reproduction

- Committed visual evidence: [desktop Dashboard](evidence/v0.6.0-language-usage-2026-10-29/dashboard-desktop.png),
  [mobile Dashboard](evidence/v0.6.0-language-usage-2026-10-29/dashboard-mobile.png),
  [existing Full before opt-in](evidence/v0.6.0-language-usage-2026-10-29/privacy-before-zh-CN.png),
  [after opt-in](evidence/v0.6.0-language-usage-2026-10-29/privacy-after-zh-CN.png).
- The same evidence directory includes all five UI locales and compact check records.
- Local raw logs, isolated fixture script/data, UI capture script, browser snapshots and failed/
  successful full runs remain under `build/language-usage-20261029/`; old evidence is untouched.
- Reproducible automated commands are in [the protocol document](telemetry-language-usage.md#本地验证--local-acceptance).
  API-only workerd and migration checks are local, not production.

Synthetic Dashboard fixture: 60 classified outcomes (56 successes/4 failures),45 unclassified;
API 52, offline 5, cache 3, unknown 0. Every dimension has one actual installation-day even when it
appears in several directions. These figures only verify rendering/denominators, **not usage in
production**. Mobile document width 390px at a 390px viewport; wide tables scroll internally.

## Release boundary

Source implementation is ready for the next local package build. Production still requires
authorized schema verification,0006/0007 migrations as needed, compatible Worker with the new
flag initially false, capability/ACK smoke tests, then explicit flag activation and client delivery.
The shipped/previously built EXE has not acquired this source change automatically.

Full EXE verification of the new Privacy control and actual consented production reporting are
not performed here; offscreen components and local browser fixtures do not replace them.
Rollback disables the capability first and retains additive tables and high watermarks.
