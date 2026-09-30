"""Detect extreme repeated-word output from ASR without a reference transcript.

This is a conservative guard for obvious decoding failures. It is not intended to
judge ordinary disfluencies or to replace transcript scoring against a reference.
"""

from dataclasses import dataclass
import math
import re


_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:['’][A-Za-z0-9]+)*")
_MAX_NGRAM_WORDS = 12
_MIN_ABNORMAL_WORD_COUNT = 24
_MIN_MULTIWORD_REPEAT_SPAN = 20
_MIN_MULTIWORD_REPEAT_COUNT = 4
_MIN_SINGLE_WORD_REPEAT_COUNT = 12
_MIN_WORDS_PER_SECOND = 8.0


@dataclass(frozen=True)
class RepetitionAnalysis:
    """Summary of the strongest adjacent repeated n-gram in a transcript."""

    word_count: int
    max_repeat_count: int
    max_repeat_span_words: int
    repeated_ngram_words: int


def _tokens(text: str) -> list[str]:
    # Apostrophes and punctuation are formatting here; compare word content only.
    return [match.group(0).lower().replace("'", "").replace("’", "") for match in _WORD_RE.finditer(text)]


def _repeated_runs(words: list[str]):
    """Yield ``(span_words, repeat_count, ngram_words)`` for every repeated run."""
    max_n = min(_MAX_NGRAM_WORDS, len(words))
    for ngram_words in range(1, max_n + 1):
        # lcp[i] is the number of equal words beginning at i and i+n. Filling
        # it backwards finds each repeated run in linear time for this n-gram.
        lcp = [0] * (len(words) + 1)
        for start in range(len(words) - ngram_words - 1, -1, -1):
            if words[start] == words[start + ngram_words]:
                lcp[start] = 1 + lcp[start + 1]
        for start in range(len(words) - ngram_words + 1):
            count = 1 + lcp[start] // ngram_words
            if count > 1:
                yield ngram_words * count, count, ngram_words


def analyze_repetition(text: str) -> RepetitionAnalysis:
    """Analyze contiguous exact repetitions of 1-12 Latin-word n-grams.

    Repetition counts use adjacent, non-overlapping copies of each n-gram. The
    reported candidate maximizes covered span, then repeat count, then n-gram
    length, providing a deterministic summary when runs tie.
    """
    words = _tokens(text if isinstance(text, str) else "")
    best_span = best_count = best_n = 0
    for span, count, ngram_words in _repeated_runs(words):
        if (span, count, ngram_words) > (best_span, best_count, best_n):
            best_span, best_count, best_n = span, count, ngram_words

    return RepetitionAnalysis(
        word_count=len(words),
        max_repeat_count=best_count,
        max_repeat_span_words=best_span,
        repeated_ngram_words=best_n,
    )


def is_runaway_repetition(
    text: str,
    duration_seconds: float = 0,
    compression_ratio: float = 0,
) -> bool:
    """Return whether text looks like an extreme Whisper repetition failure.

    A candidate must be long, cover a substantial repeated span, and repeat a
    multiword phrase at least four times or a single word at least twelve times.
    When audio duration is supplied, the transcript must also exceed 8 words/s.
    ``compression_ratio`` is accepted for integration with Whisper results, but
    is not used as a standalone signal; the repeated text must meet these gates.
    """
    analysis = analyze_repetition(text)
    if analysis.word_count < _MIN_ABNORMAL_WORD_COUNT:
        return False

    try:
        duration = float(duration_seconds or 0)
    except (TypeError, ValueError):
        duration = 0
    if math.isfinite(duration) and duration > 0:
        if analysis.word_count / duration < _MIN_WORDS_PER_SECOND:
            return False

    words = _tokens(text if isinstance(text, str) else "")
    return any(
        (ngram_words == 1
         and count >= _MIN_SINGLE_WORD_REPEAT_COUNT
         and span >= _MIN_SINGLE_WORD_REPEAT_COUNT)
        or (ngram_words > 1
            and span >= _MIN_MULTIWORD_REPEAT_SPAN
            and count >= _MIN_MULTIWORD_REPEAT_COUNT)
        for span, count, ngram_words in _repeated_runs(words)
    )
