"""Unit tests for STTM-style first-letter Gurbani search helpers."""

import re
import unittest

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "server"))

from retrieval import (  # noqa: E402
    build_gurmukhi_first_letter_pattern,
    build_latin_first_letter_pattern,
    looks_like_first_letter_query,
    parse_first_letter_query,
)


class TestFirstLetterPatterns(unittest.TestCase):
    def test_latin_pattern_matches_romanization_line(self):
        letters = ["t", "m", "t"]
        pat = re.compile(build_latin_first_letter_pattern(letters), re.IGNORECASE | re.UNICODE)
        self.assertTrue(pat.search("tapat maahi thaadh varataaee ||"))
        self.assertFalse(pat.search("maahi thaadh tapat"))

    def test_latin_continuous_query_parsed(self):
        script, letters = parse_first_letter_query("tmt")
        self.assertEqual(script, "latin")
        self.assertEqual(letters, ["t", "m", "t"])

    def test_latin_spaced_query_parsed(self):
        script, letters = parse_first_letter_query("t m t")
        self.assertEqual(script, "latin")
        self.assertEqual(letters, ["t", "m", "t"])

    def test_gurmukhi_query_parsed(self):
        script, letters = parse_first_letter_query("ੲਤਮਪ")
        self.assertEqual(script, "gurmukhi")
        self.assertEqual(len(letters), 4)

    def test_gurmukhi_pattern_with_ladder_key(self):
        # ੲ can match ਇ at word start (STTM-style)
        letters = ["ੲ", "ਤ", "ਮ", "ਪ"]
        pat = re.compile(build_gurmukhi_first_letter_pattern(letters), re.UNICODE)
        line = "ਇਹੁ ਤਨੁ ਮਾਇਆ ਪਾਹਿਆ ਪਿਆਰੇ ਲੀਤੜਾ ਲਬਿ ਰੰਗਾਏ ॥"
        self.assertTrue(pat.search(line))

    def test_looks_like_first_letter_heuristic(self):
        self.assertTrue(looks_like_first_letter_query("stmp"))
        self.assertTrue(looks_like_first_letter_query("ੲਤਮਪ"))
        self.assertFalse(looks_like_first_letter_query("satgur meri"))
        self.assertFalse(looks_like_first_letter_query("ab"))  # continuous too short


if __name__ == "__main__":
    unittest.main()
