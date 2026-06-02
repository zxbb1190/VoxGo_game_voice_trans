"""
音频捕获模块
使用 WASAPI Loopback 捕获系统音频输出
"""

import queue
import wave
from dataclasses import dataclass
from typing import Optional, Callable

import numpy as np
try:
    import pyaudiowpatch as pyaudio
    HAS_WASAPI_LOOPBACK = True
except ImportError:
    import pyaudio
    HAS_WASAPI_LOOPBACK = False
from loguru import logger


@dataclass
class AudioConfig:
    sample_rate: int = 16000
    channels: int = 1
    chunk_duration_ms: int = 30
    silence_threshold: float = -40.0
    speech_threshold_blocks: int = 8
    silence_limit_blocks: int = 20
    max_buffer_blocks: int = 500
    input_device_index: Optional[int] = None
    input_device_name: str = ""
    format: int = pyaudio.paInt16


def list_input_devices():
    """Return system-audio loopback devices first, then normal inputs."""
    audio = pyaudio.PyAudio()
    devices = []
    seen_indexes = set()

    def append_device(info, is_loopback=False):
        index = int(info.get("index"))
        if index in seen_indexes:
            return
        channels = int(info.get("maxInputChannels", 0) or 0)
        if channels <= 0:
            return
        seen_indexes.add(index)
        devices.append({
            "index": index,
            "name": info.get("name", ""),
            "channels": channels,
            "sample_rate": int(float(info.get("defaultSampleRate", 0) or 0)),
            "is_loopback": bool(is_loopback or info.get("isLoopbackDevice")),
        })

    try:
        if HAS_WASAPI_LOOPBACK and hasattr(audio, "get_loopback_device_info_generator"):
            for info in audio.get_loopback_device_info_generator():
                append_device(info, is_loopback=True)

        for index in range(audio.get_device_count()):
            info = audio.get_device_info_by_index(index)
            append_device(info)
    finally:
        audio.terminate()
    return devices


