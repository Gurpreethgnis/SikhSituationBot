import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from server.retrieval import find_similar_shabads
from server.app import app


def test_find_similar_shabads_returns_results_and_orders():
    fake_ordered = MagicMock()
    fake_limit = MagicMock()
    fake_limit.all.return_value = ['s1', 's2']
    fake_ordered.limit.return_value = fake_limit

    fake_query_object = MagicMock()
    fake_query_object.order_by.return_value = fake_ordered
    fake_query_object.filter.return_value = fake_query_object

    with app.app_context():
        with patch('server.retrieval.Shabad.query', fake_query_object):
            results = find_similar_shabads([0.1, 0.2, 0.3], limit=2, persona='adult')

    assert results == ['s1', 's2']
    fake_query_object.order_by.assert_called_once()

