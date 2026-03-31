"""synthesize_chat_response grounding and Parmaan canonical prefix (Issue #49)."""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "server"))

# Flask / DB may be required when importing app; llm_synthesis only needs models on settings
import llm_synthesis  # noqa: E402


class TestLlmSynthesisGrounding(unittest.TestCase):
    @patch.object(llm_synthesis, "_generate_gemini")
    @patch.object(llm_synthesis, "get_llm_settings")
    def test_parmaan_prepends_canonical_section(self, mock_settings, mock_gen):
        mock_settings.return_value = ("gemini", "models/gemini-2.5-flash-lite")
        mock_gen.return_value = "Matched verse #1. Theme commentary for #1.\n\n[SUGGESTIONS]\n- a\n- b\n- c"
        shabads = [
            {
                "shabad_id": "sggs_470",
                "gurmukhi": "ਸਤਿਗੁਰ ਤੇਰੀ ਸਾਸਾ ॥ " + "x" * 40,
                "english_translation": "English line " * 8,
                "romanization": "",
                "source": "SGGS Ang 470",
            }
        ]
        text, prov, mid = llm_synthesis.synthesize_chat_response(
            "Satgur teri aasa",
            shabads,
            "adult",
            guidance_mode="parmaan",
            parmaan_discovery_type="similar",
            style_state={"last_profile": "reflective", "last_length_mode": "short"},
        )
        self.assertEqual(prov, "gemini")
        self.assertIn("Retrieved Gurbani (verbatim from database)", text)
        self.assertIn("shabad?id=470", text)
        self.assertIn("Matched verse #1", text)
        mock_gen.assert_called()
        prompt_arg = mock_gen.call_args[0][1]
        self.assertIn("RETRIEVAL SUMMARY", prompt_arg)
        self.assertNotIn("ਸਤਿਗੁਰ ਤੇਰੀ", prompt_arg)
        self.assertNotIn("English line", prompt_arg)
        self.assertIn("STYLE PROFILE", prompt_arg)

    @patch.object(llm_synthesis, "_generate_gemini")
    @patch.object(llm_synthesis, "get_llm_settings")
    def test_guidance_retries_and_repairs_on_bad_output(self, mock_settings, mock_gen):
        mock_settings.return_value = ("gemini", "models/gemini-2.5-flash-lite")
        bad = (
            "### ☬ Timeless Shabad (Reference)\n\n"
            "I will invent a verse.\n\n"
            "### 🕯️\n\nx\n\n[SUGGESTIONS]\n- a\n- b\n- c"
        )
        good = (
            "### ☬ Timeless Shabad (Reference)\n\n"
            + "ਗੁਰਮੁਖੀ ਹਰਿ ਹਰਿਹ " * 5
            + "\n\n"
            + "Eng trans eng trans eng trans eng trans eng trans eng trans "
            + "\n\n[SUGGESTIONS]\n- a\n- b\n- c"
        )
        mock_gen.side_effect = [bad, good]
        shabads = [
            {
                "shabad_id": "sggs_1",
                "gurmukhi": "ਗੁਰਮੁਖੀ ਹਰਿ ਹਰਿਹ " * 5,
                "english_translation": "Eng trans eng trans eng trans eng trans eng trans eng trans ",
                "source": "SGGS Ang 100",
            }
        ]
        text, _, _ = llm_synthesis.synthesize_chat_response(
            "I need peace",
            shabads,
            "adult",
            guidance_mode="guidance",
        )
        self.assertIn("ਗੁਰਮੁਖੀ", text)
        self.assertEqual(mock_gen.call_count, 2)


if __name__ == "__main__":
    unittest.main()
