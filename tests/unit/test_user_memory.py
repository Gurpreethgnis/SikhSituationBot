import os
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "server"))

from user_memory import (  # noqa: E402
    _parse_extraction_json,
    format_memory_context_for_prompt,
    _normalize_content,
)


class TestUserMemory(unittest.TestCase):
    def test_normalize_content(self):
        self.assertEqual(_normalize_content("  Hello   World  "), "hello world")

    def test_parse_extraction_json_array(self):
        raw = '[{"fact_type": "situation", "content": "User mentioned job stress.", "importance": 7}]'
        out = _parse_extraction_json(raw)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["fact_type"], "situation")
        self.assertEqual(out[0]["importance"], 7)

    def test_parse_strips_markdown_fence(self):
        raw = '```json\n[{"fact_type": "topic", "content": "Interested in naam simran.", "importance": 4}]\n```'
        out = _parse_extraction_json(raw)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["fact_type"], "topic")

    def test_parse_rejects_bad_fact_type(self):
        raw = '[{"fact_type": "invalid", "content": "x" * 20, "importance": 5}]'
        out = _parse_extraction_json(raw)
        self.assertEqual(out, [])

    def test_format_memory_context(self):
        rows = [
            SimpleNamespace(fact_type="situation", content="User is grieving.", importance=8),
            SimpleNamespace(fact_type="preference", content="Prefers gentle tone.", importance=5),
        ]
        block = format_memory_context_for_prompt(rows)
        self.assertIn("situation", block)
        self.assertIn("grieving", block)
        self.assertIn("preference", block)

    def test_format_empty(self):
        self.assertEqual(format_memory_context_for_prompt([]), "")


if __name__ == "__main__":
    unittest.main()
