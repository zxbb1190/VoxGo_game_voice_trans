"""
语音识别模块
使用 faster-whisper 进行本地语音转文字
"""

import asyncio
import inspect
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
from faster_whisper import WhisperModel
try:
    from faster_whisper.vad import VadOptions
except Exception:
    VadOptions = None
from loguru import logger


GENERAL_INITIAL_PROMPT = (
    "以下是实时语音字幕，内容可能来自 PC 游戏、Discord 语音、直播、视频、网页、"
    "广告或会议。请准确转写中文、英文以及中英文混杂内容；保留品牌名、产品名、"
    "人名、地名、游戏术语、应用名、文件格式、字母缩写和数字，例如 Speechify、"
    "Discord、Steam、PDFs、Google Docs、OpenAI、GG、FPS。"
)

GAME_INITIAL_PROMPT = (
    "以下是游戏语音聊天，可能包含中文、英文以及中英文混杂。请准确保留人名、"
    "地名、游戏术语、技能名、枪械名、英雄名、地图点位和字母缩写，例如 Discord、"
    "Steam、Valorant、Apex、GG、NT、WP、FPS。"
)

PROMPT_PROFILES = {
    "none": None,
    "off": None,
    "general": GENERAL_INITIAL_PROMPT,
    "game": GAME_INITIAL_PROMPT,
}

ASR_HALLUCINATION_PATTERNS = (
    "请准确转写",
    "请准确翻译",
    "实时语音字幕",
    "游戏语音聊天",
    "广告或会议",
    "中英文混杂",
    "thank you for watching",
    "thanks for watching",
    "感谢观看",
    "谢谢观看",
)

_LIBROSA = None
_LIBROSA_IMPORT_FAILED = False


@dataclass
class WhisperConfig:
    model_size: str = "small"
    device: str = "auto"
    compute_type: str = "auto"
    language: str = "auto"
    beam_size: int = 5
    vad_filter: bool = False
    vad_parameters: dict = None
    model_dir: str = ".models"
    local_files_only: bool = False
    prompt_profile: str = "none"
    initial_prompt: str = ""
    condition_on_previous_text: bool = False
    temperature: float = 0.0
    no_speech_threshold: float = 0.6
    log_prob_threshold: float = -1.0
    compression_ratio_threshold: float = 2.4
    normalize_audio: bool = True
    target_rms_dbfs: float = -20.0
    max_gain_db: float = 12.0
    min_gain_rms_dbfs: float = -50.0


@dataclass
class TranscriptionResult:
    text: str
    language: str = ""
    language_probability: float = 0.0


