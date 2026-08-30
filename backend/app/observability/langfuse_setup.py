from functools import lru_cache
import logging

from langfuse import Langfuse

from app.config import get_settings


logger = logging.getLogger(__name__)


@lru_cache
def get_langfuse_client() -> Langfuse:
    """Return the shared Langfuse client."""
    settings = get_settings()

    try:
        return Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
    except Exception as e:
        logger.warning(f"Langfuse initialization failed: {e}")
        return None


@lru_cache
def get_langfuse_handler():
    """Return a shared LangChain Langfuse callback handler."""
    settings = get_settings()

    # Langfuse callback handler may not be available in all versions
    try:
        from langfuse.callback import CallbackHandler
        # Initialize the Langfuse client so tracing is enabled.
        client = get_langfuse_client()
        if client is not None:
            return CallbackHandler(
                public_key=settings.langfuse_public_key,
            )
    except ImportError as e:
        logger.warning(f"Langfuse callback handler not available: {e}")
    except Exception as e:
        logger.warning(f"Langfuse handler initialization failed: {e}")

    from langchain_core.callbacks import BaseCallbackHandler

    # Return a no-op handler that conforms to BaseCallbackHandler
    class _NoOpHandler(BaseCallbackHandler):
        pass

    return _NoOpHandler()