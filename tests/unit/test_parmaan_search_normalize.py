import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "server"))

from parmaan_search_normalize import latin_token_search_variants, token_has_gurmukhi


class TestParmaanSearchNormalize(unittest.TestCase):
    def test_gurmukhi_detection(self):
        self.assertTrue(token_has_gurmukhi("ਸਤਿਗੁਰ"))
        self.assertTrue(token_has_gurmukhi("satgurਸ"))
        self.assertFalse(token_has_gurmukhi("satgur"))
        self.assertFalse(token_has_gurmukhi(""))

    def test_satgur_includes_satigur(self):
        v = latin_token_search_variants("satgur")
        self.assertIn("satgur", v)
        self.assertIn("satigur", v)

    def test_satigur_includes_satgur(self):
        v = latin_token_search_variants("satigur")
        self.assertIn("satgur", v)
        self.assertIn("satigur", v)

    def test_aasya_includes_sttm_spellings(self):
        v = latin_token_search_variants("aasya")
        self.assertIn("aasya", v)
        self.assertIn("aasaiaa", v)
        self.assertIn("aasiaa", v)

    def test_wahe_vahe(self):
        v = latin_token_search_variants("waheguru")
        self.assertIn("waheguru", v)
        self.assertIn("vaheguru", v)

    def test_teri_teree_word_boundary(self):
        v = latin_token_search_variants("teri")
        self.assertIn("teri", v)
        self.assertIn("teree", v)

    def test_bound_under_max_variants(self):
        for tok in ("satgur", "teri", "nanak", "prabhu", "waheguru"):
            v = latin_token_search_variants(tok)
            self.assertLessEqual(len(v), 14, tok)

    def test_guru_gur(self):
        v = latin_token_search_variants("waheguru")
        self.assertIn("waheguru", v)
        self.assertIn("wahegur", v)

    def test_naam_nam(self):
        v = latin_token_search_variants("naam")
        self.assertIn("naam", v)
        self.assertIn("nam", v)

    def test_har_hari(self):
        v = latin_token_search_variants("har")
        self.assertIn("har", v)
        self.assertIn("hari", v)

    def test_nanak_naanak(self):
        v = latin_token_search_variants("nanak")
        self.assertIn("nanak", v)
        self.assertIn("naanak", v)

    def test_ratre_includes_ratare_sttm_romanization(self):
        """Informal 'ratre' must match DB lines romanized as 'ratare' (ਚੋਲੇ ਰਤੜੇ)."""
        v = latin_token_search_variants("ratre")
        self.assertIn("ratre", v)
        self.assertIn("ratare", v)

    def test_pyare_includes_piaare(self):
        v = latin_token_search_variants("pyare")
        self.assertIn("pyare", v)
        self.assertIn("piaare", v)

    def test_kant_includes_sttm_ka_nt(self):
        v = latin_token_search_variants("kant")
        self.assertIn("kant", v)
        self.assertIn("ka(n)t", v)


if __name__ == "__main__":
    unittest.main()
