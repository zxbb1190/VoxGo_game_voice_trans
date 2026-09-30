# VoxGo ASR Benchmark

This local benchmark compares the same labelled English clip in three paths:

- `whole`: one transcription of the full decoded clip.
- `capture_cut`: replay 16 kHz mono PCM in VoxGo's current `AudioConfig` blocks through `SystemAudioCapture`'s VAD and cut logic, then transcribe each emitted segment and join the text.
- `full_pipeline`: replay audio blocks at wall-clock speed through `SystemAudioCapture` and VoxGo's actual `SpeechPipeline` worker thread, including candidate classification/merge, queue admission, Whisper, and output filters. This captures queue contention within an isolated clip, though it cannot reproduce an entire game session.

The default matrix evaluates `base.en` and `small.en` with `fast` / `balanced`, Prompt `off` / `game_en`, and clean / noisy audio through all three paths. `game_en` is a short English gaming term list; a sentence-style initial Prompt caused `small.en` to repeat the Prompt itself in some cut segments during a synthetic smoke test. The app's existing `game` profile also selects the English term list whenever the effective Whisper model ends in `.en`. Reports are written to `diagnostics/asr-benchmark/report.html` and `report.json`. The output directory and prepared corpus directory are ignored by Git.

For the current natural-speech diagnostic we use the official [OpenSLR SLR12 LibriSpeech test-clean](https://www.openslr.org/12/) release (CC BY 4.0). The official `test-clean.tar.gz` MD5 is `32fa31d27d2e1cad72775fee3f4849a9`. It is human-read English from audiobooks, not spontaneous gamer conversation; speaker accents are not labelled. Keep its scores separate from SAPI game phrases and treat a game-callout hit rate on this corpus as not applicable.

```powershell
.\.venv-win\Scripts\python.exe -m scripts.prepare_asr_benchmark --librispeech data\asr_benchmark\corpora\test-clean.tar.gz --limit 120 --seed 20260930 --noise-source natural --noise-wav diagnostics\asr-benchmark\synthetic-noise.wav --noise-license "locally generated synthetic noise" --snr-db 20 --snr-db 0 --output data\asr_benchmark\librispeech_manifest.jsonl
```

This selects 120 utterances across 40 speakers (30 short, 60 ordinary, 30 longer by reference word count) and produces 360 clean/20 dB/0 dB entries. The 20 dB and 0 dB cases reuse the existing noise mixer. The local synthetic noise is a controlled stressor, not an actual game soundtrack or Discord session. Do not publish the raw audio or treat speaker count as accent coverage.

## Prepare labelled samples

Download [Common Voice Spontaneous Speech 5.0 English](https://mozilladatacollective.com/datasets/cmu5nqn1h00vwmi07b4dbk085) from Mozilla Data Collective, then use its archive or extracted directory. Mozilla lists this release as CC0-1.0; the dataset is about 519 MB. Its download may require a Mozilla Data Collective account. The script samples up to 200 validated clips from the held-out `test` split by default (the release lists 357 such clips); use `--seed`, `--limit`, and `--cv-split` to control selection. Keep downloaded corpus audio local; Mozilla's dataset terms forbid re-hosting or re-sharing it.

```powershell
.\.venv-win\Scripts\python.exe -m scripts.prepare_asr_benchmark --common-voice C:\path\to\common-voice-english.tar.gz
```

For noise experiments, supply local noise audio downloaded under its own license. [MUSAN](https://www.openslr.org/17/) is CC BY 4.0, but its full archive is about 11 GB; the tool does not download it. CHiME access and terms differ by release, so use only a dataset you obtained under its applicable terms. Mix the selected Common Voice clips with noise at specified SNRs:

```powershell
.\.venv-win\Scripts\python.exe -m scripts.prepare_asr_benchmark --common-voice C:\path\to\common-voice-english.tar.gz --noise-wav C:\path\to\noise.wav --noise-license "CC BY 4.0 (MUSAN)" --noise-source natural --snr-db 20 --snr-db 10 --snr-db 0
```

The balanced synthetic set in `data/asr_balanced_phrases.tsv` contains exactly 100 distinct texts: 30 normal short sentences, 30 game callouts, 20 longer utterances, and 20 number / direction / place sentences. On Windows, generate one clean clip per sentence with an installed SAPI voice (repeat `--tts-voice` for multiple voices):

```powershell
.\.venv-win\Scripts\python.exe -m scripts.prepare_asr_benchmark --tts-tsv data\asr_balanced_phrases.tsv --tts-voice Zira --output data\asr_benchmark\balanced_clean.jsonl
```

To add light (20 dB) and heavy (0 dB) noise to each of those clips, supply a noise recording with its source and license:

```powershell
.\.venv-win\Scripts\python.exe -m scripts.prepare_asr_benchmark --tts-tsv data\asr_balanced_phrases.tsv --tts-voice Zira --noise-source synthetic --noise-wav C:\path\to\noise.wav --noise-license "source and license" --snr-db 20 --snr-db 0 --output data\asr_benchmark\balanced_manifest.jsonl
```

This produces 300 manifest entries from 100 underlying sentences. The original 112 game texts in `data/asr_game_phrases.txt` remain available through `--game-tts`:

```powershell
.\.venv-win\Scripts\python.exe -m scripts.prepare_asr_benchmark --game-tts --tts-voice Zira
```

Synthetic output is marked in the manifest; it does not measure real accents. You can also import audio recorded by the user or generated elsewhere using a tab-separated file with `audio` and `reference` columns via `--game-tsv`. Add `--noise-wav` to mix those game clips with local background audio. No player or teammate audio is collected by this tool.

In the original 100-clip SAPI clean-audio run, `game_en` caused rare long repetitions after `capture_cut`. The reentry fix and runaway guard should be evaluated against that historical report. Keep Prompt `off` as the default until natural speech and real game-noise cases show a consistent benefit. The HTML report exposes the affected transcripts; the JSON keeps them in full.

## Run the benchmark

```powershell
.\.venv-win\Scripts\python.exe -m scripts.run_asr_benchmark --manifest data/asr_benchmark/balanced_manifest.jsonl --device auto --resume
```

Model downloads are disabled by default. Missing models are listed as failures in the report. Add `--allow-download` to fetch missing models. For a quick check, add `--limit 5 --presets fast --prompts off`. The full 300-clip default matrix produces 7,200 scored rows and can take a long time on CPU. Each preset loads its own model instance: `fast` follows the app's standard low-impact policy (CPU/int8, one CPU thread), while `balanced` uses the requested `--device` / `--compute-type` and two CPU threads. The report records the actual runtime device, compute type, and thread count, and separates them if a device fallback occurs. Every 20 successful results are saved to JSON; `--resume` reuses them only when selected case IDs, audio content, benchmark implementation, model files, and matrix settings match. HTML is written when the run finishes. `medium.en` and `accurate` remain opt-in via `--models` and `--presets`.

A run exits with a nonzero status if any clip or model fails. Treat such a report as incomplete: its per-group sample counts may differ, so do not use its WER rows to rank configurations. Check the failure list and rerun after resolving the underlying issue. Use `--paths` to select a subset of `whole capture_cut full_pipeline`; the default includes all three.

The benchmark times ASR inference calls only. It excludes model loading, decoding, cutting, translation, UI, and network work. `full_pipeline` starts the real speech worker and replays blocks in real time, so its text includes queue-pressure and worker scheduling effects within each clip. The reported inference latency does not include capture, candidate waiting, queue waiting, or display time. Each clip starts a fresh noise calibration and `SpeechPipeline`, unlike a continuous game session. Use this comparison to locate likely cut/filter regressions, then verify a promising configuration in the live app.

The JSON report records model, actual runtime device and compute type, per-case transcript, word error counts, segment count, and failures. Current WER ignores case/punctuation; normalized WER additionally removes apostrophes and expands integer digits below 1,000 into English words. The normalized metric matches the earlier report's WER definition. Compare rows on the same corpus and actual device. Empty output counts as deletions rather than disappearing from the denominator. Use actual player speech and game noise before changing defaults.

Each scored row now keeps both the delivered `hypothesis` and Whisper's `raw_hypothesis`. The runtime guard can blank a segment that contains extreme repeated text; `runaway_guarded` records that action, and the raw text remains local for diagnosis. The report separately counts repeated output in delivered and raw text, plus raw output above `max(reference_words * 4, reference_words + 20)`. The length ratio is recognized words divided by reference words. Summary rows also include P50/P95 inference time and average segment count/duration. Per-segment diagnostics record cumulative emitted-audio timing, RMS, VAD/energy ratios when capture supplied them, Prompt, Whisper settings, text, compression ratio, log probability, no-speech probability, and call latency. `capture_cut` timing is **not** an exact offset in the source file: capture may omit leading unvoiced blocks or use pre-roll. Ordinary application logs do not print these full diagnostic transcripts.
