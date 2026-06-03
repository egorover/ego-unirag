# Ego-RagaScope
Microscopic insights into your RAG pipeline performance.

[![CI](https://github.com/egorover/ego-ragascope/actions/workflows/ci.yml/badge.svg)](https://github.com/egorover/ego-ragascope/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-9%20passed-success)](https://github.com/egorover/ego-ragascope/actions/workflows/ci.yml)
[![Security Scan](https://img.shields.io/badge/security-scan%20ok-blue)](https://github.com/egorover/ego-ragascope/actions/workflows/ci.yml)

## О проекте
Ego-RagaScope — это MVP-решение для комплексного аудита и оценки эффективности RAG-систем. Проект демонстрирует работу с локальной векторной базой данных ChromaDB и автоматическое вычисление ключевых метрик качества с помощью фреймворка Ragas.

**Ключевые возможности**

- **Retrieval**: оценка релевантности контекста и точности поиска.
- **Generation**: анализ качества, связности и достоверности ответов LLM.
- **Sources**: валидация используемых первоисточников.
- **Metrics**: расчет продуктовых и технических метрик качества.

**Интерфейс:**
- 🖥️ **Консольный (терминальный) интерфейс** — все операции выполняются через командную строку

**Поддержка API:**
- 🇷🇺 **Российский Proxy API** (основной по умолчанию)
- 🌐 **OpenAI API** (опционально)

## Что внутри
- Оценка качества генерации.
- Анализ retrieval-части.
- Сравнение ответов с источниками.
- Отчёты и метрики.
- Полный цикл RAG: индексация, поиск контекста, генерация ответов.

## CI/CD

Проект полностью автоматизирован:

- ✅ **Автотесты** — 9 unit-тестов на каждом коммите
- 🔒 **Сканирование секретов** — gitleaks + detect-secrets
- 🚀 **CI/CD пайплайн** — GitHub Actions
- 📦 **Python 3.12** — на Ubuntu

```bash
python -m unittest discover -s tests -v
# Ran 9 tests in ~0.7s — OK
```

## Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Создайте файл `.env` в корне проекта и настройте API:

### Вариант 1: Российский Proxy API (рекомендуется)
```
API_PROVIDER=proxy
PROXY_API_URL=https://api.proxyapi.ru/openai/v1
PROXY_API_KEY=your_proxy_api_key_here
```

### Вариант 2: OpenAI API (опционально)
```
API_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
```

### Дополнительные настройки (опционально):
```
EMBEDDING_MODEL=text-embedding-3-small
CHAT_MODEL=gpt-3.5-turbo
CHUNK_SIZE=500
CHUNK_OVERLAP=100
TOP_K=5
DATA_DIR=./data
```

## Запуск

### 1. Индексация документов
Запустите скрипт для загрузки документов из папки `data/` и создания векторной базы:
```bash
python ingest.py
```

### 2. Задать вопрос ассистенту
Запустите интерактивный режим ассистента:
```bash
python rag_assistant.py
```


### 3. Оценка качества через RAGAS
Запустите скрипт оценки:
```bash
python evaluate_rag.py
```

## Метрики оценки
Скрипт оценки автоматически рассчитывает метрики:
- **Faithfulness** - верность ответа (насколько ответ основан на контексте)
- **Answer Relevancy** - релевантность ответа вопросу
- **Context Precision** - точность выбранного контекста

## Тестирование

Офлайн-тесты (без API-ключей):

```bash
python -m unittest discover -s tests -v
```

Перед первым запуском ассистента выполните индексацию: `python ingest.py`.

## Безопасность

- Файл `.env` **не коммитить** — он в `.gitignore`.
- Используйте `.env.example` как шаблон с плейсхолдерами.
- При `API_PROVIDER=proxy` обязательны `PROXY_API_URL` и `PROXY_API_KEY`.
- Если `.env` ранее попадал в Git, **ротируйте ключи** в консоли провайдера.
- Подробный отчёт аудита: [AUDIT_REPORT.md](AUDIT_REPORT.md).

## Кодировка

Все текстовые файлы проекта — **UTF-8**. На Windows для корректного вывода кириллицы в консоли скрипты автоматически переключают stdout/stderr на UTF-8 (`utils/console.py`).

## Структура проекта

```
ego-ragascope/
├── data/                 # Исходные документы (UTF-8)
├── tests/                # Офлайн-тесты
├── utils/                # API-клиент, настройка консоли
├── text_processing.py    # Чанкинг и очистка текста
├── chroma_db/            # ChromaDB (создаётся ingest.py, не коммитить)
├── ingest.py
├── rag_assistant.py
├── evaluate_rag.py
├── config.py
├── requirements.txt
├── .env.example          # Шаблон конфигурации
├── AUDIT_REPORT.md       # Отчёт аудита
└── README.md
```

