from aiosqlite import Connection
from typing import Dict, Optional
from datetime import datetime
from auxify.models import cast_key


class SpotifyTokenPersistence:
    def __init__(self, db: Connection):
        self.db = db

    async def upsert_token(self, user_id: int, spotify_user_id: str, access_token: str, refresh_token: Optional[str], created_at: datetime, duration_seconds: int)-> int:
        upsert_query = """
            INSERT INTO spotify_token (user_id, spotify_user_id, access_token, refresh_token, created_at, duration_seconds)
            VALUES (:user_id, :spotify_user_id, :access_token, :refresh_token, :created_at, :duration_seconds)
            ON CONFLICT (spotify_user_id) DO UPDATE SET
                access_token = :access_token,
                refresh_token = :refresh_token,
                created_at = :created_at,
                duration_seconds = :duration_seconds
        """

        params = {
            "user_id": user_id,
            "spotify_user_id": spotify_user_id,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "created_at": created_at,
            "duration_seconds": duration_seconds
        }

        result = await self.db.execute(upsert_query, params)
        await self.db.commit()
        return result.lastrowid

    @cast_key("created_at", datetime.fromisoformat)
    async def get_token_by_user(self, user_id: int)-> Dict:
        get_token = """
            SELECT token_id, user_id, spotify_user_id, access_token, refresh_token, created_at, duration_seconds
            FROM spotify_token
            WHERE user_id = :user_id 
            LIMIT 1
        """

        params = {
            "user_id": user_id
        }

        cursor = await self.db.execute(get_token, params)
        result = await cursor.fetchone()
        return dict(result) if result else {}