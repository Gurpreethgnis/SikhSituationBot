import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add server directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'server'))

from retrieval import find_similar_shabads, find_shabads_by_text_match


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
        mock_shabad_class.recommended_persona.in_.assert_called_once_with(['adult', 'any'])
        mock_query.order_by.assert_called_once()
        mock_query.limit.assert_called_once_with(3)

    def test_find_similar_shabads_empty_embedding(self):
        """Test search with empty embedding."""
        result = find_similar_shabads([])
        self.assertEqual(result, [])

    @patch('retrieval.Shabad')
    def test_find_similar_shabads_db_error(self, mock_shabad_class):
        """Test search when database error occurs."""
        from sqlalchemy.exc import SQLAlchemyError

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.side_effect = SQLAlchemyError("Database connection failed")
        mock_shabad_class.query = mock_query

        result = find_similar_shabads(self.test_embedding)

        self.assertEqual(result, [])

    @patch('retrieval.Shabad')
    def test_find_similar_shabads_parmaan_quality_overfetch(self, mock_shabad_class):
        """Parmaan mode requests more candidates before trimming to limit."""
        mock_query = MagicMock()
        mock_shabad_class.query = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        doubled = self.test_shabads + self.test_shabads
        mock_query.all.return_value = doubled

        result = find_similar_shabads(
            self.test_embedding, limit=2, exclude_parmaan_low_quality=True
        )
        self.assertEqual(len(result), 2)
        # min(max(2*8, 24), 120) == 24
        mock_query.limit.assert_called_once_with(24)

    def test_find_shabads_by_text_match_short_query(self):
        """Text match returns empty for very short queries."""
        self.assertEqual(find_shabads_by_text_match("ab"), [])

    @patch("retrieval.Shabad")
    def test_find_shabads_by_text_match_db_error(self, mock_shabad_class):
        from sqlalchemy.exc import SQLAlchemyError

        mock_query = MagicMock()
        mock_shabad_class.query = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.side_effect = SQLAlchemyError("fail")

        result = find_shabads_by_text_match("waheguru ji")
        self.assertEqual(result, [])


if __name__ == '__main__':
    unittest.main()