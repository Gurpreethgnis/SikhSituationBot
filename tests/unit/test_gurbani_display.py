"""Tests for canonical Gurbani display and grounding (Issue #49)."""
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "server"))

from gurbani_display import (
    canonical_shabad_markdown,
    ensure_all_sttm_links_for_retrieved_shabads,
    ensure_guidance_grounded,
    format_parmaan_commentary_context,
    guidance_grounding_ok,
    parmaan_canonical_section,
    prettify_sttm_links_in_prose,
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

    def test_format_parmaan_commentary_context_no_gurbani(self):
        """LLM context must not include verse text (avoids echoing Raag/Mahalla as the shabad)."""
        rows = [
            {
                "shabad_id": "sggs_456",
                "gurmukhi": "ਆਸਾ ਮਹਲਾ ੫ ॥",
                "english_translation": "Aasaa, Fifth Mehla (header line only)",
                "source": "SGGS Ang 456",
                "context_tags": ["hope", "refuge"],
            }
        ]
        ctx = format_parmaan_commentary_context(rows)
        self.assertIn("sggs_456", ctx)
        self.assertIn("SGGS Ang 456", ctx)
        self.assertIn("theme_tags", ctx)
        self.assertNotIn("ਆਸਾ", ctx)
        self.assertNotIn("Gurmukhi:", ctx)
        self.assertNotIn("Fifth Mehla", ctx)

    @patch("gurbani_display.fetch_banidb_shabad_display", return_value=None)
    def test_parmaan_canonical_section_multiple(self, _mock_fetch):
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

    @patch("gurbani_display.fetch_banidb_shabad_display", return_value=None)
    def test_repair_inserts_before_suggestions(self, _mock_fetch):
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

    @patch("gurbani_display.fetch_banidb_shabad_display", return_value=None)
    def test_repair_appends_all_missing_shabads_before_suggestions(self, _mock_fetch):
        """When only the first shabad appears in prose, append verbatim blocks for the rest."""
        shabads = [
            {
                "shabad_id": "sggs_1",
                "gurmukhi": "a" * 50,
                "english_translation": "alpha " * 15,
                "source": "SGGS Ang 1",
            },
            {
                "shabad_id": "sggs_2",
                "gurmukhi": "b" * 50,
                "english_translation": "beta " * 15,
                "source": "SGGS Ang 2",
            },
        ]
        body = "Here is " + ("a" * 50) + " and " + ("alpha " * 15) + "\n\n[SUGGESTIONS]\n- x\n"
        out = repair_guidance_with_canonical(body, shabads)
        # Shabad 1 already appears verbatim in prose; repair only appends the missing shabad(s).
        self.assertIn("Shabad 2", out)
        self.assertIn("b" * 50, out)
        self.assertIn("beta ", out)
        self.assertLess(out.find("b" * 50), out.rfind("[SUGGESTIONS]"))

    @patch("gurbani_display.fetch_banidb_shabad_display", return_value=None)
    def test_guidance_grounding_ok_requires_each_shabad(self, _mock_fetch):
        shabads = [
            {
                "shabad_id": "sggs_1",
                "gurmukhi": "x" * 50,
                "english_translation": "ex " * 15,
                "source": "SGGS Ang 1",
            },
            {
                "shabad_id": "sggs_2",
                "gurmukhi": "y" * 50,
                "english_translation": "why " * 15,
                "source": "SGGS Ang 2",
            },
        ]
        only_first = ("x" * 50) + " " + ("ex " * 15) + " SGGS Ang 1"
        self.assertFalse(guidance_grounding_ok(only_first, shabads))
        both = only_first + " " + ("y" * 50) + " " + ("why " * 15) + " SGGS Ang 2"
        self.assertTrue(guidance_grounding_ok(both, shabads))

    @patch("gurbani_display.fetch_banidb_shabad_display", return_value=None)
    def test_ensure_all_sttm_inserts_missing_second_url(self, _mock_fetch):
        """When prose cites two shabads but only embeds one STTM URL, append the other before SUGGESTIONS."""
        shabads = [
            {
                "shabad_id": "sggs_10",
                "gurmukhi": "A" * 50,
                "english_translation": "ea " * 15,
                "source": "SGGS Ang 10",
            },
            {
                "shabad_id": "sggs_20",
                "gurmukhi": "B" * 50,
                "english_translation": "eb " * 15,
                "source": "SGGS Ang 20",
            },
        ]
        u10 = "https://www.sikhitothemax.org/shabad?id=10"
        u20 = "https://www.sikhitothemax.org/shabad?id=20"
        body = (
            f"Reflection.\n\n{'A' * 50}\n{('ea ' * 15).strip()}\n{u10}\n\n"
            f"{'B' * 50}\n{('eb ' * 15).strip()}\n\n[SUGGESTIONS]\n- a\n- b\n- c\n"
        )
        out = ensure_all_sttm_links_for_retrieved_shabads(body, shabads)
        self.assertIn("complete references", out)
        self.assertIn(u20, out)
        self.assertLess(out.find(u20), out.rfind("[SUGGESTIONS]"))
        self.assertGreaterEqual(out.count(u10), 1)

    def test_prettify_sttm_labeled_line(self):
        raw = "English: hello\nSikhiToTheMax link: https://www.sikhitothemax.org/shabad?id=99\n\nMore."
        out = prettify_sttm_links_in_prose(raw)
        self.assertIn("[Open on SikhiToTheMax](https://www.sikhitothemax.org/shabad?id=99)", out)
        self.assertNotIn("SikhiToTheMax link:", out)

    def test_prettify_skips_already_markdown(self):
        md = "See [Open on SikhiToTheMax](https://www.sikhitothemax.org/shabad?id=1) for more."
        self.assertEqual(prettify_sttm_links_in_prose(md), md)

    @patch("gurbani_display.fetch_banidb_shabad_display", return_value=None)
    def test_ensure_all_sttm_noop_when_all_urls_present(self, _mock_fetch):
        shabads = [
            {
                "shabad_id": "sggs_3",
                "gurmukhi": "C" * 50,
                "english_translation": "ec " * 15,
                "source": "SGGS Ang 3",
            },
        ]
        u3 = "https://www.sikhitothemax.org/shabad?id=3"
        body = f"{'C' * 50}\n{u3}\n\n[SUGGESTIONS]\n- x\n"
        out = ensure_all_sttm_links_for_retrieved_shabads(body, shabads)
        self.assertNotIn("complete references", out)
        self.assertEqual(out, body)


if __name__ == "__main__":
    unittest.main()
