from models import spotify_token
from controllers import err
import logging
from config import Config
from utils import jwt
from typing import Dict
from urllib.parse import urlencode
from external import spotify_api
from datetime import datetime

logger = logging.getLogger(__name__)

REQUIRED_SCOPES = "user-read-private user-read-email user-modify-playback-state"


async def spotify_auth(user_id: int, config: Config):
    """
    Initiate authentication with the spotify API
    """
    token = jwt.generate_jwt(user_id, jwt.Aud.API, config.jwt_key())
    query_parameters = {
        "response_type": "code",
        "client_id": config.spotify_client_id(),
        "scope": REQUIRED_SCOPES,
        "redirect_uri": config.spotify_redirect(),
        "state": token
    }
    query_string = urlencode(query_parameters)
    redirect = f"https://accounts.spotify.com/authorize?{query_string}"

    logger.debug("Redirecting user to %s", redirect)
    err.redirect_to(redirect)


async def handle_spotify_callback(query_params: Dict, config: Config):
    if query_params.get("error"):
        raise err.failed_dependency(
            "Please allow access to your Spotify account to proceed")
    token = query_params.get("state")
    if not token:
        raise err.bad_request(
            "'state' query parameter required but not provided")
    try:
        claims = jwt.get_claims_from_jwt(token, config.jwt_key(), jwt.Aud.API)
        user_id = int(claims["sub"])
    except Exception as e:
        logger.debug("Failed to decode state as JWT: %s", e)
        raise err.bad_request("Invalid state from Spotify callback")

    code = query_params.get("code")
    if not code:
        raise err.failed_dependency(
            "Spotify authorization failed; no valid code returned")

    request = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": config.spotify_redirect(),
        "client_id": config.spotify_client_id(),
        "client_secret": config.spotify_secret()
    }

    try:
        session = config.get_session()
        tokens_response = await spotify_api.request_tokens(request, session)

        access_token = tokens_response["access_token"]
        refresh_token = tokens_response["refresh_token"]
        created_at = datetime.utcnow()
        expires_in = tokens_response["expires_in"]

        spotify_user_data = await spotify_api.spotify_user_data(access_token, session)
        spotify_user_id = spotify_user_data["id"]
    except Exception as e:
        logger.exception("Failed to authorize user(id=%s): %s", user_id, e)
        raise err.internal_server_error(
            "Something went wrong logging in with Spotify")

    try:
        async with config.get_database_connection() as db:
            await spotify_token.SpotifyTokenPersistence(db).upsert_token(
                user_id,
                spotify_user_id,
                access_token,
                refresh_token,
                created_at,
                expires_in
            )
    except Exception as e:
        logger.exception(
            "Failed to upsert Spotify token for user(id=%s): %s", user_id, e)
        raise err.internal_server_error()
    
    return { "success": True }