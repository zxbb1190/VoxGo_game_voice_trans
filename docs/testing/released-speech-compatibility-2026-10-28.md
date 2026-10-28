# Released ASR policy: compatibility, no candidate switch

2026-10-28 · `codex/multilingual-online-053` · base `05beab2b`, clean.

The user approved removing the candidate speech-completeness switch and using the compatibility policy internally. This supersedes the earlier recommendation to expose experimental JA/KO/RU policy choices. It is a release-configuration decision, not new evidence of recognition quality or release approval.

## Behavior and implementation

- `voxgo/ui/settings_dialog.py`: removed the checkbox, tooltip, visibility handling and toggle callback. Collecting Settings selects `legacy`. The five-language message catalog no longer contains either candidate notice.
- `voxgo/asr/whisper_engine.py` and `voxgo/ui/config_models.py`: the retained compatibility field defaults to `legacy`.
- `voxgo/config/loader.py`: omitted fields use the new default; explicit old candidate/unknown fields are read as `legacy`. Saving explicitly persists `legacy`, avoiding the previous omitted-field ambiguity and keeping rollback readable by older clients. Other tuning and source/target choices are preserved. This change does not directly edit existing user files; the application retains its existing normal save/migration behavior.
- `voxgo/asr/language_profiles.py::effective_speech_config`: normal client calls always retain the selected compatibility configuration, even if an old in-memory object contains `language_aware`. Therefore a hidden field cannot silently keep the old candidate overrides active.
- `voxgo/runtime/settings_controller.py`: Settings application fixes this field to `legacy`; switching languages cannot re-enable the candidate. Cached fallbacks in the app/controller agree with the new default.
- Historical experimental profiles remain reproducible through an explicit, code-only `experimental=True` argument in six research scripts. This argument is absent from all `voxgo/` call sites and is not a persisted config/UI option. Existing experiment evidence is unchanged; no experiment or online batch was run.
- `scripts/release_preflight.py`: the narrow added-field guard now requires `legacy`; a test proves `language_aware` is rejected. Existing EN/ZH tuning guards remain intact.

Fast/Balanced/Accurate definitions, explicit custom tuning, ASR filtering/Prompt, translation/OPUS rules, the 20 online routes and the 63-field telemetry protocol are unchanged. The preceding Simplified Chinese source display and five interface languages are preserved. Compatibility does not force every user to base: existing performance modes and explicit model choices retain their established behavior; the candidate's automatic Korean-small override is inactive.

## Verification

Evidence: `docs/testing/evidence/v0.5.3-released-speech-compatibility-2026-10-28/`.

- Client suite: **660 tests passed**, 55.925 seconds, including all 20 routes, four modes and three old in-memory policy values; isolated missing/legacy/candidate/unknown file load, save and restart; bundled config; candidate-default rejection; all five interface languages × five source choices without the checkbox.
- Existing Settings language-switch test confirms Korean uses compatibility `base` in the normal Fast fixture and returning to English restores its original model/thread configuration and event revision handling. Historical candidate tests use explicit research opt-in and still pass.
- EN/ZH comparison: **48/48 equal** to `afc33a67` for actual configuration/model/decoding/Pipeline scheduling. This is compatibility evidence, not a new acoustic quality experiment.
- Release preflight passed with published update manifest still at 0.5.2.
- Native Windows source `SettingsDialog` launched with a fresh Korean→Japanese fixture, showed no candidate switch, collected an old candidate value as `legacy` and closed normally. Screenshot/JSON retained. This is a source GUI check, **not Full EXE acceptance**. No package was built or overwritten.
- No real translation API requests, model downloads or production operations. Original settings and protected paths/ledgers checked unchanged; see `safety-check.json`.

Commands from the isolated worktree:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
$env:VOXGO_API_ROOT='E:/my/my/voxgo-api'
.venv-win/Scripts/python.exe -B -X utf8 -m unittest discover -s tests -q
.venv-win/Scripts/python.exe -B -X utf8 scripts/verify_english_chinese_compatibility.py --base-ref afc33a67 --output build/release-speech-policy-enzh.json
.venv-win/Scripts/python.exe -B -X utf8 scripts/release_preflight.py --version 0.5.3 --base-ref afc33a67
```

The next formal package must be built from this change and checked before distribution; currently installed or previously built EXEs are untouched. Bilingual human, real-game/FPS, low-end hardware and production Worker/D1 release conditions remain separate outstanding acceptance items. No push/tag/release was performed.

Rollback: revert only this scoped local commit to restore the prior switch/default; do not revert the previous UI, routing, truncation/cancellation or Chinese display fixes. Old clients understand the explicit `legacy` value saved by this version.
