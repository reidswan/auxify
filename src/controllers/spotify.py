from models import spotify_token
from controllers import err
import logging
from config import Config
from utils import jwt
from typing import Dict, Union
from urllib.parse import urlencode
from datetime import datetime, timedelta
from enum import Enum
import aiohttp.client_exceptions
from pymysql.err import DatabaseError

logger = logging.getLogger(__name__)

REQUIRED_SCOPES = "user-read-private user-read-email user-modify-playback-state"
PRE_EXPIRY_REFRESH_WINDOW = timedelta(minutes=1)

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
        tokens_response = await config.get_spotify_api().request_tokens(request)

        access_token = tokens_response["access_token"]
        refresh_token = tokens_response["refresh_token"]
        created_at = datetime.utcnow()
        expires_in = tokens_response["expires_in"]

        spotify_user_data = await config.get_spotify_api().spotify_user_data(access_token)
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
    

def is_token_expired(token: Dict)-> bool:
    now = datetime.utcnow()
    if not "created_at" in token or not "duration_seconds" in token:
        logger.warn("Spotify token for user %s did not have created_at or duration_seconds keys", token.get("user_id"))
        return True

    expires = token["created_at"] + timedelta(seconds=token["duration_seconds"]) - PRE_EXPIRY_REFRESH_WINDOW
    return expires <= now


class GetTokenError(Enum):
    NOT_AUTHED = "User has not authorized with Spotify"
    EXPIRED = "Auxify session with Spotify has expired; reauthorization with Spotify required"
    API_ERROR = "Something went wrong communicating with the Spotify API"
    DB_ERROR = "Something went wrong"


async def get_valid_token_for_user(user_id: int, config: Config)-> Union[str, GetTokenError]:
    try:
        async with config.get_database_connection() as db:
            token_persistence = spotify_token.SpotifyTokenPersistence(db)
            stored_token = await token_persistence.get_token_by_user(user_id)
            
            if not stored_token:
                # the user never auth'd
                return GetTokenError.NOT_AUTHED
            
            if not stored_token.get("access_token") and not stored_token.get("refresh_token"):
                # we're not in a position to use or refresh the token and need the user to re-auth
                return GetTokenError.EXPIRED

            if not is_token_expired(stored_token):
                return stored_token["access_token"]
            elif not stored_token.get("refresh_token"):
                # user session has expired and is not refreshable
                return GetTokenError.EXPIRED
            
            # we have a refresh token to use
            response = await config.get_spotify_api().refresh_tokens(stored_token["refresh_token"])
            created_at = datetime.utcnow()
 
            if not "access_token" in response:
                return GetTokenError.NOT_AUTHED

            await token_persistence.upsert_token(
                user_id,
                stored_token["spotify_user_id"],
                response["access_token"],
                response.get("refresh_token"),
                created_at, 
                response["expires_in"]
            )
            return response["access_token"]
    except aiohttp.client_exceptions.ClientResponseError as e:
        logger.exception("Something went wrong when refreshing tokens for user %s: %s", user_id, e)
        return GetTokenError.API_ERROR
    except DatabaseError as e:
        logger.exception("Something went wrong retrieving or storing tokens for user %s: %s", user_id, e)
        return GetTokenError.DB_ERROR
    