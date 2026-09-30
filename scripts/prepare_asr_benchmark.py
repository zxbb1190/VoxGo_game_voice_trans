"""Prepare a local, reproducible JSONL manifest for ASR benchmarks.

No corpora are downloaded by this script. Common Voice archives must be
obtained by the user from Mozilla and may be passed directly or extracted.
"""
from __future__ import annotations

import argparse
import hashlib
import csv
import json
import math
import random
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import wave
import zipfile
from array import array
from pathlib import Path
from typing import Iterable

BALANCED_SUBSETS = {"normal", "game", "longer", "number_direction_place"}


def _safe_extract(archive: Path, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as zf:
            for member in zf.infolist():
                mode = member.external_attr >> 16
                if stat.S_ISLNK(mode):
                    raise ValueError(f"symbolic links are not supported in dataset archives: {member.filename}")
                target = (root / member.filename).resolve()
                if target != root and root not in target.parents:
                    raise ValueError(f"unsafe archive member: {member.filename}")
                if not member.is_dir():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(member) as src, target.open("wb") as dst:
                        shutil.copyfileobj(src, dst)
    elif tarfile.is_tarfile(archive):
        with tarfile.open(archive, "r:*") as tf:
            for member in tf.getmembers():
                if member.issym() or member.islnk():
                    raise ValueError(f"links are not supported in dataset archives: {member.name}")
                if not (member.isfile() or member.isdir()):
                    continue
                target = (root / member.name).resolve()
                if target != root and root not in target.parents:
                    raise ValueError(f"unsafe archive member: {member.name}")
                if member.isfile():
                    src = tf.extractfile(member)
                    if src is not None:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        with src, target.open("wb") as dst:
                            shutil.copyfileobj(src, dst)
    else:
        raise ValueError("Common Voice input must be an extracted directory, ZIP, or TAR archive")
    return destination


def _find_tsv(root: Path) -> Path:
    matches = sorted(root.rglob("*.tsv"))
    spontaneous = [p for p in matches if p.name.lower().startswith("ss-corpus-")]
    if spontaneous:
        return spontaneous[0]
    preferred = [p for p in matches if p.name.lower() in {"validated.tsv", "validated_spontaneous.tsv"}]
    if not preferred:
        preferred = [p for p in matches if "spontaneous" in p.name.lower()]
    if not preferred:
        raise FileNotFoundError("no Common Voice validated/spontaneous TSV found")
    return preferred[0]


def _common_voice_rows(root: Path, limit: int, seed: int, split: str = "test") -> list[dict]:
    tsv = _find_tsv(root)
    with tsv.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        has_split_column = "split" in (reader.fieldnames or [])
        rows = list(reader)
    usable = []
    for row in rows:
        # Spontaneous Speech v5 uses audio_file/transcription and an audios/
        # directory. Scripted Common Voice releases use path/sentence + clips/.
        sentence = (row.get("transcription") or row.get("sentence") or "").strip()
        clip = (row.get("audio_file") or row.get("path") or "").strip()
        if not sentence or not clip:
            continue
        if has_split_column:
            row_split = (row.get("split") or "").strip().lower()
            if row_split not in {"train", "dev", "test"} or (split != "all" and row_split != split):
                continue
        audio_dir = "audios" if row.get("audio_file") else "clips"
        audio = tsv.parent / audio_dir / clip
        if sentence and clip and audio.is_file():
            usable.append((clip, sentence, audio))
    usable.sort(key=lambda item: item[0])
    rng = random.Random(seed)
    if limit > 0 and len(usable) > limit:
        usable = sorted(rng.sample(usable, limit), key=lambda item: item[0])
    return [{"id": f"natural-{i:04d}", "category": "natural", "audio": str(audio.resolve()),
             "reference": sentence, "source": f"Mozilla Common Voice Spontaneous Speech:{tsv.name}",
             "license": "CC0-1.0"}
            for i, (_clip, sentence, audio) in enumerate(usable, 1)]


def _librispeech_rows(root: Path, limit: int, seed: int) -> list[dict]:
    """Select diverse speakers and utterance lengths from LibriSpeech test-clean."""
    transcripts = sorted(root.rglob("*.trans.txt"))
    if not transcripts:
        raise FileNotFoundError(f"no LibriSpeech transcript files under {root}")
    buckets = {"short": {}, "ordinary": {}, "longer": {}}
    for transcript in transcripts:
        if "test-clean" not in transcript.parts:
            continue
        for line in transcript.read_text(encoding="utf-8").splitlines():
            clip_id, separator, sentence = line.partition(" ")
            sentence = sentence.strip()
            if not separator or not sentence:
                continue
            audio = transcript.parent / f"{clip_id}.flac"
            if not audio.is_file():
                continue
            count = len(sentence.split())
            if count <= 8:
                subset = "short"
            elif count <= 18:
                subset = "ordinary"
            elif count <= 35:
                subset = "longer"
            else:
                continue
            speaker = clip_id.split("-", 1)[0]
            buckets[subset].setdefault(speaker, []).append((clip_id, sentence, audio))
    if not any(buckets.values()):
        raise ValueError("LibriSpeech input has no usable test-clean FLAC/transcript pairs")

    rng = random.Random(seed)
    for speakers in buckets.values():
        for clips in speakers.values():
            rng.shuffle(clips)
    selected = []
    target = limit if limit > 0 else sum(len(clips) for speakers in buckets.values()
                                          for clips in speakers.values())
    quotas = {"short": target // 4, "ordinary": target // 2,
              "longer": target - target // 4 - target // 2}
    for subset in ("short", "ordinary", "longer"):
        speakers = buckets[subset]
        order = sorted(speakers)
        rng.shuffle(order)
        while order and sum(row[0] == subset for row in selected) < quotas[subset]:
            next_order = []
            for speaker in order:
                if sum(row[0] == subset for row in selected) >= quotas[subset]:
                    break
                clips = speakers[speaker]
                if clips:
                    selected.append((subset, speaker, *clips.pop()))
                if clips:
                    next_order.append(speaker)
            order = next_order
    if len(selected) < target:
        remaining = [(subset, speaker, *clip)
                     for subset, speakers in buckets.items()
                     for speaker, clips in speakers.items() for clip in clips]
        rng.shuffle(remaining)
        selected.extend(remaining[:target - len(selected)])
    selected.sort(key=lambda row: row[2])
    return [{"id": f"librispeech-{clip_id}", "category": "natural", "subset": subset,
             "audio": str(audio.resolve()), "reference": sentence,
             "source": "OpenSLR SLR12 LibriSpeech test-clean", "license": "CC BY 4.0",
             "speaker_id": speaker}
            for subset, speaker, clip_id, sentence, audio in selected]


def import_game_tsv(tsv_path: Path) -> list[dict]:
    """Import user-recorded or locally generated audio; columns: audio, reference."""
    rows = []
    with tsv_path.open("r", encoding="utf-8-sig", newline="") as stream:
        for i, row in enumerate(csv.DictReader(stream, delimiter="\t"), 1):
            value = (row.get("audio") or row.get("path") or "").strip()
            reference = (row.get("reference") or row.get("sentence") or "").strip()
            if not value or not reference:
                continue
            audio = Path(value).expanduser()
            if not audio.is_absolute():
                audio = tsv_path.parent / audio
            if not audio.is_file():
                raise FileNotFoundError(f"game phrase audio not found: {audio}")
            record = {"id": f"game-{i:04d}", "category": "game", "audio": str(audio.resolve()),
                      "reference": reference, "source": (row.get("source") or "user-provided game phrase audio").strip()}
            if row.get("subset"):
                record["subset"] = row["subset"].strip()
            rows.append(record)
    return rows


def _ensure_unique_ids(rows: list[dict]) -> None:
    seen: set[str] = set()
    for row in rows:
        original = row["id"]
        candidate = original
        suffix = 2
        while candidate in seen:
            candidate = f"{original}-{suffix}"
            suffix += 1
        row["id"] = candidate
        seen.add(candidate)


def _read_phrase_lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8-sig").splitlines()
            if line.strip() and not line.lstrip().startswith("#")]


def _read_labelled_phrases(path: Path) -> list[dict[str, str]]:
    """Read phrase TSV with `subset` and `text` (or `reference`) columns."""
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    phrases = []
    for line, row in enumerate(rows, 2):
        subset = (row.get("subset") or "").strip()
        text = (row.get("text") or row.get("reference") or row.get("sentence") or "").strip()
        if not subset or not text:
            raise ValueError(f"labelled phrase TSV row {line} needs subset and text columns")
        if subset not in BALANCED_SUBSETS:
            raise ValueError(f"labelled phrase TSV row {line} has unsupported subset: {subset}")
        phrases.append({"subset": subset, "text": text})
    if not phrases:
        raise ValueError(f"no labelled phrases found in {path}")
    return phrases


def generate_sapi_tsv_audio(phrase_tsv: Path, output_dir: Path,
                            voice_filters: list[str] | None = None) -> list[dict]:
    """Generate labelled, explicitly synthetic samples with installed SAPI voices."""
    if sys.platform != "win32":
        raise ValueError("--tts-tsv requires Windows and an installed SAPI voice")
    powershell = shutil.which("powershell.exe") or shutil.which("powershell")
    if not powershell:
        raise ValueError("Windows PowerShell was not found")
    phrases = _read_labelled_phrases(phrase_tsv)
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="voxgo-sapi-") as tmp:
        temp = Path(tmp)
        phrases_path, voice_names_path = temp / "phrases.json", temp / "voices.json"
        result_path, script_path = temp / "generated.json", temp / "generate.ps1"
        phrases_path.write_text(json.dumps(phrases, ensure_ascii=False), encoding="utf-8")
        voice_names_path.write_text(json.dumps(voice_filters or [], ensure_ascii=False), encoding="utf-8")
        script_path.write_text(r'''param([string]$PhrasesPath, [string]$OutputDirectory, [string]$ResultPath, [string]$VoiceNamesPath)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Speech
$phrases = Get-Content -LiteralPath $PhrasesPath -Raw -Encoding UTF8 | ConvertFrom-Json
$filters = [string[]](Get-Content -LiteralPath $VoiceNamesPath -Raw -Encoding UTF8 | ConvertFrom-Json)
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$tokens = @($synth.GetInstalledVoices() | Where-Object { $_.Enabled })
if ($filters.Count -gt 0) { $tokens = @($tokens | Where-Object { $name = $_.VoiceInfo.Name; @($filters | Where-Object { $name -like "*$_*" }).Count -gt 0 }) }
if ($tokens.Count -eq 0) { throw ("No enabled SAPI voices matched: filters={0}" -f ($filters -join ',')) }
$items = New-Object System.Collections.Generic.List[object]
$voiceIndex = 0
foreach ($token in $tokens) {
  $voiceIndex++; $synth.SelectVoice($token.VoiceInfo.Name)
  for ($i = 0; $i -lt $phrases.Count; $i++) {
    $audioName = "voice-{0:D2}-phrase-{1:D3}.wav" -f $voiceIndex, ($i + 1)
    $audioPath = Join-Path $OutputDirectory $audioName
    $synth.SetOutputToWaveFile($audioPath); $synth.Speak([string]$phrases[$i].text); $synth.SetOutputToNull()
    $items.Add(@{ audio = $audioPath; reference = [string]$phrases[$i].text; subset = [string]$phrases[$i].subset; voice = $token.VoiceInfo.Name })
  }
}
$synth.Dispose()
$json = ConvertTo-Json -InputObject ($items.ToArray()) -Depth 4
[IO.File]::WriteAllText($ResultPath, $json, (New-Object System.Text.UTF8Encoding($false)))
''', encoding="utf-8")
        command = [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script_path),
                   "-PhrasesPath", str(phrases_path), "-OutputDirectory", str(output_dir.resolve()),
                   "-ResultPath", str(result_path), "-VoiceNamesPath", str(voice_names_path)]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode:
            detail = (completed.stderr or completed.stdout).strip()
            raise RuntimeError(f"Windows SAPI generation failed: {detail or completed.returncode}")
        generated = json.loads(result_path.read_text(encoding="utf-8-sig"))
    if isinstance(generated, dict):
        generated = [generated]
    rows = []
    for i, item in enumerate(generated, 1):
        audio = Path(item["audio"]).resolve()
        if not audio.is_file():
            raise FileNotFoundError(f"Windows SAPI did not create expected audio: {audio}")
        rows.append({"id": f"game-sapi-{i:04d}", "category": "game", "subset": item["subset"],
                     "audio": str(audio), "reference": item["reference"],
                     "source": f"synthetic Windows SAPI TTS ({item['voice']})", "synthetic": True})
    return rows


