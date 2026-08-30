from unittest.mock import MagicMock

import pytest

from app.errors import AppError, ErrorCode
from app.retry_utils import with_groq_retry


class RateLimitError(Exception):
    pass


def test_with_groq_retry_succeeds_without_retrying_on_first_try():
    mock_fn = MagicMock(return_value="ok")
    wrapped = with_groq_retry(mock_fn)

    result = wrapped()

    assert result == "ok"
    assert mock_fn.call_count == 1


def test_with_groq_retry_retries_then_succeeds():
    mock_fn = MagicMock(side_effect=[RateLimitError("rate limited"), "ok"])
    wrapped = with_groq_retry(mock_fn)

    result = wrapped()

    assert result == "ok"
    assert mock_fn.call_count == 2


def test_with_groq_retry_raises_app_error_after_exhausting_retries():
    mock_fn = MagicMock(side_effect=RateLimitError("rate limited"))
    wrapped = with_groq_retry(mock_fn)

    with pytest.raises(AppError) as exc_info:
        wrapped()

    assert exc_info.value.code == ErrorCode.RATE_LIMITED
    assert (
        mock_fn.call_count == 3
    )  # 1 original + 2 retries, per spec's backoff schedule
