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
            api_url: URL ProxiAPI прокси-сервера
            api_key: API ключ для аутентификации
            default_model: модель по умолчанию
        """
        self.api_url = api_url or os.getenv("PROXI_API_URL")
        self.api_key = api_key or os.getenv("PROXI_API_KEY")
        self.default_model = default_model
        
        if not self.api_url:
            raise ValueError("PROXI_API_URL не установлен")
        
        # Если API ключ не указан, работаем без него (публичный прокси)
        self.use_auth = self.api_key is not None
        
        print(f"✓ ProxiAPI клиент инициализирован: {self.api_url}")
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
        
        try:
            response = requests.post(
                self.api_url,
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
            raise Exception(f"Ошибка запроса к ProxiAPI: {e}")
    
    def get_embeddings(
        self, 
        texts: List[str], 
        model: str = "text-embedding-ada-002"
    ) -> List[List[float]]:
        """
        Получение векторных представлений текстов через ProxiAPI.
        
        Args:
            texts: список текстов для векторизации
            model: модель для embeddings
            
        Returns:
            список векторов
        """
        # ProxiAPI может не поддерживать embeddings напрямую
        # В таком случае используем fallback через sentence-transformers
        try:
            payload = {
                "model": model,
                "input": texts
            }
            
            response = requests.post(
                f"{self.api_url}/embeddings",
                headers=self._get_headers(),
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            
            if 'data' in data:
                return [item['embedding'] for item in data['data']]
            else:
                raise Exception("Embeddings не поддерживаются этим прокси")
                
        except Exception as e:
            # Fallback: используем локальные sentence-transformers
            print(f"⚠️  Embeddings через ProxiAPI недоступны, используется fallback")
            return self._fallback_embeddings(texts)
    
    def _fallback_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Fallback для создания embeddings через sentence-transformers.
        
        Args:
            texts: список текстов
            
        Returns:
            список векторов
        """
        try:
            from sentence_transformers import SentenceTransformer
            
            # Загрузка предобученной модели
            model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            
            # Создание embeddings
            embeddings = model.encode(texts, convert_to_numpy=True)
            
            # Преобразование в список списков
            return embeddings.tolist()
            
        except ImportError:
            raise Exception(
                "Для fallback embeddings установите: pip install sentence-transformers"
            )
        except Exception as e:
            # Крайний fallback: простые хэш-based embeddings
            print(f"⚠️  Используется простой хэш-based fallback")
            import hashlib
            embeddings = []
            for text in texts:
                hash_obj = hashlib.sha256(text.encode())
                hash_bytes = hash_obj.digest()
                vector = []
                for i in range(768):
                    vector.append((hash_bytes[i % len(hash_bytes)] / 255.0) - 0.5)
                embeddings.append(vector)
            return embeddings
    
    def get_models(self) -> List[Dict[str, Any]]:
        """
        Получение списка доступных моделей через ProxiAPI.
        
        Returns:
            список моделей
        """
        try:
            response = requests.get(
                f"{self.api_url}/models",
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
