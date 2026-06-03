# -*- coding: utf-8 -*-
"""
Конфигурация проекта для assistant_proxy_api.
Поддержка: ProxiAPI (основной) и OpenAI API (опционально).
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Загрузка переменных окружения из .env в корне проекта
# __file__ = путь к этому файлу config.py
# .parent = assistant_proxy_api/
# .parent.parent = корень проекта (ego-unirag/)
root_dir = Path(__file__).parent.parent
env_file = root_dir / ".env"

if env_file.exists():
    load_dotenv(str(env_file))
else:
    # Fallback: ищем в текущей рабочей директории
    load_dotenv()

VALID_API_PROVIDERS = ("proxy", "openai")

# ==================== API НАСТРОЙКИ ====================

API_PROVIDER = os.getenv("API_PROVIDER", "proxy").lower()

PROXY_API_URL = os.getenv("PROXI_API_URL", "https://api.proxyapi.ru/openai/v1")
# В .env используется PROXI_API_KEY, а не PROXY_API_KEY
PROXY_API_KEY = os.getenv("PROXI_API_KEY", "")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Убираем строгую проверку при импорте - проверка будет только при запуске скрипта

# ==================== МОДЕЛИ ====================

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")

# ==================== CHROMADB НАСТРОЙКИ ====================

CHROMA_DB_PATH = "./chroma_db"

# ==================== ПАРАМЕТРЫ ЧАНКИНГА ====================

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 500))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 100))

# ==================== ПАРАМЕТРЫ ПОИСКА ====================

TOP_K = int(os.getenv("TOP_K", 5))

# ==================== ПУТЬ К ДАННЫМ ====================

DATA_DIR = os.getenv("DATA_DIR", "./data")
