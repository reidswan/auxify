from aiohttp import web
from aiohttp.web import Request, Response, json_response
from typing import Mapping, Any
from controllers import err
from utils import jwt
import config
import logging
import ujson
import jsonschema

logger = logging.getLogger(__name__)

routes_tab = web.RouteTableDef()


def error(message: str, status: int) -> Response:
    return json_response({
        "error": True,
        "status": status,
        "message": message
    }, status=status, dumps=ujson.dumps)


def json_router(verb: str):
    register_route = routes_tab.__getattribute__(verb)

    def json_endpoint(url_pattern: str, url_variable_types: Mapping[str, type] = {}, accepts_body: bool = False, body_schema: Mapping[Any, Any] = None):
        def wrapper(f):
            @register_route(url_pattern)
            async def inner(request: Request):
                kwargs = {}
                for var, cast_type in url_variable_types.items():
                    try:
                        kwargs[var] = cast_type(request.match_info[var])
                    except Exception as e:
                        logger.debug(
                            "Treating %s as not found due to error: %s", request.url(), e)
                        return error(f"{request.url()} not found", 404)
                if accepts_body:
                    if not request.body_exists:
                        return error("Expected request body", 400)
                    body = await request.json()
                    if body_schema:
                        try:
                            jsonschema.validate(
                                instance=body, schema=body_schema)
                        except Exception as e:
                            return error("Malformed JSON body", 400)
                    kwargs['body'] = body
                response = await f(request, **kwargs)
                if isinstance(response, dict):
                    return json_response(response, status=200)
                return response
            return inner
        return wrapper
    return json_endpoint


def login_required(f):
    """ Decorator to check for the existence of and validate a JWT """
    
    _unauthorized = err.unauthorized("A valid login token is required in order to access this resource")
    
    def handler_wrapper(request: Request, *a, **k):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise _unauthorized
        try:
            token = auth_header.split(" ")[1]
            claims = jwt.get_claims_from_jwt(token, config.Config.get_config().jwt_key(), jwt.Aud.AUTH)
        except Exception as e:
            logger.exception(e)
            raise _unauthorized
        
        k["claims"] = claims
        
        return f(request, *a, **k)
        
    return handler_wrapper


get = json_router("get")
post = json_router("post")
put = json_router("put")
delete = json_router("delete")
patch = json_router("patch")


import routes.auth
import routes.rooms