class SystemAudioCapture:
    """WASAPI Loopback 音频捕获"""

    def __init__(self, config: AudioConfig = None):
        self.config = config or AudioConfig()
        self._audio = pyaudio.PyAudio()
        self._stream: Optional[pyaudio.Stream] = None
        self._running = False
        self._audio_queue = queue.Queue()
        self._on_speech_callback: Optional[Callable] = None
        self._speech_buffer = []
        self._stream_channels = max(1, self.config.channels)
        self._capture_sample_rate = self.config.sample_rate
        self._silence_counter = 0
        self._speech_threshold = self.config.speech_threshold_blocks
        self._silence_limit = self.config.silence_limit_blocks
        self._energy_threshold = self.config.silence_threshold
        self._max_buffer_blocks = self.config.max_buffer_blocks

    def find_loopback_device(self) -> Optional[int]:
        """Find the configured or most likely system-audio input device."""
        configured = self._configured_device_candidates()
        if configured:
            selected = self._first_usable_device(configured)
            if selected is not None:
                return selected

        candidates = self._auto_device_candidates()
        selected = self._first_usable_device(candidates)
        if selected is not None:
            return selected

        logger.error("未找到可用音频输入设备")
        return None

    def _default_loopback_candidates(self):
        if not HAS_WASAPI_LOOPBACK:
            return []
        candidates = []

        if hasattr(self._audio, "get_default_wasapi_loopback"):
            try:
                info = self._audio.get_default_wasapi_loopback()
                candidates.append((int(info["index"]), info))
            except Exception as e:
                logger.debug("默认 WASAPI loopback 获取失败: {}", e)

        try:
            wasapi_info = self._audio.get_host_api_info_by_type(pyaudio.paWASAPI)
            default_output_index = wasapi_info.get("defaultOutputDevice")
            if default_output_index is not None and default_output_index >= 0:
                output_info = self._audio.get_device_info_by_index(default_output_index)
                if output_info.get("isLoopbackDevice"):
                    candidates.append((int(output_info["index"]), output_info))
                elif hasattr(self._audio, "get_loopback_device_info_generator"):
                    output_name = output_info.get("name", "")
                    for loopback in self._audio.get_loopback_device_info_generator():
                        if output_name and output_name in loopback.get("name", ""):
                            candidates.append((int(loopback["index"]), loopback))
                            break
        except Exception as e:
            logger.debug("默认输出设备 loopback 匹配失败: {}", e)

        unique = []
        seen = set()
        for index, info in candidates:
            if index not in seen:
                seen.add(index)
                unique.append((index, info))
        return unique

    def _configured_device_candidates(self):
        candidates = []
        configured_index = self.config.input_device_index
        configured_name = (self.config.input_device_name or "").strip().lower()

        if configured_index is not None:
            try:
                info = self._audio.get_device_info_by_index(int(configured_index))
                if int(info.get("maxInputChannels", 0) or 0) > 0:
                    candidates.append((int(configured_index), info))
            except Exception as e:
                logger.warning("已保存的音频设备索引不可用: {} ({})", configured_index, e)

        if configured_name:
            for index in range(self._audio.get_device_count()):
                info = self._audio.get_device_info_by_index(index)
                name = info.get("name", "")
                if int(info.get("maxInputChannels", 0) or 0) <= 0:
                    continue
                if configured_name == name.lower() or configured_name in name.lower():
                    if not any(item[0] == index for item in candidates):
                        candidates.append((index, info))

        return candidates

    def _auto_device_candidates(self):
        devices = []
        for index, info in self._default_loopback_candidates():
            devices.append((0, index, info))

        if HAS_WASAPI_LOOPBACK and hasattr(self._audio, "get_loopback_device_info_generator"):
            for info in self._audio.get_loopback_device_info_generator():
                devices.append((1, int(info["index"]), info))

        preferred_keywords = [
            "立体声混音", "stereo mix", "what u hear", "wave out",
            "cable", "voicemeeter", "virtual", "loopback", "monitor",
        ]
        for index in range(self._audio.get_device_count()):
            info = self._audio.get_device_info_by_index(index)
            if int(info.get("maxInputChannels", 0) or 0) <= 0:
                continue
            name = info.get("name", "")
            lowered = name.lower()
            preferred = any(keyword in lowered for keyword in preferred_keywords)
            score = 2 if preferred else 10
            devices.append((score, index, info))

        unique = []
        seen = set()
        for score, index, info in sorted(devices, key=lambda item: (item[0], item[1])):
            if index in seen:
                continue
            seen.add(index)
            unique.append((index, info))
        return unique

    def _stream_parameter_candidates(self, info):
        channels = int(info.get("maxInputChannels", 0) or 0)
        default_rate = int(float(info.get("defaultSampleRate", 0) or self.config.sample_rate))
        is_loopback = bool(info.get("isLoopbackDevice"))

        if is_loopback:
            # WASAPI loopback devices are most reliable at their native rate/channels.
            yield max(1, min(channels, 2)), default_rate
            yield 1, default_rate
            yield 1, self.config.sample_rate
        else:
            yield max(1, min(self.config.channels, channels)), self.config.sample_rate
            yield max(1, min(channels, 2)), default_rate

    def _first_usable_device(self, candidates) -> Optional[int]:
        for idx, info in candidates:
            for channels, sample_rate in self._stream_parameter_candidates(info):
                try:
                    test_stream = self._audio.open(
                        format=self.config.format,
                        channels=channels,
                        rate=sample_rate,
                        input=True,
                        input_device_index=idx,
                        frames_per_buffer=512,
                    )
                    test_stream.close()
                    self._stream_channels = channels
                    self._capture_sample_rate = sample_rate
                    device_type = "系统声音" if info.get("isLoopbackDevice") else "输入设备"
                    logger.info(
                        "选中{} [{}]: {} ({}Hz/{}ch)",
                        device_type,
                        idx,
                        info.get("name", ""),
                        sample_rate,
                        channels,
                    )
                    return idx
                except Exception as e:
                    logger.warning(
                        "音频设备 [{}] 不可用: {} ({}Hz/{}ch, {})",
                        idx,
                        info.get("name", ""),
                        sample_rate,
                        channels,
                        e,
                    )
        return None

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """音频回调"""
        if status:
            logger.warning(f"音频状态: {status}")
        if self._stream_channels > 1:
            samples = np.frombuffer(in_data, dtype=np.int16)
            try:
                samples = samples.reshape(-1, self._stream_channels)
                mono = samples.mean(axis=1).astype(np.int16)
                in_data = mono.tobytes()
            except ValueError:
                logger.warning("音频通道数据长度异常，按原始数据处理")
        self._audio_queue.put(in_data)
        return (None, pyaudio.paContinue)

    def start(self):
        """开始音频捕获"""
        device_index = self.find_loopback_device()
        if device_index is None:
            raise RuntimeError("未找到可用的音频输入设备")

        self.config.sample_rate = self._capture_sample_rate
        self.config.channels = 1
        self._stream = self._audio.open(
            format=self.config.format,
            channels=self._stream_channels,
            rate=self._capture_sample_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=int(
                self._capture_sample_rate * self.config.chunk_duration_ms / 1000
            ),
            stream_callback=self._audio_callback,
        )

        self._running = True
        self._stream.start_stream()
        logger.info("音频捕获已启动: {}Hz/{}ch -> mono", self._capture_sample_rate, self._stream_channels)

    def stop(self):
        """停止音频捕获"""
        self._running = False
        if self._stream:
            try:
                self._stream.stop_stream()
            except Exception:
                pass
            try:
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        if self._audio:
            self._audio.terminate()
        logger.info("音频捕获已停止")

    def set_speech_callback(self, callback: Callable):
        """设置语音检测回调"""
        self._on_speech_callback = callback

    def process_audio(self) -> Optional[bytes]:
        """处理音频队列，检测语音片段"""
        frames = []
        while not self._audio_queue.empty():
            try:
                data = self._audio_queue.get_nowait()
                frames.append(data)
            except queue.Empty:
                break

        if not frames:
            return None

        audio_data = b"".join(frames)
        logger.debug(f'收到音频块: {len(audio_data)} 字节')

        # 基于能量的语音活动检测（固定阈值高于视频背景音）
        audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
        if len(audio_np) == 0:
            return None
        rms = 20 * np.log10(np.sqrt(np.mean(audio_np ** 2)) + 1e-10)
        is_speech = rms > self._energy_threshold
        logger.debug(f'RMS: {rms:.1f} dB, 阈值: {self._energy_threshold}, 语音: {is_speech}')

        if is_speech:
            self._speech_buffer.append(audio_data)
            self._silence_counter = 0
            logger.debug(f'语音缓冲区: {len(self._speech_buffer)} 块')
            # 防止缓冲区无限增长
            if len(self._speech_buffer) > self._max_buffer_blocks:
                logger.warning('缓冲区超过上限，强制切分语音片段')
                speech_data = b"".join(self._speech_buffer)
                self._speech_buffer.clear()
                self._silence_counter = 0
                if self._on_speech_callback:
                    self._on_speech_callback(speech_data)
                return speech_data
        elif self._speech_buffer:
            self._silence_counter += 1
            logger.debug(f'静音计数: {self._silence_counter}/{self._silence_limit}')
            if (self._silence_counter >= self._silence_limit
                    and len(self._speech_buffer) < self._speech_threshold):
                logger.debug(f'丢弃过短片段: {len(self._speech_buffer)} 块')
                self._speech_buffer.clear()
                self._silence_counter = 0

        # 检测语音片段结束
        if (self._silence_counter >= self._silence_limit
                and len(self._speech_buffer) >= self._speech_threshold):
            speech_data = b"".join(self._speech_buffer)
            logger.info(f'检测到语音片段: {len(speech_data)} 字节, {len(self._speech_buffer)} 块')
            self._speech_buffer.clear()
            self._silence_counter = 0

            if self._on_speech_callback:
                self._on_speech_callback(speech_data)

            return speech_data

        return None

    def save_audio(self, data: bytes, filepath: str):
        """保存音频到文件"""
        with wave.open(filepath, "wb") as wf:
            wf.setnchannels(self.config.channels)
            wf.setsampwidth(self._audio.get_sample_size(self.config.format))
            wf.setframerate(self.config.sample_rate)
            wf.writeframes(data)
