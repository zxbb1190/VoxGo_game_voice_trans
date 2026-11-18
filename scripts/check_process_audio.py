"""Opt-in Windows hardware acceptance: two independent apps emit quiet tones.

No models or network. Writes only aggregate spectral evidence, not captured audio.
Run: python scripts/check_process_audio.py --output diagnostics/process-audio.json
"""
import argparse
from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def producer(frequency, seconds, child=False):
    if child:
        # Target process itself is silent; its child renders the selected tone.
        return subprocess.call([sys.executable, __file__, "--producer", str(frequency), "--seconds", str(seconds)])
    import numpy as np
    import pyaudiowpatch as pa
    engine = pa.PyAudio()
    stream = None
    try:
        device = engine.get_host_api_info_by_type(pa.paWASAPI)["defaultOutputDevice"]
        rate = int(engine.get_device_info_by_index(int(device))["defaultSampleRate"])
        stream = engine.open(format=pa.paInt16, channels=2, rate=rate, output=True, output_device_index=int(device))
        block = (np.sin(2 * np.pi * frequency * np.arange(rate // 10) / rate) * 1100).astype(np.int16)
        stereo = np.repeat(block[:, None], 2, axis=1).tobytes()
        for _ in range(int(seconds * 10)):
            stream.write(stereo)
    finally:
        if stream:
            stream.stop_stream()
            stream.close()
        engine.terminate()
    return 0


def run(output, seconds):
    import numpy as np
    from voxgo.audio.capture import AudioConfig
    from voxgo.audio.process_loopback import ProcessAudioCapture, process_identity, resolve_target, support_error
    if support_error():
        raise RuntimeError(support_error())
    processes = []
    capture = None
    try:
        for tone, child in ((440, True), (880, False)):
            # Use the actual interpreter PID, not the venv launcher. The UI also
            # selects the process owning the app window, never a launcher wrapper.
            executable = getattr(sys, "_base_executable", sys.executable)
            env = dict(os.environ, PYTHONPATH=os.pathsep.join(sys.path))
            args = [executable, __file__, "--producer", str(tone), "--seconds", str(seconds + 3)]
            if child:
                args.append("--child")
            processes.append(subprocess.Popen(args, creationflags=subprocess.CREATE_NO_WINDOW,
                                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env))
        identity = process_identity(processes[0].pid)
        config = AudioConfig(source_mode="process", process_path=identity["path"],
                             process_id=identity["pid"], process_started=identity["started"])
        capture = ProcessAudioCapture(config)
        capture.start()
        chunks = []
        until = time.monotonic() + seconds
        while time.monotonic() < until:
            while not capture._audio_queue.empty():
                chunks.append(capture._audio_queue.get_nowait())
            time.sleep(0.03)
        samples = np.frombuffer(b"".join(chunks), dtype=np.int16).astype(float)
        samples = samples[int(44100):]  # allow the rendering sessions to start
        frequencies = np.fft.rfftfreq(len(samples), 1 / 44100)
        amplitudes = np.abs(np.fft.rfft(samples * np.hanning(len(samples))))
        def energy(tone):
            return float(np.max(amplitudes[(frequencies > tone - 3) & (frequencies < tone + 3)]))
        selected, excluded = energy(440), energy(880)
        rejection = 20 * np.log10(max(selected, 1) / max(excluded, 1))
        for process in processes:
            _, errors = process.communicate(timeout=seconds + 8)
            if process.returncode:
                raise RuntimeError(f"Audio producer failed ({process.returncode}): {errors.decode(errors='replace')}")
        time.sleep(0.6)
        exited = capture.health_error() is not None
        reused_pid_rejected = False
        try:
            resolve_target(replace(config, process_id=processes[1].pid, process_started=identity["started"]))
        except RuntimeError:
            reused_pid_rejected = True
        report = {"windows_build": sys.getwindowsversion().build, "sample_seconds": len(samples) / 44100,
                  "selected_child_frequency_hz": 440, "excluded_app_frequency_hz": 880,
                  "rms_dbfs": float(20 * np.log10(max(np.sqrt(np.mean(samples ** 2)), 1e-9) / 32768)),
                  "other_app_rejection_db": float(rejection), "target_exit_detected": exited,
                  "stale_identity_rejected": reused_pid_rejected,
                  "passed": bool(selected > 1000 and rejection > 30 and exited and reused_pid_rejected)}
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 0 if report["passed"] else 1
    finally:
        if capture:
            capture.stop()
        for process in processes:
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "diagnostics/process-audio.json")
    parser.add_argument("--seconds", type=float, default=6)
    parser.add_argument("--producer", type=int)
    parser.add_argument("--child", action="store_true")
    args = parser.parse_args()
    raise SystemExit(producer(args.producer, args.seconds, args.child) if args.producer else run(args.output, args.seconds))
