import os
import sys
import unittest
from unittest.mock import patch, MagicMock, mock_open
import json

# Add server directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

from prompts import (
    build_gemini_response_prompt,
    format_shabad_context,
    PERSONA_CONTEXTS,
    SYSTEM_PROMPT
)


class TestGeminiSynthesis(unittest.TestCase):
    """Unit tests for Gemini API response synthesis functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_shabads = [
            {
                "shabad_id": "test-1",
                "gurmukhi": "ਤਪਤਿ ਮਾਹਿ ਠਾਢਿ ਵਰਤਾਈ ॥",
                "romanization": "tapat maahi thaadh varataaee ||",
                "english_translation": "In the midst of the burning heat, a cooling breeze has begun to blow.",
                "source": "SGGS Page 1",
                "context_tags": ["anxiety", "peace"]
            },
            {
                "shabad_id": "test-2",
                "gurmukhi": "ਨਿਰਭਉ ਜਪੈ ਸਗਲ ਭਉ ਮਿਟੈ ॥",
                "romanization": "nirabhau japai sagal bhau mitai ||",
                "english_translation": "Meditating on the Fearless Lord, all fear departs.",
                "source": "SGGS Page 293",
                "context_tags": ["fear", "courage"]
            }
        ]

        self.user_query = "I'm feeling anxious about my future"
        self.persona = "adult"

    def test_format_shabad_context(self):
        """Test formatting shabad context for prompts."""
        context = format_shabad_context(self.sample_shabads)

        # Should contain both shabads
        self.assertIn("1.", context)
        self.assertIn("2.", context)

        # Should contain key information
        self.assertIn("burning heat", context)
        self.assertIn("Fearless Lord", context)
        self.assertIn("SGGS Page 1", context)
        self.assertIn("SGGS Page 293", context)

    def test_format_shabad_context_empty(self):
        """Test formatting empty shabad context."""
        context = format_shabad_context([])
        self.assertIn("No specific verses were found", context)

    def test_build_gemini_response_prompt_adult(self):
        """Test building Gemini prompt for adult persona."""
        prompt = build_gemini_response_prompt(self.user_query, self.sample_shabads, "adult")

        # Should contain system prompt
        self.assertIn("SikhSituationBot", prompt)

        # Should contain user query
        self.assertIn(self.user_query, prompt)

        # Should contain persona guidance
        self.assertIn("adult", prompt)
        self.assertIn("philosophical", prompt)

        # Should contain shabad context
        self.assertIn("burning heat", prompt)
        self.assertIn("Fearless Lord", prompt)

    def test_build_gemini_response_prompt_child(self):
        """Test building Gemini prompt for child persona."""
        prompt = build_gemini_response_prompt(self.user_query, self.sample_shabads, "child")

        # Should contain child-specific guidance
        self.assertIn("child", prompt)
        self.assertIn("simple words", prompt)
        self.assertIn("comforting metaphors", prompt)

    def test_build_gemini_response_prompt_teen(self):
        """Test building Gemini prompt for teen persona."""
        prompt = build_gemini_response_prompt(self.user_query, self.sample_shabads, "teen")

        # Should contain teen-specific guidance
        self.assertIn("teen", prompt)
        self.assertIn("modern language", prompt)
        self.assertIn("peer pressure", prompt)

    def test_build_gemini_response_prompt_no_shabads(self):
        """Test building Gemini prompt when no shabads are found."""
        prompt = build_gemini_response_prompt(self.user_query, [], "adult")

        # Should handle empty shabad list gracefully
        self.assertIn(self.user_query, prompt)
        self.assertIn("No specific verses were found", prompt)

    def test_build_gemini_response_prompt_invalid_persona(self):
        """Test building Gemini prompt with invalid persona."""
        prompt = build_gemini_response_prompt(self.user_query, self.sample_shabads, "invalid")

        # Should fallback to adult
        self.assertIn("adult", prompt)
        self.assertIn("philosophical", prompt)

    def test_persona_contexts_structure(self):
        """Test that persona contexts have required structure."""
        required_keys = ["tone", "language", "examples", "focus"]

        for persona, context in PERSONA_CONTEXTS.items():
            self.assertIsInstance(context, dict)
            for key in required_keys:
                self.assertIn(key, context)
                self.assertIsInstance(context[key], str)
                self.assertTrue(len(context[key]) > 0)

    def test_system_prompt_content(self):
        """Test that system prompt contains key elements."""
        self.assertIn("SikhSituationBot", SYSTEM_PROMPT)
        self.assertIn("Guru Granth Sahib", SYSTEM_PROMPT)
        self.assertIn("compassionate", SYSTEM_PROMPT)
        self.assertIn("wisdom", SYSTEM_PROMPT)

    @patch('server.app.genai')
    @patch('server.app.GEMINI_API_KEY', 'test-key')
    def test_synthesize_gemini_response_success(self, mock_genai):
        """Test successful Gemini response synthesis."""
        # Mock the Gemini API response
        mock_response = MagicMock()
        mock_response.text = "This is a test response from Gemini."
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        from server.app import synthesize_gemini_response

        result = synthesize_gemini_response("test query", self.sample_shabads, "adult")

        self.assertEqual(result, "This is a test response from Gemini.")
        mock_genai.GenerativeModel.assert_called_with('gemini-1.5-flash')
        mock_model.generate_content.assert_called_once()

    @patch('server.app.genai')
    @patch('server.app.GEMINI_API_KEY', None)
    def test_synthesize_gemini_response_no_api_key(self, mock_genai):
        """Test Gemini synthesis when API key is not configured."""
        from server.app import synthesize_gemini_response

        result = synthesize_gemini_response("test query", self.sample_shabads, "adult")

        self.assertIn("timeless Sikh wisdom", result)
        mock_genai.GenerativeModel.assert_not_called()

    @patch('server.app.genai')
    @patch('server.app.GEMINI_API_KEY', 'test-key')
    def test_synthesize_gemini_response_api_error(self, mock_genai):
        """Test Gemini synthesis when API call fails."""
        # Mock API failure
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API Error")
        mock_genai.GenerativeModel.return_value = mock_model

        from server.app import synthesize_gemini_response

        result = synthesize_gemini_response("test query", self.sample_shabads, "adult")

        self.assertIn("Sikh wisdom", result)
        self.assertIn("Guru Granth Sahib", result)

    @patch('server.app.genai')
    @patch('server.app.GEMINI_API_KEY', 'test-key')
    def test_synthesize_gemini_response_empty_response(self, mock_genai):
        """Test Gemini synthesis when API returns empty response."""
        # Mock empty response
        mock_response = MagicMock()
        mock_response.text = ""
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        from server.app import synthesize_gemini_response

        result = synthesize_gemini_response("test query", self.sample_shabads, "adult")

        self.assertIn("Guru's wisdom", result)
        self.assertIn("divine guidance", result)


if __name__ == '__main__':
    unittest.main()