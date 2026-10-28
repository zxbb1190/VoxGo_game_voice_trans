# Chinese source transcript: Simplified display

2026-10-28 · branch `codex/multilingual-online-053` · implementation base `6bb4a98c` (clean).

## Scope and result

Chinese → English/Japanese/Korean/Russian now displays the recognized source transcript in Simplified Chinese. This is a UI conversion, using the transcript event's source-language snapshot; switching languages later cannot simplify Japanese kanji in another event. The mobile mirror follows the same display rule. It is independent of the software interface language.

`voxgo/app.py`: `_handle_transcript_ready` converts only the overlay argument. Pipeline memory, event text and `_start_async_translation` retain the original ASR text. `_handle_translation_ready` converts only the mobile display's original-text field; translated output is untouched. No ASR normalization, recognition correction, translation Prompt, OPUS rule, filtering or telemetry change. A damaged display resource preserves the original text and logs the exception class once, without text content.

`voxgo/ui/chinese_text.py`: lazy, bounded, thread-protected `t2s` conversion. `voxgo/ui/_opencc/` vendors the minimal pure-Python subset of opencc-python-reimplemented 0.1.7, with Apache-2.0 license, notice and byte-level provenance. Seven upstream files total 63,353 bytes. No pip requirement, native runtime or model download was added. `VoxGo.spec` explicitly includes dictionaries, configuration, license and provenance. This is character/script conversion, not regional vocabulary substitution or typo correction.

Source: [upstream project](https://github.com/yichen0831/opencc-python), [version distribution](https://pypi.org/project/opencc-python-reimplemented/0.1.7/). The wheel SHA256 is `41b3b92943c7bed291f448e9c7fad4b577c8c2eae30fcfe5a74edf8818493aa6`; individual retained file hashes are in `voxgo/ui/_opencc/UPSTREAM.json`. Only this 481,813-byte source distribution was downloaded; no translation service was called.

Examples checked:

| Raw recognition | Display |
| --- | --- |
| 這並不是告別。 | 这并不是告别。 |
| 這是一個偏章的結束，也是新偏章的開始。 | 这是一个偏章的结束，也是新偏章的开始。 |
| 後衛在後門，還有15秒，不要開槍。 | 后卫在后门，还有15秒，不要开枪。 |
| 乾隆與乾淨的頭髮 | 乾隆与干净的头发 |

The recognition typo `偏章` stays a typo. Japanese `後ろへ移動` stays unchanged. Numbers, negation, Unicode and actual target-language translations are preserved.

## Verification

Evidence: `docs/testing/evidence/v0.5.3-chinese-source-display-2026-10-28/`.

- Focused tests: 29/29, including six new tests for all four routes, mobile event snapshots, raw input preservation, non-Chinese isolation, failure behavior and vendored/package resource fingerprints.
- Entire client suite: 654/654, 56.474 seconds. Expected fixture warnings remain in the raw log.
- English/Chinese runtime compatibility: 48/48 equal to `afc33a67` (configuration, model selection, decoding and Pipeline policy; not a new recognition-quality experiment).
- Existing release preflight passed without weakening its dependency or formal-parameter guards.
- Native Windows Qt overlay: two fixture transcripts displayed Simplified Chinese while the queued translation argument remained Traditional; screenshot and verification JSON saved. Local marker output is explicitly not a real translation. No private audio or real API used.
- A minimal PyInstaller EXE successfully converted Chinese, preserved Japanese and validated every bundled dictionary/configuration/license hash while launched outside the source directory. It tests packaging of this component; it is **not a rebuilt or reaccepted Full EXE**.
- The initial cross-drive PyInstaller invocation failed before building. A second build succeeded but its test's JSON stdout failed on emoji under GBK. The third build used ASCII-escaped JSON and passed. All attempt logs are retained; no successful Full-package claim is based on those failures.

Relevant commands (from the isolated worktree; Python `.venv-win/Scripts/python.exe`):

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.venv-win/Scripts/python.exe -B -X utf8 -m unittest tests.test_chinese_display tests.test_ui_five_languages tests.test_beta_release_blockers tests.test_release_preflight -q
$env:VOXGO_API_ROOT='E:/my/my/voxgo-api'
.venv-win/Scripts/python.exe -B -X utf8 -m unittest discover -s tests -q
```

The frozen smoke source is retained as `frozen_smoke.py`; its build command/spec are in the evidence. EXE artifacts remain outside Git at `E:/my/my/VoxGo053ChineseDisplay-Smoke-20261028-v3/dist/ChineseDisplaySmoke/`. No Full EXE, published installation, models or original user settings were replaced.

## Boundaries and rollback

Protected runtime paths, original user-settings hash and prior 255/20/24-request ledgers were checked unchanged; see `safety-check.json`. Real API requests: **0**. No production migration, deployment, upload, push, tag or release.

Release quality status and outstanding human/game acceptance remain unchanged. The user's existing EXE will gain this display change only after a separately built candidate is installed. Rollback is the scoped local commit revert (two display call sites, helper/vendor, packaging resources, tests and documents); do not roll back earlier five-language UI/routing work.
