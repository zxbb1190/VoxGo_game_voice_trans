from dataclasses import dataclass, field

from voxgo.audio.capture import SpeechSegment


@dataclass
class LatencyTrace:
    item_id: str
    speech_detected_at: float
    queued_at: float
    source_lang: str = ""
    target_lang: str = ""
    whisper_language: str = ""
    language_revision: int = 0
    latency_mode: str = ""
    candidate_labels: tuple = field(default_factory=tuple)
    segment_voice_seconds: float = 0.0
    segment_total_seconds: float = 0.0
    whisper_model_size: str = ""
    whisper_device: str = ""
    whisper_compute_type: str = ""
    whisper_cpu_threads: int = 0
    fast_path_allowed: bool = False
    fast_path_ready: bool = False
    dequeued_at: float = 0.0
    transcription_started_at: float = 0.0
    transcription_finished_at: float = 0.0
    translation_started_at: float = 0.0
    translation_finished_at: float = 0.0
    overlay_updated_at: float = 0.0

    def summary_ms(self) -> dict:
        wait_ms = self._elapsed_ms(self.queued_at, self.dequeued_at)
        recognition_ms = self._elapsed_ms(self.transcription_started_at, self.transcription_finished_at)
        translation_ms = self._elapsed_ms(self.translation_started_at, self.translation_finished_at)
        overlay_ms = self._elapsed_ms(self.translation_finished_at, self.overlay_updated_at)
        total_ms = self._elapsed_ms(self.speech_detected_at, self.overlay_updated_at)
        return {
            "wait_ms": wait_ms,
            "recognition_ms": recognition_ms,
            "translation_ms": translation_ms,
            "overlay_ms": overlay_ms,
            "total_ms": total_ms,
            "latency_mode": self.latency_mode,
            "candidate_labels": ",".join(self.candidate_labels or ()),
            "segment_voice_ms": int(round(max(0.0, self.segment_voice_seconds) * 1000)),
            "segment_total_ms": int(round(max(0.0, self.segment_total_seconds) * 1000)),
            "whisper_model_size": self.whisper_model_size,
            "whisper_device": self.whisper_device,
            "whisper_compute_type": self.whisper_compute_type,
            "whisper_cpu_threads": self.whisper_cpu_threads,
            "fast_path_allowed": self.fast_path_allowed,
            "fast_path_ready": self.fast_path_ready,
        }

    @staticmethod
    def _elapsed_ms(start: float, end: float) -> int:
        if not start or not end:
            return 0
        return int(round(max(0.0, end - start) * 1000))


@dataclass
class SpeechWorkItem:
    segment: SpeechSegment
    trace: LatencyTrace
    candidate_labels: tuple = field(default_factory=tuple)
    candidate_reason: str = ""
    low_confidence: bool = False
    short_segment: bool = False
    dumped_low_confidence: bool = False
    source_lang: str = ""
    target_lang: str = ""
    whisper_language: str = ""
    language_revision: int = 0
