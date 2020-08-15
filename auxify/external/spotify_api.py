import aiohttp
from typing import Dict
import rapidjson
import logging
import base64


logger = logging.getLogger(__name__)

class SpotifyApi:
    def __init__(self, session: aiohttp.ClientSession, client_id: str, client_secret: str):
        self.session = session
        self.client_id = client_id
        self.client_secret = client_secret
        self.encoded_client_details = self._base64_encoded_client_details()

    def _base64_encoded_client_details(self)-> str:
        return base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()

    def client_auth_header(self)-> Dict:
        return {
            "Authorization": f"Basic {self.encoded_client_details}"
        }

    def user_auth_header(self, token)-> Dict:
        return {
            "Authorization": f"Bearer {token}"
        }

    async def request_tokens(self, body: Dict)-> Dict:
        async with self.session.post("https://accounts.spotify.com/api/token", data=body) as resp:
            resp.raise_for_status()
            return await resp.json(loads=rapidjson.loads)

    async def spotify_user_data(self, token: str)-> Dict:
        async with self.session.get("https://api.spotify.com/v1/me", headers=self.user_auth_header(token)) as resp:
            resp.raise_for_status()
            return await resp.json(loads=rapidjson.loads)

    async def refresh_tokens(self, refresh_token: str)-> Dict:
        request = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        async with self.session.post(
            "https://accounts.spotify.com/api/token",
            data=request,
            headers=self.client_auth_header()
        ) as resp:
            resp.raise_for_status()
            return await resp.json(loads=rapidjson.loads)

    async def enqueue_song(self, track_uri: str, token: str):
        request = {
            "uri": track_uri
        }
        headers = self.user_auth_header(token)
        # headers["Content-Type"] = "application/json"
        async with self.session.post(
            "https://api.spotify.com/v1/me/player/queue",
            headers=headers,
            params=request,
            json={} # sets Content-Type=application/json
        ) as resp:
            resp.raise_for_status()

