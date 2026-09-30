import csv
import json
import math
import stat
import subprocess
import tarfile
import tempfile
import unittest
import wave
import zipfile
from array import array
from pathlib import Path
from unittest.mock import patch

from scripts import prepare_asr_benchmark as module


def write_wav(path: Path, samples, rate=16000):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(array("h", samples).tobytes())


class PrepareAsrBenchmarkTest(unittest.TestCase):
    def test_librispeech_sampling_spreads_speakers_and_lengths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for speaker in range(10):
                chapter = root / "LibriSpeech" / "test-clean" / str(speaker) / "1"
                chapter.mkdir(parents=True)
                lines = []
                for index, words in enumerate(("short spoken phrase", "a few more ordinary words in this sentence today",
                                               "this is a substantially longer natural human spoken passage with many more words in the same recorded sentence than the other examples")):
                    clip = f"{speaker}-1-{index:04d}"
                    (chapter / f"{clip}.flac").write_bytes(b"flac-placeholder")
                    lines.append(f"{clip} {words}")
                (chapter / f"{speaker}-1.trans.txt").write_text("\n".join(lines), encoding="utf-8")
            rows = module._librispeech_rows(root, 20, 20260930)
            again = module._librispeech_rows(root, 20, 20260930)
            self.assertEqual([row["id"] for row in rows], [row["id"] for row in again])
            self.assertEqual(len(rows), 20)
            self.assertGreaterEqual(len({row["speaker_id"] for row in rows}), 8)
            self.assertEqual({row["subset"] for row in rows}, {"short", "ordinary", "longer"})
            self.assertTrue(all(row["category"] == "natural" and row["license"] == "CC BY 4.0"
                                for row in rows))

    def test_common_voice_sampling_is_repeatable_and_manifest_is_correct(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clips = root / "clips"
            clips.mkdir()
            for name in ("a.mp3", "b.mp3", "c.mp3"):
                (clips / name).write_bytes(b"audio")
            with (root / "validated.tsv").open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["path", "sentence"], delimiter="\t")
                writer.writeheader()
                for name in ("c.mp3", "a.mp3", "b.mp3"):
                    writer.writerow({"path": name, "sentence": f"text {name}"})
            first = module._common_voice_rows(root, 2, 71)
            second = module._common_voice_rows(root, 2, 71)
            self.assertEqual([r["audio"] for r in first], [r["audio"] for r in second])
            self.assertEqual(len(first), 2)
            self.assertTrue(all(r["category"] == "natural" for r in first))
            self.assertTrue(all(Path(r["audio"]).is_absolute() for r in first))

    def test_common_voice_blank_split_is_excluded_from_test_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audios = root / "audios"
            audios.mkdir()
            for name in ("test.wav", "blank.wav", "train.wav"):
                (audios / name).write_bytes(b"audio")
            with (root / "ss-corpus-en.tsv").open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=["audio_file", "transcription", "split"],
                                        delimiter="\t")
                writer.writeheader()
                writer.writerow({"audio_file": "test.wav", "transcription": "test phrase", "split": "test"})
                writer.writerow({"audio_file": "blank.wav", "transcription": "blank phrase", "split": ""})
                writer.writerow({"audio_file": "train.wav", "transcription": "train phrase", "split": "train"})
            rows = module._common_voice_rows(root, 0, 1, "test")
            self.assertEqual([row["reference"] for row in rows], ["test phrase"])

    def test_noise_mix_creates_pcm16_with_expected_duration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            speech = root / "speech.wav"
            noise = root / "noise.wav"
            output = root / "mixed.wav"
            write_wav(speech, [5000] * 1000)
            write_wav(noise, [1000, -1000] * 100)
            metadata = module.mix_noise(speech, noise, 10, output)
            rate, samples = module._read_pcm16(output)
            self.assertEqual(rate, 16000)
            self.assertEqual(len(samples), 1000)
            self.assertNotEqual(samples.tolist(), [5000] * 1000)
            attenuation = 10 ** (metadata["mix_attenuation_db"] / 20)
            speech_component = 5000 * attenuation
            noise_component = [sample - speech_component for sample in samples]
            measured_snr = 20 * math.log10(abs(speech_component) / module._rms(noise_component))
            self.assertAlmostEqual(measured_snr, 10, delta=0.1)

    def test_game_tsv_resolves_relative_audio_and_manifest_serializes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_wav(root / "voice.wav", [100] * 10)
            listing = root / "phrases.tsv"
            listing.write_text("audio\treference\nvoice.wav\trotate B\n", encoding="utf-8")
            rows = module.import_game_tsv(listing)
            self.assertEqual(rows[0]["category"], "game")
            self.assertEqual(json.loads(json.dumps(rows[0]))["reference"], "rotate B")

    def test_noise_resamples_inputs_to_16000_hz(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_wav(root / "speech.wav", [100] * 10, 16000)
            write_wav(root / "noise.wav", [100, -100] * 10, 44100)
            metadata = module.mix_noise(root / "speech.wav", root / "noise.wav", 10, root / "out.wav")
            rate, samples = module._read_pcm16(root / "out.wav")
            self.assertEqual(rate, 16000)
            self.assertEqual(metadata["sample_rate"], rate)
            self.assertEqual(len(samples), 10)
            self.assertGreaterEqual(metadata["noise_offset_samples"], 0)

    def test_noise_offset_and_clipping_metadata_are_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_wav(root / "speech.wav", [32000] * 100)
            write_wav(root / "noise.wav", [16000, -16000] * 30)
            first = module.mix_noise(root / "speech.wav", root / "noise.wav", -10,
                                     root / "first.wav", seed=99)
            second = module.mix_noise(root / "speech.wav", root / "noise.wav", -10,
                                      root / "second.wav", seed=99)
            self.assertEqual(first, second)
            self.assertGreater(first["would_clip_samples"], 0)
            self.assertLess(first["mix_attenuation_db"], 0)
            self.assertEqual(first["clipped_samples"], 0)

    def test_cli_mixes_sampled_common_voice_directly(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            corpus = root / "corpus"
            audios = corpus / "audios"
            audios.mkdir(parents=True)
            write_wav(audios / "natural.wav", [2000, -2000] * 100)
            write_wav(root / "a" / "gunfire.wav", [500, -500] * 70)
            write_wav(root / "b" / "gunfire.wav", [600, -600] * 80)
            with (corpus / "ss-corpus-en.tsv").open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["audio_file", "transcription", "split"], delimiter="\t")
                writer.writeheader()
                writer.writerow({"audio_file": "natural.wav", "transcription": "hold this angle", "split": "test"})
            manifest = root / "manifest.jsonl"
            result = module.main([
                "--common-voice", str(corpus), "--noise-wav", str(root / "a" / "gunfire.wav"),
                "--noise-wav", str(root / "b" / "gunfire.wav"),
                "--snr-db", "10", "--noise-source", "natural", "--noise-license", "CC BY 4.0 (MUSAN)",
                "--output", str(manifest),
            ])
            self.assertEqual(result, 0)
            records = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines()]
            noisy_records = [row for row in records if row["category"] == "noise"]
            noisy = noisy_records[0]
            self.assertEqual(noisy["reference"], "hold this angle")
            self.assertEqual(noisy["clean_category"], "natural")
            self.assertEqual(noisy["license"], "speech: CC0-1.0; noise: CC BY 4.0 (MUSAN)")
            self.assertEqual(noisy["snr_db"], 10.0)
            self.assertEqual(len(noisy_records), 2)
            self.assertEqual(len({row["audio"] for row in noisy_records}), 2)
            self.assertEqual(len({row["id"] for row in records}), len(records))
            self.assertTrue(Path(noisy["audio"]).is_file())

    def test_duplicate_game_tsv_argument_does_not_duplicate_manifest_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_wav(root / "voice.wav", [1000, -1000] * 20)
            game_tsv = root / "game.tsv"
            game_tsv.write_text("audio\treference\nvoice.wav\trotate B\n", encoding="utf-8")
            noise = root / "noise.wav"
            write_wav(noise, [200, -200] * 12)
            manifest = root / "manifest.jsonl"
            module.main(["--game-tsv", str(game_tsv), "--noise-reference-tsv", str(game_tsv),
                         "--noise-wav", str(noise), "--snr-db", "10", "--output", str(manifest)])
            records = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len({row["id"] for row in records}), len(records))
            self.assertEqual(sum(row["category"] == "game" for row in records), 1)
            self.assertEqual(sum(row["category"] == "noise" for row in records), 1)

    def test_game_phrase_prompts_are_100_plus_unique_lines(self):
        phrase_file = Path(__file__).resolve().parents[1] / "data" / "asr_game_phrases.txt"
        phrases = module._read_phrase_lines(phrase_file)
        self.assertGreaterEqual(len(phrases), 100)
        self.assertEqual(len({phrase.casefold() for phrase in phrases}), len(phrases))

    def test_balanced_phrase_file_has_exact_requested_counts_and_unique_text(self):
        phrase_file = Path(__file__).resolve().parents[1] / "data" / "asr_balanced_phrases.tsv"
        rows = module._read_labelled_phrases(phrase_file)
        counts = {subset: sum(row["subset"] == subset for row in rows)
                  for subset in module.BALANCED_SUBSETS}
        self.assertEqual(counts, {"normal": 30, "game": 30, "longer": 20,
                                  "number_direction_place": 20})
        self.assertEqual(len({row["text"].casefold() for row in rows}), 100)

    def test_labelled_sapi_smoke_preserves_subsets_and_synthetic_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            phrase_tsv = root / "phrases.tsv"
            phrase_tsv.write_text("subset\ttext\nnormal\tCheck the west door.\ngame\tRotate B now.\n",
                                  encoding="utf-8")

            def fake_powershell(command, **_kwargs):
                phrases_path = Path(command[command.index("-PhrasesPath") + 1])
                output_dir = Path(command[command.index("-OutputDirectory") + 1])
                result_path = Path(command[command.index("-ResultPath") + 1])
                phrases = json.loads(phrases_path.read_text(encoding="utf-8"))
                generated = []
                for i, phrase in enumerate(phrases, 1):
                    audio = output_dir / f"voice-01-phrase-{i:03d}.wav"
                    write_wav(audio, [1000, -1000] * 20)
                    generated.append({"audio": str(audio), "reference": phrase["text"],
                                      "subset": phrase["subset"], "voice": "Test English Voice"})
                result_path.write_text(json.dumps(generated), encoding="utf-8")
                return subprocess.CompletedProcess(command, 0, "", "")

            with patch.object(module.sys, "platform", "win32"), \
                    patch.object(module.shutil, "which", return_value="powershell.exe"), \
                    patch.object(module.subprocess, "run", side_effect=fake_powershell):
                rows = module.generate_sapi_tsv_audio(phrase_tsv, root / "tts", ["Test English"])
            self.assertEqual([row["subset"] for row in rows], ["normal", "game"])
            self.assertTrue(all(row["category"] == "game" and row["synthetic"] for row in rows))
            self.assertEqual(len({row["audio"] for row in rows}), 2)

    def test_labelled_tts_cli_keeps_subset_on_clean_and_light_heavy_noise(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            phrase_tsv = root / "phrases.tsv"
            phrase_tsv.write_text("subset\ttext\ngame\tRotate B now.\n", encoding="utf-8")
            noise = root / "noise.wav"
            write_wav(noise, [100, -100] * 30)
            output = root / "manifest.jsonl"

            def generated(*_args):
                audio = root / "speech.wav"
                write_wav(audio, [2000, -2000] * 100)
                return [{"id": "game-sapi-0001", "category": "game", "subset": "game",
                         "audio": str(audio), "reference": "Rotate B now.", "source": "synthetic TTS",
                         "synthetic": True}]

            with patch.object(module, "generate_sapi_tsv_audio", side_effect=generated):
                module.main(["--tts-tsv", str(phrase_tsv), "--noise-source", "synthetic",
                             "--noise-wav", str(noise), "--snr-db", "15", "--snr-db", "0",
                             "--output", str(output)])
            records = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
            clean = next(row for row in records if row["category"] == "game")
            noisy = [row for row in records if row["category"] == "noise"]
            self.assertEqual(clean["subset"], "game")
            self.assertTrue(clean["synthetic"])
            self.assertEqual({row["noise_level"] for row in noisy}, {"light", "heavy"})
            self.assertTrue(all(row["subset"] == "game" and row["synthetic"] for row in noisy))

    def test_sapi_generation_manifest_is_synthetic_without_requiring_real_voices(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            phrase_file = root / "phrases.txt"
            phrase_file.write_text("rotate B\n", encoding="utf-8")
            output = root / "sapi"

            def fake_powershell(command, **_kwargs):
                phrases_path = Path(command[command.index("-PhrasesPath") + 1])
                voices_path = Path(command[command.index("-VoiceNamesPath") + 1])
                output_dir = Path(command[command.index("-OutputDirectory") + 1])
                result_path = Path(command[command.index("-ResultPath") + 1])
                phrases = json.loads(phrases_path.read_text(encoding="utf-8"))
                self.assertEqual(json.loads(voices_path.read_text(encoding="utf-8")),
                                 ["Voice One", "Voice Two"])
                generated = []
                for i, voice in enumerate(("Test Voice One", "Test Voice Two"), 1):
                    audio = output_dir / f"voice-{i:02d}-phrase-001.wav"
                    write_wav(audio, [100] * 20)
                    generated.append({"audio": str(audio), "reference": phrases[0], "voice": voice})
                result_path.write_text(json.dumps(generated), encoding="utf-8")
                return subprocess.CompletedProcess(command, 0, "", "")

            with patch.object(module.sys, "platform", "win32"), \
                    patch.object(module.shutil, "which", return_value="powershell.exe"), \
                    patch.object(module.subprocess, "run", side_effect=fake_powershell):
                rows = module.generate_sapi_game_audio(phrase_file, output,
                                                       ["Voice One", "Voice Two"])
            self.assertEqual(len(rows), 2)
            self.assertTrue(all(row["category"] == "game" for row in rows))
            self.assertTrue(all("synthetic" in row["source"].lower() for row in rows))
            self.assertEqual({row["reference"] for row in rows}, {"rotate B"})

    def test_spontaneous_speech_v5_layout_uses_transcription_and_skips_unlabelled(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "archive-root"
            audios = root / "audios"
            audios.mkdir(parents=True)
            for name in ("ok.mp3", "train.mp3", "pending.mp3", "empty.mp3", "unassigned.mp3"):
                (audios / name).write_bytes(b"audio")
            with (root / "ss-corpus-en.tsv").open("w", encoding="utf-8", newline="") as f:
                fields = ["audio_id", "audio_file", "transcription", "split"]
                writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
                writer.writeheader()
                writer.writerows([
                    {"audio_id": "1", "audio_file": "ok.mp3", "transcription": "spoken words", "split": "test"},
                    {"audio_id": "5", "audio_file": "train.mp3", "transcription": "training words", "split": "train"},
                    {"audio_id": "2", "audio_file": "pending.mp3", "transcription": "pending words", "split": "unassigned"},
                    {"audio_id": "3", "audio_file": "empty.mp3", "transcription": "", "split": "dev"},
                    {"audio_id": "4", "audio_file": "unassigned.mp3", "transcription": "unvalidated text", "split": "unassigned"},
                ])
            rows = module._common_voice_rows(root, 0, 1)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["reference"], "spoken words")
            self.assertEqual(rows[0]["audio"], str((audios / "ok.mp3").resolve()))
            self.assertEqual(rows[0]["license"], "CC0-1.0")

    def test_archive_symlinks_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "links.tar"
            with tarfile.open(archive, "w") as tf:
                link = tarfile.TarInfo("escape")
                link.type = tarfile.SYMTYPE
                link.linkname = "../../outside"
                tf.addfile(link)
            with self.assertRaisesRegex(ValueError, "links are not supported"):
                module._safe_extract(archive, root / "extracted")

            zip_archive = root / "links.zip"
            info = zipfile.ZipInfo("escape")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            with zipfile.ZipFile(zip_archive, "w") as zf:
                zf.writestr(info, "../../outside")
            with self.assertRaisesRegex(ValueError, "symbolic links are not supported"):
                module._safe_extract(zip_archive, root / "zip-extracted")


if __name__ == "__main__":
    unittest.main()
