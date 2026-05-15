import pytest

from wacken_playlist.i18n import (
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    load_all_translations,
    load_translations,
    normalize_language,
)


@pytest.mark.parametrize("language", SUPPORTED_LANGUAGES)
def test_each_language_loads(language):
    bundle = load_translations(language)
    assert isinstance(bundle, dict)
    assert bundle, f"{language} bundle is empty"


def test_all_languages_share_the_same_keys():
    bundles = load_all_translations()
    reference_keys = set(bundles[DEFAULT_LANGUAGE].keys())
    for lang, bundle in bundles.items():
        assert set(bundle.keys()) == reference_keys, (
            f"{lang} has different keys than {DEFAULT_LANGUAGE}"
        )


def test_count_placeholder_present_in_pluralized_strings():
    for lang in SUPPORTED_LANGUAGES:
        bundle = load_translations(lang)
        assert "{count}" in bundle["band_count"]
        assert "{count}" in bundle["preview_tracks"]


def test_unknown_language_falls_back_to_default():
    assert load_translations("xx-YY") == load_translations(DEFAULT_LANGUAGE)
    assert normalize_language(None) == DEFAULT_LANGUAGE
    assert normalize_language("zz") == DEFAULT_LANGUAGE
    assert normalize_language("pt-BR") == "pt-BR"
