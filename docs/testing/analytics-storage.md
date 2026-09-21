# Local analytics storage contract

LocalAnalytics is connected to application startup, translation runtime results,
accepted ASR transcripts, pause state, active processing time and shutdown.
This local-only buffer is never uploaded. A separate consent-only remote buffer is
described in [remote-telemetry.md](remote-telemetry.md). Each process writes
runtime_dir/analytics/<random UUID>/
YYYY-MM-DD.json. UUIDs isolate simultaneous writers; they are not installation IDs.
Retention, file count and byte budgets also apply across these process directories.

A process counts one session on each UTC day it runs. Each active mode counts
once per process per UTC day, including uninterrupted midnight rollover. session_seconds measures active backend time, excluding pause; scheduling
gaps are capped at two seconds to avoid counting long suspension as activity.
Successful cached translations count as success, not as paid API requests.
Empty/error responses count as failure; cancellation, filtering, stale results
and untranslated notices do not. Translation latency samples cover completed
responses; raised errors have no latency sample. ASR latency covers published
transcripts, not filtered/empty recognition attempts.

No text, exception details, keys or paths enter metrics. Package and environment
metadata remain unknown/empty until reliable runtime metadata is available.
The background worker flushes every 30 seconds. Stop requests a final flush
without blocking exit; forced termination may lose the last unflushed interval.

## Bounds

- Keep today and the preceding 29 days by default, even without uploads.
- At most 90 owned files and 2 MiB total, including quarantine and temp files.
- Individual snapshots are limited to 32 KiB.
- Prefer today's valid snapshot, then other snapshots, over auxiliary files.
- Remove old temporary files after their creation day; they also share the caps.
- Never delete unrelated filenames or follow file symlinks during cleanup.
- Bounds are best effort when filesystem permissions prevent deletion.

## Upload acknowledgement

The local store exposes acknowledgement using `store.revision(snapshot)`.
The remote uploader instead uses the durable aggregate outbox described above.
Only after server acknowledgement may it call `mark_uploaded(day, revision)`.
An old acknowledgement cannot remove a subsequently changed snapshot. Today's
file remains because it contains cumulative counters. Closed-day snapshots may
be deleted after exact acknowledgement; failed uploads expire under retention.

## Collection and persistence

Counters and latency observations are allowlisted, numeric and bounded. Events
accumulate in memory under a lock, without disk writes. `flush()` persists pending
days and the current day using atomic replacement. Cross-day rollover is driven
by an injectable UTC date. Failed writes retain bounded pending memory.

The runtime adapter owns a bounded queue and performs all disk access on a daemon
thread. Full queues drop statistics without interrupting translation. Remote
upload aggregates separate authorized per-process snapshots with stable revisioned
keys instead of overwriting daily totals with one process's counters.

Windows validation: 8 storage tests cover stale acknowledgements, today's file,
cross-day reload, concurrent increments, no per-event IO, retention, total byte
and file limits, corruption, write failures and invalid inputs.
