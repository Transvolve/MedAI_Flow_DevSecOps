import functools, time

def latency_timer(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        elapsed = round((time.time() - start)*1000, 3)
        return {"result": result, "latency_ms": elapsed}
    return wrapper