def generate_sapi_game_audio(phrase_file: Path, output_dir: Path,
                             voice_filters: list[str] | None = None) -> list[dict]:
    """Generate explicitly synthetic game samples with installed Windows SAPI voices."""
    if sys.platform != "win32":
        raise ValueError("--game-tts requires Windows and an installed SAPI voice")
    powershell = shutil.which("powershell.exe") or shutil.which("powershell")
    if not powershell:
        raise ValueError("Windows PowerShell was not found; use --game-tsv to import existing audio")
    phrases = _read_phrase_lines(phrase_file)
    if not phrases:
        raise ValueError(f"no game phrase prompts found in {phrase_file}")
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="voxgo-sapi-") as tmp:
        temp = Path(tmp)
        phrases_path = temp / "phrases.json"
        voice_names_path = temp / "voices.json"
        result_path = temp / "generated.json"
        script_path = temp / "generate.ps1"
        phrases_path.write_text(json.dumps(phrases, ensure_ascii=False), encoding="utf-8")
        voice_names_path.write_text(json.dumps(voice_filters or [], ensure_ascii=False), encoding="utf-8")
        script_path.write_text(r'''param([string]$PhrasesPath, [string]$OutputDirectory, [string]$ResultPath, [string]$VoiceNamesPath)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Speech
$phrases = Get-Content -LiteralPath $PhrasesPath -Raw -Encoding UTF8 | ConvertFrom-Json
$filters = [string[]](Get-Content -LiteralPath $VoiceNamesPath -Raw -Encoding UTF8 | ConvertFrom-Json)
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$tokens = @($synth.GetInstalledVoices() | Where-Object { $_.Enabled })
if ($filters.Count -gt 0) {
  $tokens = @($tokens | Where-Object {
    $name = $_.VoiceInfo.Name
    @($filters | Where-Object { $name -like "*$_*" }).Count -gt 0
  })
}
if ($tokens.Count -eq 0) { throw ("No enabled SAPI voices matched: filters={0}" -f ($filters -join ',')) }
$items = New-Object System.Collections.Generic.List[object]
$voiceIndex = 0
foreach ($token in $tokens) {
  $voiceIndex++
  $synth.SelectVoice($token.VoiceInfo.Name)
  for ($i = 0; $i -lt $phrases.Count; $i++) {
    $audioName = "voice-{0:D2}-phrase-{1:D3}.wav" -f $voiceIndex, ($i + 1)
    $audioPath = Join-Path $OutputDirectory $audioName
    $synth.SetOutputToWaveFile($audioPath)
    $synth.Speak([string]$phrases[$i])
    $synth.SetOutputToNull()
    $items.Add(@{ audio = $audioPath; reference = [string]$phrases[$i]; voice = $token.VoiceInfo.Name })
  }
}
$synth.Dispose()
$json = ConvertTo-Json -InputObject ($items.ToArray()) -Depth 4
[IO.File]::WriteAllText($ResultPath, $json, (New-Object System.Text.UTF8Encoding($false)))
''', encoding="utf-8")
        command = [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script_path),
                   "-PhrasesPath", str(phrases_path), "-OutputDirectory", str(output_dir.resolve()),
                   "-ResultPath", str(result_path), "-VoiceNamesPath", str(voice_names_path)]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode:
            detail = (completed.stderr or completed.stdout).strip()
            raise RuntimeError(f"Windows SAPI generation failed: {detail or completed.returncode}")
        generated = json.loads(result_path.read_text(encoding="utf-8-sig"))
    if isinstance(generated, dict):
        generated = [generated]
    rows = []
    for i, item in enumerate(generated, 1):
        audio = Path(item["audio"]).resolve()
        if not audio.is_file():
            raise FileNotFoundError(f"Windows SAPI did not create expected audio: {audio}")
        rows.append({"id": f"game-sapi-{i:04d}", "category": "game", "audio": str(audio),
                     "reference": item["reference"],
                     "source": f"synthetic Windows SAPI TTS ({item['voice']})", "synthetic": True})
    return rows


