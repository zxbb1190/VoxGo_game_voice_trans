"""CPU-only CTranslate2 inference; no HTTP or implicit model downloads."""
import asyncio
from collections import OrderedDict
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
import threading
import time

from .glossary import preprocess, postprocess
from .base import ProviderTestResult, TranslationRequest, TranslationResult, TranslatorProvider
from .local_models import DEFAULT_LOCAL_MODEL, LOCAL_MODELS, is_model_ready, model_path

# Shared executor prevents multiple providers from competing with game/ASR CPU.
_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="voxgo-local-translation")
_SLOTS = threading.BoundedSemaphore(2)
# Accessed only by the single executor thread. At most two loaded directions.
_ENGINES = OrderedDict()


def shutdown_local_translation():
    """Cancel queued inference and report native work that cannot be interrupted."""
    _EXECUTOR.shutdown(wait=False, cancel_futures=True)
    deadline = time.monotonic() + 3
    for thread in tuple(_EXECUTOR._threads):
        thread.join(timeout=max(0, deadline - time.monotonic()))
    return not any(thread.is_alive() for thread in _EXECUTOR._threads)


class LocalTranslationProvider(TranslatorProvider):
    name = "local"

    def __init__(self, config, model_root=None):
        super().__init__(config)
        self.model_root = model_root

    def requires_api_key(self):
        return False

    def _translate_sync(self, request, model_id=None):
        model_id = model_id or getattr(self.config, "local_model", DEFAULT_LOCAL_MODEL)
        direction = f"{request.source_lang}-{request.target_lang}"
        model = LOCAL_MODELS.get(model_id)
        if model is None or direction not in {d.direction for d in model.directions}:
            raise ValueError("Offline translation supports English ↔ Chinese only")
        path = model_path(model_id, self.model_root)
        try:
            signature = tuple((str((path / d.direction / f.name).resolve()),
                               (path / d.direction / f.name).stat().st_size,
                               (path / d.direction / f.name).stat().st_mtime_ns)
                              for d in model.directions for f in d.files)
        except OSError:
            signature = ()
        key = (str(path.resolve()), model_id, direction, signature)
        if key not in _ENGINES:
            if not is_model_ready(model_id, self.model_root):
                raise RuntimeError("Offline translation model is not ready; download it in Settings first")
            import ctranslate2
            import sentencepiece
            folder = path / direction
            translator = ctranslate2.Translator(str(folder), device="cpu", compute_type="int8", inter_threads=1, intra_threads=2)
            source = sentencepiece.SentencePieceProcessor(model_file=str(folder / "source.spm"))
            target = sentencepiece.SentencePieceProcessor(model_file=str(folder / "target.spm"))
            # Evict before retaining a new engine to bound steady-state RAM.
            while len(_ENGINES) >= 2:
                _ENGINES.popitem(last=False)
            _ENGINES[key] = (translator, source, target)
        _ENGINES.move_to_end(key)
        translator, source, target = _ENGINES[key]
        plan = preprocess(request.text, request.source_lang, request.target_lang)
        if plan.translated_override:
            return plan.translated_override
        tokens = source.encode(plan.normalized_text, out_type=str)
        if direction == "en-zh":
            tokens = [">>cmn_Hans<<"] + tokens
        if len(tokens) + 1 > 256:
            raise ValueError("Offline translation input is too long (maximum 256 tokens including language tag and EOS)")
        output = translator.translate_batch([tokens + ["</s>"]], beam_size=2, max_input_length=256, max_decoding_length=256)
        return postprocess(target.decode(output[0].hypotheses[0]), plan)

    async def translate(self, request, session=None):
        start = time.monotonic()
        if not _SLOTS.acquire(blocking=False):
            raise RuntimeError("Offline translator is busy; please try again")
        try:
            future = _EXECUTOR.submit(self._translate_sync, replace(request), getattr(self.config, "local_model", DEFAULT_LOCAL_MODEL))
        except BaseException:
            _SLOTS.release()
            raise
        future.add_done_callback(lambda _: _SLOTS.release())
        wrapped = asyncio.wrap_future(future)
        # Retrieve late failures too when the awaiting request already timed out.
        wrapped.add_done_callback(lambda done: None if done.cancelled() else done.exception())
        # Timeout/cancellation cannot kill native inference; keep its queue slot
        # occupied until completion to prevent unbounded retries and CPU work.
        translated = await asyncio.wait_for(asyncio.shield(wrapped), timeout=max(1.0, float(self.config.timeout_seconds)))
        return TranslationResult(translated, request.source_lang, request.target_lang, self.name, time.monotonic() - start)

    async def test(self):
        start = time.monotonic()
        try:
            source = getattr(self.config, "source_lang", "en")
            target = "en" if source == "zh" else "zh"
            text = "请在桥边等我。" if source == "zh" else "Please wait for me near the bridge."
            result = await self.translate(TranslationRequest(text, source or "en", target))
            return ProviderTestResult(bool(result.translated), result.translated, int((time.monotonic() - start) * 1000))
        except Exception as exc:
            return ProviderTestResult(False, str(exc), int((time.monotonic() - start) * 1000))
