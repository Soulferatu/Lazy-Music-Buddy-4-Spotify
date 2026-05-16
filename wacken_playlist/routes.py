import logging
import secrets

from flask import (
    Blueprint,
    Response,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    session,
)

from .i18n import load_all_translations, load_translations, normalize_language
from .models import Band, PlaylistRequest
from .services import (
    NoMatchedTracksError,
    SpotifyAPIError,
    SpotifyAuthError,
    SpotifyConfigError,
)

logger = logging.getLogger(__name__)

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


def _default_context(language):
    return {
        "language": language,
        **_lineup_context(),
        "preview": None,
        "result": None,
        "errors": [],
        "form_values": {"playlist_name": "", "bands": [], "language": language},
    }


@main.get("/")
def index():
    language = normalize_language(request.args.get("lang", "en"))
    return _render(_default_context(language))


@main.post("/preview")
def preview():
    selected_bands = request.form.getlist("bands")
    playlist_name = request.form.get("playlist_name", "").strip()
    language = normalize_language(request.form.get("language", "en"))
    repo = current_app.lineup
    valid_names = [b for b in selected_bands if repo.is_valid_band(b, CURRENT_YEAR)]
    errors = []

    if not playlist_name:
        errors.append(build_error("playlist_name_required", language))
    if not valid_names:
        errors.append(build_error("bands_required", language))

    preview_view = None
    if not errors:
        playlist_request = PlaylistRequest(
            playlist_name=playlist_name,
            bands=[Band(name=name, year=CURRENT_YEAR) for name in valid_names],
            language=language,
        )
        try:
            preview = current_app.playlist_builder.build_preview(playlist_request)
        except SpotifyConfigError:
            errors.append(build_error("spotify_config_error", language))
            preview = None
        except SpotifyAuthError:
            errors.append(build_error("spotify_auth_error", language))
            preview = None
        except SpotifyAPIError:
            errors.append(build_error("spotify_api_error", language))
            preview = None

        if preview is not None:
            preview_view = {
                "playlist_name": preview.playlist_name,
                "bands": [b.name for b in preview.bands],
                "track_count": preview.track_count,
                "matched": [
                    {
                        "band": m.band.name,
                        "artist_name": m.artist_name,
                        "tracks": m.tracks,
                    }
                    for m in preview.matched
                ],
                "unmatched": preview.unmatched,
            }

    return _render({
        "language": language,
        **_lineup_context(),
        "preview": preview_view,
        "result": None,
        "errors": errors,
        "form_values": {
            "playlist_name": playlist_name,
            "bands": valid_names,
            "language": language,
        },
    })


@main.post("/create")
def create():
    selected_bands = request.form.getlist("bands")
    playlist_name = request.form.get("playlist_name", "").strip()
    language = normalize_language(request.form.get("language", "en"))
    repo = current_app.lineup
    valid_names = [b for b in selected_bands if repo.is_valid_band(b, CURRENT_YEAR)]
    errors = []

    if not playlist_name:
        errors.append(build_error("playlist_name_required", language))
    if not valid_names:
        errors.append(build_error("bands_required", language))

    result_view = None
    if not errors:
        playlist_request = PlaylistRequest(
            playlist_name=playlist_name,
            bands=[Band(name=name, year=CURRENT_YEAR) for name in valid_names],
            language=language,
        )
        try:
            result = current_app.playlist_builder.build_and_create(playlist_request)
            result_view = {
                "playlist_name": result.playlist_name,
                "spotify_url": result.spotify_url,
                "track_count": result.track_count,
                "skipped_bands": result.skipped_bands,
            }
        except SpotifyConfigError as e:
            logger.exception("Spotify config error during /create")
            key = (
                "spotify_refresh_token_missing"
                if "REFRESH_TOKEN" in str(e)
                else "spotify_config_error"
            )
            errors.append(build_error(key, language))
        except SpotifyAuthError:
            logger.exception("Spotify auth error during /create")
            errors.append(build_error("spotify_auth_error", language))
        except SpotifyAPIError:
            logger.exception("Spotify API error during /create")
            errors.append(build_error("spotify_api_error", language))
        except NoMatchedTracksError:
            errors.append(build_error("create_no_tracks_error", language))

    return _render({
        "language": language,
        **_lineup_context(),
        "preview": None,
        "result": result_view,
        "errors": errors,
        "form_values": {
            "playlist_name": playlist_name,
            "bands": valid_names,
            "language": language,
        },
    })


@main.get("/auth/spotify/login")
def spotify_login():
    """One-time setup: redirect the operator to Spotify to authorize the
    app-owned account. The resulting refresh token must be pasted into
    SPOTIFY_APP_REFRESH_TOKEN in .env. Only available when DEBUG is on.
    """
    if not current_app.config.get("DEBUG"):
        return Response("Not available outside development.", status=404)
    state = secrets.token_urlsafe(24)
    session["spotify_oauth_state"] = state
    try:
        url = current_app.spotify.build_authorize_url(state)
    except SpotifyConfigError as e:
        return Response(f"Spotify config error: {e}", status=500)
    return redirect(url)


@main.get("/auth/spotify/callback")
def spotify_callback():
    """Receive the auth code, exchange it for a refresh token, and display
    the value so the operator can paste it into .env. Dev-only."""
    if not current_app.config.get("DEBUG"):
        return Response("Not available outside development.", status=404)

    error = request.args.get("error")
    if error:
        return Response(f"Spotify returned an error: {error}", status=400)

    code = request.args.get("code")
    state = request.args.get("state")
    expected_state = session.pop("spotify_oauth_state", None)
    if not code or not state or state != expected_state:
        return Response(
            "Invalid OAuth state. Restart the flow at /auth/spotify/login.",
            status=400,
        )

    try:
        payload = current_app.spotify.exchange_code_for_refresh_token(code)
    except (SpotifyAuthError, SpotifyConfigError) as e:
        return Response(f"Token exchange failed: {e}", status=500)

    refresh_token = payload["refresh_token"]
    scope = payload.get("scope", "")
    body = (
        "<h1>Spotify app-owned account authorized</h1>"
        "<p>Copy the value below into your <code>.env</code> file as "
        "<code>SPOTIFY_APP_REFRESH_TOKEN</code>, then restart the dev "
        "server.</p>"
        f"<pre style='white-space:pre-wrap;word-break:break-all;"
        f"padding:1em;background:#eee'>{refresh_token}</pre>"
        f"<p><strong>Scopes granted:</strong> {scope}</p>"
        "<p>This page is shown once. Treat the token as a secret — do not "
        "commit it.</p>"
    )
    return Response(body, mimetype="text/html")


@main.get("/health")
def health():
    return jsonify({"status": "ok", "app": "wacken-playlist"})


@main.get("/service-worker.js")
def service_worker():
    response = current_app.response_class(
        render_template("service-worker.js"),
        mimetype="application/javascript",
    )
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache"
    return response
