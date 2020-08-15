from aiohttp.web import Request, Response
from typing import Dict

from auxify.routes import get, post, put, login_required
from auxify.schema.auth import register_user_schema, login_schema
from auxify.controllers import auth, spotify
from auxify import config
from auxify import models



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
