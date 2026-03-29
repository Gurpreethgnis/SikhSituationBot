import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from server.vector_utils import get_embedding


def test_get_embedding_success():
    with patch('server.vector_utils.genai.embed_content') as mock_embed:
        mock_embed.return_value = {'embedding': [0.123, 0.456, 0.789]}

        emb = get_embedding('some test query')

        assert emb == [0.123, 0.456, 0.789]
        mock_embed.assert_called_once()


def test_get_embedding_empty_text_returns_none():
    assert get_embedding('') is None
