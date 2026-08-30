from unittest.mock import patch

import pytest

from app.auth import verify_api_key
from app.errors import AppError, ErrorCode


def test_verify_api_key_accepts_correct_key():
    with patch("app.auth.get_settings") as mock_settings:
        mock_settings.return_value.backend_api_key = "correct-key-123"
        verify_api_key(x_api_key="correct-key-123")  # should not raise


def test_verify_api_key_rejects_wrong_key():
    with patch("app.auth.get_settings") as mock_settings:
        mock_settings.return_value.backend_api_key = "correct-key-123"
        with pytest.raises(AppError) as exc_info:
            verify_api_key(x_api_key="wrong-key")
        assert exc_info.value.code == ErrorCode.INVALID_API_KEY


def test_verify_api_key_rejects_missing_key():
    with patch("app.auth.get_settings") as mock_settings:
        mock_settings.return_value.backend_api_key = "correct-key-123"
        with pytest.raises(AppError) as exc_info:
            verify_api_key(x_api_key=None)
        assert exc_info.value.code == ErrorCode.INVALID_API_KEY
