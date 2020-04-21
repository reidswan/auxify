from models import rooms
from config import Config
from typing import Optional, cast, Dict, Union
from controllers import spotify, err
from controllers.spotify import GetTokenError
import logging
from aiohttp.web_exceptions import HTTPException
from aiohttp.client_exceptions import ClientResponseError

logger = logging.getLogger(__name__)


def _handle_token_result(token_result: Union[str, GetTokenError])-> str:
    if isinstance(token_result, GetTokenError):
        if token_result == GetTokenError.EXPIRED:
            raise err.failed_dependency("Spotify token has expired")
        elif token_result == GetTokenError.NOT_AUTHED:
            raise err.failed_dependency("User must be authorized with Spotify to perform this operation")
        elif token_result == GetTokenError.API_ERROR:
            raise err.internal_server_error(token_result.value)
        else:
            raise err.internal_server_error()
    return token_result


async def create_room(user_id: int, room_code: Optional[str], config: Config) -> Dict:
    try:
        # only users that have auth'd with Spotify may create rooms
        token_result = await spotify.get_valid_token_for_user(user_id, config)
        token = _handle_token_result(token_result)

        async with config.get_database_connection() as db:
            room_persistence = rooms.RoomPersistence(db)
            room_id = await room_persistence.create_room(user_id, room_code)
            logger.debug("Created room(id=%s) for user(id=%s)",
                         room_id, user_id)
            created_room = await room_persistence.get_room(room_id)
            return created_room
    except Exception as e:
        logger.exception("Failed to create room for user %s: %s", user_id, e)
        raise e


async def get_owned_room_for_user(user_id: int, config: Config) -> Dict:
    try:
        async with config.get_database_connection() as db:
            room_persistence = rooms.RoomPersistence(db)
            room = await room_persistence.get_room_by_owner(user_id)
            return room
    except Exception as e:
        logger.exception("Failed to create room for user %s: %s", user_id, e)
        raise e


async def enqueue_song(user_id: int, room_id: int, track_uri: str, config: Config) -> Dict:
    try:
        async with config.get_database_connection() as db:
            room_persistence = rooms.RoomPersistence(db)
            room = await room_persistence.get_room(room_id)
            if not room:
                raise err.not_found(f"No room with id {room_id}")

            user_in_room = user_id == room["owner"] or await room_persistence.check_user_in_room(user_id, room_id)

            if not user_in_room:
                raise err.forbidden(f"User {user_id} is not permitted to play tracks in room {room_id}")

            token_result = await spotify.get_valid_token_for_user(room["owner"], config)
            token = _handle_token_result(token_result)

        await config.get_spotify_api().enqueue_song(track_uri, token)

        return {"success": True}

    except HTTPException:
        raise
    except ClientResponseError as e:
        logger.warning("Failed to enqueue track with Spotify for user %s in room %s: %s", user_id, room_id, e)
        if e.status == 403:
            raise err.forbidden("Unable to enqueue track: user is not a premium subscriber")
        if e.status == 404:
            raise err.not_found("The requested track could not be found")
        raise e
    except Exception as e:
        logger.exception(
            "Failed to play track for user(id=%s) in room(id=%s): %s", user_id, room_id, e)
        raise
