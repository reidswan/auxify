from routes import get, post, put, login_required
from aiohttp.web import Request, Response
from schema.rooms import create_room_schema, enqueue_song_schema
from typing import Dict
from controllers import rooms
from config import Config


@post("/rooms", accepts_body=True, body_schema=create_room_schema)
@login_required
async def create_room(request: Request, body: Dict, claims: Dict) -> Dict:
    return await rooms.create_room(int(claims["sub"]), body.get("room_code"), Config.get_config())


@get("/rooms/owned")
@login_required
async def get_owned_room(request: Request, claims: Dict)-> dict:
    return await rooms.get_owned_room_for_user(int(claims["sub"]), Config.get_config())


@put("/rooms/{room_id:\d+}/enqueue", url_variable_types={"room_id": int},
     accepts_body=True, body_schema=enqueue_song_schema)
@login_required
async def enqueue_song(request: Request, room_id: int, body: Dict, claims: Dict) -> Dict:
    return await rooms.enqueue_song(int(claims["sub"]), room_id, body["uri"], Config.get_config())

