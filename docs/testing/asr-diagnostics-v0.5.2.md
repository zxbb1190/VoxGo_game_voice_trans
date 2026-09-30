# ASR Daily Snapshot diagnostics in v0.5.2

The production path is `SystemAudioCapture.on_speech -> VoxGoApp._on_speech_detected
-> SpeechPipeline -> VoxGoApp._analytics_call -> AuthorizedAnalytics`.
The callback is optional for standalone benchmarks/tests and cannot change ASR
admission, model settings, or filters when collection fails.

## Counter definitions

| Counter | Counting point |
| --- | --- |
| `asr_segments` | One valid capture segment admitted by CandidatePolicy, before pending merges or queueing. |
| `asr_forced_max_duration_splits` | Admitted capture segments whose cut reason is the existing maximum-duration cut. |
| `asr_short_fragment_segments` | Admitted capture segments classified by the existing short-segment policy: voiced duration below 0.8 seconds. |
| `asr_segment_duration_sum_ms` | Total original capture duration, rounded to milliseconds; not merged ASR input duration. |
| `asr_segment_duration_samples` | One duration observation per admitted capture segment. |
| `asr_weak_candidate_drops` | Weak work items rejected by pre-ASR rules, inference budget, busy-buffer expiry, queue capacity or queue restoration overflow. |
| `asr_post_filter_drops` | ASR results rejected as empty/too short, by VAD/output/language filters, or by the repetition guard. |
| `asr_runaway_repetition_blocks` | Results blocked specifically by the runaway guard; a subset of post-filter drops. |

Weak drops count **work items**, which may contain merged capture segments.
Manual clears, pause/stop and language-switch discards are excluded. Post-filter
drops exclude stale results discarded after a user changes language direction.
These aggregate counts do not measure WER or identify the words that were lost.
The quotient `duration_sum_ms / duration_samples` measures capture segment length.
Different counting points mean drop counts need not share the capture count as a
denominator. Collection is bounded and best effort; pressure/exit may lose events.

## Storage, consent and compatibility

- Each segment's count, duration and flags are one queued event and one locked
  daily update. Event callbacks do not write snapshots themselves.
- UTC Daily Snapshots retain the existing bounded local/remote storage policy.
- Only fixed counter names and integers are added. No audio, recognition or
  translation text, paths, game names or new free-form metadata enter the payload.
- Full reporting still requires existing consent version 3 and the same durable
  authorization epoch. Full off disables remote ASR reporting. Local counts may
  continue; independent Basic reporting contains no ASR metrics.
- New Full snapshots remain schema 2 and contain 35 fields. Existing v1 and
  27-field v2 pending snapshots keep their exact payload/hash, identity and
  revision until new data creates a later snapshot. No user configuration or
  consent migration is added for this release.
- The compatible API accepts old 11/13-field v1 and 27/35-field v2. D1 migration
  `0005_asr_daily_counters.sql` adds eight columns. Older payloads omit these
  fields and preserve previously recorded values.

Deploy the compatible API and apply its additive migration **before distributing
v0.5.2**. Tests/dry runs and local counters do not establish production deployment
or real-player validation. See the RC acceptance record and API deployment notes.
