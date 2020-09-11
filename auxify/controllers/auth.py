import logging
from typing import Dict
from sqlite3 import IntegrityError
import bcrypt
import asyncio

from auxify.config import Config
from auxify.utils import jwt
from auxify.models import users, rooms
from auxify.controllers import err, spotify


logger = logging.getLogger(__name__)

async def login(email: str, password: str, config: Config)-> Dict:
    """
    Get user from DB, check password hash matches and return a JWT token if so
    """
    try:
        async with config.get_database_connection() as db:
            user = await users.UsersPersistence(db).get_user_by_email(email)
    except Exception as e:
        logger.exception("Failed to get user with email %s from db: %s", email, e)
        raise err.internal_server_error()

    auth_failed = err.unauthorized("Failed to log you in with the provided credentials; please try again")
    if not user:
        logger.debug("User not found with email %s", email)
        raise auth_failed
    
    if not bcrypt.checkpw(password.encode(), user["password_hash"]):
        logger.debug("Incorrect password for user(id=%s)", user["user_id"])
        raise auth_failed

    return {
        "token": jwt.generate_jwt(user["user_id"], jwt.Aud.AUTH, config.jwt_key())
    }


async def register_user(first_name: str, last_name: str, email: str, password: str, config: Config):
    if not check_password(password):
        raise err.bad_request("Please provide a password at least 8 characters long, containing letters and symbols")

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    try:
        async with config.get_database_connection() as db:
            user_persistence = users.UsersPersistence(db)
            created_user_id = await user_persistence.create_user(first_name, last_name, email, password_hash)
            user = await user_persistence.get_user_by_id(created_user_id)
    except IntegrityError as e:
        logger.debug("IntegrityError registering user with email %s: %s", email, e)
        raise err.bad_request("Email address is already in use")
    except Exception as e:
        logger.exception("Failed to get user with email %s from db: %s", email, e)
        raise err.internal_server_error()    

    return {
        "token": jwt.generate_jwt(user["user_id"], jwt.Aud.AUTH, config.jwt_key())
    }


async def me(user_id: int, config: Config)-> Dict:
    try:
        async with config.get_database_connection() as db:
            get_user = users.UsersPersistence(db).get_user_by_id(user_id)
            get_joined_rooms = rooms.RoomPersistence(db).get_joined_rooms_by_user(user_id)
            get_token = spotify.get_valid_token_for_user(user_id, config)
            (user, joined_rooms, token) = await asyncio.gather(get_user, get_joined_rooms,
                                                               get_token, return_exceptions=False)
    except Exception as e:
        logger.exception("Failed to get user(id=%s) from db: %s", user_id, e)
        raise err.internal_server_error()
    del user["password_hash"]
    user["rooms"] = joined_rooms
    user["authed_with_spotify"] = isinstance(token, str)
    return user


def check_password(password: str) -> bool:
    """
    Require that a password is at least 15 chars long, or if between 8 and 14 chars, contains
    an alphabetic and a non-alphabetic char
    """

    if len(password) >= 15:
        return True
    elif len(password) >= 8:
        return any(c.isalpha() for c in password) and any(not c.isalpha() for c in password)
    else:
        return False
