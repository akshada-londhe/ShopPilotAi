from fastapi import Header

from app.config import get_settings
from app.errors import AppError, ErrorCode


def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """FastAPI dependency for X-API-Key authentication."""

    settings = get_settings()

    if x_api_key is None or x_api_key != settings.backend_api_key:
        raise AppError(
            code=ErrorCode.INVALID_API_KEY,
            message="Missing or invalid API key. Provide it via the X-API-Key header.",
        )
