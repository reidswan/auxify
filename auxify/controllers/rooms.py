from typing import Optional, cast, Dict, Union
import logging
from aiohttp.web_exceptions import HTTPException
from aiohttp.client_exceptions import ClientResponseError
from aiosqlite import Connection

from auxify.models import rooms
from auxify.config import Config
from auxify.controllers import spotify, err
from auxify.controllers.spotify import GetTokenError


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


async def get_room_by_id(room_id: int, user_id: int, config: Config)-> Dict:
    """
    Delegates to the get_room_for_user_assertive method
    """
    try:
        async with config.get_database_connection() as db:
            return await get_room_for_user_assertive(room_id, user_id, db)
    except Exception as e:
        logger.exception("Failed to retrieve room %s for user %s: %s", room_id, user_id, e)
        raise e


async def get_room_for_user_assertive(room_id: int, user_id: int, db: Connection):
    """
    helper method to get a room if the room exists, is active, and the user is a member of it
    raises HTTPException if any condition fails
    """
    room_persistence = rooms.RoomPersistence(db)
    room = await room_persistence.get_room(room_id)
    if not room:
        raise err.not_found(f"No room with id {room_id}")

    user_in_room = user_id == room["owner_id"] or await room_persistence.check_user_in_room(user_id, room_id)

    if not user_in_room:
        raise err.forbidden(f"User {user_id} is not permitted to play tracks in room {room_id}")
    elif not room.get("active"):
        raise err.forbidden(f"Room {room_id} is no longer active")
    else:
        return room


async def create_room(user_id: int, room_code: Optional[str], room_name: str, config: Config) -> Dict:
    try:
        # only users that have auth'd with Spotify may create rooms
        token_result = await spotify.get_valid_token_for_user(user_id, config)
        token = _handle_token_result(token_result)

        async with config.get_database_connection() as db:
            room_persistence = rooms.RoomPersistence(db)
            room_id = await room_persistence.create_room(user_id, room_code, room_name)
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


async def get_joined_rooms_for_user(user_id: int, config: Config)-> Dict:
    """Get rooms which the user is a member of"""
    try:
        async with config.get_database_connection() as db:
            room_persistence = rooms.RoomPersistence(db)
            joined_rooms = await room_persistence.get_joined_rooms_by_user(user_id)
            return {"rooms": joined_rooms}
    except Exception as e:
        logger.exception("Failed to get rooms for user %s: %s", user_id, e)
        raise e


async def enqueue_song(user_id: int, room_id: int, track_uri: str, config: Config) -> Dict:
    try:
        async with config.get_database_connection() as db:
            room = await get_room_for_user_assertive(room_id, user_id, db)
            token_result = await spotify.get_valid_token_for_user(room["owner_id"], config, requested_by=user_id)
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


async def search(user_id: int, room_id: int, query: str, config: Config)-> Dict:
    logger.info("HERE")
    if not query:
        raise err.bad_request("No query string supplied to search for")
    
    try:
        async with config.get_database_connection() as db:
            room = await get_room_for_user_assertive(room_id, user_id, db)
            token_result = await spotify.get_valid_token_for_user(room["owner_id"], config, requested_by=user_id)
            token = _handle_token_result(token_result)

        search_results = await config.get_spotify_api().search(query, token)
        return {
            "results": extract_relevant_data_from_search_results(search_results)
        }
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


def extract_relevant_data_from_search_results(search_results: Dict):
    tracks = [
        track for track in search_results.get("tracks", {}).get("items", [])
        if track.get("is_playable") and "uri" in track
    ]
    return [{
        "name": track.get("name"),
        "artists": [{"name": artist.get("name")} for artist in track.get("artists", [])],
        "uri": track.get("uri"),
        "images": track.get("album", {}).get("images", [])
    } for track in tracks]