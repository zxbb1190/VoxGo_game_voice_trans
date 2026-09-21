# Package edition and shutdown counters

## Fields and identity

`VoxGo.spec` embeds `package-info.json` inside the application bundle. Its value is
`lite`, `full`, or `full-cuda`, selected from the same model/CUDA build flags as
the package contents. Source execution reports `source`. A legacy/corrupt frozen
bundle without this metadata reports `unknown`; directory names are not trusted.
Existing pending payloads retain their exact hash and edition until new cumulative
data creates a new revision. A daily row records the edition of its latest snapshot,
not an edition-by-edition history if a user changes editions during that day.

## Shutdown counts

- `clean_exits`: Qt's event loop returned normally (or KeyboardInterrupt), and
  application service cleanup completed. A shutdown request, tray hide, cleanup
  failure, or force quit is not a clean exit.
- `unclean_starts`: a later start discovers a prior run marker whose OS lock is
  no longer held and which has no clean-exit intent. A still-running second
  instance is not counted. This indicates an unconfirmed shutdown, not a proven
  application crash: power loss, force termination and disk errors may contribute.

The marker is local, scoped to the telemetry authorization epoch. Only numeric
daily shards are uploaded, never stack traces, error messages, PIDs or paths.
Recovery uses deterministic shard identities and a persisted intent so replay
cannot increase the same outcome twice. Detection is counted on the recovery
day; it is not proof that the currently running version caused the prior failure.
Normal-exit shards are written locally after cleanup and sent by a later uploader
round/start. No network request or network wait is introduced on exit. Local
finalization runs on a daemon worker with a maximum 200 ms wait per collector;
a stuck disk cannot hold application exit indefinitely. If that local write
cannot complete, the later marker means an unconfirmed exit, not proof of a crash.

Local-only lifecycle data is under `analytics/shards` and shares the existing
90-file / 2 MiB snapshot budget with local usage data; consented data is under
the existing epoch's `analytics-remote`. Markers are recovered within a 7-day
window and lifecycle shards retained up to 30 days (remote retention can prune
them earlier). IO remains best effort; absence of a marker or failed disk writes
cannot establish that a run was clean. The counters are not real-time online counts.

## Consent and backend compatibility

Consent version 3 explicitly discloses package edition and shutdown counters.
Version 2 authorization cannot send this expanded scope. The user must confirm
again, creating a new epoch; pre-consent/local-only data is never backfilled.

The backend accepts either the original 11 metrics or all 13 including both new
counters. Both new fields are bounded integers, and the original wire payload is
hashed without normalization. Apply backend migration `0002_telemetry_lifecycle.sql`
before deploying the new Worker. Old client uploads remain supported and preserve
already stored lifecycle counters. Old dates are not retrospectively populated
with measured values: migration defaults of zero mean no recorded events.

The existing daily UPSERT key, monotonically increasing counters/revisions, exact
ACK checks, retry policy and outbox cleanup rules are unchanged. GET timeout stays
5 seconds; POST stays 15 seconds; urllib default proxy discovery is unchanged.
