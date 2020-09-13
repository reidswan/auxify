from aiohttp.web import Request, Response
from typing import Dict

from auxify.controllers import rooms
from auxify.config import Config
from auxify.routes import get, post, put, login_required
from auxify.schema.rooms import create_room_schema, enqueue_song_schema, join_room_schema


@post("/rooms", accepts_body=True, body_schema=create_room_schema)
@login_required
async def create_room(request: Request, body: Dict, claims: Dict) -> Dict:
    return await rooms.create_room(int(claims["sub"]), body.get("room_code"), body["room_name"], Config.get_config())


@get("/rooms/owned")
@login_required
async def get_owned_room(request: Request, claims: Dict)-> dict:
    return await rooms.get_owned_room_for_user(int(claims["sub"]), Config.get_config())


@put("/rooms/{room_id:\d+}/queue", url_variable_types={"room_id": int},
     accepts_body=True, body_schema=enqueue_song_schema)
@login_required
async def enqueue_song(request: Request, room_id: int, body: Dict, claims: Dict) -> Dict:
    return await rooms.enqueue_song(int(claims["sub"]), room_id, body["uri"], Config.get_config())

@get("/rooms")
@login_required
async def get_rooms(request: Request, claims: Dict)-> Dict:
    return await rooms.get_joined_rooms_for_user(int(claims["sub"]), Config.get_config())


@get("/rooms/{room_id:\d+}/search", url_variable_types={"room_id": int})
@login_required
async def search(request: Request, room_id: int, claims: Dict)-> Dict:
    query = request.query.get("q")
    return await rooms.search(int(claims["sub"]), room_id, query, Config.get_config())


@get("/rooms/{room_id:\d+}", url_variable_types={"room_id": int})
@login_required
async def get_room_by_id(request: Request, room_id: int, claims: Dict)-> Dict:
    return await rooms.get_room_by_id(room_id, int(claims["sub"]), Config.get_config())


@get("/rooms/{room_id:\d+}/minimal", url_variable_types={"room_id": int})
@login_required
async def get_room_by_id_minimal(request: Request, room_id: int, claims: Dict)-> Dict:
    """Like /room/{room_id}, but with redactions & manipulations for secrecy; for users not in the room"""
    return await rooms.get_room_by_id_minimal(room_id, int(claims["sub"]), Config.get_config())


@put("/rooms/{room_id:\d+}/join", url_variable_types={"room_id": int}, accepts_body=True, body_schema=join_room_schema)
@login_required
async def join_room(request: Request, room_id: int, body: Dict, claims: Dict)-> Dict:
    room_code = None
    if body:
        room_code = body.get("room_code")
    return await rooms.join_room(int(claims["sub"]), room_id, room_code, Config.get_config()) 

