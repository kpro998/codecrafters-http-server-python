from typing import Callable, Awaitable, Any

HTTPCallback = Callable[..., Awaitable[Any]]
