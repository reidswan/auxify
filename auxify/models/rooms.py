from aiosqlite import Connection
from typing import Dict, Optional, List
from datetime import datetime

from . import cast_key


class RoomPersistence:
    def __init__(self, db: Connection):
        self.db = db

    async def create_room(self, owner: int, room_code: Optional[str], room_name: str)-> int:
        deactivate_old_rooms = """
            UPDATE room
            SET active = :false
            WHERE owner_id = :owner
        """
        deactivate_old_room_params = {
            "false": False,
            "owner": owner
        }

        create_room = """
            INSERT INTO room (owner_id, active, room_code, room_name)
            VALUES (:owner, :true, :room_code, :room_name)
        """
        create_room_params = {
            "owner": owner,
            "true": True,
            "room_code": room_code,
            "room_name": room_name
        }

        async with self.db.cursor() as cur: # treats the block as a transaction
            await cur.execute(deactivate_old_rooms, deactivate_old_room_params)
            await cur.execute(create_room, create_room_params)
            await self.db.commit()
            return cur.lastrowid


    async def add_user_to_room(self, room_id: int, user_id: int):
        insert = """
            INSERT INTO room_member (room_id, user_id)
            VALUES (:room_id, :user_id)
            ON CONFLICT DO NOTHING
        """

        params = {
            "room_id": room_id,
            "user_id": user_id
        }

        await self.db.execute(insert, params)
        await self.db.commit()

    async def remove_user_from_room(self, room_id: int, user_id: int):
        delete_user = """
            DELETE FROM room_member 
            WHERE   user_id = :user_id
                AND room_id = :room_id
        """
        params = {
            "user_id": user_id,
            "room_id": room_id
        }

        await self.db.execute(delete_user, params)
        await self.db.commit()


    async def check_user_in_room(self, user_id: int, room_id: int)-> bool:
        query = """
            SELECT user_id
            FROM room_member
            WHERE   room_member.user_id = :user_id
                AND room_member.room_id = :room_id 
            LIMIT 1
        """
        params = {
            "user_id": user_id,
            "room_id": room_id
        }

        cursor = await self.db.execute(query, params)
        result = await cursor.fetchone()
        return bool(result)

    @cast_key("active", bool)
    async def get_room(self, room_id: int)-> Dict:
        query = """
            SELECT room_id, owner_id, active, created_at, room_code, room_name
            FROM room
            WHERE room_id = :room_id
            LIMIT 1
        """
        params = {
            "room_id": room_id
        }

        cursor = await self.db.execute(query, params)
        result = await cursor.fetchone()
        return dict(result) if result else {}
    
    @cast_key("active", bool)
    async def get_room_by_owner(self, owner_id: int)-> Dict:
        query = """
            SELECT room_id, owner_id, active, created_at, room_code, room_name
            FROM room
            WHERE owner_id = :owner
              AND active = :true
            ORDER BY created_at DESC
            LIMIT 1
        """
        params = {
            "owner": owner_id,
            "true": True
        }

        cursor = await self.db.execute(query, params)
        result = await cursor.fetchone()
        return dict(result) if result else {}

    async def get_joined_rooms_by_user(self, user_id: int)-> List[Dict]:
        query = """
            SELECT room.room_id as room_id, room.owner_id,
                   room.created_at, room.room_name as room_name
            FROM room
            LEFT JOIN room_member
            ON room_member.room_id = room.room_id
            WHERE (room_member.user_id = :user_id OR room.owner_id = :user_id)
              AND active = :true
            ORDER BY created_at DESC
        """
        params = {
            "user_id": user_id,
            "true": True
        }

        cursor = await self.db.execute(query, params)
        return [dict(row) for row in await cursor.fetchall()]

