from . import ModelTest
from auxify.models import users
import aiosqlite
from sqlite3 import IntegrityError
from unittest.async_case import IsolatedAsyncioTestCase

class TestUsers(ModelTest, IsolatedAsyncioTestCase):

    async def test_create_user(self):
        """tests that the correct data is persisted"""
        test_user = {
            "first_name": "MyFirst",
            "last_name": "TestUser",
            "email": "test",
            "password_hash": "test"
        }
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            user_model = users.UsersPersistence(db)
            user_id = await user_model.create_user(**test_user)
            stored_data = await user_model.get_user_by_id(user_id)
            self.assertEqual(user_id, stored_data["user_id"])
            for key in test_user:
                self.assertIn(key, stored_data)
                self.assertEqual(test_user[key], stored_data[key])

    async def test_collision_on_email(self):
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            user_model = users.UsersPersistence(db)
            test_user = {
                "first_name": "MyFirst",
                "last_name": "TestUser",
                "email": "abc",
                "password_hash": "test"
            }
            await user_model.create_user(**test_user)
            with self.assertRaises(IntegrityError):
                await user_model.create_user(**test_user)

    async def test_get_user_by_id(self):
        user = await self.random_new_user()
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            user_model = users.UsersPersistence(db)
            stored_data = await user_model.get_user_by_id(user["user_id"])
            for key in user:
                self.assertIn(key, stored_data)
                self.assertEqual(user[key], stored_data[key])

    async def test_get_user_by_id_does_not_exist(self):
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            user_model = users.UsersPersistence(db)
            stored_data = await user_model.get_user_by_id(9999999)
            self.assertEqual(stored_data, {})

    async def test_get_user_by_email(self):
        user = await self.random_new_user()
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            user_model = users.UsersPersistence(db)
            stored_data = await user_model.get_user_by_email(user["email"])
            for key in user:
                self.assertIn(key, stored_data)
                self.assertEqual(user[key], stored_data[key])

    async def test_get_user_by_email_does_not_exist(self):
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            user_model = users.UsersPersistence(db)
            stored_data = await user_model.get_user_by_email("blahblahblahfakeblah")
            self.assertEqual(stored_data, {})