import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add server directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'server'))

from vector_utils import (
    get_embedding,
    get_embedding_gemini,
    get_embedding_local,
    _calculate_backoff_delay,
    _load_local_model
)


class TestVectorUtils(unittest.TestCase):
    """Unit tests for vector utility functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_text = "This is a test text for embedding"
        self.test_embedding = [0.1, 0.2, 0.3] * 256  # 768-dim vector

    def test_calculate_backoff_delay(self):
        """Test exponential backoff delay calculation."""
        # First retry
        delay1 = _calculate_backoff_delay(0)
        self.assertGreaterEqual(delay1, 1.0)
        self.assertLessEqual(delay1, 2.0)

        # Second retry
        delay2 = _calculate_backoff_delay(1)
        self.assertGreaterEqual(delay2, 2.0)
        self.assertLessEqual(delay2, 4.0)

        # High retry count
        delay_high = _calculate_backoff_delay(5)
        self.assertLessEqual(delay_high, 11.0)  # Max delay with jitter

    @patch('vector_utils.GEMINI_API_KEY', 'test-key')
    @patch('vector_utils.genai')
    def test_get_embedding_gemini_success(self, mock_genai):
        """Test successful Gemini embedding generation."""
        # Mock the API response - Gemini returns a dict-like object
        mock_result = {'embedding': self.test_embedding}
        mock_genai.embed_content.return_value = mock_result

        result = get_embedding_gemini(self.test_text)

        self.assertEqual(result, self.test_embedding)
        mock_genai.embed_content.assert_called_once()

    @patch('vector_utils.GEMINI_API_KEY', None)
    def test_get_embedding_gemini_no_api_key(self):
        """Test Gemini embedding when API key is not available."""
        result = get_embedding_gemini(self.test_text)
        self.assertIsNone(result)

    @patch('vector_utils.GEMINI_API_KEY', 'test-key')
    @patch('vector_utils.genai')
    @patch('vector_utils.time.sleep')
    def test_get_embedding_gemini_rate_limit_retry(self, mock_sleep, mock_genai):
        """Test Gemini embedding with rate limit retry."""
        # Mock rate limit exception, then success
        mock_genai.embed_content.side_effect = [
            Exception("Resource exhausted"),  # Rate limit
            {'embedding': self.test_embedding}  # Success
        ]

        result = get_embedding_gemini(self.test_text)

        self.assertEqual(result, self.test_embedding)
        self.assertEqual(mock_genai.embed_content.call_count, 2)
        mock_sleep.assert_called_once()

    @patch('vector_utils.GEMINI_API_KEY', 'test-key')
    @patch('vector_utils.genai')
    @patch('vector_utils.time.sleep')
    def test_get_embedding_gemini_max_retries_exceeded(self, mock_sleep, mock_genai):
        """Test Gemini embedding when max retries are exceeded."""
        # Always raise exception
        mock_genai.embed_content.side_effect = Exception("Service unavailable")

        result = get_embedding_gemini(self.test_text)

        self.assertIsNone(result)
        self.assertEqual(mock_genai.embed_content.call_count, 3)  # MAX_RETRIES
        self.assertEqual(mock_sleep.call_count, 2)  # 2 retries

    @patch('vector_utils.SentenceTransformer')
    def test_get_embedding_local_success(self, mock_st_class):
        """Test successful local embedding generation."""
        mock_model = MagicMock()
        # Mock numpy array with tolist method
        mock_embedding = MagicMock()
        mock_embedding.tolist.return_value = self.test_embedding
        mock_model.encode.return_value = mock_embedding
        mock_st_class.return_value = mock_model

        result = get_embedding_local(self.test_text)

        self.assertEqual(result, self.test_embedding)
        mock_model.encode.assert_called_once_with(self.test_text, normalize_embeddings=True)

    @patch('vector_utils.SentenceTransformer')
    def test_get_embedding_local_failure(self, mock_st_class):
        """Test local embedding generation failure."""
        mock_st_class.side_effect = Exception("Model loading failed")

        result = get_embedding_local(self.test_text)

        self.assertIsNone(result)

    @patch('vector_utils.get_embedding_gemini')
    @patch('vector_utils.get_embedding_local')
    @patch('vector_utils.GEMINI_API_KEY', 'test-key')
    def test_get_embedding_prefer_gemini_success(self, mock_local, mock_gemini):
        """Test embedding with Gemini preference - Gemini succeeds."""
        mock_gemini.return_value = self.test_embedding
        mock_local.return_value = None

        result = get_embedding(self.test_text, prefer_gemini=True)

        self.assertEqual(result, self.test_embedding)
        mock_gemini.assert_called_once()
        mock_local.assert_not_called()

    @patch('vector_utils.get_embedding_gemini')
    @patch('vector_utils.get_embedding_local')
    @patch('vector_utils.GEMINI_API_KEY', 'test-key')
    def test_get_embedding_prefer_gemini_fallback(self, mock_local, mock_gemini):
        """Test embedding with Gemini preference - falls back to local."""
        mock_gemini.return_value = None
        mock_local.return_value = self.test_embedding

        result = get_embedding(self.test_text, prefer_gemini=True)

        self.assertEqual(result, self.test_embedding)
        mock_gemini.assert_called_once()
        mock_local.assert_called_once()

    @patch('vector_utils.get_embedding_gemini')
    @patch('vector_utils.get_embedding_local')
    @patch('vector_utils.GEMINI_API_KEY', None)
    def test_get_embedding_no_gemini_key(self, mock_local, mock_gemini):
        """Test embedding when Gemini API key is not available."""
        mock_gemini.return_value = None  # Gemini returns None when no API key
        mock_local.return_value = self.test_embedding

        result = get_embedding(self.test_text)

        self.assertEqual(result, self.test_embedding)
        mock_gemini.assert_called_once()  # Still called but returns None
        mock_local.assert_called_once()

    def test_get_embedding_empty_text(self):
        """Test embedding with empty text."""
        result = get_embedding("")
        self.assertIsNone(result)

        result = get_embedding(None)
        self.assertIsNone(result)

    @patch('vector_utils.get_embedding_gemini')
    @patch('vector_utils.get_embedding_local')
    @patch('vector_utils.GEMINI_API_KEY', 'test-key')
    def test_get_embedding_prefer_local(self, mock_local, mock_gemini):
        """Test embedding with local preference."""
        mock_local.return_value = self.test_embedding
        mock_gemini.return_value = None

        result = get_embedding(self.test_text, prefer_gemini=False)

        self.assertEqual(result, self.test_embedding)
        mock_local.assert_called_once()
        mock_gemini.assert_not_called()

    @patch('vector_utils.get_embedding_gemini')
    @patch('vector_utils.get_embedding_local')
    @patch('vector_utils.GEMINI_API_KEY', 'test-key')
    def test_get_embedding_prefer_local_fallback(self, mock_local, mock_gemini):
        """Test embedding with local preference - falls back to Gemini."""
        mock_local.return_value = None
        mock_gemini.return_value = self.test_embedding

        result = get_embedding(self.test_text, prefer_gemini=False)

        self.assertEqual(result, self.test_embedding)
        mock_local.assert_called_once()
        mock_gemini.assert_called_once()

    def test_get_embedding_long_text_truncation(self):
        """Test that very long text is truncated."""
        long_text = "word " * 3000  # Very long text
        self.assertGreater(len(long_text), 10000)

        with patch('vector_utils.get_embedding_gemini') as mock_gemini:
            mock_gemini.return_value = self.test_embedding
            result = get_embedding(long_text)

            # Check that truncated text was passed to Gemini
            args, kwargs = mock_gemini.call_args
            passed_text = args[0]
            self.assertLessEqual(len(passed_text), 10000)
            self.assertEqual(result, self.test_embedding)

    @patch('vector_utils._local_model', None)
    @patch('vector_utils.SentenceTransformer')
    def test_load_local_model_caching(self, mock_st_class):
        """Test that local model is cached properly."""
        mock_model = MagicMock()
        mock_st_class.return_value = mock_model

        # First call
        result1 = _load_local_model()
        self.assertEqual(result1, mock_model)
        mock_st_class.assert_called_once()

        # Second call should use cache
        result2 = _load_local_model()
        self.assertEqual(result2, mock_model)
        mock_st_class.assert_called_once()  # Still only called once


if __name__ == '__main__':
    unittest.main()