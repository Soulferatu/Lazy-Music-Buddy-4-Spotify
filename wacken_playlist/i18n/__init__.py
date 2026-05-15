from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

SUPPORTED_LANGUAGES = ("en", "pt-BR")
DEFAULT_LANGUAGE = "en"

_I18N_DIR = Path(__file__).parent


@lru_cache(maxsize=None)
def load_translations(language: str) -> dict[str, str]:
    """Load the translation bundle for a single language."""
    if language not in SUPPORTED_LANGUAGES:
        language = DEFAULT_LANGUAGE
    path = _I18N_DIR / f"{language}.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_all_translations() -> dict[str, dict[str, str]]:
    """Load every supported language. Used to inject the full client bundle."""
    return {lang: load_translations(lang) for lang in SUPPORTED_LANGUAGES}


def normalize_language(language: str | None) -> str:
    return language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
