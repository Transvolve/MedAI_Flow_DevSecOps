import functools

_cache = {}

def cache_result(func):
    @functools.wraps(func)
    def wrapper(*args):
        if args in _cache:
            return _cache[args]
        res = func(*args)
        _cache[args] = res
        return res
    return wrapper
