# Classified Full diagnostics: local acceptance, 2026-10-14

Later additive language usage is documented in [telemetry-language-usage.md](telemetry-language-usage.md).
It preserves these 63 metric meanings and adds a separately authorized, capability-negotiated
schema3 envelope; this historical schema2 acceptance retains its original scope.

This is a prepared next-version change, not a client release or a production
deployment. The app version, Fast/Balanced/Accurate parameters, Whisper models,
translation prompts, capture admission and ASR filters are unchanged.

## Protocol and counting

Full snapshots remain schema 2. New snapshots contain exactly 63 metrics: the
existing 35 plus 28 numeric counters. Basic and consent version 3 are unchanged.

For each mode `fast`, `balanced`, `accurate`, `custom`, add
`asr_{mode}_{suffix}` for these five suffixes:

- `segments`
- `forced_max_duration_splits`
- `short_fragment_segments`
- `segment_duration_sum_ms`
- `segment_duration_samples`

The capture emitter pins the mode on `SpeechSegment` before invoking callbacks.
The pipeline records that label on admission, before queueing or merging; legacy
callers without a capture label use the admission-time audio setting. The mode
never comes from the last daily setting, upload-time configuration or the
recognition scheduling policy (Custom can reuse Balanced scheduling). The
existing duration, short-fragment and forced-cut definitions remain unchanged.
One queued event and one locked daily update include both global and mode counts.

API failures add `api_translation_failed_{reason}` for `timeout`, `network`,
`rate_limit`, `http_error`, `empty_result`, `other`; independently add
`api_translation_failed_google` and `api_translation_failed_openai_compatible`.
The task's configuration snapshot pins provider attribution, even if settings
change while awaiting a response. A local-cache shortcut or unknown provider
does not become an API/provider attempt.

Providers carry a local structured `failure_reason`. Timeout exceptions, typed
connection/payload failures, HTTP 429, other non-success HTTP statuses and empty
translation output determine categories. Other handles new failures with no
reliable category; no substring matching of messages, URLs or private response
bodies is used. Cancellation, shutdown and stale language results/errors remain
excluded from attempts. Only fixed numeric counters enter Full telemetry.

## History, authorization and compatibility

Old 11/13-field v1 and 27/35-field v2 payloads stay accepted by the compatible API.
The aggregate baseline normalizes missing new fields to zero, while an existing
pending payload, hash, identity and revision stay byte-semantically exact until
a real event delta creates a newer snapshot. No old ASR mode, reason or provider
is inferred. Global totals minus classified subtotals remain unclassified; they
are not copied to `other`.

Full off creates no remote collector/uploader and regrant uses the existing new
authorization epoch. Local analytics may continue. Independent Basic includes
none of these metrics. No seed, text, audio, error messages, endpoint/model names
or new free-form dimensions are transmitted. Existing retention, bounds and
exact ACK rules remain in effect.

API migration `0006_classified_diagnostics.sql` adds 28 zero-default counters and
one internal zero-default reporting marker. The marker becomes 1 only upon an
accepted complete 63-field revision; historical zeros never prove support.
Dashboard reports classified payload / Full installation-day coverage separately
from classified event / all event coverage, plus per-mode event installation days.
Missing event denominators display no rate. Provider/reason tables are separate
subtotals, not a provider-by-reason cross-tab.

## Local validation

- Client: `.venv-win/Scripts/python.exe -m unittest discover -s tests -v` with
  `VOXGO_API_ROOT` pointing to the sibling API checkout: **489/489 passed**.
  Log: `build/telemetry-classified-all-tests.log` (ignored).
- API: `npm test`: **67/67 passed**; `npm run build` and Wrangler
  `deploy --dry-run` passed. No real deploy ran.
- Isolated local Wrangler D1: migrations 0001–0006 applied successfully with
  `--local --persist-to .wrangler/classified-migration-validation`; a second apply
  reported no migrations to apply. Logs are retained in API `.wrangler/`.
- Shared `tests/fixtures/telemetry-v2-classified.json` is generated from real
  `DailyMetrics` events and copied byte-for-byte to the API repo. Both languages
  verify its field set and canonical SHA-256; it includes historical residuals.
- Opt-in `tests/test_telemetry_api_contract.py` exercises the real Python background
  writer/AggregateStore, a populated 0005 SQLite database migrated through 0006,
  actual Worker requests, aggregate Dashboard response and exact local ACK. It
  checks duplicates, reversed revisions, conflicts, decreasing counters, older
  writer omissions, privacy and the 100-bind ceiling (maximum 73). Requests are
  in-process synthetic requests, not production HTTP uploads.
- Client regressions cover all four mode labels, capture callback/config changes,
  all six reasons through both providers, in-flight provider switches, queue
  pressure, UTC rollover, old pending hash/watermarks and Full/Basic lifecycle.
- Independent read-only review completed; incompatible-API rollback guidance and
  Windows cross-process test encoding/IP setup were corrected.

The synthetic browser preview uses the actual Dashboard HTML and real SQLite
aggregate results. Desktop/narrow-screen, history with no classification support,
and 7/14/30-day rendering were checked locally. This is separate from production
Dashboard login and packaged-client acceptance.

## Production audit and release checklist

The API repository's `docs/telemetry-audit-2026-10-14.md` records the read-only
2026-10-07 through 10-13 production audit, query time, aggregate numerators,
denominators, daily distributions and zero telemetry writes. It contains no
installation identifiers. Existing production data cannot explain modes or
failure causes; do not infer them from these aggregates.

Before a separately authorized release:

1. Review both commits and privately back up D1. Confirm existing migrations
   0001–0005, switches and limits. Take aggregate baselines without exporting IDs.
2. Apply **0006 first**, once using the migration ledger. Check all 29 columns,
   zero defaults and unchanged historical counters/revisions/hashes/timestamps.
3. Deploy the compatible Worker while preserving existing switches/Secrets.
   Verify health, old 11/13/27/35 shapes, a 63-field exact ACK, duplicates and
   authenticated Dashboard. History must remain unclassified with no new support.
4. Then package/release the client. Verify a real same-day mode switch, pending
   upgrade/retry, provider failures, opt-out and regrant in a controlled environment.
5. After complete UTC days, check support coverage, event coverage and failure
   categories using aggregate-only queries. Do not treat missing samples as health.

Once new clients are distributed, retain a Worker compatible with 63 fields for
rollback. If an incompatible older Worker is unavoidable, disable Full telemetry
first and verify POST returns retryable 503, then restore compatibility before
re-enabling. HTTP 400 is terminal for the pending revision; it is not retried.
Keep additive columns and all historical semantics intact.

This task performs no production D1 migration, Worker deployment, GitHub push or
client release. Production and packaged-client checks above remain release work.
