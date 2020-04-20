from routes import get, post, put, login_required
from aiohttp.web import Request, Response
from schema.auth import register_user_schema, login_schema
from typing import Dict
from controllers import auth, spotify
import config
import models
from databases import Database


@post("/register", accepts_body=True, body_schema=register_user_schema)
async def register_user(request: Request, body: Dict) -> Dict:
    return await auth.register_user(
        body["first_name"],
        body["last_name"],
        body["email"],
        body["password"],
        config.CONFIG)


@get("/callback")
async def callback(request: Request) -> Dict:
    return await spotify.handle_spotify_callback(dict(request.query), config.CONFIG)


@get("/spotify_auth")
@login_required
async def spotify_auth(request: Request, claims: Dict):
    await spotify.spotify_auth(int(claims["sub"]), config.CONFIG)


@post("/login", accepts_body=True, body_schema=login_schema)
async def login(request: Request, body: Dict) -> Dict:
    return await auth.login(body["email"], body["password"], config.CONFIG)


@get("/me")
@login_required
async def me(request: Request, claims: Dict) -> Dict:
    return await auth.me(int(claims["sub"]), config.CONFIG)
