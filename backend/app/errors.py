from enum import StrEnum

from pydantic import BaseModel


class ErrorCode(StrEnum):
    INVALID_API_KEY = "invalid_api_key"
    RATE_LIMITED = "rate_limited"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    NORMALIZATION_FAILED = "normalization_failed"
    INTERNAL_ERROR = "internal_error"


# Spec API Schemas section: error code -> HTTP status mapping.
ERROR_STATUS_CODES: dict[ErrorCode, int] = {
    ErrorCode.INVALID_API_KEY: 401,
    ErrorCode.RATE_LIMITED: 429,
    ErrorCode.PROVIDER_UNAVAILABLE: 503,
    ErrorCode.NORMALIZATION_FAILED: 422,
    ErrorCode.INTERNAL_ERROR: 500,
}


class ErrorDetail(BaseModel):
    code: ErrorCode
    message: str
    details: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class AppError(Exception):
    """Raised anywhere in the app to produce a structured API error response."""

    def __init__(self, code: ErrorCode, message: str, details: str | None = None):
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)

    def to_response(self) -> ErrorResponse:
        return ErrorResponse(error=ErrorDetail(code=self.code, message=self.message, details=self.details))

    @property
    def status_code(self) -> int:
        return ERROR_STATUS_CODES[self.code]
