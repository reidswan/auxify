from routes import get, post, put, login_required
from aiohttp.web import Request, Response
from schema.auth import register_user_schema, login_schema
from typing import Dict
from controllers import auth, spotify
import config
import models
from databases import Database


# @post("/me/password")
# async def change_password(...)
#   """Used to change password when logged in & password is known"""

# @post("/reset_password")
# async def reset_password(...)
#   """Used to send a password reset email"""

@get("/me")
@login_required
async def me(request: Request, claims: Dict) -> Dict:
    return await auth.me(int(claims["sub"]), config.Config.get_config())
