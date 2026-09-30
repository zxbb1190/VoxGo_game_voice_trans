# VoxGo v0.5.2 Release Candidate acceptance

Date: 2026-09-30. Client baseline: GitHub `main`
`22a608a3b49b1eb6620f5dcbedee2d23fa78762e` (verified with `git ls-remote`).
Scope: production ASR stability fixes, numeric daily diagnostics and community
links. No new ASR experiment or model strategy is adopted.

## Git and delivery status

The five existing local commits are preserved, in order:

| Commit | Scope |
| --- | --- |
| `0752e6d3` | Production speech reentry fix, runaway guard/output safeguards, corresponding tests and initial benchmark. |
| `a5f75e70` | Natural speech and real full-pipeline benchmark tooling. |
| `e7a17fdd` | Three-path evaluation findings. |
| `d7bf012a` | Failed-case diagnostics and bounded A/B tools/findings. |
| `6d62b1ab` | Ignore local ASR chain experiment outputs. |

This round adds a separate client RC commit. Its exact hash is returned in the
completion message and can be read with `git log --oneline origin/main..HEAD`.
The previous ASR fixes and benchmark history have not been rewritten.

The API working tree already contained uncommitted Telemetry v2, Dashboard and
authentication work before this round. Its ASR extension is tested in that working
tree and remains **uncommitted**, preserving those existing changes. Do not treat
the API repository's committed HEAD as containing the extension. Review and commit
that API working tree before deploying it.

No client source/tag has been pushed, no GitHub Release has been created, and no
production Worker deployment or D1 mutation has been performed. Website download
links and `docs/update.json` still describe published v0.5.1.

## Production behavior

- `SystemAudioCapture` cuts an old utterance before admitting a renewed onset
  after inactive windows, preserving PCM and applying the correct mode pause
  threshold. The app's real capture callback reaches `SpeechPipeline`.
- The real Whisper array transcription path blocks extreme repetition. Guard
  exceptions preserve the model result. The Pipeline rejects guarded results with
  the dedicated reason and records the numeric counter.
- Normal brief repeated callouts such as `go go go` and `push push push` survive.
  The callout exemption now retains existing cross-segment deduplication and
  language-confidence checks. It does not turn off other false-positive filters.
- Eight fixed numeric ASR metrics use the existing Daily Snapshot and Full consent
  path. Full off creates no remote ASR collector/uploader. Basic has no ASR fields.
  See [counter definitions](asr-diagnostics-v0.5.2.md).
- Existing Help & Feedback links use `https://kook.vip/hr0hMS` and the project-confirmed
  `https://discord.gg/mtnFmUJJ4y`. Chinese puts KOOK first; English puts Discord first;
  GitHub Issues remains. Both invitation URLs returned HTTP 200; Discord identified
  the VoxGo community. Joining/authenticated browser behavior is not part of this check.
- A packaging smoke check exposed Python 3.10 argparse writing to absent console
  streams on `--help`. A small windowed parser safeguard preserves normal argument
  defaults and allows clean help exit. This is an additional startup safeguard.

## Experiment pollution audit

| Item | Result against baseline |
| --- | --- |
| `config.example.json`, config loader/schema and requirements | No change. |
| Fast model selection | Existing `base` / pure-English `base.en`; ultra-low strategy unchanged. |
| Non-Fast model selection | Existing configured `small` / pure-English `small.en`; no automatic GPU upgrade. |
| English-to-Chinese Fast max segment | Still 2.5 s. |
| English-to-Chinese Balanced max segment | Still 4.0 s. |
| General Fast/Balanced presets | Existing 3.0 / 4.5 s remain unchanged. These predate the A/B experiment. |
| Candidate wait, cooldown, queue policy and CPU strategy | No experimental values adopted. |
| Prompt | Default `none`, empty initial prompt, previous-text conditioning false. |
| English game prompt | Existing conditional English term list when the effective model ends in `.en` and the user selects `game`; defaults unchanged. |
| Benchmark execution | Explicit scripts/CLI options; ordinary startup does not run them. |
| Packaging dependencies | No requirement added; scripts/tests/diagnostics excluded from import analysis. |
| User configuration | Local ignored files preserved; their last-write dates remain June 6 / September 12. |

