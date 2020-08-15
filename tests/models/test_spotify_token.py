from . import ModelTest
from auxify.models import spotify_token
import aiosqlite
from sqlite3 import IntegrityError
from unittest.async_case import IsolatedAsyncioTestCase
from datetime import datetime

class TestUsers(ModelTest, IsolatedAsyncioTestCase):

    async def test_upsert_token_does_not_exist(self):
        """test upserting a token when one does not yet exist"""
        user = await self.get_or_create_user()
        token = {
            "user_id": user["user_id"],
            "spotify_user_id": "user1234",
            "access_token": "123abc",
            "refresh_token": None,
            "created_at": datetime.now(),
            "duration_seconds": 10000
        }
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            model = spotify_token.SpotifyTokenPersistence(db)
            await model.upsert_token(**token)
            stored_data = await model.get_token_by_user(user["user_id"])
            for key in token:
                self.assertIn(key, stored_data)
                self.assertEqual(token[key], stored_data[key])

    async def test_upsert_token_exists(self):
        """test upserting a token  when one does exist"""
        user = await self.get_or_create_user()
        token = {
            "user_id": user["user_id"],
            "spotify_user_id": "user1234",
            "access_token": "123abc",
            "refresh_token": None,
            "created_at": datetime.now(),
            "duration_seconds": 10000
        }
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            model = spotify_token.SpotifyTokenPersistence(db)
            await model.upsert_token(**token)
            token["duration_seconds"] = 100
            await model.upsert_token(**token)

            stored_data = await model.get_token_by_user(user["user_id"])
            for key in token:
                self.assertIn(key, stored_data)
                self.assertEqual(token[key], stored_data[key])

