# Development checks

Use Python 3.10 on Windows and the application dependencies. Test tools are
separate from the shipped runtime:

```powershell
.\.venv-win\Scripts\python.exe -m pip install -r requirements.txt -r requirements-test.txt
.\.venv-win\Scripts\python.exe -m ruff check voxgo main.py tests scripts diagnostics hooks
.\.venv-win\Scripts\python.exe -m coverage run -m unittest discover -s tests -v
.\.venv-win\Scripts\python.exe -m coverage report
.\.venv-win\Scripts\python.exe scripts/index_test_evidence.py --check
```

`pyproject.toml` enables branch measurement and a 74% combined statement/branch
coverage floor. Third-party OpenCC code is excluded. Test count and coverage do
not establish real audio/model accuracy or packaged GPU acceptance.

The [Code Quality workflow](../../.github/workflows/quality.yml) runs on branch
pushes, pull requests, manual dispatch and daily at 20:00 UTC. It checks syntax, unused/undefined
Python names, regression tests and coverage. Logs and coverage JSON are retained
as Actions artifacts for 14 days. The separate release workflow builds and
publishes only on its existing release triggers.

## Local Worker contracts

Two tests need the private `zxbb1190/voxgo-api` source and Node 22 or later. They
execute the real Worker against in-memory SQLite, without deployment or network
requests to a service:

```powershell
$env:VOXGO_API_ROOT = 'E:\my\my\voxgo-api'
.\.venv-win\Scripts\python.exe -m unittest tests.test_telemetry_api_contract tests.test_language_usage_api_contract -v
```

On CI, optionally configure repository variable `VOXGO_API_CONTRACTS=true`,
read-only secret `VOXGO_API_READ_TOKEN`, and `VOXGO_API_REF` (defaults to `main`).
The checkout is allowed only on the default branch, never pull requests. When
not configured, the workflow explicitly reports the two skipped contracts;
client regression tests still run. Record both repositories' SHAs for acceptance.

## Focused runtime regressions

- [First subtitle and application capture acceptance](first-success-2026-11-11.md):
  live setup checks, per-application audio isolation, once-only community invitation,
  native audio/model/Qt acceptance and validation limits.

- `test_mobile_runtime.py`: actual loopback HTTP/static assets, WebSocket ping,
  two-client broadcast, reconnect, shutdown, occupied-port rejection and membership races.
- `test_update_runtime.py`: real worker scheduling, manual/automatic rules,
  request deduplication, immutable settings snapshots and late shutdown results.
- `test_windows_online_acceptance.py`: header-gate status/body checks and full-body
  rejection evidence. A connection reset alone never counts as a successful gate.
- `test_telemetry_migration.py`: durable identity, concurrency, failed persistence,
  consent revocation and keeping cold locale discovery outside the settings lock.

## Output guard audio regressions

`tests/test_output_guard_regressions.py` runs in the regular quality workflow.
It replays captured decoder output through the actual guard, verifies fixture
hashes, protects readable text and short callouts, and checks failure accounting
and the Qt/mobile delivery boundary. Decoder replay is explicitly separate from
fresh model inference.

For fresh inference with already cached Whisper base and OPUS-MT models:

```powershell
.\.venv-win\Scripts\python.exe scripts/check_output_guard_audio.py --output diagnostics/asr-benchmark/output-guard/audio-regressions.json
```

This command denies external connections and does not download models. It runs
the real recognizer and post-ASR pipeline on the recorded anomalous game excerpt,
quiet normal speech, an attenuated excerpt, and three synthetic callouts at two
volumes. It also feeds the original anomalous transcript directly into the real
offline translator to verify the independent invalid-output guard. A missing
model or failed assertion is a failed run, never a skip or fabricated pass.

The manifest at `tests/assets/output_guard/captured.json` records hashes, offsets,
gain, decoder output and provenance. The game audio reuses the existing
`pubg_voice_30s.m4a`; its ASR text is a captured baseline, not a human reference.
The three WAVs were generated locally with Windows SAPI Microsoft Zira Desktop
and are explicitly synthetic. Passing tests prove preservation/rejection for
these samples, not speech accuracy, physical capture or live VAD performance.

## Historical records

[Evidence index](evidence/README.md) lists immutable batches, sizes and tree hashes.
Original snapshots stay at their published paths. Dated plans and acceptance
reports describe that run only; [the release procedure](../release_process.md)
is the maintained process. Do not infer today's release status from archived logs.
