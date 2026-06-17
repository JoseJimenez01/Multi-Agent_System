from functools import lru_cache

from src.config.settings import configure_langfuse_env, get_settings


def record_exception(observation, error: Exception) -> None:
    """Marca una observación de Langfuse con nivel ERROR y el detalle de la excepción."""
    if observation is None:
        return
    try:
        observation.update(
            level="ERROR",
            status_message=f"{type(error).__name__}: {error}",
        )
    except Exception:
        pass


def record_current_exception(error: Exception) -> None:
    """Marca la observación activa con nivel ERROR (cuando no hay referencia directa)."""
    client = get_langfuse_client()
    if client is None:
        return
    try:
        client.update_current_span(
            level="ERROR",
            status_message=f"{type(error).__name__}: {error}",
        )
    except Exception:
        pass


def configure_langfuse() -> None:
    get_settings.cache_clear()
    configure_langfuse_env()


def is_tracing_enabled() -> bool:
    settings = get_settings()
    return bool(settings.langfuse_public_key and settings.langfuse_secret_key)


def traced(*args, **kwargs):
    """Apply Langfuse @observe only when tracing credentials are configured."""

    def decorator(func):
        if not is_tracing_enabled():
            return func

        from langfuse import observe

        return observe(*args, **kwargs)(func)

    if args and callable(args[0]) and not kwargs:
        return decorator(args[0])

    return decorator


@lru_cache(maxsize=1)
def get_langfuse_client():
    if not is_tracing_enabled():
        return None

    configure_langfuse_env()
    from langfuse import get_client

    return get_client()


def flush_langfuse() -> None:
    client = get_langfuse_client()
    if client is not None:
        client.flush()
