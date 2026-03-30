"""Tests for canonical Gurbani display and grounding (Issue #49)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "server"))

from gurbani_display import (
    canonical_shabad_markdown,
    ensure_guidance_grounded,
    guidance_grounding_ok,
    parmaan_canonical_section,
    repair_guidance_with_canonical,
    response_angs_match_sources,
    response_contains_primary_gurbani,
)


class TestGurbaniDisplay(unittest.TestCase):
    def test_canonical_shabad_markdown_sttm_link(self):
        s = {
            "shabad_id": "sggs_470",
            "gurmukhi": "ਸਤਿਗੁਰ ਤੇਰੀ ਸਾਸਾ ॥",
            "english_translation": "The True Guru is Your Hope.",
            "romanization": "satigur teree saasaa ||",
            "source": "SGGS Ang 470",
        }
        md = canonical_shabad_markdown(s, index=1)
        self.assertIn("470", md)
        self.assertIn("shabad?id=470", md)
        self.assertIn("ਸਤਿਗੁਰ ਤੇਰੀ ਸਾਸਾ", md)
        self.assertIn("The True Guru is Your Hope", md)
        self.assertIn("SGGS Ang 470", md)

    def test_parmaan_canonical_section_multiple(self):
        rows = [
            {
                "shabad_id": "sggs_1",
                "gurmukhi": "a" * 30,
                "english_translation": "e" * 40,
                "source": "SGGS Ang 1",
            },
            {
                "shabad_id": "sggs_2",
                "gurmukhi": "b" * 30,
                "english_translation": "f" * 40,
                "source": "SGGS Ang 2",
            },
        ]
        sec = parmaan_canonical_section(rows)
        self.assertIn("verbatim from database", sec.lower())
        self.assertIn("Shabad 1", sec)
        self.assertIn("Shabad 2", sec)
        self.assertIn("a" * 30, sec)

    def test_response_contains_primary_gurbani(self):
        primary = {"gurmukhi": "ਸਤਿਗੁਰ ਤੇਰੀ ਸਾਸਾ ॥ " * 5, "english_translation": "Hope text " * 10}
        good = "### ☬\n\n" + primary["gurmukhi"] + "\n\n" + primary["english_translation"]
        self.assertTrue(response_contains_primary_gurbani(good, primary))
        bad = "Fully generic devotional prose with no Gurmukhi from the database."
        self.assertFalse(response_contains_primary_gurbani(bad, primary))

    def test_response_angs_match_sources_regression_470(self):
        shabads = [
            {
                "shabad_id": "sggs_470",
                "gurmukhi": "x",
                "english_translation": "y",
                "source": "SGGS Ang 470",
            }
        ]
        wrong = "This shabad is on Ang 157 in Raag Gauree."
        self.assertFalse(response_angs_match_sources(wrong, shabads))
        ok = "See Source SGGS Ang 470 above."
        self.assertTrue(response_angs_match_sources(ok, shabads))

    def test_ensure_guidance_grounded_repairs(self):
        shabads = [
            {
                "shabad_id": "sggs_470",
                "gurmukhi": "ਸਤਿਗੁਰ ਤੇਰੀ ਸਾਸਾ ॥ " + "॥ " * 20,
                "english_translation": "The True Guru sustains you through hope and faith.",
                "source": "SGGS Ang 470",
            }
        ]
        bad = "### Reflection\n\nNice words.\n\n[SUGGESTIONS]\n- a\n- b\n- c"
        fixed = ensure_guidance_grounded(bad, shabads)
        self.assertIn("ਸਤਿਗੁਰ ਤੇਰੀ", fixed)
        self.assertIn("SUGGESTIONS", fixed)

    def test_repair_inserts_before_suggestions(self):
        shabads = [
            {
                "shabad_id": "sggs_1",
                "gurmukhi": "g" * 50,
                "english_translation": "eng " * 15,
                "source": "SGGS Ang 1",
            }
        ]
        out = repair_guidance_with_canonical("Intro only\n\n[SUGGESTIONS]\n- x\n", shabads)
        s_pos = out.find("[SUGGESTIONS]")
        self.assertGreater(out.find("g" * 50), -1)
        self.assertLess(out.find("g" * 50), s_pos)


if __name__ == "__main__":
    unittest.main()
