from databases import Database
from typing import Dict, Optional
from datetime import datetime


class SpotifyTokenPersistence:
    def __init__(self, db: Database):
        self.db = db

    async def upsert_token(self, user_id: int, spotify_user_id: str, access_token: str, refresh_token: Optional[str], created_at: datetime, duration_seconds: int)-> int:
        upsert_query = """
            INSERT INTO spotify_token (user_id, spotify_user_id, access_token, refresh_token, created_at, duration_seconds)
            VALUES (:user_id, :spotify_user_id, :access_token, :refresh_token, :created_at, :duration_seconds)
            ON DUPLICATE KEY UPDATE
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

        return await self.db.execute(query=upsert_query, values=params)

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

        result = await self.db.fetch_one(query=get_token, values=params)
        return dict(result) if result else {}