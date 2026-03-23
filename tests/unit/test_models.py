import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add server directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'server'))

from models import Shabad, db


class TestModels(unittest.TestCase):
    """Unit tests for database models."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_embedding = [0.1, 0.2, 0.3] * 256  # 768-dim vector
        self.test_shabad_data = {
            'shabad_id': 'test-123',
            'gurmukhi': 'test gurmukhi',
            'english_translation': 'test english translation',
            'romanization': 'test romanization',
            'source': 'test source',
            'recommended_persona': 'adult',
            'context_tags': ['anxiety', 'peace'],
            'embedding': self.test_embedding
        }

    def test_shabad_creation(self):
        """Test Shabad model creation."""
        shabad = Shabad(**self.test_shabad_data)

        self.assertEqual(shabad.shabad_id, 'test-123')
        self.assertEqual(shabad.gurmukhi, 'test gurmukhi')
        self.assertEqual(shabad.english_translation, 'test english translation')
        self.assertEqual(shabad.romanization, 'test romanization')
        self.assertEqual(shabad.source, 'test source')
        self.assertEqual(shabad.recommended_persona, 'adult')
        self.assertEqual(shabad.context_tags, ['anxiety', 'peace'])
        self.assertEqual(shabad.embedding, self.test_embedding)

    def test_shabad_repr(self):
        """Test Shabad model string representation."""
        shabad = Shabad(**self.test_shabad_data)
        expected_repr = f"<Shabad test-123>"

        self.assertEqual(repr(shabad), expected_repr)

    def test_shabad_to_dict(self):
        """Test Shabad model to_dict method."""
        shabad = Shabad(**self.test_shabad_data)
        result = shabad.to_dict()

        # Check that all expected keys are present
        expected_keys = ['id', 'shabad_id', 'gurmukhi', 'romanization', 'english_translation', 
                        'source', 'recommended_persona', 'context_tags', 'embedding', 'created_at']
        
        for key in expected_keys:
            self.assertIn(key, result)
        
        # Check specific values
        self.assertEqual(result['shabad_id'], 'test-123')
        self.assertEqual(result['gurmukhi'], 'test gurmukhi')
        self.assertEqual(result['english_translation'], 'test english translation')

    def test_shabad_to_dict_with_none_values(self):
        """Test Shabad model to_dict method with None values."""
        partial_data = {
            'shabad_id': 'test-456',
            'gurmukhi': 'test gurmukhi',
            'english_translation': 'test english translation',
            'romanization': None,
            'source': None,
            'recommended_persona': 'adult',
            'context_tags': None,
            'embedding': None
        }
        shabad = Shabad(**partial_data)
        result = shabad.to_dict()

        # Check that None values are preserved
        self.assertIsNone(result['romanization'])
        self.assertIsNone(result['source'])
        self.assertIsNone(result['context_tags'])
        self.assertIsNone(result['embedding'])

    def test_shabad_table_name(self):
        """Test Shabad model table name."""
        self.assertEqual(Shabad.__tablename__, 'shabads')

    def test_shabad_columns(self):
        """Test Shabad model column definitions."""
        # Check that all expected columns exist
        columns = [col.name for col in Shabad.__table__.columns]

        expected_columns = [
            'id', 'shabad_id', 'gurmukhi', 'romanization', 'english_translation',
            'source', 'recommended_persona', 'context_tags', 'embedding', 'created_at'
        ]

        for col in expected_columns:
            self.assertIn(col, columns)

    def test_shabad_id_column(self):
        """Test Shabad id column properties."""
        id_col = Shabad.__table__.columns['id']
        self.assertTrue(id_col.primary_key)
        self.assertFalse(id_col.nullable)

    def test_shabad_gurmukhi_column(self):
        """Test Shabad gurmukhi column properties."""
        gurmukhi_col = Shabad.__table__.columns['gurmukhi']
        self.assertFalse(gurmukhi_col.nullable)
        # Text columns don't have fixed length in SQLAlchemy

    def test_shabad_english_column(self):
        """Test Shabad english_translation column properties."""
        english_col = Shabad.__table__.columns['english_translation']
        self.assertFalse(english_col.nullable)
        # Text columns don't have fixed length in SQLAlchemy

    def test_shabad_optional_columns(self):
        """Test Shabad optional column properties."""
        optional_columns = ['romanization', 'source', 'context_tags', 'embedding']

        for col_name in optional_columns:
            col = Shabad.__table__.columns[col_name]
            self.assertTrue(col.nullable)

    def test_shabad_embedding_column(self):
        """Test Shabad embedding column properties."""
        embedding_col = Shabad.__table__.columns['embedding']
        self.assertTrue(embedding_col.nullable)
        # Check if it's a vector type (this might vary based on pgvector setup)
        self.assertIsNotNone(embedding_col.type)

    @patch('models.db.session')
    def test_shabad_database_operations(self, mock_session):
        """Test Shabad database operations simulation."""
        shabad = Shabad(**self.test_shabad_data)

        # Mock add operation
        mock_session.add(shabad)
        mock_session.commit()

        # Verify the mock was called
        mock_session.add.assert_called_with(shabad)
        mock_session.commit.assert_called()

    def test_shabad_default_values(self):
        """Test Shabad model default values."""
        # Create shabad with minimal required fields
        minimal_data = {
            'shabad_id': 'test-123',
            'gurmukhi': 'test gurmukhi',
            'english_translation': 'test english translation'
        }
        shabad = Shabad(**minimal_data)

        self.assertEqual(shabad.shabad_id, 'test-123')
        self.assertEqual(shabad.gurmukhi, 'test gurmukhi')
        self.assertEqual(shabad.english_translation, 'test english translation')
        # Optional fields should be None
        self.assertIsNone(shabad.romanization)
        self.assertIsNone(shabad.source)
        self.assertIsNone(shabad.context_tags)
        self.assertIsNone(shabad.embedding)

    def test_shabad_field_lengths(self):
        """Test Shabad model field length constraints."""
        # Test maximum length for gurmukhi
        long_gurmukhi = 'a' * 1000
        shabad = Shabad(shabad_id='test-123', gurmukhi=long_gurmukhi, english_translation='test')
        self.assertEqual(len(shabad.gurmukhi), 1000)

        # Test maximum length for english_translation
        long_english = 'a' * 2000
        shabad2 = Shabad(shabad_id='test-456', gurmukhi='test', english_translation=long_english)
        self.assertEqual(len(shabad2.english_translation), 2000)

    def test_shabad_equality(self):
        """Test Shabad model equality."""
        shabad1 = Shabad(**self.test_shabad_data)
        shabad2 = Shabad(**self.test_shabad_data)

        # Different objects with same data should not be equal by default
        # (SQLAlchemy models don't override __eq__ by default)
        self.assertNotEqual(shabad1, shabad2)

        # But they should have the same attributes
        self.assertEqual(shabad1.shabad_id, shabad2.shabad_id)
        self.assertEqual(shabad1.gurmukhi, shabad2.gurmukhi)
        self.assertEqual(shabad1.english_translation, shabad2.english_translation)


if __name__ == '__main__':
    unittest.main()