from __future__ import annotations

import rapidjson
from typing import Tuple
from jsonschema import validate
from jwcrypto import jwk
from os import getenv
import logging
from aiosqlite import Connection, connect, Row
import aiohttp

from auxify.utils import jwt
from auxify.external.spotify_api import SpotifyApi

ENV_LOG_LEVEL = "LOG_LEVEL"

config_schema = {
    "type": "object",
    "properties": {
        "spotify": {
            "type": "object",
            "properties": {
                "client_id": {"type": "string"},
                "secret": {"type": "string"},
                "redirect_url": {"type": "string"}
            },
            "required": ["client_id", "secret", "redirect_url"]
        },
        "jwt": {
            "type": "object",
            "properties": {
                "secret": {"type": "string"}
            },
            "required": ["secret"]
        },
        "db": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            }
        }
    }
}


class Config:
    _config = None

    @classmethod
    def configure(cls):
        cls._config = Config("Config.json")

    @classmethod
    def get_config(cls)-> Config:
        if cls._config is None:
            cls.configure()
        return cls._config # type: ignore

    def __init__(self, file_name: str):
        with open(file_name) as infile:
            self.data = rapidjson.loads(infile.read())
            validate(schema=config_schema, instance=self.data)

        self.jwk = jwt.key_from_secret(self.data["jwt"]["secret"])
        self.session = aiohttp.ClientSession()

    def database_location(self) -> str:
        return self.data["db"]["location"]

    def jwt_key(self) -> jwk.JWK:
        return self.jwk

    @staticmethod
    def configure_logging():
        try:
            loglevel_str = getenv(ENV_LOG_LEVEL, "INFO")
            loglevel = getattr(logging, loglevel_str)
        except:
            loglevel = logging.INFO
        
        logging.basicConfig(level=loglevel)

    def get_database_connection(self)-> Connection:
        connection = connect(self.database_location())
        connection.row_factory = Row
        return connection

    def get_session(self)-> aiohttp.ClientSession:
        if self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    def get_spotify_api(self)-> SpotifyApi:
        return SpotifyApi(self.get_session(), self.spotify_client_id(), self.spotify_secret())

    async def deferred_cleanup(self, _app):
        yield
        if self.session and not self.session.closed:
            await self.session.close()

    def spotify_client_id(self)-> str:
        return self.data["spotify"]["client_id"]

    def spotify_secret(self)-> str:
        return self.data["spotify"]["secret"]

    def spotify_redirect(self)-> str:
        return self.data["spotify"]["redirect_url"]

