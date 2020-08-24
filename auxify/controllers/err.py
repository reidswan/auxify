import aiohttp.web_exceptions as exc
from typing import Callable
from auxify.utils import json_dumps_with_default


JSON = "application/json"

def _error(exc_class, message: str)-> exc.HTTPException:
    return exc_class(content_type=JSON, body=json_dumps_with_default({
        "error": True,
        "message": message
    }))

def not_found(message: str)-> exc.HTTPException:
    return _error(exc.HTTPNotFound, message)

def unauthorized(message: str)-> exc.HTTPException:
    return _error(exc.HTTPUnauthorized, message)

def internal_server_error(message: str = "An internal error has occured. Please try again in a little while.")-> exc.HTTPException:
    return _error(exc.HTTPInternalServerError, message) 

def bad_request(message: str)-> exc.HTTPException:
    return _error(exc.HTTPBadRequest, message)

def found(url: str)-> exc.HTTPFound:
    return exc.HTTPFound(url)

def redirect_to(url: str):
    raise found(url)

def failed_dependency(message: str):
    return _error(exc.HTTPFailedDependency, message)

def forbidden(message: str):
    return _error(exc.HTTPForbidden, message)
