# VoxGo v0.5.2 Release Candidate acceptance

RC checks: 2026-09-30. Production acceptance update: 2026-10-06.
Client baseline: GitHub `main`
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

The separate client RC commit is `8adfdeca`.
The previous ASR fixes and benchmark history have not been rewritten.

The API production source is committed and pushed as
`ab8da2f85b1bfbc6d72a627f730de8fd89810cc7`. Production D1 migration 0005
and the compatible API deployment completed on 2026-09-30, after a production
backup. Old v1, old 27-field v2 and new 35-field v2 contracts are supported.
See the API repository's `docs/deployment-asr-2026-09-30.md` for deployment evidence.

The user authorized the client release flow on 2026-10-06. Client `main` and the
annotated `v0.5.2` tag are pushed. The tag resolves to
`7dc4eef6d40f5f70e2c8e25b7dbaaec4388290ab`. All four formal GitHub Release
assets are published; `docs/update.json` and website downloads now describe
v0.5.2. Final delivery verification is recorded below.

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

### Production acceptance on 2026-10-06

The final Windows suite was rerun: 479 tests passed in 33.332 seconds.
`compileall`, release preflight against the published baseline, and
`git diff --check` passed. The experiment pollution audit again confirmed
unchanged runtime defaults and no benchmark-only dependencies or package inputs.

The user launched the packaged v0.5.2 Full RC, enabled Full telemetry consent,
and confirmed that actual audio produced captions. The normal scheduled uploader
received HTTP 200 and acknowledged revision 32; pending was false and failures
were zero. The matching production D1 daily row was updated at
`2026-10-06T03:19:47.309Z`, with app version 0.5.2 and revision 32.
No forced sync or fabricated counters were used.

| ASR metric | Production value |
| --- | ---: |
| `asr_forced_max_duration_splits` | 6 |
| `asr_short_fragment_segments` | 4 |
| `asr_weak_candidate_drops` | 2 |
| `asr_post_filter_drops` | 15 |
| `asr_runaway_repetition_blocks` | 2 |
| `asr_segments` | 23 |
| `asr_segment_duration_sum_ms` | 42000 |
| `asr_segment_duration_samples` | 23 |

The production seven-day aggregate matched these counters. After the Dashboard
cache expired, the user confirmed authenticated Dashboard access and nonzero ASR
values. This verifies the packaged runtime-to-Dashboard telemetry path; it does
not measure recognition accuracy or validate real-player WER. Private telemetry
identities and local evidence files are excluded from this record and release.

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

API extension, subsequently committed and deployed:

- `lib/validation.js`, `lib/d1-store.js`, `lib/admin-stats.js`, `lib/dashboard-page.js`.
- `migrations/0005_asr_daily_counters.sql` (eight additive integer columns).
- `tests/{cloudflare,admin-stats,admin-routes,dashboard-auth}.test.js`.
- `docs/telemetry-v2.md`, `docs/admin-dashboard.md`, `README.md`.

Existing unrelated client untracked files, API authentication/configuration work,
prepared corpora and local reports are preserved. No test audio, report HTML/JSON,
personal settings or model cache is committed or included as benchmark package data.

## API deployment commands (completed on 2026-09-30)

These describe the completed deployment in `E:\my\my\voxgo-api`.
Do not reapply migration 0005 for the client release. The production ledger and
all eight columns were verified, and the production backup was retained privately.

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

## Client build and release commands (historical)

These document the release flow in `E:\my\my\game_voice_translator`.
The version is already published; do not recreate its tag or rebuild its assets
to replace the verified official downloads.

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

These commands publish; they follow the user's 2026-10-06 release authorization.
The workflow builds/uploads
all editions before advancing manifests/download links. GitCode remains a release-only
Lite mirror using the verified GitHub artifact; client source is not pushed there.

## Acceptance boundary

