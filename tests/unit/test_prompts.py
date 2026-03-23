import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add server directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'server'))

from prompts import (
    PERSONA_CONTEXTS,
    build_gemini_response_prompt,
    format_shabad_context,
    get_persona_context
)
from app import synthesize_gemini_response


class TestPrompts(unittest.TestCase):
    """Unit tests for prompt engineering functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_query = "What is the meaning of life?"
        self.test_persona = "adult"
        self.test_shabad_context = "Gurmukhi: test gurmukhi\nEnglish: test english"
        self.test_shabads = [
            {
                'id': 1,
                'gurmukhi': 'test gurmukhi 1',
                'english': 'test english 1',
                'translation': 'test translation 1'
            },
            {
                'id': 2,
                'gurmukhi': 'test gurmukhi 2',
                'english': 'test english 2',
                'translation': 'test translation 2'
            }
        ]

    def test_persona_contexts_structure(self):
        """Test that PERSONA_CONTEXTS has expected structure."""
        expected_personas = ['child', 'teen', 'adult']

        for persona in expected_personas:
            self.assertIn(persona, PERSONA_CONTEXTS)
            self.assertIn('context', PERSONA_CONTEXTS[persona])
            self.assertIn('response_style', PERSONA_CONTEXTS[persona])
            self.assertIsInstance(PERSONA_CONTEXTS[persona]['context'], str)
            self.assertIsInstance(PERSONA_CONTEXTS[persona]['response_style'], str)

    def test_persona_contexts_content(self):
        """Test that PERSONA_CONTEXTS contains appropriate content."""
        # Check child persona
        child_context = PERSONA_CONTEXTS['child']
        self.assertIn('child', child_context['context'].lower())
        self.assertIn('simple', child_context['response_style'].lower())

        # Check teen persona
        teen_context = PERSONA_CONTEXTS['teen']
        self.assertIn('teen', teen_context['context'].lower())
        self.assertIn('youth', teen_context['response_style'].lower())

        # Check adult persona
        adult_context = PERSONA_CONTEXTS['adult']
        self.assertIn('adult', adult_context['context'].lower())
        self.assertIn('mature', adult_context['response_style'].lower())

    def test_build_gemini_response_prompt_basic(self):
        """Test basic Gemini response prompt building."""
        result = build_gemini_response_prompt(
            self.test_query,
            self.test_shabads,
            self.test_persona
        )

        self.assertIn(self.test_query, result)
        self.assertIn(self.test_persona, result)
        self.assertIn('test gurmukhi 1', result)
        self.assertIn('test english 1', result)
        self.assertIn('CONTEXT:', result)
        self.assertIn('QUESTION:', result)

    def test_build_gemini_response_prompt_with_persona_context(self):
        """Test prompt building includes persona-specific context."""
        result = build_gemini_response_prompt(
            self.test_query,
            'child',
            self.test_shabad_context
        )

        # Should include child-specific context
        self.assertIn(PERSONA_CONTEXTS['child']['context'], result)
        self.assertIn(PERSONA_CONTEXTS['child']['response_style'], result)

    def test_build_gemini_response_prompt_invalid_persona(self):
        """Test prompt building with invalid persona defaults to adult."""
        result = build_gemini_response_prompt(
            self.test_query,
            'invalid_persona',
            self.test_shabad_context
        )

        # Should default to adult persona
        self.assertIn(PERSONA_CONTEXTS['adult']['context'], result)
        self.assertIn(PERSONA_CONTEXTS['adult']['response_style'], result)

    def test_build_gemini_response_prompt_empty_context(self):
        """Test prompt building with empty shabad context."""
        result = build_gemini_response_prompt(
            self.test_query,
            self.test_persona,
            ""
        )

        self.assertIn(self.test_query, result)
        self.assertIn(self.test_persona, result)
        self.assertIn('CONTEXT: No relevant Gurbani verses found', result)

    def test_format_shabad_context_single_shabad(self):
        """Test formatting context for single shabad."""
        result = format_shabad_context(self.test_shabads[0])

        self.assertIn('Gurmukhi:', result)
        self.assertIn('test gurmukhi 1', result)
        self.assertIn('English:', result)
        self.assertIn('test english 1', result)
        self.assertIn('Translation:', result)
        self.assertIn('test translation 1', result)

    def test_format_shabad_context_multiple_shabads(self):
        """Test formatting context for multiple shabads."""
        result = format_shabad_context(self.test_shabads)

        # Should contain both shabads
        self.assertIn('test gurmukhi 1', result)
        self.assertIn('test gurmukhi 2', result)
        self.assertIn('test english 1', result)
        self.assertIn('test english 2', result)

        # Should have separators
        self.assertIn('---', result)

    def test_format_shabad_context_empty_list(self):
        """Test formatting context for empty shabad list."""
        result = format_shabad_context([])
        self.assertEqual(result, "No relevant Gurbani verses found.")

    def test_format_shabad_context_none(self):
        """Test formatting context for None input."""
        result = format_shabad_context(None)
        self.assertEqual(result, "No relevant Gurbani verses found.")

    def test_format_shabad_context_minimal_fields(self):
        """Test formatting context with minimal shabad fields."""
        minimal_shabad = {'id': 1, 'gurmukhi': 'test', 'english': 'test'}
        result = format_shabad_context(minimal_shabad)

        self.assertIn('Gurmukhi:', result)
        self.assertIn('English:', result)
        # Should not include fields that don't exist
        self.assertNotIn('Punjabi:', result)
        self.assertNotIn('Translation:', result)

    @patch('prompts.genai')
    @patch('prompts.GEMINI_API_KEY', 'test-key')
    def test_synthesize_gemini_response_success(self, mock_genai):
        """Test successful Gemini response synthesis."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Test synthesized response"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        result = synthesize_gemini_response("test prompt")

        self.assertEqual(result, "Test synthesized response")
        mock_genai.GenerativeModel.assert_called_once()
        mock_model.generate_content.assert_called_once_with("test prompt")

    @patch('prompts.GEMINI_API_KEY', None)
    def test_synthesize_gemini_response_no_api_key(self):
        """Test Gemini synthesis when API key is not available."""
        result = synthesize_gemini_response("test prompt")
        self.assertIsNone(result)

    @patch('prompts.genai')
    @patch('prompts.GEMINI_API_KEY', 'test-key')
    def test_synthesize_gemini_response_api_error(self, mock_genai):
        """Test Gemini synthesis when API call fails."""
        mock_genai.GenerativeModel.side_effect = Exception("API Error")

        result = synthesize_gemini_response("test prompt")

        self.assertIsNone(result)

    @patch('prompts.genai')
    @patch('prompts.GEMINI_API_KEY', 'test-key')
    def test_synthesize_gemini_response_empty_response(self, mock_genai):
        """Test Gemini synthesis with empty response."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = ""
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        result = synthesize_gemini_response("test prompt")

        self.assertEqual(result, "")

    @patch('prompts.genai')
    @patch('prompts.GEMINI_API_KEY', 'test-key')
    def test_synthesize_gemini_response_whitespace_response(self, mock_genai):
        """Test Gemini synthesis with whitespace-only response."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "   \n\t   "
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        result = synthesize_gemini_response("test prompt")

        self.assertEqual(result, "   \n\t   ")

    def test_build_gemini_response_prompt_structure(self):
        """Test that prompt has correct structure."""
        result = build_gemini_response_prompt(
            self.test_query,
            self.test_persona,
            self.test_shabad_context
        )

        # Check that sections are in correct order
        persona_pos = result.find('PERSONA:')
        context_pos = result.find('CONTEXT:')
        question_pos = result.find('QUESTION:')

        self.assertLess(persona_pos, context_pos)
        self.assertLess(context_pos, question_pos)

    def test_format_shabad_context_field_order(self):
        """Test that shabad context formats fields in consistent order."""
        shabad = {
            'id': 1,
            'gurmukhi': 'gurmukhi',
            'english': 'english',
            'punjabi': 'punjabi',
            'hindi': 'hindi',
            'roman': 'roman',
            'translation': 'translation',
            'explanation': 'explanation',
            'source': 'source',
            'section': 'section'
        }

        result = format_shabad_context(shabad)

        # Check field order
        fields = ['Gurmukhi', 'English', 'Punjabi', 'Hindi', 'Roman', 'Translation', 'Explanation', 'Source', 'Section']
        positions = []

        for field in fields:
            pos = result.find(f'{field}:')
            if pos != -1:
                positions.append((field, pos))

        # Verify fields appear in expected order
        ordered_fields = [field for field, pos in sorted(positions, key=lambda x: x[1])]
        expected_order = ['Gurmukhi', 'English', 'Punjabi', 'Hindi', 'Roman', 'Translation', 'Explanation', 'Source', 'Section']

        for i, field in enumerate(ordered_fields):
            if i < len(expected_order):
                self.assertEqual(field, expected_order[i])

    def test_persona_contexts_no_duplicates(self):
        """Test that persona contexts don't have duplicate content."""
        contexts = [PERSONA_CONTEXTS[p]['context'] for p in PERSONA_CONTEXTS]
        self.assertEqual(len(contexts), len(set(contexts)), "Persona contexts should be unique")

        styles = [PERSONA_CONTEXTS[p]['response_style'] for p in PERSONA_CONTEXTS]
        self.assertEqual(len(styles), len(set(styles)), "Response styles should be unique")


if __name__ == '__main__':
    unittest.main()