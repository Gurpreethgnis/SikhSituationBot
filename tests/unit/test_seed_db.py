import os
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys

# Add server directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'server'))

from seed_db import (
    seed_database,
    validate_shabad_data,
    get_embedding_content,
    check_duplicate_shabad,
    SeedingStats
)


class TestSeedDatabase(unittest.TestCase):
    """Unit tests for database seeding functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_shabad = {
            "shabad_id": "test-1",
            "gurmukhi": "ਤਪਤਿ ਮਾਹਿ ਠਾਢਿ ਵਰਤਾਈ ॥",
            "romanization": "tapat maahi thaadh varataaee ||",
            "english_translation": "In the midst of the burning heat, a cooling breeze has begun to blow.",
            "context_tags": ["anxiety", "peace", "calm"],
            "source": "SGGS Page 1",
            "recommended_persona": "any"
        }

        self.invalid_shabad = {
            "shabad_id": "test-2",
            "gurmukhi": "",  # Missing required field
            "english_translation": "Some translation"
        }

    def test_validate_shabad_data_valid(self):
        """Test validation of valid shabad data."""
        self.assertTrue(validate_shabad_data(self.valid_shabad))

    def test_validate_shabad_data_invalid(self):
        """Test validation of invalid shabad data."""
        self.assertFalse(validate_shabad_data(self.invalid_shabad))

        # Test missing english_translation
        invalid_no_translation = self.valid_shabad.copy()
        del invalid_no_translation['english_translation']
        self.assertFalse(validate_shabad_data(invalid_no_translation))

    def test_get_embedding_content(self):
        """Test extraction of content for embedding."""
        content = get_embedding_content(self.valid_shabad)

        # Should include english translation
        self.assertIn("burning heat", content)
        # Should include context tags
        self.assertIn("anxiety", content)
        self.assertIn("peace", content)
        self.assertIn("calm", content)

    def test_get_embedding_content_minimal(self):
        """Test embedding content with minimal data."""
        minimal_shabad = {
            "english_translation": "Short translation"
        }
        content = get_embedding_content(minimal_shabad)
        self.assertEqual(content, "Short translation")

    @patch('seed_db.Shabad')
    def test_check_duplicate_shabad_no_duplicate(self, mock_shabad_class):
        """Test duplicate checking when no duplicate exists."""
        mock_shabad_class.query.filter.return_value.first.return_value = None
        result = check_duplicate_shabad("test-id", "test-gurmukhi")
        self.assertFalse(result)

    @patch('seed_db.Shabad')
    def test_check_duplicate_shabad_found_duplicate(self, mock_shabad_class):
        """Test duplicate checking when duplicate exists."""
        mock_duplicate = MagicMock()
        mock_shabad_class.query.filter.return_value.first.return_value = mock_duplicate
        result = check_duplicate_shabad("test-id", "test-gurmukhi")
        self.assertTrue(result)

    @patch('seed_db.Shabad')
    @patch('seed_db.logger')
    def test_check_duplicate_shabad_error(self, mock_logger, mock_shabad_class):
        """Test duplicate checking when database error occurs."""
        mock_shabad_class.query.filter.side_effect = Exception("DB error")
        result = check_duplicate_shabad("test-id", "test-gurmukhi")
        self.assertFalse(result)
        mock_logger.error.assert_called()

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    @patch('seed_db.app')
    @patch('seed_db.db')
    @patch('seed_db.get_embedding')
    @patch('seed_db.check_duplicate_shabad')
    @patch('seed_db.Shabad')
    def test_seed_database_success(self, mock_shabad_class, mock_check_dup, mock_get_embedding,
                                  mock_db, mock_app, mock_json_load, mock_file, mock_exists):
        """Test successful database seeding."""
        # Setup mocks
        mock_exists.return_value = True
        mock_json_load.return_value = [self.valid_shabad]
        mock_check_dup.return_value = False

        mock_app.app_context.return_value.__enter__ = MagicMock()
        mock_app.app_context.return_value.__exit__ = MagicMock()

        mock_embedding = [0.1, 0.2, 0.3] * 256  # 768-dim vector
        mock_get_embedding.return_value = mock_embedding

        mock_shabad_instance = MagicMock()
        mock_shabad_class.return_value = mock_shabad_instance

        # Mock database session
        mock_session = MagicMock()
        mock_db.session = mock_session

        # Execute
        stats = seed_database("test.json", batch_size=10)

        # Assertions
        self.assertEqual(stats.total_processed, 1)
        self.assertEqual(stats.successful_embeddings, 1)
        self.assertEqual(stats.failed_embeddings, 0)
        self.assertEqual(stats.duplicates_skipped, 0)

        # Verify database operations
        mock_session.add_all.assert_called()
        mock_session.commit.assert_called()

    @patch('os.path.exists')
    def test_seed_database_file_not_found(self, mock_exists):
        """Test seeding when data file doesn't exist."""
        mock_exists.return_value = False

        stats = seed_database("nonexistent.json")

        self.assertEqual(stats.total_processed, 0)
        self.assertEqual(stats.successful_embeddings, 0)

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_seed_database_invalid_json(self, mock_json_load, mock_file, mock_exists):
        """Test seeding with invalid JSON file."""
        mock_exists.return_value = True
        mock_json_load.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

        stats = seed_database("invalid.json")

        self.assertEqual(stats.total_processed, 0)

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    @patch('seed_db.app')
    @patch('seed_db.db')
    @patch('seed_db.get_embedding')
    @patch('seed_db.check_duplicate_shabad')
    def test_seed_database_embedding_failure(self, mock_check_dup, mock_get_embedding, mock_db, mock_app,
                                           mock_json_load, mock_file, mock_exists):
        """Test seeding when embedding generation fails."""
        # Setup mocks
        mock_exists.return_value = True
        mock_json_load.return_value = [self.valid_shabad]
        mock_check_dup.return_value = False

        mock_app.app_context.return_value.__enter__ = MagicMock()
        mock_app.app_context.return_value.__exit__ = MagicMock()

        mock_get_embedding.return_value = None  # Embedding failure

        # Mock database session
        mock_session = MagicMock()
        mock_db.session = mock_session

        # Execute
        stats = seed_database("test.json")

        # Assertions
        self.assertEqual(stats.total_processed, 1)
        self.assertEqual(stats.successful_embeddings, 0)
        self.assertEqual(stats.failed_embeddings, 1)

    def test_seeding_stats(self):
        """Test SeedingStats dataclass functionality."""
        import time

        stats = SeedingStats()
        stats.start_time = time.time()
        stats.total_processed = 10
        stats.successful_embeddings = 8
        stats.failed_embeddings = 2

        # Test elapsed time calculation
        elapsed = stats.get_elapsed_time()
        self.assertGreaterEqual(elapsed, 0)

        # Test success rate calculation
        rate = stats.get_success_rate()
        self.assertEqual(rate, 80.0)

        # Test empty stats
        empty_stats = SeedingStats()
        self.assertEqual(empty_stats.get_success_rate(), 0.0)


if __name__ == '__main__':
    unittest.main()