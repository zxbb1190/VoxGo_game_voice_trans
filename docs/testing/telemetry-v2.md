# Telemetry v2: protocol and acceptance

This document records the original Telemetry v2 source acceptance. The client is included in v0.5.1; deployment and release status must be checked separately.

## Basic: daily active installations

Basic is independent of Full consent, epoch, install ID, business counters and
sampling. It counts installations, not people. Separate portable directories
may count separately; copied directories may share a seed. It cannot measure
cross-day retention or match a person to GitHub/GitCode downloads.

Persist a random UUID seed and an immutable first-run UTC date in
`user_settings.json`, with a one-time migration marker and installation origin.
Historical or uncertain installations have an empty first-run date, not today's
date. The daily ID is lowercase SHA256 of ASCII
`voxgo-basic-v1\0{canonical_uuid}\0{YYYY-MM-DD}`, using literal NUL separators.
The seed is never transmitted. Full's long-lived identity is never used here.

POST `/v1/telemetry/basic` has exactly:
`schema_version=1,date,daily_id,revision,snapshot_id,app_version,package_type,first_run,setup_completed,full_telemetry,full_telemetry_source`.
Sources are `new_install_pending`, `new_install_default`, `user_enabled`,
`user_disabled`, `migration_allowed`, `migration_denied`, `migration_unknown`,
`unknown`. Package values remain `lite,full,full-cuda,source,unknown`.

Hash the full payload without snapshot_id using recursively sorted canonical
JSON, compact separators, ASCII whitelist values. A date starts at revision 1.
State, app version or package changes increment revision; identical state does
not. First-run and setup-completed flags are sticky within a date. Full state
means the locally enabled choice, not whether the remote kill switch is enabled.

ACK is flat: `success=true,daily_id,date,revision,snapshot_id,disposition`.
Disposition is `stored` or `superseded`; all identity fields must match exactly.
An old ACK never clears a newer local snapshot. Basic keeps only a small latest
state per date, not Full's cumulative metrics or shard machinery.
The server's snapshot_id identifies the accepted request. Stored first_run and
setup_completed are sticky daily projections (logical OR with previous values),
so a database row is not a canonical copy from which to recompute that digest.

`analytics-basic/state.json` keeps at most seven UTC dates and bounded retry state.
The background daemon polls local settings every 10 seconds, writes only changed
state, and never uploads identical acknowledged state. All processes share the
uploader lock and persisted retry schedule. Startup delay is 3 seconds; GET is
5 seconds and POST 15 seconds. Request rounds are at least the server interval
(900 seconds minimum), with jitter; failed rounds back off up to 24 hours and
honor bounded Retry-After. State changes do not bypass backoff. Exit signals stop
without waiting for HTTP. Corrupt Basic state fails closed, with a fixed local
diagnostic result. Missing/corrupt Full authority does not disable Basic.

## Full: existing scope, finer aggregates

Full still uses LocalAnalytics, AuthorizedAnalytics, Daily Snapshot, epoch,
AggregateStore, cumulative revision and exact snapshot ACK. Consent version
remains 3: no new behavior category is introduced in this change.
New Full snapshots have schema_version 2 and exactly 27 metrics:
the existing 13 plus four mode-specific translation outcome counters and ten
latency buckets. New baselines normalize missing counters to zero; existing v1
pending payloads and hashes remain unchanged until real new data is aggregated.
The API accepts old 11/13-metric v1 and the new 27-metric v2. Old writes preserve
new columns. No existing D1 records are dropped.

Buckets for both ASR and translation are `lt_500`, `500_1000`, `1000_2000`,
`2000_5000`, `ge_5000`, selected using original milliseconds before sum rounding.
Mode-specific translation success/failure uses the task's configuration snapshot.
Unknown modes and local-cache shortcuts are not attributed to API/offline.
Cancellation and stale-result discard are not defined as attempts or failures.
Totals may exceed mode-specific sums; old latency samples may have no buckets.
Each translation outcome is one queued event and one locked update of its
total, mode subtotal and latency. Queue pressure cannot split these counters.
No attempts, download-source, update-click, overlay or mobile behavior counters
are added. No model names, paths, errors, content or free-form metadata are sent.

## Migration and UI

- New installation: Basic starts; Full checkbox is checked, but Full collector
  and uploader cannot start until setup completion and persisted choice.
- Historical allowed (valid consent version 3 and UUID epoch): preserve enabled
  state, migration_allowed. Historical denied/unknown remain off.
- Existing authority overrides stale settings; corrupt grants never become allowed.
- Missing authority during the 0.5.0 upgrade is restored from valid preserved
  settings. One-time loss of old Full identity/baseline/outbox is accepted. Never
  search backup directories. Server history remains unchanged.
- Turning Full off stops its remote collector/uploader and keeps Basic running.
  Re-enabling creates a new epoch, with no backfill of disabled-period data.
- Future updater preservation includes user_settings.json, telemetry_consent.json,
  analytics-basic, analytics-remote and analytics (including lifecycle markers).

## Configuration and rollout

GET `/v1/config` remains schema 1. `telemetry_enabled` and sampling retain Full
semantics. Added `basic_telemetry_enabled` is an independent, unsampled kill
switch; missing/malformed Basic config prevents Basic POST. Published 0.5.0
clients tolerate the additional field. Deploy the compatible API and additive
migration before distributing the new client; enable Basic only after checking
both routes. See the API repository `docs/telemetry-v2.md` for schema inspection,
backup, migration and deployment commands. No production actions were run here.

## Verification

Tests cover first-run persistence before wizard completion; migration allowed,
denied and unknown; corrupted settings/authority; concurrent initialization;
revoke/regrant; seven-day retention; same-state dedupe; day rotation; state/version/
package revision changes; persisted retry; exact/superseded/wrong ACK; uploader
lock; stop during blocked HTTP; all latency boundaries; v1 pending compatibility;
and real Windows updater preservation and rollback. Shared Python/JS fixtures
in `tests/fixtures` lock canonical hashes and schema field names.

Local acceptance on 2026-09-23: client `python -m unittest discover -s tests -v`
passed 366 tests (Windows, `.venv-win`); API `node --test` passed 23 tests,
including actual SQLite transactions. The client log is generated at
`build/telemetry-v2-all-tests.log` (not committed). This does not establish
production Worker/D1 deployment or packaged EXE acceptance.
