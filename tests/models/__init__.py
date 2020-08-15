import sqlite3
import os
import aiosqlite
import random
from auxify.models import users

alpha = [chr(i) for i in range(ord('A'), ord('Z') + 1)] 
alpha += [i.lower() for i in alpha]

def _random_string(length):
    return ''.join(random.choices(alpha, k=length))

class ModelTest:
    db_name = "test.db"
    data_location = "schema/schema.sql"
    test_user = None

    @classmethod
    def setUpClass(cls):
        if os.path.exists(cls.db_name):
            os.remove(cls.db_name)

        with open(cls.data_location) as sql_schema:
            contents = sql_schema.read()
            with sqlite3.connect(cls.db_name) as db:
                db.executescript(contents)
                db.commit()

    @classmethod
    def tearDownClass(cls):
        os.remove(cls.db_name)
        cls.test_user = None

    async def get_or_create_user(self):
        """Convenience method for when a test only needs a single
        existing user"""
        if not ModelTest.test_user:    
            test_user = {
                "first_name": "John",
                "last_name": "Smith",
                "email": "test@example.com",
                "password_hash": "pwhash"
            }
            async with aiosqlite.connect(self.db_name) as db:
                db.row_factory = aiosqlite.Row
                user_model = users.UsersPersistence(db)
                user_id = await user_model.create_user(**test_user)
                test_user["user_id"] = user_id
                ModelTest.test_user = test_user
        
        return ModelTest.test_user

    async def random_new_user(self):
        """Convenience method that creates a user using random strings;
        attempts to generate a unique email address up to 3 times before failing"""
        test_user = {
            "first_name": _random_string(8),
            "last_name": _random_string(8),
            "email": _random_string(16),
            "password_hash": _random_string(8)
        }
        attempt = 1
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            user_model = users.UsersPersistence(db)
            while attempt < 3:
                if await user_model.get_user_by_email(test_user["email"]):
                    test_user["email"] = _random_string(16 + attempt)
                else:
                    break
                attempt += 1
            else:
                raise Exception("Failed to generate a unique random email address when creating a user")

            user_id = await user_model.create_user(**test_user)
            test_user["user_id"] = user_id
            return test_user