class SpeechRecognizer:
    """Whisper 语音识别器"""

    def __init__(self, config: WhisperConfig = None):
        self.config = config or WhisperConfig()
        if self.config.vad_parameters is None:
            self.config.vad_parameters = DEFAULT_VAD_PARAMS.copy()
        self.config.vad_parameters = sanitize_vad_parameters(self.config.vad_parameters)
        self._model: Optional[WhisperModel] = None
        self._initialized = False
        self._model_dir = Path(self.config.model_dir)
        if not self._model_dir.is_absolute():
            self._model_dir = Path(__file__).parent / self._model_dir
        logger.info(f"Whisper 模型目录: {self._model_dir}")

    def initialize(self):
        """初始化 Whisper 模型"""
        if self._initialized:
            return

        self._model_dir.mkdir(parents=True, exist_ok=True)
        last_error = None
        for device, compute_type in self._model_load_candidates():
            logger.info(
                "加载 Whisper 模型: {} (device={}, compute_type={})",
                self.config.model_size,
                device,
                compute_type
            )
            try:
                self._model = WhisperModel(
                    self.config.model_size,
                    device=device,
                    compute_type=compute_type,
                    download_root=str(self._model_dir),
                    local_files_only=self.config.local_files_only
                )
                self.config.device = device
                self.config.compute_type = compute_type
                self._initialized = True
                logger.info("Whisper 模型加载完成")
                return
            except Exception as e:
                last_error = e
                logger.warning(
                    "加载 Whisper 模型失败，将尝试下一个设备配置: device={}, compute_type={}, error={}",
                    device,
                    compute_type,
                    e,
                )

        raise RuntimeError("Whisper 模型加载失败，没有可用的设备配置") from last_error

    def _model_load_candidates(self):
        configured_device = (self.config.device or "auto").strip().lower()
        if configured_device == "auto":
            return [
                ("cuda", self._compute_type_for_device("cuda")),
                ("cpu", "int8"),
            ]

        candidates = [(configured_device, self._compute_type_for_device(configured_device))]
        if configured_device != "cpu":
            candidates.append(("cpu", "int8"))
        elif candidates[0][1] != "int8":
            candidates.append(("cpu", "int8"))
        return candidates

    def _compute_type_for_device(self, device: str) -> str:
        configured = (self.config.compute_type or "auto").strip().lower()
        if configured in ("", "auto", "default"):
            return "float16" if device == "cuda" else "int8"
        return configured

    def _initial_prompt(self) -> Optional[str]:
        custom_prompt = (self.config.initial_prompt or "").strip()
        if custom_prompt:
            return custom_prompt
        profile = (self.config.prompt_profile or "none").strip().lower()
        return PROMPT_PROFILES.get(profile)

    def _resample_to_16k(self, audio_array: np.ndarray, sample_rate: int) -> np.ndarray:
        if sample_rate == 16000:
            return audio_array.astype(np.float32, copy=False)

        original_len = len(audio_array)
        try:
            librosa = _load_librosa()
            resampled = librosa.resample(
                audio_array,
                orig_sr=sample_rate,
                target_sr=16000,
            ).astype(np.float32, copy=False)
            logger.debug(
                "librosa 重采样: {}Hz -> 16000Hz, {} -> {} 点",
                sample_rate,
                original_len,
                len(resampled),
            )
            return resampled
        except Exception as e:
            logger.warning("librosa 重采样失败，退回线性插值: {}", e)
            target_len = int(original_len * 16000 / sample_rate)
            x_old = np.linspace(0, 1, original_len, dtype=np.float32)
            x_new = np.linspace(0, 1, target_len, dtype=np.float32)
            resampled = np.interp(x_new, x_old, audio_array).astype(np.float32)
            logger.debug(
                "线性插值重采样: {}Hz -> 16000Hz, {} -> {} 点",
                sample_rate,
                original_len,
                len(resampled),
            )
            return resampled

    def _normalize_for_transcription(self, audio_array: np.ndarray) -> np.ndarray:
        if not self.config.normalize_audio or len(audio_array) == 0:
            return audio_array.astype(np.float32, copy=False)

        audio_array = audio_array.astype(np.float32, copy=False)
        rms = float(np.sqrt(np.mean(audio_array ** 2)))
        rms_dbfs = 20 * np.log10(max(rms, 1e-10))
        min_gain_rms = float(getattr(self.config, "min_gain_rms_dbfs", -50.0))
        target_rms = float(getattr(self.config, "target_rms_dbfs", -20.0))
        max_gain = max(0.0, float(getattr(self.config, "max_gain_db", 12.0)))

        if rms_dbfs < min_gain_rms:
            logger.debug("跳过识别前增益: rms={:.1f} dBFS 低于 {:.1f} dBFS", rms_dbfs, min_gain_rms)
            return audio_array

        gain_db = min(max_gain, max(0.0, target_rms - rms_dbfs))
        if gain_db <= 0.1:
            return audio_array

        gain = 10 ** (gain_db / 20)
        normalized = np.clip(audio_array * gain, -1.0, 1.0).astype(np.float32, copy=False)
        logger.debug(
            "识别前增益: rms={:.1f} dBFS -> target={:.1f} dBFS, gain={:.1f} dB",
            rms_dbfs,
            target_rms,
            gain_db,
        )
        return normalized

    def transcribe_audio_bytes(self, audio_bytes: bytes, sample_rate: int = 44100) -> str:
        """将音频字节转录为文字"""
        return self.transcribe_audio_bytes_with_language(audio_bytes, sample_rate).text

    def transcribe_audio_bytes_with_language(self, audio_bytes: bytes, sample_rate: int = 44100) -> TranscriptionResult:
        """将音频字节转录为文字，并返回 Whisper 检测到的语言。"""
        if not self._initialized:
            self.initialize()

        # 将字节转换为 numpy 数组
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0

        # 重采样到 16kHz（Whisper 要求）
        audio_array = self._resample_to_16k(audio_array, sample_rate)
        audio_array = self._normalize_for_transcription(audio_array)

        # 转录
        start_time = time.time()
        language = None if self.config.language in (None, "", "auto") else self.config.language
        initial_prompt = self._initial_prompt()
        segments, info = self._model.transcribe(
            audio_array,
            language=language,
            beam_size=self.config.beam_size,
            vad_filter=self.config.vad_filter,
            vad_parameters=self.config.vad_parameters if self.config.vad_filter else None,
            initial_prompt=initial_prompt,
            condition_on_previous_text=self.config.condition_on_previous_text,
            temperature=self.config.temperature,
            no_speech_threshold=self.config.no_speech_threshold,
            log_prob_threshold=self.config.log_prob_threshold,
            compression_ratio_threshold=self.config.compression_ratio_threshold
        )

        # 合并所有片段
        text_parts = []
        for segment in segments:
            text_parts.append(segment.text.strip())

        full_text = " ".join(text_parts)
        elapsed = time.time() - start_time

        detected_language = getattr(info, "language", "") or ""
        language_probability = float(getattr(info, "language_probability", 0.0) or 0.0)
        logger.debug(
            "转录完成: {} 字符, language={}, prob={:.2f}, 耗时: {:.2f}s",
            len(full_text),
            detected_language,
            language_probability,
            elapsed
        )
        return TranscriptionResult(full_text, detected_language, language_probability)

    def transcribe_audio_file(self, audio_file: str) -> str:
        """转录音频文件"""
        if not self._initialized:
            self.initialize()

        start_time = time.time()
        language = None if self.config.language in (None, "", "auto") else self.config.language
        initial_prompt = self._initial_prompt()
        segments, info = self._model.transcribe(
            audio_file,
            language=language,
            beam_size=self.config.beam_size,
            vad_filter=self.config.vad_filter,
            vad_parameters=self.config.vad_parameters if self.config.vad_filter else None,
            initial_prompt=initial_prompt,
            condition_on_previous_text=self.config.condition_on_previous_text,
            temperature=self.config.temperature,
            no_speech_threshold=self.config.no_speech_threshold,
            log_prob_threshold=self.config.log_prob_threshold,
            compression_ratio_threshold=self.config.compression_ratio_threshold
        )

        text_parts = []
        for segment in segments:
            text_parts.append(segment.text.strip())

        full_text = " ".join(text_parts)
        elapsed = time.time() - start_time

        logger.info(f"文件转录完成: {len(full_text)} 字符, 耗时: {elapsed:.2f}s")
        return full_text

    async def transcribe_async(self, audio_bytes: bytes, sample_rate: int = 44100) -> str:
        """异步转录"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.transcribe_audio_bytes, audio_bytes, sample_rate
        )

    def get_model_info(self) -> dict:
        """获取模型信息"""
        if not self._initialized:
            return {"status": "not_initialized"}
        return {
            "model_size": self.config.model_size,
            "device": self.config.device,
            "compute_type": self.config.compute_type,
            "language": self.config.language,
            "prompt_profile": self.config.prompt_profile,
        }

    def cleanup(self):
        """清理资源"""
        self._model = None
        self._initialized = False


# VAD 参数配置
DEFAULT_VAD_PARAMS = {
    "threshold": 0.5,
    "min_speech_duration_ms": 250,
    "max_speech_duration_s": 8,
    "min_silence_duration_ms": 2000,
    "speech_pad_ms": 400
}


def sanitize_vad_parameters(vad_parameters: Optional[dict]) -> Optional[dict]:
    if not vad_parameters:
        return vad_parameters
    if VadOptions is None:
        return dict(vad_parameters)
    try:
        supported_keys = set(inspect.signature(VadOptions).parameters)
    except Exception:
        return dict(vad_parameters)
    cleaned = {
        key: value
        for key, value in dict(vad_parameters).items()
        if key in supported_keys
    }
    removed = sorted(set(vad_parameters) - set(cleaned))
    if removed:
        logger.debug("忽略当前 faster-whisper 不支持的 VAD 参数: {}", ", ".join(removed))
    return cleaned


def _load_librosa():
    global _LIBROSA, _LIBROSA_IMPORT_FAILED
    if _LIBROSA is not None:
        return _LIBROSA
    if _LIBROSA_IMPORT_FAILED:
        raise RuntimeError("librosa 不可用")
    try:
        import librosa
    except Exception:
        _LIBROSA_IMPORT_FAILED = True
        raise
    _LIBROSA = librosa
    return _LIBROSA


def is_likely_asr_hallucination(text: str) -> bool:
    normalized = " ".join((text or "").strip().casefold().split())
    if not normalized:
        return True
    if normalized in ASR_HALLUCINATION_PATTERNS:
        return True
    return any(pattern in normalized for pattern in ASR_HALLUCINATION_PATTERNS)
