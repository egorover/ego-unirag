# Тесты проекта RAG Assistant

## Структура тестов

```
tests/
├── __init__.py
├── test_cache.py           # Unit тесты для модуля кеша
├── test_vector_store.py    # Unit тесты для векторного хранилища
└── test_rag_pipeline.py    # Интеграционные тесты для RAG pipeline
```

## Запуск тестов локально

### Установка зависимостей

```bash
# Установка основных зависимостей
pip install -r requirements.txt

# Или установка с тестовыми зависимостями
pip install -r requirements.txt -r requirements-test.txt
```

### Запуск всех тестов

```bash
# Через pytest
pytest

# С подробным выводом
pytest -v

# С покрытием кода
pytest --cov=assistant_proxy_api tests/

# Конкретный тест
pytest tests/test_cache.py -v
```

### Запуск через unittest

```bash
python -m unittest discover -s tests
```

## CI/CD пайплайн

Тесты автоматически запускаются при:
- Пуше в ветки `main` или `master`
- Создании Pull Request

Конфигурация находится в `.github/workflows/ci.yml`

## Требования к тестам

Все тесты используют мок-объекты для внешних зависимостей:
- `ProxyAPIClient` - мок для API клиента
- `VectorStore` - мок для векторного хранилища
- `RAGCache` - мок для кеша

Это позволяет запускать тесты без реальных API ключей и внешних сервисов.

## Добавление новых тестов

1. Создайте файл `test_*.py` в папке `tests/`
2. Используйте `unittest` или `pytest` фреймворк
3. Для внешних зависимостей используйте `@patch` декораторы
4. Запустите тесты перед коммитом: `pytest`

## Пример теста

```python
import unittest
from unittest.mock import Mock, patch

class TestExample(unittest.TestCase):
    
    @patch('module.ExternalClass')
    def test_something(self, mock_external):
        mock_external.return_value = Mock()
        
        # Ваш тестовый код
        self.assertEqual(result, expected)
```
