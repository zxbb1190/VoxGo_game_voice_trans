UI_LANGUAGE_ZH = "zh-CN"
UI_LANGUAGE_EN = "en-US"
UI_LANGUAGE_JA = "ja-JP"
UI_LANGUAGE_KO = "ko-KR"
UI_LANGUAGE_RU = "ru-RU"

UI_LANGUAGE_OPTIONS = (
    (UI_LANGUAGE_ZH, "简体中文"),
    (UI_LANGUAGE_EN, "English"),
    (UI_LANGUAGE_JA, "日本語"),
    (UI_LANGUAGE_KO, "한국어"),
    (UI_LANGUAGE_RU, "Русский"),
)

UI_LANGUAGE_LABELS = dict(UI_LANGUAGE_OPTIONS)


def system_ui_language() -> str:
    """New installs only; preserve the existing Chinese territory policy."""
    from PyQt5.QtCore import QLocale
    name = QLocale.system().name()
    if name in ('zh_CN', 'zh_TW'):
        return UI_LANGUAGE_ZH
    return {'ja': UI_LANGUAGE_JA, 'ko': UI_LANGUAGE_KO, 'ru': UI_LANGUAGE_RU}.get(name.split('_')[0], UI_LANGUAGE_EN)


def normalize_ui_language(value: str) -> str:
    text = str(value or "").strip().lower().replace("_", "-")
    aliases = {
        "": UI_LANGUAGE_ZH,
        "zh": UI_LANGUAGE_ZH,
        "zh-cn": UI_LANGUAGE_ZH,
        "cn": UI_LANGUAGE_ZH,
        "chinese": UI_LANGUAGE_ZH,
        "simplified chinese": UI_LANGUAGE_ZH,
        "简体中文": UI_LANGUAGE_ZH,
        "中文": UI_LANGUAGE_ZH,
        "en": UI_LANGUAGE_EN,
        "en-us": UI_LANGUAGE_EN,
        "english": UI_LANGUAGE_EN,
        "us": UI_LANGUAGE_EN,
        "英文": UI_LANGUAGE_EN,
        "英语": UI_LANGUAGE_EN,
        "ja": UI_LANGUAGE_JA, "ja-jp": UI_LANGUAGE_JA, "jp": UI_LANGUAGE_JA,
        "japanese": UI_LANGUAGE_JA, "日本語": UI_LANGUAGE_JA, "日语": UI_LANGUAGE_JA,
        "ko": UI_LANGUAGE_KO, "ko-kr": UI_LANGUAGE_KO, "kr": UI_LANGUAGE_KO,
        "korean": UI_LANGUAGE_KO, "한국어": UI_LANGUAGE_KO, "韩语": UI_LANGUAGE_KO,
        "ru": UI_LANGUAGE_RU, "ru-ru": UI_LANGUAGE_RU,
        "russian": UI_LANGUAGE_RU, "русский": UI_LANGUAGE_RU, "俄语": UI_LANGUAGE_RU,
    }
    return aliases.get(text, UI_LANGUAGE_ZH)


def is_english_ui(language: str) -> bool:
    return normalize_ui_language(language) == UI_LANGUAGE_EN


def ui_text(language: str, zh: str, en: str) -> str:
    language = normalize_ui_language(language)
    if language == UI_LANGUAGE_ZH:
        return zh
    return en if language == UI_LANGUAGE_EN else localize_text(language, en)


def language_label(code: str, ui_language: str = UI_LANGUAGE_ZH) -> str:
    labels = {
        UI_LANGUAGE_ZH: {"en": "英语", "zh": "中文", "ja": "日语", "ko": "韩语", "ru": "俄语"},
        UI_LANGUAGE_EN: {"en": "English", "zh": "Chinese", "ja": "Japanese", "ko": "Korean", "ru": "Russian"},
    }
    language = normalize_ui_language(ui_language)
    if language == UI_LANGUAGE_ZH:
        return labels[UI_LANGUAGE_ZH].get(code, code)
    return localize_text(language, labels[UI_LANGUAGE_EN].get(code, code))


def uses_english_source(language: str) -> bool:
    """Select existing English UI templates for catalog lookup, never an ASR route."""
    return normalize_ui_language(language) != UI_LANGUAGE_ZH


def localize_text(language: str, text: str) -> str:
    """Translate app-owned UI text only. Unknown/external content is preserved.

    Formatted message templates are matched in full, with each captured value
    preserved verbatim. No network, substring substitutions or user-text rewrite.
    """
    from voxgo.i18n_catalog import translate_message
    return translate_message(normalize_ui_language(language), str(text or ''))


def localized_output(language):
    """Localize the existing English branch of a UI formatter, including lists."""
    import functools
    import inspect
    def decorate(function):
        signature = inspect.signature(function)
        @functools.wraps(function)
        def wrapped(*args, **kwargs):
            code = language(*args, **kwargs) if callable(language) else signature.bind(*args, **kwargs).arguments.get(language, UI_LANGUAGE_ZH)
            def convert(value):
                if isinstance(value, str):
                    return value if normalize_ui_language(code) in (UI_LANGUAGE_ZH, UI_LANGUAGE_EN) else localize_text(code, value)
                if isinstance(value, (tuple, list)):
                    return type(value)(convert(v) for v in value)
                return value
            return convert(function(*args, **kwargs))
        return wrapped
    return decorate


def set_qt_ui_language(language):
    """Translate Qt-owned dialog buttons without changing system/data locales."""
    from PyQt5.QtCore import QTranslator
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        return
    previous = getattr(app, '_voxgo_ui_translator', None)
    code = normalize_ui_language(language)
    if previous and previous.language == code:
        return
    if previous:
        app.removeTranslator(previous)
        previous.deleteLater()
    from PyQt5.QtGui import QFont, QFontDatabase
    if not hasattr(app, '_voxgo_base_ui_font'):
        app._voxgo_base_ui_font = QFont(app.font())
    font = QFont(app._voxgo_base_ui_font)
    families = {UI_LANGUAGE_JA: ('Yu Gothic UI', 'Meiryo', 'Segoe UI'),
                UI_LANGUAGE_KO: ('Malgun Gothic', 'Segoe UI'), UI_LANGUAGE_RU: ('Segoe UI',)}
    if code in families:
        available = set(QFontDatabase().families())
        for family in families[code]:
            if family in available:
                font.setFamily(family)
                break
    app.setFont(font)
    class UiTranslator(QTranslator):
        def isEmpty(self):
            return False
        def translate(self, context, sourceText, disambiguation=None, n=-1):
            from voxgo.i18n_catalog import QT_MESSAGES
            if context in ('QDialogButtonBox', 'QMessageBox', 'QColorDialog', 'QPlatformTheme') and sourceText in QT_MESSAGES:
                return localize_text(language, sourceText)
            # An empty Python string is a *valid empty translation* to Qt,
            # which would blank unrelated standard widgets and button labels.
            return sourceText
    app._voxgo_ui_translator = UiTranslator(app)
    app._voxgo_ui_translator.language = code
    app.installTranslator(app._voxgo_ui_translator)
