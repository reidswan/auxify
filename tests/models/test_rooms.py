from . import ModelTest
from auxify.models import rooms, users
import aiosqlite
from unittest.async_case import IsolatedAsyncioTestCase

class TestRooms(ModelTest, IsolatedAsyncioTestCase):

    async def test_create_room_no_existing_rooms(self):
        """test creating a room when the user has no existing rooms"""
        user_id = (await self.get_or_create_user())["user_id"]
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            room_model = rooms.RoomPersistence(db)
            room_id = await room_model.create_room(user_id, "test_room_code", "test_room_name")

            room_data = await room_model.get_room(room_id)
            expected_room_data = {
                "room_id": room_id,
                "active": True,
                "owner_id": user_id,
                "room_code": "test_room_code",
                "room_name": "test_room_name"
            }
            for key in expected_room_data:
                self.assertIn(key, room_data)
                self.assertEqual(expected_room_data[key], room_data[key])

    async def test_create_room_deactivates_old_room(self):
        """test creating a room when the user has an existing rooms
        - the existing room should be deactivated"""
        user_id = (await self.get_or_create_user())["user_id"]
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            room_model = rooms.RoomPersistence(db)
            
            existing_room_id = await room_model.create_room(user_id, "test_room_code", "test_room_name_1")
            new_room_id = await room_model.create_room(user_id, "test_room_code_2","test_room_name_2")
            
            existing_room_data = await room_model.get_room(existing_room_id)
            self.assertFalse(existing_room_data["active"], "Existing room should have been deactivated")
            room_data = await room_model.get_room(new_room_id)
            expected_room_data = {
                "room_id": new_room_id,
                "active": True,
                "owner_id": user_id,
                "room_code": "test_room_code_2",
                "room_name": "test_room_name_2"
            }
            for key in expected_room_data:
                self.assertIn(key, room_data)
                self.assertEqual(expected_room_data[key], room_data[key])

    async def test_add_user_to_room(self):
        """tests adding a user to a room they do not own"""
        user_id = (await self.get_or_create_user())["user_id"]
        other_user = await self.random_new_user()
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            room_model = rooms.RoomPersistence(db)
            
            room_id = await room_model.create_room(user_id, "test_room_code", "test_room_name")
            await room_model.add_user_to_room(room_id, other_user["user_id"])

            is_user_in_room = await room_model.check_user_in_room(other_user["user_id"], room_id)
            self.assertTrue(is_user_in_room)

    async def test_user_not_in_room(self):
        """tests check_user_in_room does not assume new users are in rooms"""
        user_id = (await self.get_or_create_user())["user_id"]
        other_user = await self.random_new_user()
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            room_model = rooms.RoomPersistence(db)
            
            room_id = await room_model.create_room(user_id, "test_room_code", "test_room_name")

            is_user_in_room = await room_model.check_user_in_room(other_user["user_id"], room_id)
            self.assertFalse(is_user_in_room)

    async def test_remove_user_from_room(self):
        """tests that removing a user from a room results in the user not being in the room"""
        user_id = (await self.get_or_create_user())["user_id"]
        other_user = await self.random_new_user()
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            room_model = rooms.RoomPersistence(db)
            
            room_id = await room_model.create_room(user_id, "test_room_code", "test_room_name")
            await room_model.add_user_to_room(room_id, other_user["user_id"])

            is_user_in_room = await room_model.check_user_in_room(other_user["user_id"], room_id)
            self.assertTrue(is_user_in_room)

            # remove the user from the room and recheck
            await room_model.remove_user_from_room(room_id, other_user["user_id"])
            is_user_in_room = await room_model.check_user_in_room(other_user["user_id"], room_id)
            self.assertFalse(is_user_in_room)

    async def test_get_room_by_owner_returns_active_room(self):
        """tests that getting a room by owner_id returns the most recent active room"""
        user_id = (await self.get_or_create_user())["user_id"]
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            room_model = rooms.RoomPersistence(db)
            
            existing_room_id = await room_model.create_room(user_id, "test_room_code", "test_room_name")
            new_room_id = await room_model.create_room(user_id, "test_room_code_2", "test_room_name_2")
            
            room = await room_model.get_room_by_owner(user_id)
            self.assertTrue(room["active"])
            self.assertEqual(room["room_id"], new_room_id)

    async def test_get_owned_rooms_multiple_members(self):
        """tests that getting a room for a user only returns each room once"""
        user_id = (await self.get_or_create_user())["user_id"]
        other_user = await self.random_new_user()
        other_user_2 = await self.random_new_user()
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            room_model = rooms.RoomPersistence(db)
            
            new_room_id = await room_model.create_room(user_id, "test_room_code_2", "test_room_name_2")
            await room_model.add_user_to_room(new_room_id, other_user["user_id"])
            await room_model.add_user_to_room(new_room_id, other_user_2["user_id"])
            await room_model.add_user_to_room(new_room_id, user_id)
            
            joined_rooms = await room_model.get_joined_rooms_by_user(user_id)
            self.assertEqual(len(joined_rooms), 1)
            self.assertEqual(joined_rooms[0]["owner_id"], user_id)

    async def test_deactivate_sets_active_false(self):
        """test that deactivating a room stops it from being active"""
        user_id = (await self.get_or_create_user())["user_id"]
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            room_model = rooms.RoomPersistence(db)
            
            new_room_id = await room_model.create_room(user_id, "test_room_code_2", "test_room_name_2")
            await room_model.deactivate_room(new_room_id)

            room = await room_model.get_room(new_room_id)
            self.assertFalse(room["active"])

    async def test_deactivate_removes_room_from_joined_for_owner(self):
        """test that deactivating a room stops it from being returned in rooms for the owner"""
        user_id = (await self.get_or_create_user())["user_id"]
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            room_model = rooms.RoomPersistence(db)
            
            new_room_id = await room_model.create_room(user_id, "test_room_code_2", "test_room_name_2")
            await room_model.deactivate_room(new_room_id)

            joined_rooms = await room_model.get_joined_rooms_by_user(user_id)
            self.assertFalse(any(room["room_id"] == new_room_id for room in joined_rooms))
    
    async def test_deactivate_removes_room_from_joined_for_non_owner(self):
        """test that deactivating a room stops it from being returned in rooms for the owner"""
        user_id = (await self.get_or_create_user())["user_id"]
        other_user = await self.random_new_user()
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            room_model = rooms.RoomPersistence(db)
            
            new_room_id = await room_model.create_room(user_id, "test_room_code_2", "test_room_name_2")
            await room_model.add_user_to_room(new_room_id, other_user["user_id"])
            await room_model.deactivate_room(new_room_id)

            joined_rooms = await room_model.get_joined_rooms_by_user(other_user["user_id"])
            self.assertFalse(any(room["room_id"] == new_room_id for room in joined_rooms))
            