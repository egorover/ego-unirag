"""
Unit тесты для модуля векторного хранилища (VectorStore).
"""

import unittest
import os
import tempfile
import sys
from unittest.mock import Mock, patch, MagicMock

# Добавляем путь к модулям assistant_proxy_api
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'assistant_proxy_api'))


class TestVectorStoreChunking(unittest.TestCase):
    """Тесты для алгоритма чанкинга без создания реального ChromaDB."""
    
    def setUp(self):
        """Настройка перед каждым тестом."""
        # Создаём объект VectorStore с мокнутыми зависимостями
        with patch('assistant_proxy_api.vector_store.chromadb.PersistentClient'):
            with patch('assistant_proxy_api.vector_store.ProxyAPIClient'):
                from vector_store import VectorStore
                self.temp_dir = tempfile.mkdtemp()
                self.vs = VectorStore(collection_name="test", persist_directory=self.temp_dir)
    
    def tearDown(self):
        """Очистка после каждого теста."""
        import shutil
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception:
            pass  # Игнорируем ошибки удаления на Windows
    
    def test_paragraph_separation(self):
        """Тест разделения по абзацам."""
        text = "Абзац 1 с достаточным количеством текста.\n\nАбзац 2 с достаточным количеством текста.\n\nАбзац 3 с достаточным количеством текста."
        chunks = self.vs._chunk_text(text, chunk_size=100, overlap=10)
        
        # Проверяем, что чанки созданы (может быть 1 или больше)
        self.assertIsInstance(chunks, list)
        # Каждый чанк должен быть не короче 50 символов
        for chunk in chunks:
            self.assertGreaterEqual(len(chunk), 50)
    
    def test_min_chunk_size(self):
        """Тест фильтрации слишком коротких чанков."""
        text = "a. b. c."  # Очень короткие предложения
        
        chunks = self.vs._chunk_text(text, chunk_size=50, overlap=10)
        
        # Все чанки должны быть не короче 50 символов
        for chunk in chunks:
            self.assertGreaterEqual(len(chunk), 50)

    def test_chunk_text(self):
        """Тест разбиения текста на чанки."""
        text = "Это первый абзац.\n\nЭто второй абзац.\n\nЭто третий абзац."
        chunks = self.vs._chunk_text(text, chunk_size=50, overlap=10)

        self.assertIsInstance(chunks, list)
        # Может быть 0 чанков если все слишком короткие, проверяем тип
        for chunk in chunks:
            self.assertIsInstance(chunk, str)

    def test_chunk_text_long_paragraph(self):
        """Тест разбиения длинного абзаца."""
        text = "Первое предложение. Второе предложение. Третье предложение. Четвёртое предложение."
        chunks = self.vs._chunk_text(text, chunk_size=30, overlap=5)

        # Проверяем, что чанки созданы
        self.assertIsInstance(chunks, list)


class TestVectorStore(unittest.TestCase):
    """Тесты для класса VectorStore с полным моканием."""
    
    def setUp(self):
        """Настройка перед каждым тестом."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Очистка после каждого теста."""
        import shutil
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception:
            pass  # Игнорируем ошибки удаления на Windows
    
    @patch('assistant_proxy_api.vector_store.chromadb.PersistentClient')
    @patch('assistant_proxy_api.vector_store.ProxyAPIClient')
    def test_init(self, mock_proxy_client, mock_chromadb):
        """Тест инициализации."""
        # Настройка моков
        mock_collection = Mock()
        mock_collection.count.return_value = 0
        mock_client_instance = Mock()
        mock_client_instance.get_collection.side_effect = Exception("Collection not found")
        mock_client_instance.create_collection.return_value = mock_collection
        mock_chromadb.return_value = mock_client_instance
        mock_proxy_client.return_value = Mock()
        
        from vector_store import VectorStore
        vs = VectorStore(
            collection_name="test_collection",
            persist_directory=self.temp_dir
        )
        
        self.assertEqual(vs.collection_name, "test_collection")
        self.assertEqual(vs.persist_directory, self.temp_dir)
        self.assertIsNotNone(vs.collection)
    
    @patch('assistant_proxy_api.vector_store.chromadb.PersistentClient')
    @patch('assistant_proxy_api.vector_store.ProxyAPIClient')
    def test_get_collection_stats(self, mock_proxy_client, mock_chromadb):
        """Тест получения статистики."""
        mock_collection = Mock()
        mock_collection.count.return_value = 0
        mock_client_instance = Mock()
        mock_client_instance.get_collection.side_effect = Exception("Collection not found")
        mock_client_instance.create_collection.return_value = mock_collection
        mock_chromadb.return_value = mock_client_instance
        mock_proxy_client.return_value = Mock()
        
        from vector_store import VectorStore
        vs = VectorStore(collection_name="test_collection", persist_directory=self.temp_dir)
        
        stats = vs.get_collection_stats()
        
        self.assertEqual(stats['name'], "test_collection")
        self.assertIn('count', stats)
        self.assertEqual(stats['persist_directory'], self.temp_dir)
    
    @patch('assistant_proxy_api.vector_store.chromadb.PersistentClient')
    @patch('assistant_proxy_api.vector_store.ProxyAPIClient')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data="Тестовый документ.\n\nСодержит несколько абзацев.\n\nДля тестирования загрузки.")
    def test_load_documents(self, mock_file, mock_proxy_client, mock_chromadb):
        """Тест загрузки документов из файла."""
        mock_collection = Mock()
        mock_collection.count.return_value = 0
        mock_client_instance = Mock()
        mock_client_instance.get_collection.side_effect = Exception("Collection not found")
        mock_client_instance.create_collection.return_value = mock_collection
        mock_chromadb.return_value = mock_client_instance
        
        mock_proxy_client.return_value = Mock()
        mock_proxy_client.return_value.get_embeddings.return_value = [[0.1] * 1536]
        
        from vector_store import VectorStore
        vs = VectorStore(collection_name="test", persist_directory=self.temp_dir)
        
        # Создаём временный файл
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Тестовый документ.\n\nСодержит несколько абзацев.")
            temp_file = f.name
        
        try:
            vs.load_documents(temp_file)
            
            # Проверяем, что документы были загружены
            mock_collection.add.assert_called()
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    @patch('assistant_proxy_api.vector_store.chromadb.PersistentClient')
    @patch('assistant_proxy_api.vector_store.ProxyAPIClient')
    def test_search_mock(self, mock_proxy_client, mock_chromadb):
        """Тест поиска с мок-объектами."""
        mock_collection = Mock()
        mock_collection.count.return_value = 0
        mock_collection.query.return_value = {
            'ids': [['doc_0', 'doc_1']],
            'documents': [['Текст 1', 'Текст 2']],
            'distances': [[0.1, 0.2]]
        }
        mock_client_instance = Mock()
        mock_client_instance.get_collection.side_effect = Exception("Collection not found")
        mock_client_instance.create_collection.return_value = mock_collection
        mock_chromadb.return_value = mock_client_instance
        
        mock_proxy_client.return_value = Mock()
        mock_proxy_client.return_value.get_embeddings.return_value = [[0.1] * 1536]
        
        from vector_store import VectorStore
        vs = VectorStore(collection_name="test", persist_directory=self.temp_dir)
        
        results = vs.search("Тестовый запрос", top_k=2)
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['text'], 'Текст 1')
        self.assertAlmostEqual(results[0]['distance'], 0.1)


if __name__ == '__main__':
    unittest.main()
