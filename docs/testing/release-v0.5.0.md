# v0.5.0 release preflight

Date: 2026-09-21. This record supersedes the production-disabled observations in
`local-preview-20260921.md`, which describe an earlier preview stage.

- Windows Python full suite: 323 tests passed, including real PowerShell update
  replacement, user-data preservation, invalid executable rollback and cache-link cases.
- Python compileall and git diff --check passed.
- Fresh Lite PyInstaller EXE started independently, displayed the main overlay,
  and exited with code 0 after WM_CLOSE using the remembered quit action.
- Real Windows Qt tray: nonempty icon, visible, valid system geometry, production
  menu popup and hide passed. Business callbacks were stubbed; Qt/tray were real.
- Production HTTPTransport GET /v1/config returned Cloudflare HTTP 200 and
  telemetry_enabled=true three consecutive times. Earlier intermittent routing to
  the old provider is not proven permanently resolved by this sample.
- POST remains 15 seconds, GET 5 seconds; default urllib proxy discovery,
  exact ACK matching, backoff and outbox rules are unchanged.
- Release notes and manifest PowerShell blocks parse; the manifest block ran in
  an isolated fixture and preserved five Chinese/English notes and v0.5.0 URLs.
  The two Unicode release steps now use pwsh to avoid the Windows PowerShell
  encoding failure seen in the prior v0.4.2 workflow.

The tag workflow builds and publishes all four packages. Final release asset,
SHA256, live manifest and website deployment checks occur after that workflow.
No runtime diagnostic snapshots or test-installation state belong in this commit.
