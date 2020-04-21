def cast_key(key, cast):
    def wrapper(f):
        async def inner(*a, **k):
            result = await f(*a, **k)
            if isinstance(result, dict) and key in result:
                result[key] = cast(result[key])
            return result
        return inner
    return wrapper
