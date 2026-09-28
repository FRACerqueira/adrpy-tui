"""The interface's language packs (ADR005V01): one JSON file per language
adrpy supports, `en-us` being the reference."""

import json
import locale
import os
import sys
from importlib import resources

# adrpy's own list (`adrpy help init`, --language); tests/test_i18n.py
# checks the two match.
LANGUAGES = (
    "en-us", "pt-br", "de-de", "es-es", "fr-fr", "it-it", "ja-jp", "ko-kr", "nl-be", "ru-ru", "zh-cn",
)
DEFAULT_LANGUAGE = "en-us"


class Texts:
    def __init__(self, language, messages):
        self.language = language
        self._messages = messages

    def __call__(self, key, **params):
        return self._messages[key].format(**params)


def load(language):
    resource = resources.files("adrpy_tui.resources.language_packs").joinpath(f"{language}.json")
    return Texts(language, json.loads(resource.read_text(encoding="utf-8")))


def match_language(name):
    """The supported language closest to a locale name (`pt_BR.UTF-8`,
    `pt-BR`, `pt_PT`), or None: the exact language and region first, then
    the language alone."""
    if not name:
        return None
    code = name.split(".")[0].split("@")[0].replace("_", "-").lower()
    if code in LANGUAGES:
        return code
    language = code.split("-")[0]
    return next((supported for supported in LANGUAGES if supported.split("-")[0] == language), None)


def system_language():
    """The operating system's interface language, when it is a supported
    one, else the default."""
    for variable in ("LC_ALL", "LC_MESSAGES", "LANG"):
        found = match_language(os.environ.get(variable))
        if found:
            return found
    if sys.platform == "win32":
        import ctypes

        buffer = ctypes.create_unicode_buffer(85)
        if ctypes.windll.kernel32.GetUserDefaultLocaleName(buffer, len(buffer)):
            found = match_language(buffer.value)
            if found:
                return found
    return match_language(locale.getlocale()[0]) or DEFAULT_LANGUAGE
