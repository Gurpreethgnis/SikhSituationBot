import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add server directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'server'))

from retrieval import find_similar_shabads


class TestRetrieval(unittest.TestCase):
    """Unit tests for retrieval functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_embedding = [0.1, 0.2, 0.3] * 256  # 768-dim vector
        self.test_shabad = MagicMock()
        self.test_shabad.id = 1
        self.test_shabad.shabad_id = 'test-123'
        self.test_shabad.gurmukhi = 'test gurmukhi'
        self.test_shabad.english_translation = 'test english'
        self.test_shabad.source = 'test source'
        self.test_shabad.embedding = self.test_embedding
        self.test_shabads = [self.test_shabad]

    @patch('retrieval.Shabad')
    def test_find_similar_shabads_success(self, mock_shabad_class):
        """Test successful similar shabad search."""
        # Mock the query chain
        mock_query = MagicMock()
        mock_shabad_class.query = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = self.test_shabads

        result = find_similar_shabads(self.test_embedding, limit=5)

        self.assertEqual(result, self.test_shabads)
        mock_query.order_by.assert_called_once()
        mock_query.limit.assert_called_once_with(5)
        mock_query.all.assert_called_once()

    @patch('retrieval.Shabad')
    def test_find_similar_shabads_with_persona(self, mock_shabad_class):
        """Test similar shabad search with persona filter."""
        # Mock the query chain
        mock_query = MagicMock()
        mock_shabad_class.query = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = self.test_shabads

        result = find_similar_shabads(self.test_embedding, limit=3, persona='adult')

        self.assertEqual(result, self.test_shabads)
        # Should call filter once for persona
        mock_query.filter.assert_called_once_with(mock_shabad_class.recommended_persona == 'adult')
        mock_query.order_by.assert_called_once()
        mock_query.limit.assert_called_once_with(3)

    def test_find_similar_shabads_empty_embedding(self):
        """Test search with empty embedding."""
        result = find_similar_shabads([])
        self.assertEqual(result, [])

    @patch('retrieval.Shabad')
    def test_find_similar_shabads_db_error(self, mock_shabad_class):
        """Test search when database error occurs."""
        # Mock a database error by making order_by raise an exception
        from sqlalchemy.exc import SQLAlchemyError
        mock_query = MagicMock()
        mock_query.order_by.side_effect = SQLAlchemyError("Database connection failed")
        mock_shabad_class.query = mock_query

        result = find_similar_shabads(self.test_embedding)

        self.assertEqual(result, [])


if __name__ == '__main__':
    unittest.main()

    def test_format_shabad_context_complete(self):
        """Test formatting shabad context with all fields."""
        result = format_shabad_context(self.test_shabad)

        self.assertIn('Gurmukhi:', result)
        self.assertIn('test gurmukhi', result)
        self.assertIn('English:', result)
        self.assertIn('test english', result)
        self.assertIn('Punjabi:', result)
        self.assertIn('test punjabi', result)
        self.assertIn('Hindi:', result)
        self.assertIn('test hindi', result)
        self.assertIn('Roman:', result)
        self.assertIn('test roman', result)
        self.assertIn('Translation:', result)
        self.assertIn('test translation', result)
        self.assertIn('Explanation:', result)
        self.assertIn('test explanation', result)
        self.assertIn('Source:', result)
        self.assertIn('test source', result)
        self.assertIn('Section:', result)
        self.assertIn('test section', result)

    def test_format_shabad_context_minimal(self):
        """Test formatting shabad context with minimal fields."""
        minimal_shabad = {
            'id': 1,
            'gurmukhi': 'minimal gurmukhi',
            'english': 'minimal english'
        }

        result = format_shabad_context(minimal_shabad)

        self.assertIn('Gurmukhi:', result)
        self.assertIn('minimal gurmukhi', result)
        self.assertIn('English:', result)
        self.assertIn('minimal english', result)
        # Should not include fields that are None or missing
        self.assertNotIn('Punjabi:', result)
        self.assertNotIn('Translation:', result)

    def test_format_shabad_context_empty(self):
        """Test formatting shabad context with empty dict."""
        result = format_shabad_context({})

        self.assertEqual(result, "")

    def test_format_shabad_context_none(self):
        """Test formatting shabad context with None."""
        result = format_shabad_context(None)

        self.assertEqual(result, "")

    @patch('retrieval.get_embedding')
    @patch('retrieval.db.session')
    def test_search_similar_shabads_database_error(self, mock_session, mock_get_embedding):
        """Test search when database query fails."""
        mock_get_embedding.return_value = self.test_embedding
        mock_session.query.side_effect = Exception("Database connection failed")

        result = search_similar_shabads(self.test_query)

        self.assertEqual(result, [])
        mock_get_embedding.assert_called_once_with(self.test_query)

    @patch('retrieval.db.session')
    def test_get_shabad_by_id_database_error(self, mock_session):
        """Test shabad retrieval when database fails."""
        mock_session.query.side_effect = Exception("Database connection failed")

        result = get_shabad_by_id(1)

        self.assertIsNone(result)

    @patch('retrieval.db.session')
    def test_get_random_shabads_database_error(self, mock_session):
        """Test random shabad retrieval when database fails."""
        mock_session.query.side_effect = Exception("Database connection failed")

        result = get_random_shabads(3)

        self.assertEqual(result, [])

    @patch('retrieval.get_embedding')
    @patch('retrieval.db.session')
    def test_search_similar_shabads_with_limit(self, mock_session, mock_get_embedding):
        """Test search with custom limit."""
        mock_get_embedding.return_value = self.test_embedding

        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = self.test_shabads

        result = search_similar_shabads(self.test_query, limit=10)

        self.assertEqual(result, self.test_shabads)
        # Verify limit was called with 10
        mock_query.limit.assert_called_with(10)

    @patch('retrieval.get_embedding')
    @patch('retrieval.db.session')
    def test_search_similar_shabads_default_limit(self, mock_session, mock_get_embedding):
        """Test search with default limit."""
        mock_get_embedding.return_value = self.test_embedding

        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = self.test_shabads

        result = search_similar_shabads(self.test_query)

        self.assertEqual(result, self.test_shabads)
        # Verify limit was called with default 5
        mock_query.limit.assert_called_with(5)


if __name__ == '__main__':
    unittest.main()