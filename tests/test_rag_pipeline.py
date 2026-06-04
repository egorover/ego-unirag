"""
Интеграционные тесты для RAG Pipeline.
"""

import unittest
import os
import tempfile
import sys
from unittest.mock import Mock, patch, MagicMock

# Добавляем путь к модулям assistant_proxy_api
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'assistant_proxy_api'))

from rag_pipeline import RAGPipeline


class TestRAGPipeline(unittest.TestCase):
    """Тесты для класса RAGPipeline."""
    
    def setUp(self):
        """Настройка перед каждым тестом."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_env = os.environ.get('PROXI_API_URL')
        os.environ['PROXI_API_URL'] = 'http://test-api-url.com'
    
    def tearDown(self):
        """Очистка после каждого теста."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        
        # Восстанавливаем окружение
        if self.original_env:
            os.environ['PROXI_API_URL'] = self.original_env
        else:
            os.environ.pop('PROXI_API_URL', None)
    
    @patch('rag_pipeline.ProxyAPIClient')
    @patch('rag_pipeline.VectorStore')
    @patch('rag_pipeline.RAGCache')
    def test_init(self, mock_cache, mock_vector_store, mock_proxy_client):
        """Тест инициализации pipeline."""
        mock_proxy_client.return_value = Mock()
        mock_vector_store.return_value.collection.count.return_value = 0
        mock_cache.return_value = Mock()
        
        pipeline = RAGPipeline(
            collection_name="test_collection",
            cache_db_path=os.path.join(self.temp_dir, "test_cache.db"),
            model="test-model"
        )
        
        self.assertEqual(pipeline.model, "test-model")
        self.assertIsNotNone(pipeline.proxy_client)
        self.assertIsNotNone(pipeline.vector_store)
        self.assertIsNotNone(pipeline.cache)
    
    @patch('rag_pipeline.ProxyAPIClient')
    @patch('rag_pipeline.VectorStore')
    @patch('rag_pipeline.RAGCache')
    def test_query_not_from_cache(self, mock_cache, mock_vector_store, mock_proxy_client):
        """Тест запроса, не найденного в кеше."""
        mock_proxy_client.return_value = Mock()
        mock_proxy_client.return_value.chat_completion.return_value = "Тестовый ответ"
        
        mock_vector_store.return_value.collection.count.return_value = 0
        mock_vector_store.return_value.search.return_value = [
            {'text': 'Контекст 1'},
            {'text': 'Контекст 2'}
        ]
        
        mock_cache_instance = Mock()
        mock_cache_instance.get.return_value = None  # Нет в кеше
        mock_cache.return_value = mock_cache_instance
        
        pipeline = RAGPipeline(
            collection_name="test",
            cache_db_path=os.path.join(self.temp_dir, "test_cache.db"),
            model="test-model"
        )
        
        result = pipeline.query("Тестовый вопрос", use_cache=True)
        
        self.assertEqual(result['query'], "Тестовый вопрос")
        self.assertEqual(result['answer'], "Тестовый ответ")
        self.assertFalse(result['from_cache'])
        self.assertEqual(len(result['context_docs']), 2)
        self.assertEqual(result['model'], "test-model")
        self.assertEqual(result['mode'], "ProxiAPI")
        
        # Проверка, что кеш был обновлён
        mock_cache_instance.set.assert_called_once()
    
    @patch('rag_pipeline.ProxyAPIClient')
    @patch('rag_pipeline.VectorStore')
    @patch('rag_pipeline.RAGCache')
    def test_query_from_cache(self, mock_cache, mock_vector_store, mock_proxy_client):
        """Тест запроса из кеша."""
        mock_proxy_client.return_value = Mock()
        mock_vector_store.return_value.collection.count.return_value = 0
        
        cached_result = {
            'answer': 'Кэшированный ответ',
            'context': ['ctx1'],
            'created_at': '2024-01-01'
        }
        mock_cache_instance = Mock()
        mock_cache_instance.get.return_value = cached_result
        mock_cache.return_value = mock_cache_instance
        
        pipeline = RAGPipeline(
            collection_name="test",
            cache_db_path=os.path.join(self.temp_dir, "test_cache.db"),
            model="test-model"
        )
        
        result = pipeline.query("Вопрос из кеша", use_cache=True)
        
        self.assertTrue(result['from_cache'])
        self.assertEqual(result['answer'], 'Кэшированный ответ')
        self.assertEqual(result['cached_at'], '2024-01-01')
        
        # Vector search не должен вызываться
        mock_vector_store.return_value.search.assert_not_called()
        # Chat completion не должен вызываться
        mock_proxy_client.return_value.chat_completion.assert_not_called()
    
    @patch('rag_pipeline.ProxyAPIClient')
    @patch('rag_pipeline.VectorStore')
    @patch('rag_pipeline.RAGCache')
    def test_query_with_cache_disabled(self, mock_cache, mock_vector_store, mock_proxy_client):
        """Тест запроса с отключённым кешем."""
        mock_proxy_client.return_value = Mock()
        mock_proxy_client.return_value.chat_completion.return_value = "Ответ без кеша"
        
        mock_vector_store.return_value.collection.count.return_value = 0
        mock_vector_store.return_value.search.return_value = [{'text': 'Контекст'}]
        
        mock_cache.return_value = Mock()
        
        pipeline = RAGPipeline(
            collection_name="test",
            cache_db_path=os.path.join(self.temp_dir, "test_cache.db"),
            model="test-model"
        )
        
        result = pipeline.query("Вопрос", use_cache=False)
        
        self.assertFalse(result['from_cache'])
        
        # Кеш не должен использоваться вообще
        mock_cache.return_value.get.assert_not_called()
        mock_cache.return_value.set.assert_not_called()
    
    @patch('rag_pipeline.ProxyAPIClient')
    @patch('rag_pipeline.VectorStore')
    @patch('rag_pipeline.RAGCache')
    def test_create_prompt(self, mock_cache, mock_vector_store, mock_proxy_client):
        """Тест создания промпта."""
        mock_proxy_client.return_value = Mock()
        mock_vector_store.return_value.collection.count.return_value = 0
        mock_cache.return_value = Mock()
        
        pipeline = RAGPipeline(
            collection_name="test",
            cache_db_path=os.path.join(self.temp_dir, "test_cache.db"),
            model="test-model"
        )
        
        query = "Какой капитал России?"
        context_docs = [
            {'text': 'Москва - столица России'},
            {'text': 'Капитал - это экономическое понятие'}
        ]
        
        prompt = pipeline._create_prompt(query, context_docs)
        
        self.assertIn('Москва - столица России', prompt)
        self.assertIn('Какой капитал России?', prompt)
        self.assertIn('Ты - полезный AI ассистент', prompt)
    
    @patch('rag_pipeline.ProxyAPIClient')
    @patch('rag_pipeline.VectorStore')
    @patch('rag_pipeline.RAGCache')
    def test_get_stats(self, mock_cache, mock_vector_store, mock_proxy_client):
        """Тест получения статистики."""
        mock_proxy_client.return_value = Mock()
        mock_vector_store.return_value.collection.count.return_value = 10
        mock_vector_store.return_value.get_collection_stats.return_value = {
            'name': 'test_collection',
            'count': 10,
            'persist_directory': self.temp_dir
        }
        mock_cache_instance = Mock()
        mock_cache_instance.get_stats.return_value = {
            'total_entries': 5,
            'db_size_mb': 0.1
        }
        mock_cache.return_value = mock_cache_instance
        
        pipeline = RAGPipeline(
            collection_name="test",
            cache_db_path=os.path.join(self.temp_dir, "test_cache.db"),
            model="test-model"
        )
        
        stats = pipeline.get_stats()
        
        self.assertIn('vector_store', stats)
        self.assertIn('cache', stats)
        self.assertEqual(stats['model'], "test-model")
        self.assertEqual(stats['mode'], "ProxiAPI")
        self.assertEqual(stats['vector_store']['count'], 10)


if __name__ == '__main__':
    unittest.main()
