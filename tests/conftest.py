"""
Фикстуры для pytest.
Устанавливает тестовые переменные окружения перед запуском тестов.
"""

import os
import pytest


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Устанавливает тестовые переменные окружения автоматически для всех тестов."""
    # Устанавливаем тестовые значения, если они не заданы
    if not os.environ.get('PROXI_API_URL'):
        os.environ['PROXI_API_URL'] = 'https://test-api-url.com'
    
    if not os.environ.get('PROXI_API_KEY'):
        os.environ['PROXI_API_KEY'] = 'test-api-key'
    
    if not os.environ.get('GIGACHAT_AUTH_KEY'):
        os.environ['GIGACHAT_AUTH_KEY'] = 'test-gigachat-key'
    
    if not os.environ.get('OPENAI_API_KEY'):
        os.environ['OPENAI_API_KEY'] = 'test-openai-key'
    
    # Сохраняем оригинальные значения
    original_env = {
        'PROXI_API_URL': os.environ.get('PROXI_API_URL'),
        'PROXI_API_KEY': os.environ.get('PROXI_API_KEY'),
        'GIGACHAT_AUTH_KEY': os.environ.get('GIGACHAT_AUTH_KEY'),
        'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY'),
    }
    
    yield
    
    # Восстанавливаем оригинальные значения после теста
    for key, value in original_env.items():
        if value:
            os.environ[key] = value
        else:
            os.environ.pop(key, None)
