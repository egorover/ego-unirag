# Ego-UniRAG

> **Важно:** Данный проект является форком репозитория [MrGAN12009/prompt-5_8](https://github.com) и развивается как самостоятельное решение под кодовым именем **Ego-UniRAG**.

[![CI](https://github.com/egorover/ego-unirag/actions/workflows/ci.yml/badge.svg)](https://github.com/egorover/ego-unirag/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-20%20passed-success)](https://github.com/egorover/ego-unirag/actions/workflows/ci.yml)
[![Security Scan](https://github.com/egorover/ego-unirag/actions/workflows/security.yml/badge.svg)](https://github.com/egorover/ego-unirag/actions/workflows/security.yml)

## Описание проекта

**Ego-UniRAG** — это универсальная, гибко настраиваемая RAG-система (Retrieval-Augmented Generation), ориентированная на создание персонального и прикладного контекста для моделей искусственного интеллекта.

### Ключевые возможности

- **Универсальность пайплайна**: Сквозной конвейер для быстрого развёртывания RAG-систем с полным контролем над каждым этапом — от парсинга данных до генерации ответа.
- **Глубокий контроль контекста**: Тонкая настройка фильтрации, ранжирования документов и управления памятью (эго-контекстом).
- **Интеграция с ProxiAPI**: Поддержка российского провайдера для стабильного доступа к зарубежным и локальным LLM без VPN.
- **Терминальный интерфейс**: Все операции выполняются через командную строку.

### Режимы работы

| Режим | LLM Provider | Описание |
|-------|--------------|----------|
| **ProxiAPI** | ProxiAPI | Работа через российский прокси (GPT/Claude без VPN) |
| **GigaChat** | GigaChat | Работа через API Сбера |
| **OpenAI API** | OpenAI | Работа через OpenAI API |

## Что внутри

### Новые функции

- **ProxiAPI режим (Основной)**
  - Полная интеграция с российским провайдером ProxiAPI (GPT/Claude без VPN)
  - Поддержка кастомных моделей через ProxiAPI

- **Система оценки качества (RAGAS)**
  - Автоматическая оценка через `evaluate_ragas.py`
  - Метрики: Faithfulness, Context Precision

> **⚠️ ВАЖНОЕ ПРИМЕЧАНИЕ по RAGAS:**  
> RAGAS internally использует OpenAI-совместимый API для вычисления метрик оценки.  
> 
> **Поддерживаемые конфигурации:**
> - **assistant_proxy_api** — полная поддержка RAGAS (ProxiAPI для RAG + ProxiAPI для метрик)
> - **assistant_giga** — RAGAS требует прокси-конфигурацию (GigaChat для RAG + ProxiAPI для метрик)
> - **assistant_api** — RAGAS требует `OPENAI_API_KEY`
>
> Для работы метрик RAGAS необходимо настроить OpenAI-совместимый провайдер (ProxiAPI или OpenAI),  
> даже если RAG pipeline использует GigaChat или другие модели.

### Улучшения

- **Кодировка и совместимость**: Полная поддержка UTF-8 для Windows, исправление I/O ошибок с кириллицей
- **Embeddings и векторное хранилище**: Исправление размерности embeddings (384 → 1536), умный чанкинг с overlap
- **Безопасность**: Полная защита секретами через `.gitignore`, удаление `.env` из репозитория

### CI/CD

Проект автоматизирован:

- ✅ **Автотесты** — unit-тесты на каждом коммите
- 🔒 **Сканирование секретов** — gitleaks + detect-secrets
- 🚀 **CI/CD пайплайн** — GitHub Actions
- 🐍 **Python 3.11+** — на Windows/Linux/macOS

## Архитектура проекта

Проект реализует классическую RAG-архитектуру:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Ego-UniRAG                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     │
│  │   Query      │ ──→ │   Cache      │ ──→ │ Vector Store │     │
│  │   Input      │     │   (SQLite)   │     │ (ChromaDB)   │     │
│  └──────────────┘     └──────────────┘     └──────────────┘     │
│                                                   │             │
│                                                   ↓             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     │
│  │   Response   │ ←── │   LLM        │ ←── │  Prompt      │     │
│  │   Output     │     │  (GigaChat/  │     │  Builder     │     │
│  └──────────────┘     │   OpenAI/    │     └──────────────┘     │
│                       │   ProxiAPI)  │                          │
│                       └──────────────┘                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

Пайплайн обработки запросов:

1. Проверка кеша → 2. Векторный поиск → 3. Формирование промпта → 
4. Генерация ответа → 5. Сохранение в кеш

## Требования

- **Python**: 3.11+ (рекомендуется 3.13)
- **ОС**: Windows / Linux / macOS
- **Память**: Минимум 2 GB RAM
- **Интернет**: Для работы с внешними API

### Внешние зависимости

| Режим | Требование |
|-------|------------|
| **ProxiAPI** | `PROXI_API_URL`, `PROXI_API_KEY` |
| **GigaChat** | `GIGACHAT_AUTH_KEY`, `GIGACHAT_RQUID` |
| **OpenAI API** | `OPENAI_API_KEY` |

## Установка

1. **Клонируйте репозиторий**:
```bash
git clone <repository-url>
cd <project-directory>
```

2. **Создайте и активируйте виртуальное окружение**:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

3. **Настройте окружение**:
```bash
cp .env.example .env
# Отредактируйте .env и добавьте ваши ключи
```

4. **Установите зависимости**:
```bash
pip install -r requirements.txt
```

5. **Подготовьте данные**:
Разместите текстовые документы для RAG в нужной директории:
```
project/
├── assistant_giga/data/docs.txt
├── assistant_api/data/docs.txt
└── assistant_proxy_api/data/docs.txt
```

## Запуск

### Режим ProxiAPI (рекомендуется)
```bash
cd assistant_proxy_api
python app.py
```

### Режим GigaChat
```bash
cd assistant_giga
python app.py          # Консольный ассистент
# или
python rag_pipeline.py # Pipeline напрямую
```

### Режим OpenAI API
```bash
cd assistant_api
python app.py
```

### Команды в интерактивном режиме

| Команда | Описание |
|---------|----------|
| `exit`, `quit`, `q` | Выход из программы |
| `stats` | Показ статистики системы |
| `clear` | Очистка кеша |

## Компоненты системы

### RAG Pipeline
Основной модуль обработки запросов:
- `assistant_giga/rag_pipeline.py` — GigaChat режим
- `assistant_api/rag_pipeline.py` — API режим
- `assistant_proxy_api/rag_pipeline.py` — ProxiAPI режим

### Vector Store
Векторное хранилище на основе **ChromaDB**:
- Разбиение текста по абзацам и предложениям
- Перекрывание чанков (overlap) для сохранения контекста
- Cosine similarity для поиска

### Cache System
Кеширование ответов на основе **SQLite**:
- Хэширование запросов для быстрого поиска
- Хранение контекста и метаданных
- Статистика использования кеша

### LLM Clients
- `GigaChatClient` — API Сбера (авторизация, OAuth, embeddings)
- `OpenAI` — стандартный клиент для GPT
- `ProxyAPIClient` — ProxiAPI (GPT/Claude через российский прокси)

## Оценка качества

Модуль оценки через **RAGAS** доступен в `assistant_proxy_api/`.

### Запуск оценки
```bash
cd assistant_proxy_api
python evaluate_ragas.py
```

### Требования для оценки

| Переменная | Описание | Обязательно |
|------------|----------|-------------|
| `PROXI_API_URL` | URL ProxiAPI для RAG pipeline | ✅ Да |
| `PROXI_API_KEY` | API ключ ProxiAPI | ⚠️ Опционально |
| `OPENAI_API_KEY` | API ключ OpenAI для RAGAS метрик | ✅ Да |

### Метрики RAGAS

| Метрика | Описание | Диапазон |
|---------|----------|----------|
| **Faithfulness** | Соответствие ответа контексту | 0.0 - 1.0 |
| **Answer Relevancy** | Релевантность ответа вопросу | 0.0 - 1.0 |
| **Context Precision** | Качество извлечённого контекста | 0.0 - 1.0 |

### Настройка для оценки
```bash
# В файле .env добавьте:
PROXI_API_URL=https://api.proxyapi.ru/openai/v1
PROXI_API_KEY=your_proxi_api_key
OPENAI_API_KEY=your_openai_api_key  # Требуется для RAGAS метрик
```

### Подготовка датасета
Отредактируйте константу `EVALUATION_QUESTIONS` в `evaluate_ragas.py`:
```python
EVALUATION_QUESTIONS = [
    "Вопрос 1?",
    "Вопрос 2?",
]
```

## Структура проекта

```
Ego-UniRAG/
├── README.md                     # Документация
├── requirements.txt              # Зависимости
├── .env                          # Переменные окружения (не в репозитории)
│
├── assistant_giga/               # GigaChat режим
│   ├── app.py                    # Консольный интерфейс
│   ├── rag_pipeline.py           # Основной RAG pipeline
│   ├── vector_store.py           # Векторное хранилище
│   ├── cache.py                  # Система кэширования
│   ├── gigachat_client.py        # Клиент GigaChat API
│   └── data/
│       └── docs.txt              # Документы для RAG
│
├── assistant_api/                # OpenAI API режим
│   ├── app.py                    # Консольный интерфейс
│   ├── rag_pipeline.py           # Основной RAG pipeline
│   ├── vector_store.py           # Векторное хранилище
│   ├── cache.py                  # Система кэширования
│   └── data/
│       └── docs.txt              # Документы для RAG
│
├── assistant_proxy_api/          # ProxiAPI режим (РЕКОМЕНДУЕТСЯ)
│   ├── app.py                    # Консольный интерфейс
│   ├── rag_pipeline.py           # Основной RAG pipeline
│   ├── vector_store.py           # Векторное хранилище
│   ├── cache.py                  # Система кэширования
│   ├── proxy_client.py           # Клиент ProxiAPI
│   ├── evaluate_ragas.py         # Оценка через RAGAS
│   └── data/
│       └── docs.txt              # Документы для RAG
│
└── chroma_db/                    # Векторное хранилище (после запуска)
    └── chroma.sqlite3
```

## Безопасность

- Файл `.env` **не коммитьте** — он в `.gitignore`.
- Используйте `.env.example` как шаблон с плейсхолдерами.
- При `PROXI_API_URL` обязательны `PROXI_API_URL` и `PROXI_API_KEY`.
- Если `.env` ранее попадал в Git, **ротируйте ключи** в консоли провайдера.
