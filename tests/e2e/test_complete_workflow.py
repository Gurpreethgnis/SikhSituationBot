import unittest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock
import sys

# Add server directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'server'))

from app import app
from seed_db import seed_database


class TestEndToEnd(unittest.TestCase):
    """End-to-end tests for complete application workflows."""

    def setUp(self):
        """Set up test environment."""
        self.app = app
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True

        # Create test data
        self.test_shabads = [
            {
                'id': 1,
                'gurmukhi': 'ਸਤਿਗੁਰੂ ਦੇ ਸਿਖ ਹੋਏ ਸਭ ਮਿਲ ਕੇ ਏਕ ਹੋਏ',
                'english': 'All Sikhs of the True Guru have become one united.',
                'punjabi': 'ਸਤਿਗੁਰੂ ਦੇ ਸਿਖ ਹੋਏ ਸਭ ਮਿਲ ਕੇ ਏਕ ਹੋਏ',
                'translation': 'All the Sikhs of the True Guru have united together.',
                'source': 'Guru Gobind Singh Ji',
                'section': 'Unity',
                'embedding': [0.1, 0.2, 0.3] * 256
            },
            {
                'id': 2,
                'gurmukhi': 'ਨਾ ਕੋਈ ਦੁਸ਼ਮਣ ਹੈ ਨਾ ਕੋਈ ਬੈਰੀ',
                'english': 'There is no enemy and no adversary.',
                'punjabi': 'ਨਾ ਕੋਈ ਦੁਸ਼ਮਣ ਹੈ ਨਾ ਕੋਈ ਬੈਰੀ',
                'translation': 'There is no enemy and no adversary.',
                'source': 'Guru Gobind Singh Ji',
                'section': 'Peace',
                'embedding': [0.2, 0.3, 0.4] * 256
            }
        ]

    def test_health_check_workflow(self):
        """Test complete health check workflow."""
        response = self.client.get('/health')

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('timestamp', data)

    @patch('app.search_similar_shabads')
    @patch('app.synthesize_gemini_response')
    def test_complete_ask_workflow_success(self, mock_synthesize, mock_search):
        """Test complete ask workflow from request to response."""
        # Mock the search to return relevant shabads
        mock_search.return_value = self.test_shabads

        # Mock Gemini synthesis
        mock_synthesize.return_value = (
            "Based on the teachings of Guru Gobind Singh Ji, "
            "the concept of unity among Sikhs is fundamental. "
            "When we unite as one, there are no enemies or adversaries. "
            "This principle can help you find peace in your situation."
        )

        # Make the request
        request_data = {
            'query': 'How can I find peace when people around me are fighting?',
            'persona': 'adult'
        }

        response = self.client.post('/ask',
                                  data=json.dumps(request_data),
                                  content_type='application/json')

        # Verify response
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)

        # Check response structure
        required_fields = ['query', 'persona', 'response', 'shabads', 'timestamp']
        for field in required_fields:
            self.assertIn(field, data)

        # Check data integrity
        self.assertEqual(data['query'], request_data['query'])
        self.assertEqual(data['persona'], request_data['persona'])
        self.assertEqual(len(data['shabads']), 2)

        # Check that response contains synthesized content
        self.assertIn('unity', data['response'].lower())
        self.assertIn('peace', data['response'].lower())

        # Check that shabads contain expected data
        shabad_ids = [s['id'] for s in data['shabads']]
        self.assertIn(1, shabad_ids)
        self.assertIn(2, shabad_ids)

    @patch('app.search_similar_shabads')
    @patch('app.synthesize_gemini_response')
    def test_ask_workflow_different_personas(self, mock_synthesize, mock_search):
        """Test ask workflow with different personas."""
        mock_search.return_value = self.test_shabads

        persona_responses = {
            'child': 'simple explanation for children',
            'teen': 'explanation for teenagers',
            'adult': 'detailed explanation for adults'
        }

        for persona, expected_content in persona_responses.items():
            mock_synthesize.return_value = expected_content

            request_data = {
                'query': 'What is Sikhism?',
                'persona': persona
            }

            response = self.client.post('/ask',
                                      data=json.dumps(request_data),
                                      content_type='application/json')

            self.assertEqual(response.status_code, 200)

            data = json.loads(response.data)
            self.assertEqual(data['persona'], persona)
            self.assertEqual(data['response'], expected_content)

    @patch('app.get_random_shabads')
    def test_random_shabads_workflow(self, mock_get_random):
        """Test complete random shabads workflow."""
        mock_get_random.return_value = self.test_shabads

        response = self.client.get('/random-shabads?limit=5')

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('shabads', data)
        self.assertEqual(len(data['shabads']), 2)

        # Verify shabad structure
        for shabad in data['shabads']:
            required_fields = ['id', 'gurmukhi', 'english']
            for field in required_fields:
                self.assertIn(field, shabad)

    @patch('app.get_shabad_by_id')
    def test_shabad_by_id_workflow(self, mock_get_shabad):
        """Test complete shabad by ID workflow."""
        mock_get_shabad.return_value = self.test_shabads[0]

        response = self.client.get('/shabad/1')

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['gurmukhi'], self.test_shabads[0]['gurmukhi'])
        self.assertEqual(data['english'], self.test_shabads[0]['english'])

    def test_error_handling_workflow(self):
        """Test error handling in complete workflows."""
        # Test invalid JSON
        response = self.client.post('/ask',
                                  data='invalid json',
                                  content_type='application/json')

        self.assertEqual(response.status_code, 400)

        # Test missing required fields
        response = self.client.post('/ask',
                                  data=json.dumps({'query': 'test'}),
                                  content_type='application/json')

        self.assertEqual(response.status_code, 400)

        # Test empty query
        response = self.client.post('/ask',
                                  data=json.dumps({'query': '', 'persona': 'adult'}),
                                  content_type='application/json')

        self.assertEqual(response.status_code, 400)

    @patch('app.search_similar_shabads')
    @patch('app.synthesize_gemini_response')
    def test_workflow_with_no_shabads_found(self, mock_synthesize, mock_search):
        """Test workflow when no relevant shabads are found."""
        mock_search.return_value = []
        mock_synthesize.return_value = None  # Synthesis also fails

        request_data = {
            'query': 'Some very specific query with no matches',
            'persona': 'adult'
        }

        response = self.client.post('/ask',
                                  data=json.dumps(request_data),
                                  content_type='application/json')

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('No relevant Gurbani verses found', data['response'])
        self.assertEqual(data['shabads'], [])

    @patch('app.search_similar_shabads')
    @patch('app.synthesize_gemini_response')
    def test_workflow_resilience_to_failures(self, mock_synthesize, mock_search):
        """Test that workflow remains functional despite individual component failures."""
        # Search succeeds but synthesis fails
        mock_search.return_value = self.test_shabads
        mock_synthesize.return_value = None

        request_data = {
            'query': 'Test query',
            'persona': 'adult'
        }

        response = self.client.post('/ask',
                                  data=json.dumps(request_data),
                                  content_type='application/json')

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        # Should still return shabads even if synthesis fails
        self.assertEqual(len(data['shabads']), 2)
        self.assertIn('shabads', data)

    def test_cors_workflow(self):
        """Test CORS functionality in complete workflow."""
        # Test preflight request
        response = self.client.options('/ask')

        self.assertEqual(response.status_code, 200)
        self.assertIn('Access-Control-Allow-Origin', response.headers)
        self.assertIn('Access-Control-Allow-Methods', response.headers)

        # Test actual request has CORS headers
        response = self.client.post('/ask',
                                  data=json.dumps({'query': 'test', 'persona': 'adult'}),
                                  content_type='application/json')

        self.assertIn('Access-Control-Allow-Origin', response.headers)

    @patch('app.search_similar_shabads')
    @patch('app.synthesize_gemini_response')
    def test_workflow_data_integrity(self, mock_synthesize, mock_search):
        """Test that data integrity is maintained throughout the workflow."""
        mock_search.return_value = self.test_shabads
        mock_synthesize.return_value = "Test response"

        request_data = {
            'query': 'ਦੁੱਖ ਦਾ ਕਾਰਨ ਕੀ ਹੈ?',  # Punjabi query
            'persona': 'adult'
        }

        response = self.client.post('/ask',
                                  data=json.dumps(request_data),
                                  content_type='application/json')

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)

        # Verify that original query is preserved
        self.assertEqual(data['query'], request_data['query'])
        self.assertEqual(data['persona'], request_data['persona'])

        # Verify shabad data integrity
        for shabad in data['shabads']:
            self.assertIsInstance(shabad['id'], int)
            self.assertIsInstance(shabad['gurmukhi'], str)
            self.assertIsInstance(shabad['english'], str)

    def test_concurrent_requests_simulation(self):
        """Test handling of multiple concurrent requests."""
        # This is a basic test - in a real scenario you'd use threading or async
        requests = [
            {'query': 'Question 1', 'persona': 'adult'},
            {'query': 'Question 2', 'persona': 'child'},
            {'query': 'Question 3', 'persona': 'teen'}
        ]

        responses = []
        for request_data in requests:
            with patch('app.search_similar_shabads') as mock_search, \
                 patch('app.synthesize_gemini_response') as mock_synthesize:

                mock_search.return_value = [self.test_shabads[0]]
                mock_synthesize.return_value = f"Response for {request_data['persona']}"

                response = self.client.post('/ask',
                                          data=json.dumps(request_data),
                                          content_type='application/json')

                responses.append((response.status_code, request_data['persona']))

        # All requests should succeed
        for status_code, persona in responses:
            self.assertEqual(status_code, 200, f"Failed for persona: {persona}")


if __name__ == '__main__':
    unittest.main()