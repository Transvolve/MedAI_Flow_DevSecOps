import functools
import time
from typing import Any, Awaitable, Callable, Coroutine, Dict


def latency_timer(func: Callable[..., Awaitable[Any]]) -> Callable[..., Coroutine[Any, Any, Dict[str, Any]]]:
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Dict[str, Any]:
        start = time.time()
        result = await func(*args, **kwargs)
        elapsed = round((time.time() - start) * 1000, 3)
        return {"result": result, "latency_ms": elapsed}
    return wrapper

