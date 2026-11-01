"""AI Auto Router Python Thin Client SDK."""

from .client import (
    DEFAULT_BASE_URL,
    DEFAULT_TIMEOUT,
    RETRYABLE_CODES,
    USER_AGENT,
    VERSION,
    AutoRouterClient,
    RouterClientError,
    parse_retry_after,
)

__version__ = VERSION
__all__ = [
    "DEFAULT_BASE_URL",
    "DEFAULT_TIMEOUT",
    "RETRYABLE_CODES",
    "USER_AGENT",
    "AutoRouterClient",
    "RouterClientError",
    "parse_retry_after",
]
