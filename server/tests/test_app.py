import os
import sys
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from server.app import app


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


def test_ask_endpoint_semantic_path(client):
    expected_shabad = MagicMock(
        shabad_id='1',
        gurmukhi='ਗੁਰਮੁਖੀ',
        romanization='gurmukhi',
        english_translation='meaning',
        source='SGGS',
        context_tags=['peace']
    )

    with patch('server.app.get_embedding', return_value=[0.1, 0.2, 0.3]):
        with patch('server.app.find_similar_shabads', return_value=[expected_shabad]):
            resp = client.post('/ask', json={'query': 'peace', 'persona': 'adult'})

    assert resp.status_code == 200
    data = resp.get_json()
    assert data['query'] == 'peace'
    assert len(data['shabads']) == 1
    assert data['shabads'][0]['shabad_id'] == '1'
