from databases import Database
from typing import Dict, Optional
from datetime import datetime
from models import cast_key


class RoomPersistence:
    def __init__(self, db: Database):
        self.db = db

    async def create_room(self, owner: int, room_code: Optional[str])-> int:
        deactivate_old_rooms = """
            UPDATE room
            SET active = :false
            WHERE owner = :owner
        """
        deactivate_old_room_params = {
            "false": False,
            "owner": owner
        }

        create_room = """
            INSERT INTO room (owner, active, room_code)
            VALUES (:owner, :true, :room_code)
        """
        create_room_params = {
            "owner": owner,
            "true": True,
            "room_code": room_code
        }

        async with self.db.transaction():
            await self.db.execute(query=deactivate_old_rooms, values=deactivate_old_room_params)
            return await self.db.execute(query=create_room, values=create_room_params)


    async def add_user_to_room(self, room_id: int, user_id: int):
        insert = """
            INSERT IGNORE INTO room_member (room_id, user_id)
            VALUES (:room_id, :user_id)
        """

        params = {
            "room_id": room_id,
            "user_id": user_id
        }

        await self.db.execute(query=insert, values=params)

    async def remove_user_from_room(self, room_id: int, user_id: int):
        delete_user = """
            DELETE FROM room_member 
            WHERE   user_id = :user_id
                AND room_id = :room_id
            LIMIT 1
        """
        params = {
            "user_id": user_id,
            "room_id": room_id
        }

        await self.db.execute(query=delete_user, values=params)


    async def check_user_in_room(self, user_id: int, room_id: int)-> bool:
        query = """
            SELECT user_id
            FROM room
            WHERE   room.user_id = :user_id
                AND room.room_id = :room_id 
            LIMIT 1
        """
        params = {
            "user_id": user_id,
            "room_id": room_id
        }

        result = await self.db.fetch_one(query=query, values=params)
        return bool(result)

    @cast_key("active", bool)
    async def get_room(self, room_id: int)-> Dict:
        query = """
            SELECT room_id, owner, active, created_at, room_code
            FROM room
            WHERE room_id = :room_id
            LIMIT 1
        """
        params = {
            "room_id": room_id
        }

        result = await self.db.fetch_one(query=query, values=params)
        return dict(result) if result else {}
    
    @cast_key("active", bool)
    async def get_room_by_owner(self, owner_id: int)-> Dict:
        query = """
            SELECT room_id, owner, active, created_at, room_code
            FROM room
            WHERE owner = :owner
              AND active = :true
            LIMIT 1
        """
        params = {
            "owner": owner_id,
            "true": True
        }

        result = await self.db.fetch_one(query=query, values=params)
        if result:
            result = dict(result)
            result["active"] = bool(result["active"])
            return result
        else:
            return {}
