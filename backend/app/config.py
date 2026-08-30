from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

STAGE_PROVIDERS = {
    "normalizer": "openrouter",
    "generator": "openrouter",
    "extractor": "openrouter",
    "matcher": "openrouter",
    "critic": "openrouter",
    "synthesizer": "openrouter",
    "synthesizer_fallback": "openrouter",
}

STAGE_MODELS = {
    "normalizer": "openrouter_model",
    "generator": "openrouter_model",
    "extractor": "openrouter_model",
    "matcher": "openrouter_model",
    "critic": "openrouter_model",
    "synthesizer": "openrouter_model",
    "synthesizer_fallback": "openrouter_model",
}

STAGE_MAX_TOKENS = {
    "normalizer": 512,
    "generator": 512,
    "extractor": 4096,
    "matcher": 256,
    "critic": 768,
    "synthesizer": 512,
    "synthesizer_fallback": 512,
}

STAGE_TIMEOUTS = {
    "normalizer": 10,
    "generator": 8,
    "extractor": 12,
    "matcher": 8,
    "critic": 10,
    "synthesizer": 10,
    "synthesizer_fallback": 10,
}

STAGE_FALLBACK_PROVIDERS = {
    "normalizer": "openrouter",
    "generator": "openrouter",
    "extractor": "openrouter",
    "matcher": "openrouter",
    "critic": "openrouter",
    "synthesizer": "openrouter",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    openrouter_api_key: str | None = None
    openrouter_model: str = "meta-llama/llama-3.3-70b-instruct:free"
    tavily_api_key: str
    backend_api_key: str

    langfuse_public_key: str
    langfuse_secret_key: str
    langfuse_host: str = "https://cloud.langfuse.com"
    chroma_persist_dir: str = "chroma_groq"

    # Semantic memory cache (full-response RAG recall). A stored response is
    # served from memory when the raw query embedding matches at cosine
    # similarity >= this threshold. Default is near-exact (decision A);
    # lower it to demo looser semantic recall.
    memory_similarity_threshold: float = 0.95

    # Secret used to sign user JWTs. In production set a long random value.
    # If unset, auth falls back to backend_api_key (acceptable for local dev
    # only) and logs a warning.
    jwt_secret: str | None = None

    # Spec NFR (CORS): localhost:3000 for dev plus the Vercel deploy URL in prod.
    # Comma-separated list of allowed origins.
    cors_allowed_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
