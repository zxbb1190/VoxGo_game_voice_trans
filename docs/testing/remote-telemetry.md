# Remote telemetry v1 (0.4.3)

Current backend: Cloudflare Worker + D1, origin https://api.voxgo.cn.
Local implementation tests do not substitute for staging HTTP/D1 acceptance.

## Cloudflare client hardening (2026-09-21)

Consent version remains 2: the receiving HTTPS origin, numeric fields and purpose
are unchanged. Provider/retention disclosure now names Cloudflare and hourly cleanup;
a provider move alone does not force renewed consent. Material scope changes must
be reviewed separately. No lifecycle behavior is changed.

HTTP transport accepts only an explicitly selected HTTPS origin and the two fixed
API paths. Production remains https://api.voxgo.cn. All redirects, including same
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

Production TELEMETRY_ENABLED remains false. No real or synthetic production
telemetry requests are permitted for acceptance. Staging HTTP writes are pending
creation of the isolated environment below; local test results are not cloud proof.
