from routes import get, post, put
from aiohttp.web import Request, Response
from schema.rooms import create_room_schema, enqueue_song_schema
from typing import Dict


@post("/room", accepts_body=True, body_schema=create_room_schema)
async def create_room(request: Request, body: Dict) -> Dict:
    return body


@get("/room/{room_id:\d+}", url_variable_types={"room_id": int})
async def get_room(request: Request, room_id: int) -> Dict:
    return {"a": "B", "room_id": room_id}

@put("/room/{room_id:\d+}/enqueue", url_variable_types={"room_id": int},
     accepts_body=True, body_schema=enqueue_song_schema)
async def enqueue_song(request: Request, room_id: int, body: Dict) -> Dict:
    body['room_id'] = room_id
    return body

