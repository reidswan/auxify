import aiohttp
from typing import Dict
import ujson

async def request_tokens(body: Dict, session: aiohttp.ClientSession)-> Dict:
    async with session.post("https://accounts.spotify.com/api/token", data=body) as resp:
        resp.raise_for_status()
        return await resp.json(loads=ujson.loads)

async def spotify_user_data(token: str, session: aiohttp.ClientSession)-> Dict:
    async with session.get("https://api.spotify.com/v1/me", headers={"Authorization": "Bearer " + token}) as resp:
        resp.raise_for_status()
        return await resp.json(loads=ujson.loads)