Current source fixes and test/benchmark evidence are committed and pushed. The
API is committed, pushed and deployed; D1 migration and actual RC telemetry
upload plus Dashboard rendering are verified. The v0.5.2 client is now published
and offered through the update manifest. Existing v0.5.1 installations receive
these client fixes when they upgrade; this record does not imply every user has
already upgraded. Real-player accuracy validation is not claimed, and
synthetic/natural corpus findings are not rewritten as live-user WER results.

## Published delivery verification (2026-10-06)

- [Formal GitHub Release](https://github.com/zxbb1190/VoxGo_game_voice_trans/releases/tag/v0.5.2)
  is stable, non-draft, and was published at `2026-10-06T04:55:16Z`.
- [Release workflow](https://github.com/zxbb1190/VoxGo_game_voice_trans/actions/runs/37415411674)
  succeeded. Cloud Windows validation passed 479 tests in 32.985 seconds.
  Local final validation passed the same 479 tests, compileall, release preflight
  and diff hygiene. Runtime model, Prompt, preset and CPU defaults are unchanged.
- All four assets were completely downloaded from their actual public GitHub
  URLs. Size, SHA256 against both Release notes and GitHub asset digest, ZIP CRC,
  edition, model/CUDA inclusion and safe package contents passed. No local
  telemetry, personal settings, audio or benchmark reports are bundled.
- The formal Lite EXE exits 0 for windowed `--help`. Its embedded archive contains
  v0.5.2 production capture, Pipeline, repetition guard and daily metrics, with
  benchmark/test modules excluded. This is a startup/package smoke check, not
  a new GUI, GPU inference or recognition-accuracy experiment.

| Formal GitHub asset | Bytes | SHA256 |
| --- | ---: | --- |
| `VoxGo-v0.5.2-lite.zip` | 137471214 | `3d173c6fa8c5e9287324105a5ede8c8f7bdc0928ef6723c3dd036f09c2e966c4` |
| `VoxGo-v0.5.2-full.zip` | 717268901 | `9404e1299c98106550528053c37be4073edc9d82ba79df55dcca905b37f4a11f` |
| `VoxGo-v0.5.2-full-cuda.zip` | 1307985196 | `50fb398241dda712bdceb8e40af7cdf62a0ae9d6890e698cc44e5af942f74ef3` |
| `VoxGo-v0.5.2-cuda-runtime.zip` | 590591465 | `6ba1c2d5a3896ca27c00318eff87dbeeab306ed791def9644f3aad04779f905f` |

The CI mirror step explicitly skipped synchronization because its
`GITCODE_TOKEN` Secret was absent. The documented local fallback subsequently
uploaded the exact formal GitHub Lite ZIP and verified a complete GET from the
[public domestic download URL](https://gitcode.com/zxbb1190/VoxGo/releases/download/v0.5.2/VoxGo-v0.5.2-lite.zip),
with the same 137471214 bytes and SHA256. GitCode source HEAD remained
`942a8df83f671e89a0b045a2cdd2b66fa33f4ddb`; no client source was pushed there.
The local token was ignored and untracked, and its temporary environment variable
was cleared. This successful fallback does not imply the CI Secret is configured.

Website commit `38e4f8a70b9cf0630f6b149a523e23f08892c635` adds the static
changelog generated from published bilingual Release notes and advances all four
Chinese/English domestic entrances. Its
[Pages deployment](https://github.com/zxbb1190/VoxGo_game_voice_trans/actions/runs/37416312423)
succeeded. Actual public GETs of `/`, `/en/`, `/update.json`, `/changelog/`,
`/changelog/v0.5.2/` and `/sitemap.xml` returned 200 and matched accepted source.
The live manifest's four GitHub URLs and SHA256 values match the formal assets;
Chinese and English notes are present. No API deploy or D1 change was performed
during this client release.

Local detailed validation outputs remain ignored under `build/` and
`release/official-v0.5.2/`; unrelated preexisting untracked files are preserved.
