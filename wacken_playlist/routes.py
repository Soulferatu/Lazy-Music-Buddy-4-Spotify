from flask import Blueprint, jsonify, render_template, request

from .lineup import WACKEN_2026_BANDS, WACKEN_2026_SOURCE_URLS


main = Blueprint("main", __name__)

APP_NAME = "Play[my W:O:A]list"

MESSAGES = {
    "en": {
        "playlist_name_required": "Name the playlist before previewing it.",
        "bands_required": "Select at least one Wacken 2026 band.",
    },
    "pt-BR": {
        "playlist_name_required": "Dê um nome à playlist antes de visualizar.",
        "bands_required": "Selecione pelo menos uma banda do Wacken 2026.",
    },
}


def normalize_language(language):
    return language if language in MESSAGES else "en"


def build_error(key, language):
    return {"key": key, "message": MESSAGES[language][key]}


@main.get("/")
def index():
    language = normalize_language(request.args.get("lang", "en"))
    return render_template(
        "index.html",
        app_name=APP_NAME,
        language=language,
        bands=WACKEN_2026_BANDS,
        source_urls=WACKEN_2026_SOURCE_URLS,
        preview=None,
        errors=[],
        form_values={"playlist_name": "", "bands": [], "language": language},
    )


@main.post("/preview")
def preview():
    selected_bands = request.form.getlist("bands")
    playlist_name = request.form.get("playlist_name", "").strip()
    language = normalize_language(request.form.get("language", "en"))
    valid_bands = [band for band in selected_bands if band in WACKEN_2026_BANDS]
    errors = []

    if not playlist_name:
        errors.append(build_error("playlist_name_required", language))
    if not valid_bands:
        errors.append(build_error("bands_required", language))

    preview_data = None
    if not errors:
        preview_data = {
            "playlist_name": playlist_name,
            "bands": valid_bands,
            "track_count": len(valid_bands) * 10,
        }

    return render_template(
        "index.html",
        app_name=APP_NAME,
        language=language,
        bands=WACKEN_2026_BANDS,
        source_urls=WACKEN_2026_SOURCE_URLS,
        preview=preview_data,
        errors=errors,
        form_values={
            "playlist_name": playlist_name,
            "bands": valid_bands,
            "language": language,
        },
    )


@main.get("/health")
def health():
    return jsonify({"status": "ok", "app": "wacken-playlist"})
