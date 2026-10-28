# Internal source ASR policies — 2026-10-28

Branch `codex/multilingual-online-053`, clean base `f2b9c741`.

The user selected an internal per-source combination with no strategy UI. “汉语” was interpreted as “韩语” from the preceding discussion of Korean performance; both Chinese and English remain unchanged. This supersedes the previous all-compatibility configuration in `released-speech-compatibility-2026-10-28.md`.

| Source | Internal policy | Existing Fast / CPU low-impact fixture |
| --- | --- | --- |
| zh / en | Existing formal behavior | Unchanged; existing English-only option retains its conditions |
| ja | `legacy` | base, 1 thread, beam 1; 3s / 300ms pre-roll / 350ms idle |
| ko | `legacy` | base, 1 thread, beam 1; no automatic candidate-small upgrade |
| ru | Existing `language_aware` | base, 2 threads, beam 1; 4.5s / 450ms pre-roll / 450ms idle |

These are the actual default fixture settings, not forced replacements for every user's model choice. Russian overrides retain the existing applicability rules: supported online direction, Google/OpenAI-compatible, Fast, non-Ultra-Low impact. Balanced/Accurate/Custom, explicit model selections, existing `.en` capability checks and GPU rules retain their prior behavior. No new ASR numbers, filters, normalization or Prompt were introduced.

## Implementation

`voxgo/asr/language_profiles.py::SOURCE_SPEECH_STRATEGIES` fixes JA/KO/RU to legacy/legacy/language_aware. `effective_speech_config` resolves this internal map independently of the retired shared setting. Effective copies carry the real strategy and existing `ru_speech_v1` / Custom diagnostic metadata, without changing the persisted config. Translation target does not select the source ASR policy.

The old shared field still reads/saves as `legacy` for compatibility and rollback; it cannot enable JA/KO candidates or disable the internal RU choice. Settings has no checkbox. Historical tools explicitly using `experimental=True` continue to reproduce their selected old strategies without consulting the new product map.

`audio_runtime_signature` and the app's existing runtime view resolve the same map. Switching into Russian changes capture/Whisper snapshots; switching back restores the compatibility settings and existing queue/revision isolation. The 63-field telemetry contract is unchanged: RU overrides use the already established Custom classification rather than relabeling them as the original Fast preset.

## Verification

Evidence: `docs/testing/evidence/v0.5.3-source-asr-policy-2026-10-28/`.

- **662 client tests passed**, 56.338s. Covers all 20 directions × four modes × legacy/candidate/unknown old values; RU provider/impact/GPU gates; omitted/old config save/restart; inference snapshots; EN→KO→RU→EN capture/config restoration and revision changes; existing no-checkbox checks in all five UI languages.
- **48/48 EN/ZH configurations equal** to `afc33a67`, comparing actual model/decoding/audio/Pipeline policies. This is compatibility evidence, not new recognition-quality measurement.
- Existing release preflight passed. Its guard still requires the retired shared field to default to legacy; it does not allow new EN/ZH defaults or formal preset changes.
- `runtime-matrix.json` stores actual default runtime snapshots for all 20 online directions. No models were loaded or downloaded, no audio replay or real API request occurred, and no Full EXE was built or reaccepted this round.
- Protected translation, filtering, capture presets, telemetry, UI and Chinese-display paths, original user settings and prior request ledgers were checked unchanged; see `safety-check.json`.

Commands:

```powershell
$env:QT_QPA_PLATFORM='offscreen'; $env:VOXGO_API_ROOT='E:/my/my/voxgo-api'
.venv-win/Scripts/python.exe -B -X utf8 -m unittest discover -s tests -q
.venv-win/Scripts/python.exe -B -X utf8 scripts/verify_english_chinese_compatibility.py --base-ref afc33a67 --output build/source-policy-enzh-20261028.json
.venv-win/Scripts/python.exe -B -X utf8 scripts/release_preflight.py --version 0.5.3 --base-ref afc33a67
```

This applies an already measured Russian profile; it adds no human/game quality evidence and does not turn the earlier averages into a release-quality guarantee. The next formal package must include this source revision; old EXEs are unchanged. No production operation, push, tag or release was performed. Rollback is a scoped revert of this commit, restoring `f2b9c741`'s all-compatibility product policy with the UI switch still absent.
