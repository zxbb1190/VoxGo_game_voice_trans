"""Local-only instrumentation around the unmodified capture and SpeechPipeline.

No second segmentation/filter implementation: all decisions delegate to production
methods. Frame provenance follows actual queue objects, not ambiguous byte.find().
"""
from collections import defaultdict
from dataclasses import asdict
import hashlib
import json
import queue
import sys
import threading
import time
import wave

import numpy as np
from loguru import logger

from voxgo.audio.capture import SystemAudioCapture
from voxgo.asr.pipeline import SpeechPipeline
from voxgo.asr.whisper_engine import SpeechRecognizer
from voxgo.runtime.work_items import SpeechWorkItem


def sha(data):
    return hashlib.sha256(data).hexdigest()


def coalesce(spans):
    """Coalesce adjacency only; preserve overlaps, gaps and playback order."""
    out = []
    for start, end in spans:
        if out and out[-1][1] == start:
            out[-1][1] = end
        else:
            out.append([start, end])
    return out


def write_wav(path, data, rate=16000):
    with wave.open(str(path), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(rate)
        stream.writeframes(data)


class Journal:
    def __init__(self, output, stream, clips):
        self.output, self.stream, self.clips = output, stream, clips
        self.lock = threading.RLock()
        self.local = threading.local()
        self.events, self.segments, self.items, self.windows = [], {}, {}, []
        self.refs, self.byte_spans = {}, {}
        self.active_asr_segment = None
        self.started = time.perf_counter()
        self.handle = (output / "events.jsonl").open("x", encoding="utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.handle.close()

    def event(self, kind, **data):
        with self.lock:
            row = dict(sequence=len(self.events), kind=kind,
                       elapsed_ms=(time.perf_counter() - self.started) * 1000,
                       thread=threading.current_thread().name, **data)
            self.events.append(row)
            self.handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            self.handle.flush()
        return row

    def keep_bytes(self, data, spans):
        self.refs[id(data)] = data  # Retain identity even for identical silence.
        self.byte_spans[id(data)] = coalesce(spans)

    def locations(self, spans):
        return [dict(id=c["id"], wav_start_frame=max(start, c["stream_start_frame"]) - c["stream_start_frame"],
                     wav_end_frame=min(end, c["stream_end_frame"]) - c["stream_start_frame"],
                     stream_start_frame=max(start, c["stream_start_frame"]),
                     stream_end_frame=min(end, c["stream_end_frame"]))
                for start, end in spans for c in self.clips
                if start < c["stream_end_frame"] and end > c["stream_start_frame"]]

    def segment(self, segment, spans=None, parents=()):
        key = id(segment)
        if key not in self.segments:
            sid = f"s{len(self.segments) + 1:03d}"
            spans = coalesce(spans if spans is not None else self.byte_spans[id(segment.audio_data)])
            reconstructed = b"".join(self.stream[a*2:b*2] for a, b in spans)
            if reconstructed != segment.audio_data:
                raise ValueError("PCM provenance mismatch; stop")
            self.refs[key] = segment
            self.keep_bytes(segment.audio_data, spans)
            row = {k: v for k, v in vars(segment).items() if k != "audio_data"}
            row.update(segment_id=sid, spans=spans, sources=self.locations(spans),
                       pcm_sha256=sha(segment.audio_data), parents=list(parents),
                       captured=not bool(parents), status="captured" if not parents else "merged")
            self.segments[key] = row
            write_wav(self.output / f"{sid}.wav", segment.audio_data)
            self.event("captured" if not parents else "merged_segment", **row)
        return self.segments[key]

    def item(self, item):
        if not isinstance(item, SpeechWorkItem):
            return None
        key = id(item)
        if key not in self.items:
            self.refs[key] = item
            segment = self.segment(item.segment)
            self.items[key] = dict(item_id=f"w{len(self.items)+1:03d}", segment_id=segment["segment_id"],
                                   status="admitted", candidate_labels=list(item.candidate_labels),
                                   candidate_reason=item.candidate_reason,
                                   config_snapshot=asdict(item.whisper_config_snapshot) if item.whisper_config_snapshot else None)
            self.event("work_item", **self.items[key])
        return self.items[key]

    def current(self):
        return getattr(self.local, "item", None)

    def log(self, message):
        name = message.record["name"]
        if name.startswith(("voxgo.asr", "voxgo.audio.capture")):
            item = self.current()
            self.event("diagnostic", message=message.record["message"], level=message.record["level"].name,
                       item_id=self.item(item)["item_id"] if item else None)


class RawQueue:
    def __init__(self, original, owner):
        self.original, self.owner = original, owner

    def __getattr__(self, name):
        return getattr(self.original, name)

    def get_nowait(self):
        data = self.original.get_nowait()
        spans = self.owner.journal.byte_spans[id(data)]
        if self.owner.processing and threading.get_ident() == self.owner.processing_thread:
            self.owner.drained.extend(spans)
            self.owner.drained_blocks += 1
        else:
            self.owner.journal.event("raw_queue_drop", spans=spans, reason="production_drop_oldest")
        return data


class ObservedCapture(SystemAudioCapture):
    def __init__(self, config, journal):
        super().__init__(config)
        self.journal = journal
        self._audio_queue = RawQueue(self._audio_queue, self)
        self.processing = False
        self.processing_thread = None
        self.drained, self.drained_blocks = [], 0
        self.emitting = None
        self.pre_roll_used = []

    def feed(self, data, start, end, deadline):
        self.journal.keep_bytes(data, [[start, end]])
        self.journal.event("injected", spans=[[start, end]],
                           scheduling_lateness_ms=max(0, (time.perf_counter()-deadline)*1000))
        self._enqueue_audio_block(data)

    def process_audio(self):
        self.drained, self.drained_blocks = [], 0
        self.processing = True
        self.processing_thread = threading.get_ident()
        try:
            return super().process_audio()
        finally:
            self.processing = False

    def _is_vad_speech(self, audio_np):
        # Read the actual joined bytes object; never alter the production local.
        caller = sys._getframe(1)
        if caller.f_code.co_name != "process_audio":
            raise RuntimeError("capture observer no longer matches source")
        data = caller.f_locals["audio_data"]
        self.journal.keep_bytes(data, self.drained)
        expected = b"".join(self.journal.stream[a*2:b*2] for a, b in self.drained)
        if expected != data:
            raise ValueError("joined capture block provenance mismatch")
        vad, ratio = super()._is_vad_speech(audio_np)
        rms = float(caller.f_locals["rms"])
        row = dict(spans=coalesce(self.drained), joined_blocks=self.drained_blocks,
                   vad_speech=bool(vad), vad_ratio=float(ratio), rms_dbfs=rms,
                   energy_threshold_dbfs=float(self._energy_threshold),
                   energy_activity=bool(rms > self._energy_threshold),
                   previous_peak_rms_dbfs=float(self._speech_peak_rms) if self._speech_peak_rms is not None else None,
                   silence_counter_before=self._silence_counter,
                   relative_tail_candidate=bool(self._speech_peak_rms is not None and rms <= self._speech_peak_rms-self._soft_silence_margin_db),
                   near_gate_candidate=bool(rms <= self._energy_threshold+self._soft_silence_gate_margin_db))
        self.journal.windows.append(row)
        self.journal.event("activity_window", **row)
        return vad, ratio

    def _clear_pre_roll(self):
        if getattr(self, "processing", False) and self._pre_roll_buffer:
            self.pre_roll_used = coalesce([span for data, _ in self._pre_roll_buffer
                                          for span in self.journal.byte_spans[id(data)]])
        super()._clear_pre_roll()

    def _emit_speech_buffer(self, reason):
        self.emitting = coalesce([span for data in self._speech_buffer
                                  for span in self.journal.byte_spans[id(data)]])
        try:
            return super()._emit_speech_buffer(reason)
        finally:
            self.emitting = None
            self.pre_roll_used = []

    def observe_segment(self, segment):
        row = self.journal.segment(segment, self.emitting)
        row["pre_roll_spans"] = self.pre_roll_used
        row["pre_roll_actual_frames"] = sum(b-a for a, b in self.pre_roll_used)
        self.journal.event("pre_roll_used", segment_id=row["segment_id"],
                           spans=self.pre_roll_used, frames=row["pre_roll_actual_frames"])
        return row


class WorkQueue(queue.Queue):
    def __init__(self, size, journal):
        super().__init__(size)
        self.journal = journal

    def _put(self, item):
        super()._put(item)
        row = self.journal.item(item)
        if row:
            row["status"] = "queued"
            self.journal.event("queue_put", item_id=row["item_id"], depth=self._qsize())

    def _get(self):
        item = super()._get()
        row = self.journal.item(item)
        if row:
            self.journal.event("queue_get", item_id=row["item_id"], depth=self._qsize())
        return item


class ObservedPipeline(SpeechPipeline):
    def __init__(self, *args, journal, **kwargs):
        super().__init__(*args, **kwargs)
        self.journal = journal
        self._queue = WorkQueue(self._queue_size, journal)
        # Production debug is disabled; observe its existing drop call sites.
        self._debug_audio.dump_if_enabled = self.note_drop

    def note_drop(self, segment, reason, flag):
        row = self.journal.segment(segment)
        if flag != "save_low_confidence_audio":
            row.update(status="dropped", filter_reason=reason)
        self.journal.event("drop" if flag != "save_low_confidence_audio" else "weak_candidate_note",
                           segment_id=row["segment_id"], reason=reason, flag=flag)

    def _apply_language_snapshot(self, item, config):
        super()._apply_language_snapshot(item, config)
        if hasattr(self, "journal"):
            row = self.journal.item(item)
            row["config_snapshot"] = asdict(item.whisper_config_snapshot)

    def _process(self, item):
        row = self.journal.item(item)
        self.journal.local.item = item
        row["status"] = "processing"
        self.journal.event("process_start", item_id=row["item_id"],
                           since_capture_ms=(time.time()-item.trace.speech_detected_at)*1000)
        try:
            return super()._process(item)
        finally:
            segment = self.journal.segment(item.segment)
            row["status"] = segment["status"]
            row["filter_reason"] = segment.get("filter_reason", "")
            row["trace"] = asdict(item.trace)
            row["queue_wait_ms"] = max(0, (item.trace.dequeued_at-item.trace.queued_at)*1000) if item.trace.dequeued_at else None
            self.journal.event("process_end", **row)
            self.journal.local.item = None


class ObservedRecognizer(SpeechRecognizer):
    def __init__(self, config, journal):
        super().__init__(config)
        self.journal = journal

    def _normalize_for_transcription(self, audio):
        result = super()._normalize_for_transcription(audio)
        item = self.journal.current()
        if item:
            before = float(np.sqrt(np.mean(audio**2))) if len(audio) else 0.0
            after = float(np.sqrt(np.mean(result**2))) if len(result) else 0.0
            gain = min(self.config.max_gain_db, max(0., self.config.target_rms_dbfs-20*np.log10(max(before,1e-10)))) if self.config.normalize_audio and 20*np.log10(max(before,1e-10)) >= self.config.min_gain_rms_dbfs else 0.
            if gain <= .1:
                gain = 0.
            self.journal.segment(item.segment)["normalization"] = dict(
                input_rms_dbfs=float(20*np.log10(max(before,1e-10))),
                output_rms_dbfs=float(20*np.log10(max(after,1e-10))), gain_db=float(gain),
                normalized_float32_sha256=sha(result.tobytes()))
        return result

    def transcribe_audio_bytes_with_language(self, data, sample_rate=16000, language_override=None, config_override=None):
        item = self.journal.current()
        row = self.journal.segment(item.segment)
        self.journal.active_asr_segment = row
        started, cpu = time.perf_counter(), time.process_time()
        self.journal.event("whisper_start", segment_id=row["segment_id"], pcm_sha256=sha(data),
                           config_snapshot=asdict(config_override) if config_override else None)
        try:
            result = super().transcribe_audio_bytes_with_language(data, sample_rate, language_override, config_override)
        finally:
            self.journal.active_asr_segment = None
        row.update(asr=asdict(result), asr_ms=(time.perf_counter()-started)*1000,
                   asr_process_cpu_seconds=time.process_time()-cpu,
                   effective_whisper=asdict(self.config), runtime_device=self.runtime_device,
                   runtime_compute_type=self._runtime_compute_type, status="asr_completed")
        self.journal.event("whisper_end", **{k: v for k, v in row.items() if k not in {"asr", "effective_whisper"}},
                           asr=asdict(result), effective_whisper=asdict(self.config))
        return result


def observe_merge(journal, original):
    def merged(left, right, reason="merged"):
        item = original(left, right, reason)
        l, r = journal.segment(left.segment), journal.segment(right.segment)
        row = journal.segment(item.segment, l["spans"]+r["spans"], [l["segment_id"], r["segment_id"]])
        for parent in (l, r):
            parent.update(status="merged_into", merged_into=row["segment_id"])
        for parent in (left, right):
            journal.item(parent)["status"] = "merged_into"
        journal.event("work_merge", left=journal.item(left)["item_id"], right=journal.item(right)["item_id"],
                       result=journal.item(item)["item_id"], reason=reason)
        return item
    return merged
