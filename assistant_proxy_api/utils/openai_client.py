# -*- coding: utf-8 -*-
"""Фабрика клиентов OpenAI-совместимого API."""
from openai import OpenAI

import config


def create_openai_client() -> OpenAI:
    """Создаёт клиент OpenAI или ProxiAPI в зависимости от config.API_PROVIDER."""
    if config.API_PROVIDER == "openai":
        return OpenAI(api_key=config.OPENAI_API_KEY)
    return OpenAI(api_key=config.PROXY_API_KEY, base_url=config.PROXY_API_URL)


def get_langchain_openai_kwargs() -> dict:
    """Параметры для langchain_openai (ChatOpenAI, OpenAIEmbeddings)."""
    if config.API_PROVIDER == "openai":
        return {"openai_api_key": config.OPENAI_API_KEY}
    return {
        "openai_api_key": config.PROXY_API_KEY,
        "openai_api_base": config.PROXY_API_URL,
    }
