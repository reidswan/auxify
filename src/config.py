import ujson
from typing import Tuple
from jsonschema import validate
from utils import jwt
from jwcrypto import jwk
from os import getenv
import logging
from databases import Database
import aiohttp

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
                "url": {"type": "string"},
                "connections": {
                    "type": "object",
                    "properties": {
                        "min": {"type": "number"},
                        "max": {"type": "number"}
                    },
                    "required": ["min", "max"]
                }
            }
        }
    }
}


class Config:
    def __init__(self, file_name: str):
        with open(file_name) as infile:
            self.data = ujson.loads(infile.read())
            validate(schema=config_schema, instance=self.data)

        self.jwk = jwt.key_from_secret(self.data["jwt"]["secret"])
        self.session = aiohttp.ClientSession()

    def database_url(self) -> str:
        return self.data["db"]["url"]

    def db_connections(self) -> Tuple[int, int]:
        connections = self.data["db"]["connections"]
        return (connections["min"], connections["max"])

    def jwt_key(self) -> jwk.JWK:
        return self.jwk

    @staticmethod
    def configure_logging():
        try:
            loglevel_str = os.getenv(ENV_LOG_LEVEL, "INFO")
            loglevel = getattr(logging, loglevel_str)
        except:
            loglevel = logging.INFO

        logging.basicConfig(level=loglevel)

    def get_database_connection(self)-> Database:
        min_size, max_size = self.db_connections()
        return Database(self.database_url(), min_size=min_size, max_size=max_size)

    def get_session(self)-> aiohttp.ClientSession:
        return self.session

    def spotify_client_id(self)-> str:
        return self.data["spotify"]["client_id"]

    def spotify_secret(self)-> str:
        return self.data["spotify"]["secret"]

    def spotify_redirect(self)-> str:
        return self.data["spotify"]["redirect_url"]

CONFIG: Config = None # type: ignore