def _read_pcm16(path: Path) -> tuple[int, array]:
    with wave.open(str(path), "rb") as wf:
        if wf.getsampwidth() != 2 or wf.getnchannels() != 1 or wf.getcomptype() != "NONE":
            raise ValueError(f"noise mixture inputs must be uncompressed mono PCM16 WAV: {path}")
        rate = wf.getframerate()
        data = array("h")
        data.frombytes(wf.readframes(wf.getnframes()))
        if data.itemsize != 2:
            data.byteswap()
        return rate, data


def _rms(samples: Iterable[int]) -> float:
    values = list(samples)
    return math.sqrt(sum(float(x) * x for x in values) / max(1, len(values)))


def _load_mono_16k(path: Path) -> tuple[int, array]:
    # Reuse the app's decoder so Common Voice MP3 clips and varied noise WAVs
    # follow the same PyAV/soxr conversion path as benchmark audio input.
    from voxgo.audio.benchmark import load_benchmark_audio

    samples, rate = load_benchmark_audio(path, target_sample_rate=16000)
    return rate, array("h", samples.tolist())


def mix_noise(speech_path: Path, noise_path: Path, snr_db: float, output: Path,
              seed: int = 20260929) -> dict:
    rate, speech = _load_mono_16k(speech_path)
    noise_rate, noise = _load_mono_16k(noise_path)
    if rate != noise_rate:
        raise ValueError(f"audio decoder returned different sample rates ({rate} vs {noise_rate} Hz)")
    if not speech or not noise:
        raise ValueError("speech and noise WAV files must contain samples")
    digest = hashlib.blake2b(
        f"{int(seed)}\0{speech_path.resolve()}\0{noise_path.resolve()}".encode("utf-8"), digest_size=8
    ).digest()
    offset = int.from_bytes(digest, "big") % len(noise)
    repeated_noise = [noise[(offset + i) % len(noise)] for i in range(len(speech))]
    speech_rms, noise_rms = _rms(speech), math.sqrt(
        sum(float(noise[(offset + i) % len(noise)]) ** 2 for i in range(len(speech))) / len(speech)
    )
    if speech_rms <= 0 or noise_rms <= 0:
        raise ValueError("speech and noise must both have non-zero RMS")
    scale = speech_rms / (noise_rms * (10.0 ** (float(snr_db) / 20.0)))
    float_mix = [s + n * scale for s, n in zip(speech, repeated_noise)]
    would_clip = sum(abs(value) > 32767 for value in float_mix)
    peak = max(abs(value) for value in float_mix)
    attenuation = min(1.0, 32767.0 / peak) if peak else 1.0
    # Scale both speech and noise together; hard clipping changes the SNR.
    mixed = array("h", (max(-32768, min(32767, round(value * attenuation))) for value in float_mix))
    output.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(mixed.tobytes())
    return {"noise_offset_samples": offset, "would_clip_samples": would_clip,
            "mix_attenuation_db": 20.0 * math.log10(attenuation),
            "clipped_samples": 0, "clip_fraction": 0.0, "sample_rate": rate}


