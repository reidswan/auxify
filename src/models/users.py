from databases import Database
from typing import Dict


class UsersPersistence:
    def __init__(self, db: Database):
        self.db = db

    async def create_user(self, first_name: str, last_name: str, email: str, password_hash: str)-> int:
        create_query = """
            INSERT INTO user (first_name, last_name, email, password_hash)
            VALUES (:first_name, :last_name, :email, :password_hash)
        """

        params = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password_hash": password_hash
        }
        for key, value in params.items():
            if not value:
                raise Exception(f"parameter {key} may not be empty")

        return await self.db.execute(query=create_query, values=params)

    async def get_user_by_id(self, user_id: int) -> Dict:
        get_user = """
            SELECT user_id, first_name, last_name, email, password_hash
            FROM user
            WHERE user.user_id = :user_id 
            LIMIT 1
        """

        if user_id is None or user_id < 0:
            raise Exception(f"parameter user_id must be a positive integer")

        params = {
            "user_id": user_id
        }

        result = await self.db.fetch_one(query=get_user, values=params)
        return dict(result) if result else {}

    async def get_user_by_email(self, email_address: str) -> Dict:
        get_user_by_email = """
            SELECT user_id, first_name, last_name, email, password_hash
            FROM user
            WHERE user.email = :email 
            LIMIT 1
        """
        if not email_address:
            raise Exception(
                f"parameter email_address must be a non-empty string")

        params = {
            "email": email_address
        }
        
        result = await self.db.fetch_one(query=get_user_by_email, values=params)
        return dict(result) if result else {}