The audit compares parsed Audio/Whisper/UI dataclass defaults and audio presets,
the baseline example config and requirements, packaging inputs and published
manifest. Source diff review also confirms the configuration loader and
`RecognitionModePolicy` have no experimental timing/thread modifications.

## Validation

| Gate | Evidence |
| --- | --- |
| Full Windows client unit suite | 479 passed, 0 failed; includes ASR, telemetry, updater and translation tests. |
| ASR production regressions | Reentry PCM conservation/callback-once/mode pause thresholds, repetition guard, normal callouts, output dedup and guard/diagnostic failure isolation passed. |
| Telemetry compatibility/privacy | Old 27-field pending hash/revision/identity retained; new 35-field snapshot; no remote collector with Full denied; atomic segment daily update passed. |
| API tests | 51 passed; old v1 and 27-field v2, complete 35-field v2, unknown/partial fields, counters and dashboard covered. |
| Python-to-JS contract | Snapshot generated with current DailyMetrics + AggregateStore validated by current API validator with 35 metrics. |
| Fresh local D1 | Migrations 0001–0005 applied to an isolated local database; eight ASR columns verified. |
| API build/deploy dry run | Build, Dashboard inline JS syntax and Wrangler dry run passed. No remote operation. |
| Release preflight | `--version 0.5.2 --base-ref origin/main` passed; six focused preflight regressions passed in full suite. |
| Python/source hygiene | `compileall -q voxgo tests scripts main.py` and `git diff --check` passed. |
| Updater preservation | Real Windows replacement/rollback transaction tests preserve config, model caches, CUDA runtime and Telemetry consent/state. |
| Local packaging | Lite, Full, Full-CUDA and CUDA-runtime archives built successfully. All three windowed EXEs exit 0 for `--help`. |

Logs are local under ignored `build/rc-0.5.2-final-tests.log` and
`build/rc-0.5.2-final-build.log`. This does not imply GUI tray review, an actual
in-place upgrade of a user's installed 0.5.1, GPU inference/performance measurement,
or real-player accuracy validation. The updater preservation gate is an automated
real Windows transaction test; package launch gates exercise imports and argument
parsing without starting telemetry, capture, translation or downloads.

### Final local artifacts

These are local RC builds, not GitHub or GitCode release artifacts. Archive
inspection verifies package edition, unchanged safe example configuration,
expected model/DLL presence and absence of benchmark/user/telemetry data. The
embedded Python archive contains the real Pipeline, runaway guard and daily
collector and excludes test/script modules.

| ZIP under `release/` | Bytes | SHA256 |
| --- | ---: | --- |
| `VoxGo-v0.5.2-lite.zip` | 140491851 | `7b931441fb8cabe75faccb405440a033667e311ff791b537bc8a707a7a879ea9` |
| `VoxGo-v0.5.2-full.zip` | 719529602 | `c6f06546c768d72180ba6e829d7f670413fa17a30cc30cf03bf2aeef617208f3` |
| `VoxGo-v0.5.2-full-cuda.zip` | 1312952445 | `3d699a06c7cbbab4c8a8b52a89e1e294f1c58ba6b2d9efda95f8662fec181c08` |
| `VoxGo-v0.5.2-cuda-runtime.zip` | 593293891 | `875940c874e7c8ab7719d45df2c48fe16bdcd4a8b1eb5bb2b29405f61b528fc5` |

Existing local NVIDIA/ctranslate2 DLLs supplied the CUDA build. No new package was
installed. Successful packaging verifies inclusion; it is not a GPU inference test.

## Modified files this round

Client:

