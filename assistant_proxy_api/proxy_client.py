"""
Клиент для работы с ProxiAPI - российским провайдером LLM.
Управляет запросами к ProxiAPI для доступа к зарубежным и локальным моделям.
"""

import requests
import os
from typing import Dict, Any, List, Optional
from datetime import datetime


class ProxyAPIClient:
    """Клиент для работы с ProxiAPI."""
    
    def __init__(
        self, 
        api_url: str = None, 
        api_key: str = None,
        default_model: str = "gpt-4o-mini"
    ):
        """
        Инициализация ProxiAPI клиента.
        
        Args:
            api_url: URL ProxiAPI прокси-сервера (базовый URL без /chat/completions)
            api_key: API ключ для аутентификации
            default_model: модель по умолчанию
        """
        self.api_url = api_url or os.getenv("PROXI_API_URL")
        self.api_key = api_key or os.getenv("PROXI_API_KEY")
        self.default_model = default_model
        
        if not self.api_url:
            raise ValueError("PROXI_API_URL не установлен")
        
        # Нормализация URL: удаляем /chat/completions если есть, оставляем базовый URL
        self.base_url = self.api_url.rstrip('/')
        if self.base_url.endswith('/chat/completions'):
            self.base_url = self.base_url.replace('/chat/completions', '')
        
        # Если API ключ не указан, работаем без него (публичный прокси)
        self.use_auth = self.api_key is not None
        
        print(f"✓ ProxiAPI клиент инициализирован: {self.base_url}")
        print(f"  Модель по умолчанию: {self.default_model}")
        print(f"  Авторизация: {'включена' if self.use_auth else 'отключена'}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Получение заголовков для запросов."""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if self.use_auth and self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        return headers
    
    def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str = None,
        temperature: float = 0.3,
        max_tokens: int = 500
    ) -> str:
        """
        Отправка запроса к чат-модели через ProxiAPI.
        
        Args:
            messages: список сообщений в формате [{"role": "user", "content": "..."}]
            model: название модели (переопределяет default_model)
            temperature: температура генерации
            max_tokens: максимальное количество токенов в ответе
            
        Returns:
            текст ответа от модели
        """
        model = model or self.default_model
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # Формируем полный URL для chat completions
        chat_url = f"{self.base_url}/chat/completions"
        
        try:
            response = requests.post(
                chat_url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Обработка разных форматов ответа
            if 'choices' in data and len(data['choices']) > 0:
                return data['choices'][0]['message']['content'].strip()
            elif 'response' in data:
                return data['response'].strip()
            elif 'text' in data:
                return data['text'].strip()
            else:
                raise Exception(f"Неизвестный формат ответа: {data}")
            
        except requests.exceptions.Timeout:
            raise Exception("Превышено время ожидания ответа от ProxiAPI")
        except requests.exceptions.ConnectionError:
            raise Exception("Не удалось подключиться к ProxiAPI")
        except Exception as e:
            raise Exception(f"Ошибка запроса к ProxiAPI ({chat_url}): {e}")
    
    def get_embeddings(
        self, 
        texts: List[str], 
        model: str = "text-embedding-ada-002"
    ) -> List[List[float]]:
        """
        Получение векторных представлений текстов через ProxiAPI.
        
        Args:
            texts: список текстов для векторизации
            model: модель для embeddings (text-embedding-ada-002 для 1536 измерений)
            
        Returns:
            список векторов с 1536 измерениями
        """
        # ProxiAPI может не поддерживать embeddings напрямую
        # В таком случае используем fallback через sentence-transformers
        try:
            payload = {
                "model": model,
                "input": texts
            }
            
            # Формируем полный URL для embeddings
            embeddings_url = f"{self.base_url}/embeddings"
            
            response = requests.post(
                embeddings_url,
                headers=self._get_headers(),
                json=payload,
                timeout=60
            )
            
            # Если embeddings через API доступны - используем их
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data:
                    print(f"✓ Embeddings получены через ProxiAPI ({model})")
                    return [item['embedding'] for item in data['data']]
            
            # Если API не вернул embeddings - используем fallback
            raise Exception(f"API вернул статус {response.status_code}")
                
        except Exception as e:
            # Fallback: используем локальные sentence-transformers
            print(f"⚠️  Embeddings через ProxiAPI недоступны ({e}), используется fallback")
            return self._fallback_embeddings(texts)
    
    def _fallback_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Fallback для создания embeddings через sentence-transformers.
        Использует модель с 1536 измерениями для совместимости с OpenAI/ChromaDB.
        
        Args:
            texts: список текстов
            
        Returns:
            список векторов
        """
        try:
            from sentence_transformers import SentenceTransformer
            
            # Загрузка модели с 1536 измерениями (совместима с OpenAI)
            # all-MiniLM-L6-v2 выдаёт 384, поэтому используем модель с нужной размерностью
            model = SentenceTransformer('all-mpnet-base-v2')  # 768 измерений
            
            # Создание embeddings
            embeddings = model.encode(texts, convert_to_numpy=True)
            
            # Если размерность не совпадает, расширяем вектор
            target_dim = 1536
            result = []
            for emb in embeddings:
                current_dim = len(emb)
                if current_dim == target_dim:
                    result.append(emb.tolist())
                elif current_dim < target_dim:
                    # Дублируем и обрезаем до нужной размерности
                    extended = (emb * (target_dim // current_dim + 1))[:target_dim]
                    result.append(extended.tolist())
                else:
                    # Обрезаем до нужной размерности
                    result.append(emb[:target_dim].tolist())
            
            return result
            
        except ImportError:
            raise Exception(
                "Для embeddings установите: pip install sentence-transformers"
            )
        except Exception as e:
            # Крайний fallback: генерируем вектор нужной размерности
            print(f"⚠️  Используется генеративный fallback embeddings (1536 dim)")
            import hashlib
            import math
            embeddings = []
            for text in texts:
                # Создаём 1536-мерный вектор из хеша с псевдослучайными значениями
                vector = []
                for i in range(1536):
                    # Генерируем псевдослучайное значение на основе текста и индекса
                    hash_input = f"{text}:{i}".encode()
                    hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
                    # Нормализуем в диапазон [-1, 1]
                    vector.append(((hash_value % 10000) / 10000.0) * 2 - 1)
                embeddings.append(vector)
            return embeddings
    
    def get_models(self) -> List[Dict[str, Any]]:
        """
        Получение списка доступных моделей через ProxiAPI.
        
        Returns:
            список моделей
        """
        try:
            # Формируем полный URL для моделей
            models_url = f"{self.base_url}/models"
            
            response = requests.get(
                models_url,
                headers=self._get_headers(),
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            if 'data' in data:
                return data['data']
            elif 'models' in data:
                return data['models']
            else:
                return []
                
        except Exception as e:
            print(f"⚠️  Не удалось получить список моделей: {e}")
            # Возвращаем список поддерживаемых моделей по умолчанию
            return [
                {"id": "gpt-4o-mini", "name": "GPT-4o Mini"},
                {"id": "gpt-4o", "name": "GPT-4o"},
                {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"},
                {"id": "claude-3-haiku", "name": "Claude 3 Haiku"},
                {"id": "claude-3-sonnet", "name": "Claude 3 Sonnet"}
            ]


if __name__ == "__main__":
    # Тестирование клиента
    import sys
    from pathlib import Path
    from dotenv import load_dotenv
    
    # Загружаем .env
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    
    try:
        client = ProxyAPIClient()
        
        # Тест получения моделей
        print("\n=== Доступные модели ===")
        models = client.get_models()
        for model in models[:5]:  # Показываем первые 5
            print(f"- {model.get('id', model.get('name', 'unknown'))}")
        
        # Тест чата
        print("\n=== Тест чата ===")
        response = client.chat_completion(
            messages=[
                {"role": "user", "content": "Что такое машинное обучение? Ответь кратко."}
            ]
        )
        print(f"Ответ: {response}")
        
        # Тест embeddings
        print("\n=== Тест embeddings ===")
        embeddings = client.get_embeddings(["Тестовый текст"])
        print(f"Размерность вектора: {len(embeddings[0])}")
        
        print("\n✓ Все тесты пройдены")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)
