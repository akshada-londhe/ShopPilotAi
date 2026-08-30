from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.errors import AppError, ErrorCode

P = ParamSpec("P")
T = TypeVar("T")


def _is_rate_limit_error(exc: BaseException) -> bool:
    """Support rate-limit exception names across installed Groq versions."""

    return exc.__class__.__name__ in {
        "RateLimitError",
        "ModelRateLimitError",
    }


# Exponential backoff: 1s, 2s, 4s.
# Maximum of 3 attempts total.
_GROQ_RETRY = retry(
    retry=retry_if_exception(_is_rate_limit_error),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    stop=stop_after_attempt(3),
    reraise=True,
)


def with_provider_retry(func: Callable[P, T]) -> Callable[P, T]:
    """Retry provider calls when they report rate limiting."""

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            return _GROQ_RETRY(func)(*args, **kwargs)

        except Exception as exc:
            if not _is_rate_limit_error(exc):
                raise
            raise AppError(
                code=ErrorCode.RATE_LIMITED,
                message=(
                    "LLM provider rate limit exceeded after 3 retries. "
                    "Please try again shortly."
                ),
                details=str(exc),
            ) from exc

    return wrapper


with_groq_retry = with_provider_retry
