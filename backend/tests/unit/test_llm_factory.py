from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.llm_factory import build_llm


def _settings():
    return SimpleNamespace(
        groq_api_key="groq-test-key",
        groq_model="groq/test-model",
        openrouter_api_key="openrouter-test-key",
        openrouter_model="openrouter/test-model",
    )


def test_build_llm_uses_groq_for_critic():
    with (
        patch("app.llm_factory.get_settings", return_value=_settings()),
        patch("app.llm_factory.ChatGroq") as chat_groq,
    ):
        build_llm("critic", provider_override="groq")

    chat_groq.assert_called_once_with(
        model="groq/test-model",
        groq_api_key="groq-test-key",
        temperature=0.0,
        max_retries=0,
        timeout=10,
        max_tokens=768,
    )


def test_build_llm_uses_openrouter_for_extractor():
    with (
        patch("app.llm_factory.get_settings", return_value=_settings()),
        patch("app.llm_factory.ChatOpenAI") as chat_openai,
    ):
        build_llm("extractor")

    chat_openai.assert_called_once_with(
        model="openrouter/test-model",
        api_key="openrouter-test-key",
        base_url="https://openrouter.ai/api/v1",
        temperature=0.0,
        max_retries=0,
        timeout=12,
        max_completion_tokens=4096,
        reasoning_effort="low",
    )


def test_build_llm_with_provider_and_timeout_override():
    with (
        patch("app.llm_factory.get_settings", return_value=_settings()),
        patch("app.llm_factory.ChatGroq") as chat_groq,
    ):
        build_llm("extractor", provider_override="groq", timeout_override=5)

    chat_groq.assert_called_once_with(
        model="groq/test-model",
        groq_api_key="groq-test-key",
        temperature=0.0,
        max_retries=0,
        timeout=5,
        max_tokens=4096,
    )


def test_build_llm_requires_configured_provider_key():
    settings = _settings()
    settings.openrouter_api_key = None

    with (
        patch("app.llm_factory.get_settings", return_value=settings),
        pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"),
    ):
        build_llm("extractor")