- Runtime: `voxgo/app.py`, `voxgo/asr/pipeline.py`, `voxgo/asr/whisper_engine.py`.
- Analytics: `voxgo/analytics/{daily_metrics,client,consent}.py`.
- Version/community: `voxgo/app_info.py`, `voxgo/ui/settings_dialog.py`.
- Packaging/release: `VoxGo.spec`, `installer/VoxGo.iss`,
  `scripts/build_portable.ps1`, `.github/workflows/publish-release.yml`.
- Checks: `scripts/release_preflight.py`, `tests/test_asr_diagnostics.py`,
  `tests/test_cli_args.py`, `tests/test_release_preflight.py`,
  `tests/test_analytics_aggregation.py`, `tests/test_feedback_links.py`.
- Documentation: `docs/releases/v0.5.2.md`, this record and ASR diagnostics notes.

API extension to its preexisting working tree:

- `lib/validation.js`, `lib/d1-store.js`, `lib/admin-stats.js`, `lib/dashboard-page.js`.
- `migrations/0005_asr_daily_counters.sql` (eight additive integer columns).
- `tests/{cloudflare,admin-stats,admin-routes,dashboard-auth}.test.js`.
- `docs/telemetry-v2.md`, `docs/admin-dashboard.md`, `README.md`.

Existing unrelated client untracked files, API authentication/configuration work,
prepared corpora and local reports are preserved. No test audio, report HTML/JSON,
personal settings or model cache is committed or included as benchmark package data.

## API deployment commands (not executed against production)

Run in `E:\my\my\voxgo-api` only after reviewing/committing its existing working
tree and confirming the target configuration. The schema ledger must match actual
columns before applying pending migrations; a partial/manual migration requires
reconciliation rather than blindly repeating ALTER statements.

```powershell
npm test
npm run build
npx wrangler d1 migrations list voxgo --remote
npx wrangler d1 execute voxgo --remote --command "PRAGMA table_info(telemetry_daily);"
npx wrangler d1 export voxgo --remote --output="$env:TEMP\voxgo-before-asr-0.5.2.sql"
npx wrangler d1 migrations apply voxgo --remote
npx wrangler d1 execute voxgo --remote --command "PRAGMA table_info(telemetry_daily);"
npx wrangler deploy --dry-run
npx wrangler deploy
```

Apply migration 0005 before deploying code that selects the new counters. Old
clients remain supported; omitted counters preserve stored values. Verify health,
old/new Full payload ACKs and Dashboard ASR aggregates before client distribution.
No consent/identity reset is needed. Keep current server telemetry switches.

## Client build and later release commands

Run in `E:\my\my\game_voice_translator`:

```powershell
.\.venv-win\Scripts\python.exe -m unittest discover -s tests -v
.\.venv-win\Scripts\python.exe -m compileall -q voxgo tests scripts main.py
.\.venv-win\Scripts\python.exe scripts\release_preflight.py --version 0.5.2 --base-ref origin/main
git diff --check
.\scripts\collect_cuda_runtime.ps1
.\scripts\build_portable.ps1 -Version "0.5.2"
```

Edition-only commands and bilingual release notes are in
[v0.5.2 release notes](../releases/v0.5.2.md). After explicit release approval and
compatible API deployment, the existing tag-triggered workflow is:

```powershell
git push origin main
git tag v0.5.2
git push origin v0.5.2
```

These commands publish; none was executed for this RC. The workflow builds/uploads
all editions before advancing manifests/download links. GitCode remains a release-only
Lite mirror using the verified GitHub artifact; client source is not pushed there.

## Acceptance boundary

Current source fixes and test/benchmark evidence are present locally. The client
RC is committed locally, and the API candidate is a tested uncommitted working
tree extension. Production API deployment and client publication remain pending.
v0.5.1 users have not received these source fixes. Real-player validation is not
claimed, and synthetic/natural corpus findings are not rewritten as live-user results.
