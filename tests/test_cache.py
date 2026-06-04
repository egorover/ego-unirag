"""
Unit тесты для модуля кеша (RAGCache).
"""

import unittest
import os
import tempfile
import json
from datetime import datetime
import sys

# Добавляем путь к модулям assistant_proxy_api
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'assistant_proxy_api'))

from cache import RAGCache


class TestRAGCache(unittest.TestCase):
    """Тесты для класса RAGCache."""
    
    def setUp(self):
        """Настройка перед каждым тестом."""
        # Создаём временный файл для БД
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.cache = RAGCache(db_path=self.temp_db.name)
    
    def tearDown(self):
        """Очистка после каждого теста."""
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)
    
    def test_set_and_get(self):
        """Тест сохранения и получения записи."""
        query = "Какой капитал Москвы?"
        answer = "Москва имеет большой капитал."
        context = ["doc1", "doc2"]
        
        self.cache.set(query, answer, context)
        result = self.cache.get(query)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['query'], query)
        self.assertEqual(result['answer'], answer)
        self.assertEqual(result['context'], context)
        self.assertTrue(result['from_cache'])
    
    def test_get_nonexistent(self):
        """Тест получения несуществующей записи."""
        result = self.cache.get("Несуществующий вопрос")
        self.assertIsNone(result)
    
    def test_case_insensitive_hash(self):
        """Тест чувствительности к регистру."""
        query1 = "Какой капитал Москвы?"
        query2 = "какой капитал москвы?"
        
        self.cache.set(query1, "Ответ 1", None)
        result2 = self.cache.get(query2)
        
        # Хеши должны совпадать из-за нормализации
        self.assertIsNotNone(result2)
        self.assertEqual(result2['answer'], "Ответ 1")
    
    def test_clear(self):
        """Тест очистки кеша."""
        self.cache.set("Вопрос 1", "Ответ 1", None)
        self.cache.set("Вопрос 2", "Ответ 2", None)
        
        stats_before = self.cache.get_stats()
        self.assertEqual(stats_before['total_entries'], 2)
        
        self.cache.clear()
        
        stats_after = self.cache.get_stats()
        self.assertEqual(stats_after['total_entries'], 0)
        
        # Проверка, что записи действительно удалены
        result = self.cache.get("Вопрос 1")
        self.assertIsNone(result)
    
    def test_update_existing(self):
        """Тест обновления существующей записи."""
        query = "Вопрос"
        self.cache.set(query, "Ответ 1", None)
        
        # Обновляем ответ
        self.cache.set(query, "Ответ 2", None)
        
        result = self.cache.get(query)
        self.assertEqual(result['answer'], "Ответ 2")
    
    def test_stats(self):
        """Тест получения статистики."""
        self.cache.set("Вопрос", "Ответ", ["ctx1"])
        
        stats = self.cache.get_stats()
        
        self.assertIn('total_entries', stats)
        self.assertIn('db_size_mb', stats)
        self.assertGreaterEqual(stats['total_entries'], 1)


if __name__ == '__main__':
    unittest.main()
