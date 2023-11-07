from collections.abc import Awaitable, Callable
from typing import Any

HTTPCallback = Callable[..., Awaitable[Any]]