def prepare(args: argparse.Namespace) -> list[dict]:
    output = Path(args.output).resolve()
    rows: list[dict] = []
    natural_rows: list[dict] = []
    game_rows: list[dict] = []
    if args.common_voice:
        source = Path(args.common_voice).expanduser().resolve()
        if source.is_file():
            source = _safe_extract(source, Path(args.extract_to or output.parent / "common_voice_extracted").resolve())
        natural_rows = _common_voice_rows(source, args.limit, args.seed, args.cv_split)
        rows.extend(natural_rows)
    if args.librispeech:
        source = Path(args.librispeech).expanduser().resolve()
        if source.is_file():
            source = _safe_extract(source, Path(args.extract_to or output.parent / "librispeech_extracted").resolve())
        librispeech_rows = _librispeech_rows(source, args.limit, args.seed)
        natural_rows.extend(librispeech_rows)
        rows.extend(librispeech_rows)
    if args.game_tsv:
        game_rows = import_game_tsv(Path(args.game_tsv).resolve())
        rows.extend(game_rows)
    if args.game_tts:
        phrase_file = Path(args.game_phrases).expanduser().resolve()
        tts_dir = Path(args.game_tts_output or output.parent / "game_tts").expanduser().resolve()
        generated_rows = generate_sapi_game_audio(phrase_file, tts_dir, args.tts_voice)
        game_rows.extend(generated_rows)
        rows.extend(generated_rows)
    if args.tts_tsv:
        phrase_tsv = Path(args.tts_tsv).expanduser().resolve()
        tts_dir = Path(args.tts_tsv_output or output.parent / "labelled_tts").expanduser().resolve()
        generated_rows = generate_sapi_tsv_audio(phrase_tsv, tts_dir, args.tts_voice)
        game_rows.extend(generated_rows)
        rows.extend(generated_rows)
    if args.noise_reference_tsv:
        extra_path = Path(args.noise_reference_tsv).resolve()
        if not args.game_tsv or extra_path != Path(args.game_tsv).resolve():
            game_rows.extend(import_game_tsv(extra_path))
    if args.noise_wav:
        speech_rows = []
        if args.noise_source in {"natural", "both"}:
            speech_rows.extend(natural_rows)
        if args.noise_source in {"game", "both", "synthetic"}:
            speech_rows.extend(row for row in game_rows
                               if args.noise_source != "synthetic" or row.get("synthetic"))
        if not speech_rows:
            raise ValueError(f"--noise-wav has no clean speech candidates for --noise-source={args.noise_source}")
        _ensure_unique_ids(rows)
        _ensure_unique_ids(game_rows if args.noise_source == "game" else speech_rows)
        for row in speech_rows:
            for noise_path in args.noise_wav:
                for snr in args.snr_db:
                    noise_file = Path(noise_path).expanduser().resolve()
                    noise_key = hashlib.blake2b(str(noise_file).encode("utf-8"), digest_size=4).hexdigest()
                    dest = output.parent / "noise" / f"{row['id']}-{noise_file.stem}-{noise_key}-{snr:g}dB.wav"
                    mix_metadata = mix_noise(Path(row["audio"]), noise_file, snr, dest, seed=args.seed)
                    rows.append({"id": f"noise-{row['id']}-{noise_file.stem}-{noise_key}-{snr:g}dB",
                                 "category": "noise", "audio": str(dest.resolve()), "reference": row["reference"],
                                 "source": f"{row['source']} + {noise_file.name}", "snr_db": float(snr),
                                 "clean_category": row["category"], "noise_audio": str(noise_file),
                                 "noise_level": "light" if snr >= 10 else "heavy" if snr <= 0 else "medium",
                                 **({"subset": row["subset"]} if row.get("subset") else {}),
                                  **({"speaker_id": row["speaker_id"]} if row.get("speaker_id") else {}),
                                 **({"synthetic": True} if row.get("synthetic") else {}),
                                 "license": f"speech: {row.get('license') or 'unspecified'}; "
                                            f"noise: {args.noise_license or 'unspecified'}",
                                 **mix_metadata})
    if not rows:
        raise ValueError("no records produced; provide --common-voice and/or --game-tsv and/or noise inputs")
    _ensure_unique_ids(rows)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="data/asr_benchmark/manifest.jsonl")
    parser.add_argument("--common-voice", help="user-downloaded archive or extracted Common Voice spontaneous corpus")
    parser.add_argument("--librispeech", help="official OpenSLR SLR12 test-clean archive or extracted directory")
    parser.add_argument("--extract-to", help="where to extract a supplied ZIP/TAR archive")
    parser.add_argument("--limit", type=int, default=200, help="maximum Common Voice clips; 0 means all")
    parser.add_argument("--cv-split", choices=("test", "dev", "train", "all"), default="test",
                        help="Common Voice SPS split to sample; test is the default held-out set")
    parser.add_argument("--seed", type=int, default=20260929)
    parser.add_argument("--noise-reference-tsv", help="legacy alias for extra clean game speech TSV (audio<TAB>reference)")
    parser.add_argument("--noise-source", choices=("natural", "game", "synthetic", "both"), default="both",
                        help="clean speech categories to mix with --noise-wav")
    parser.add_argument("--noise-wav", action="append", default=[],
                        help="user-provided background WAV/MP3; repeatable (MP3/other compressed formats require PyAV)")
    parser.add_argument("--noise-license", default="", help="license or attribution label for the supplied noise files")
    parser.add_argument("--snr-db", action="append", type=float, default=[], help="target SNR dB; repeatable (default: 20, 10, 0)")
    parser.add_argument("--game-tsv", help="TSV with audio/reference columns for user-recorded or TTS clips")
    parser.add_argument("--game-tts", action="store_true", help="generate explicitly synthetic clips with installed Windows SAPI voices")
    parser.add_argument("--game-phrases", default=str(Path(__file__).resolve().parents[1] / "data" / "asr_game_phrases.txt"),
                        help="one game callout per line; blank lines and # comments are ignored")
    parser.add_argument("--game-tts-output", help="directory for generated synthetic WAV clips")
    parser.add_argument("--tts-voice", action="append", default=[],
                        help="optional installed SAPI voice name filter; repeatable (default: all enabled voices)")
    parser.add_argument("--tts-tsv", help="labelled TSV with subset and text columns; generates synthetic game-category audio")
    parser.add_argument("--tts-tsv-output", help="directory for labelled synthetic WAV clips")
    args = parser.parse_args(argv)
    if args.noise_wav and not args.snr_db:
        args.snr_db = [20.0, 10.0, 0.0]
    try:
        rows = prepare(args)
    except (OSError, RuntimeError, ValueError, tarfile.TarError, zipfile.BadZipFile) as exc:
        parser.error(str(exc))
    print(f"Wrote {len(rows)} records to {Path(args.output).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
