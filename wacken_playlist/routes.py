from flask import Blueprint, current_app, jsonify, render_template, request

from .i18n import load_all_translations, load_translations, normalize_language

main = Blueprint("main", __name__)

APP_NAME = "Play[my W:O:A]list"
CURRENT_YEAR = 2026


def build_error(key, language):
    return {"key": key, "message": load_translations(language)[key]}


def _render(template_kwargs):
    language = template_kwargs["language"]
    return render_template(
        "index.html",
        app_name=APP_NAME,
        translations=load_translations(language),
        translations_bundle=load_all_translations(),
        **template_kwargs,
    )


def _lineup_context():
    repo = current_app.lineup
    return {
        "bands": repo.get_band_names(CURRENT_YEAR),
        "source_urls": repo.get_source_urls(CURRENT_YEAR),
    }


@main.get("/")
def index():
    language = normalize_language(request.args.get("lang", "en"))
    return _render({
        "language": language,
        **_lineup_context(),
        "preview": None,
        "errors": [],
        "form_values": {"playlist_name": "", "bands": [], "language": language},
    })


@main.post("/preview")
def preview():
    selected_bands = request.form.getlist("bands")
    playlist_name = request.form.get("playlist_name", "").strip()
    language = normalize_language(request.form.get("language", "en"))
    repo = current_app.lineup
    valid_bands = [b for b in selected_bands if repo.is_valid_band(b, CURRENT_YEAR)]
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

    return _render({
        "language": language,
        **_lineup_context(),
        "preview": preview_data,
        "errors": errors,
        "form_values": {
            "playlist_name": playlist_name,
            "bands": valid_bands,
            "language": language,
        },
    })


@main.get("/health")
def health():
    return jsonify({"status": "ok", "app": "wacken-playlist"})
