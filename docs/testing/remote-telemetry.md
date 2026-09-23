# Remote telemetry transport and consent

Current backend: Cloudflare Worker + D1, origin https://api.voxgo.cn.
Local implementation tests do not substitute for staging HTTP/D1 acceptance.

## Cloudflare client hardening (2026-09-21)

Telemetry v2 has two independent channels. Basic counts daily active installations
using an identifier that rotates on UTC dates and is not linked across days. It is
always enabled locally and sends only the Basic allowlist when its remote switch
permits. Full contains optional numeric usage and stability aggregates.

Consent version remains 3 for refinements of already authorized numeric categories.
A new installation defaults Full on in the wizard but cannot start Full before
setup completion and successful persistence. Historical allowed, denied and unknown
choices are preserved. Settings toggles apply without a second confirmation dialog.
An existing consent authority always wins; absent authority may be restored from
strictly validated preserved user settings. Invalid data never grants permission.
New data categories still require renewed authorization.

HTTP transport accepts only an explicitly selected HTTPS origin and the fixed
API paths, including /v1/telemetry/basic and /v1/telemetry/sync. Production remains https://api.voxgo.cn. All redirects, including same
origin, are refused. There is no user-controlled URL in remote configuration.

Retry classification:
- 200: configuration must validate; upload must exactly match success=true,
  revision and snapshot_id. Invalid JSON/ack retains pending state and backs off.
- POST 400: terminal for this pending revision. Remove only pending marker, never
  daily totals or source watermarks. GET 400: configuration failure, retry later.
- 403: preserve pending; retry no sooner than six hours, no bypass of challenges.
- 429: preserve pending; respect Retry-After seconds or HTTP date (cap 24 hours).
- 5xx/network/TLS/DNS/invalid response/other statuses: retain pending and retry with
  persisted exponential delay 15m,30m,1h,... capped at24h plus up to60s jitter.
- No busy-loop retry and no reset by application restart. Success resets failures.

Aggregate totals/watermarks and pending outbox are distinct fields in the same
atomic state file. Exact ACK only clears pending. Baselines expire under the
seven-day window rather than being deleted after each successful upload.

Live remote switches are deployment configuration, not constants established by
these local tests. Keep cloud acceptance isolated; local test results do not prove
production HTTP or D1 behavior.

## Upgrade preservation

The new updater preserves user_settings.json, telemetry_consent.json, analytics,
analytics-remote and analytics-basic. The 0.5.0 updater can lose old remote state;
only preserved settings authorization is recovered, without scanning rollback
backups. An installation / baseline / outbox discontinuity on that one upgrade is
accepted. Basic seed and immutable first-run date live in user_settings.json.
Atomic replacement and a bounded cross-process lock prevent simultaneous identity
creation. Persistence failures do not enable uploads with an unpersisted identity.
A failed explicit consent save is surfaced to the user and remains retryable.
