from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from app.config import (
    STAGE_MAX_TOKENS,
    STAGE_MODELS,
    STAGE_PROVIDERS,
    STAGE_TIMEOUTS,
    get_settings,
)


def build_llm(
    stage: str,
    *,
    temperature: float = 0.0,
    provider_override: str | None = None,
    timeout_override: int | None = None,
) -> BaseChatModel:
    """Build the configured provider/model for a pipeline stage with explicit timeout."""
    settings = get_settings()
    provider = provider_override or STAGE_PROVIDERS.get(stage, "groq")
    
    if provider == "groq":
        model_name = getattr(settings, "groq_model", "openai/gpt-oss-20b")
    else:
        model_name = getattr(settings, "openrouter_model", "openai/gpt-oss-20b")

    timeout_val = timeout_override if timeout_override is not None else STAGE_TIMEOUTS.get(stage, 10)
    max_tokens_val = STAGE_MAX_TOKENS.get(stage, 512)

    if provider == "groq":
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is required for this pipeline stage")
        return ChatGroq(
            model=model_name,
            groq_api_key=settings.groq_api_key,
            temperature=temperature,
            max_retries=0,
            timeout=timeout_val,
            max_tokens=max_tokens_val,
        )

    if provider == "openrouter":
        if not settings.openrouter_api_key:
            raise RuntimeError("OPENROUTER_API_KEY is required for this pipeline stage")
        return ChatOpenAI(
            model=model_name,
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=temperature,
            max_retries=0,
            timeout=timeout_val,
            max_completion_tokens=max_tokens_val,
            reasoning_effort="low",
        )

    raise ValueError(f"Unsupported LLM provider: {provider}")
