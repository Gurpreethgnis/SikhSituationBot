import unittest
import json
from unittest.mock import patch, MagicMock
import sys
import os

# Add server directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'server'))

from app import app


class TestAppIntegration(unittest.TestCase):
    """Integration tests for Flask application endpoints."""

    def setUp(self):
        """Set up test client and fixtures."""
        self.app = app
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True

        self.test_shabad = {
            'id': 1,
            'gurmukhi': 'test gurmukhi',
            'english': 'test english',
            'punjabi': 'test punjabi',
            'translation': 'test translation',
            'source': 'test source',
            'section': 'test section',
            'embedding': [0.1, 0.2, 0.3] * 256
        }

        self.valid_ask_request = {
            'query': 'What is the meaning of life?',
            'persona': 'adult'
        }

        self.invalid_ask_request = {
            'query': '',
            'persona': 'adult'
        }

    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'healthy')

    def test_cors_headers(self):
        """Test CORS headers are present."""
        response = self.client.get('/health')
        self.assertIn('Access-Control-Allow-Origin', response.headers)
        self.assertIn('Access-Control-Allow-Methods', response.headers)
        self.assertIn('Access-Control-Allow-Headers', response.headers)

    @patch('app.search_similar_shabads')
    @patch('app.synthesize_gemini_response')
    def test_ask_endpoint_success(self, mock_synthesize, mock_search):
        """Test successful ask endpoint."""
        mock_search.return_value = [self.test_shabad]
        mock_synthesize.return_value = "This is a synthesized response based on Gurbani wisdom."

        response = self.client.post('/ask',
                                  data=json.dumps(self.valid_ask_request),
                                  content_type='application/json')

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('query', data)
        self.assertIn('persona', data)
        self.assertIn('response', data)
        self.assertIn('shabads', data)
        self.assertIn('timestamp', data)

        self.assertEqual(data['query'], self.valid_ask_request['query'])
        self.assertEqual(data['persona'], self.valid_ask_request['persona'])
        self.assertEqual(len(data['shabads']), 1)

    @patch('app.search_similar_shabads')
    def test_ask_endpoint_no_shabads_found(self, mock_search):
        """Test ask endpoint when no relevant shabads are found."""
        mock_search.return_value = []

        response = self.client.post('/ask',
                                  data=json.dumps(self.valid_ask_request),
                                  content_type='application/json')

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('response', data)
        self.assertIn('No relevant Gurbani verses found', data['response'])

    def test_ask_endpoint_invalid_json(self):
        """Test ask endpoint with invalid JSON."""
        response = self.client.post('/ask',
                                  data='invalid json',
                                  content_type='application/json')

        self.assertEqual(response.status_code, 400)

        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_ask_endpoint_missing_fields(self):
        """Test ask endpoint with missing required fields."""
        incomplete_request = {'query': 'test query'}  # Missing persona

        response = self.client.post('/ask',
                                  data=json.dumps(incomplete_request),
                                  content_type='application/json')

        self.assertEqual(response.status_code, 400)

        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_ask_endpoint_empty_query(self):
        """Test ask endpoint with empty query."""
        response = self.client.post('/ask',
                                  data=json.dumps(self.invalid_ask_request),
                                  content_type='application/json')

        self.assertEqual(response.status_code, 400)

        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_ask_endpoint_invalid_persona(self):
        """Test ask endpoint with invalid persona."""
        invalid_persona_request = {
            'query': 'test query',
            'persona': 'invalid_persona'
        }

        response = self.client.post('/ask',
                                  data=json.dumps(invalid_persona_request),
                                  content_type='application/json')

        # Should still work but default to adult persona
        self.assertEqual(response.status_code, 200)

    @patch('app.search_similar_shabads')
    @patch('app.synthesize_gemini_response')
    def test_ask_endpoint_synthesis_failure(self, mock_synthesize, mock_search):
        """Test ask endpoint when synthesis fails."""
        mock_search.return_value = [self.test_shabad]
        mock_synthesize.return_value = None  # Synthesis failure

        response = self.client.post('/ask',
                                  data=json.dumps(self.valid_ask_request),
                                  content_type='application/json')

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('response', data)
        # Should still return shabad context even if synthesis fails
        self.assertIn('shabads', data)

    @patch('app.get_random_shabads')
    def test_random_shabads_endpoint_success(self, mock_get_random):
        """Test successful random shabads endpoint."""
        mock_get_random.return_value = [self.test_shabad]

        response = self.client.get('/random-shabads?limit=3')

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('shabads', data)
        self.assertEqual(len(data['shabads']), 1)

    @patch('app.get_random_shabads')
    def test_random_shabads_endpoint_no_results(self, mock_get_random):
        """Test random shabads endpoint when no results."""
        mock_get_random.return_value = []

        response = self.client.get('/random-shabads?limit=3')

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data['shabads'], [])

    def test_random_shabads_endpoint_invalid_limit(self):
        """Test random shabads endpoint with invalid limit."""
        response = self.client.get('/random-shabads?limit=invalid')

        self.assertEqual(response.status_code, 200)  # Should default to valid limit

        data = json.loads(response.data)
        self.assertIn('shabads', data)

    def test_random_shabads_endpoint_large_limit(self):
        """Test random shabads endpoint with very large limit."""
        response = self.client.get('/random-shabads?limit=1000')

        self.assertEqual(response.status_code, 200)  # Should be handled gracefully

    @patch('app.get_shabad_by_id')
    def test_shabad_by_id_endpoint_success(self, mock_get_shabad):
        """Test successful shabad by ID endpoint."""
        mock_get_shabad.return_value = self.test_shabad

        response = self.client.get('/shabad/1')

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['gurmukhi'], 'test gurmukhi')

    @patch('app.get_shabad_by_id')
    def test_shabad_by_id_endpoint_not_found(self, mock_get_shabad):
        """Test shabad by ID endpoint when not found."""
        mock_get_shabad.return_value = None

        response = self.client.get('/shabad/999')

        self.assertEqual(response.status_code, 404)

        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_shabad_by_id_endpoint_invalid_id(self):
        """Test shabad by ID endpoint with invalid ID."""
        response = self.client.get('/shabad/invalid')

        self.assertEqual(response.status_code, 404)

    def test_options_request(self):
        """Test OPTIONS request for CORS preflight."""
        response = self.client.options('/ask')

        self.assertEqual(response.status_code, 200)
        self.assertIn('Access-Control-Allow-Origin', response.headers)
        self.assertIn('Access-Control-Allow-Methods', response.headers)

    @patch('app.search_similar_shabads')
    @patch('app.synthesize_gemini_response')
    def test_ask_endpoint_different_personas(self, mock_synthesize, mock_search):
        """Test ask endpoint with different personas."""
        mock_search.return_value = [self.test_shabad]
        mock_synthesize.return_value = "Response for persona"

        for persona in ['child', 'teen', 'adult']:
            request = {'query': 'test query', 'persona': persona}
            response = self.client.post('/ask',
                                      data=json.dumps(request),
                                      content_type='application/json')

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data['persona'], persona)

    @patch('app.search_similar_shabads')
    def test_ask_endpoint_search_failure(self, mock_search):
        """Test ask endpoint when search fails."""
        mock_search.side_effect = Exception("Database connection failed")

        response = self.client.post('/ask',
                                  data=json.dumps(self.valid_ask_request),
                                  content_type='application/json')

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('response', data)
        self.assertIn('No relevant Gurbani verses found', data['response'])

    def test_error_handling_middleware(self):
        """Test that error handling middleware catches exceptions."""
        # This would require mocking an endpoint that raises an exception
        # For now, just verify the error handling is in place by checking status codes

        # Test with malformed request that might cause internal errors
        response = self.client.post('/ask',
                                  data=json.dumps({'invalid': 'structure'}),
                                  content_type='application/json')

        # Should return 400 for validation error, not 500 for unhandled exception
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()