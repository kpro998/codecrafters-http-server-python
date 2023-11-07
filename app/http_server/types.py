from typing import Any, Awaitable, Callable

HTTPCallback = Callable[..., Awaitable[Any]]
