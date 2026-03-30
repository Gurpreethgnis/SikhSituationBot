"""Unit tests for user feedback → GitHub helpers."""
import uuid

import pytest

from feedback_github import (
    MAX_FEEDBACK_PER_HOUR,
    feedback_rate_limit_allows,
    parse_screenshot_base64,
    record_feedback_submission,
    sanitize_text,
)


def test_sanitize_text_strips_control_chars():
    assert sanitize_text("hello\x00world", 100) == "helloworld"


def test_sanitize_text_truncates():
    long = "a" * 100
    out = sanitize_text(long, 20)
    assert len(out) <= 21
    assert out.endswith("…")


def test_parse_screenshot_png_data_url():
    # 1x1 PNG minimal
    raw_b64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )
    data_url = f"data:image/png;base64,{raw_b64}"
    parsed = parse_screenshot_base64(data_url)
    assert parsed is not None
    data, ext = parsed
    assert ext == "png"
    assert data[:8] == b"\x89PNG\r\n\x1a\n"


def test_parse_screenshot_empty():
    assert parse_screenshot_base64("") is None
    assert parse_screenshot_base64(None) is None


def test_rate_limit_allows_then_blocks():
    uid = int(uuid.uuid4().int % 10_000_000) + 9_000_000
    # Reset by using unique uid each test run is ok; clear module state not exposed — use high uid
    for _ in range(MAX_FEEDBACK_PER_HOUR):
        ok, err = feedback_rate_limit_allows(uid)
        assert ok is True
        assert err is None
        record_feedback_submission(uid)
    ok, err = feedback_rate_limit_allows(uid)
    assert ok is False
    assert err and "Maximum" in err
