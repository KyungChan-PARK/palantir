from functools import wraps


def cache_response(func):
    cache = {}

    @wraps(func)
    async def wrapper(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key in cache:
            return cache[key]
        res = await func(*args, **kwargs)
        cache[key] = res
        return res

    return wrapper
