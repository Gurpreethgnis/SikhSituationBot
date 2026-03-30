"""Tests for Raag/Mehla header detection and Parmaan content quality."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "server"))

from gurbani_content_quality import (  # noqa: E402
    compute_shabad_quality_fields,
    infer_verse_count_from_banidb_verses,
    is_raag_header_only,
    passes_parmaan_minimum_length,
    recompute_quality_for_stored_row,
)


class TestGurbaniContentQuality(unittest.TestCase):
    def test_header_detected_single_verse_aasaa_mehla(self):
        g = "ਆਸਾ ਮਹਲਾ ੫ ॥"
        eng = "Aasaa, Fifth Mehl."
        self.assertTrue(is_raag_header_only(g, eng, verse_count=1))

    def test_full_shabad_not_header_multiple_verses(self):
        g = "ਸਤਿਗੁਰ ਤੇਰੀ ਸਾਸਾ ॥ " * 5
        eng = "The True Guru is your hope and refuge. " * 4
        self.assertFalse(is_raag_header_only(g, eng, verse_count=4))

    def test_single_verse_substantive_text_not_header(self):
        g = "ਸਤਿਗੁਰ ਤੇਰੀ ਸਾਸਾ ॥" + " ਪੰਗਤੀ ॥" * 8
        eng = "The True Guru is your only hope; through the Word you are sustained in peace and faith."
        self.assertFalse(is_raag_header_only(g, eng, verse_count=1))

    def test_infer_verse_count_from_banidb(self):
        verses = [{"verse": "a"}, {"verse": "b"}, {"verse": ""}, {"verse": None}]
        self.assertEqual(infer_verse_count_from_banidb_verses(verses), 2)

    def test_compute_shabad_quality_fields(self):
        q = compute_shabad_quality_fields("ਆਸਾ ਮਹਲਾ ੫ ॥", "Fifth Mehl.", 1)
        self.assertTrue(q["is_header_only"])
        self.assertEqual(q["verse_count"], 1)

    def test_recompute_uses_infer_when_verse_count_none(self):
        g = "ਸਤਿਗੁਰ ਤੇਰੀ ਸਾਸਾ ॥ " * 6
        eng = "Hope and refuge in the Guru through many lines of translation here."
        q = recompute_quality_for_stored_row(g, eng, verse_count=None)
        self.assertFalse(q["is_header_only"])
        self.assertGreaterEqual(q["content_length"], 50)

    def test_passes_parmaan_minimum_length(self):
        self.assertTrue(passes_parmaan_minimum_length("a" * 50, "b" * 30))
        self.assertFalse(passes_parmaan_minimum_length("short", "short"))


if __name__ == "__main__":
    unittest.main()
