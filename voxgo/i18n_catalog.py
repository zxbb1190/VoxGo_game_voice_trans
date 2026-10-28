"""Exact catalog lookup for UI strings; formatted values stay verbatim."""
from functools import lru_cache
import re
from string import Formatter

from voxgo.i18n_messages import MESSAGES, QT_MESSAGES

_COLUMNS = {'zh-CN': 0, 'ja-JP': 1, 'ko-KR': 2, 'ru-RU': 3}
_ERROR_FIELDS = {'[Translation failed] {0}': 0, '[Translation error {0}] {1}': 1, 'Test failed: {0}': 0}
_OWNED_ERROR_DETAILS = {
    'Offline translation supports English and Chinese only',
    'Offline translation model is not ready; download it in Settings first',
    'Offline translation input is too long (maximum 256 tokens including language tag and EOS)',
    'API provider returned an error', 'Google Translation API returned an error',
}


@lru_cache(maxsize=1)
def _index():
    direct, templates = {}, []
    for english, translations in MESSAGES.items():
        sources = dict.fromkeys((english, *translations))
        for source in sources:
            direct.setdefault(source, english)
            parts, count, literal_size = [], 0, 0
            for literal, field, spec, conversion in Formatter().parse(source):
                parts.append(re.escape(literal))
                literal_size += len(literal)
                if field is not None:
                    if not field.isdigit():
                        raise ValueError('UI catalog fields must be numbered')
                    parts.append(f'(?P<p{field}>.*?)')
                    count += 1
            if count and literal_size >= 5:
                templates.append((literal_size, re.compile(''.join(parts), re.DOTALL), english))
    for english in MESSAGES:
        # Include unformatted templates as keys as well as their rendered forms.
        direct[english] = english
    return direct, sorted(templates, key=lambda row: row[0], reverse=True)


def translate_message(language, text):
    direct, templates = _index()
    def render(english):
        return english if language == 'en-US' else MESSAGES[english][_COLUMNS.get(language, 0)]
    english = direct.get(text)
    if english is not None:
        return render(english)
    # Only known full templates are matched. Captures (paths, model IDs, keys,
    # timings, provider details or a test's real translated text) are never edited.
    if len(text) <= 16000:
        for _, pattern, english in templates:
            match = pattern.fullmatch(text)
            if match:
                values = {int(key[1:]): value for key, value in match.groupdict().items()}
                detail = _ERROR_FIELDS.get(english)
                if detail is not None and direct.get(values[detail]) in _OWNED_ERROR_DETAILS:
                    values[detail] = render(direct[values[detail]])
                return render(english).format(*(values[i] for i in range(max(values)+1)))
    # Reports and model progress consist of independently owned labeled lines.
    # External diagnostics and release-note lines not in the catalog are left as-is.
    if '\n' in text:
        return '\n'.join(translate_message(language, line) for line in text.split('\n'))
    return text
