from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.core.config import get_settings


def is_llm_configured() -> bool:
    # Used by the UI/runtime endpoint to show Live LLM vs fallback mode.
    return bool(get_settings().openai_api_key)


def get_chat_model(temperature: float = 0.2) -> BaseChatModel | None:
    # Agents call this helper instead of creating ChatOpenAI directly.
    # Returning None lets the app run in fallback mode during demos without a key.
    settings = get_settings()
    if not settings.openai_api_key:
        return None
    return ChatOpenAI(
        model=settings.openai_model,
        temperature=temperature,
        api_key=settings.openai_api_key,
    )
