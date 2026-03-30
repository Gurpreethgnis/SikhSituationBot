"""
Server-side user feedback → GitHub Issues (REST API, no extra dependencies).
"""
from __future__ import annotations

import base64
import binascii
import json
import logging
import re
import threading
import time
import urllib.error
import urllib.request
import uuid
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# --- Limits (match product plan) ---
MAX_FEEDBACK_PER_HOUR = 5
FEEDBACK_WINDOW_SEC = 3600
MAX_DESCRIPTION_LEN = 5000
MAX_RESPONSE_SNIPPET_LEN = 12000
MAX_SCREENSHOT_BYTES = 2 * 1024 * 1024  # 2 MiB decoded

GITHUB_API = "https://api.github.com"

_rate_lock = threading.Lock()
# user_id -> list of unix timestamps (seconds) of submissions
_feedback_timestamps: Dict[int, List[float]] = {}


def _prune_old_timestamps(now: float, timestamps: List[float]) -> List[float]:
    cutoff = now - FEEDBACK_WINDOW_SEC
    return [t for t in timestamps if t > cutoff]


def feedback_rate_limit_allows(user_id: int) -> Tuple[bool, Optional[str]]:
    """Return (allowed, error_message). Does not consume a slot until record_feedback_submission."""
    now = time.time()
    with _rate_lock:
        ts = _feedback_timestamps.get(user_id, [])
        ts = _prune_old_timestamps(now, ts)
        _feedback_timestamps[user_id] = ts
        if len(ts) >= MAX_FEEDBACK_PER_HOUR:
            return False, f"Too many feedback submissions. Maximum {MAX_FEEDBACK_PER_HOUR} per hour."
    return True, None


def record_feedback_submission(user_id: int) -> None:
    """Call after a feedback issue is successfully created."""
    now = time.time()
    with _rate_lock:
        ts = _feedback_timestamps.get(user_id, [])
        ts = _prune_old_timestamps(now, ts)
        ts.append(now)
        _feedback_timestamps[user_id] = ts


def sanitize_text(text: str, max_len: int) -> str:
    if not text:
        return ""
    # Drop control chars except newline/tab
    cleaned = "".join(c for c in text if c == "\n" or c == "\t" or ord(c) >= 32)
    cleaned = cleaned.strip()
    if len(cleaned) > max_len:
        cleaned = cleaned[: max_len - 1].rstrip() + "…"
    return cleaned


def _detect_image_kind(raw: bytes) -> Optional[str]:
    if len(raw) < 12:
        return None
    if raw[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if raw[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if raw[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "webp"
    return None


def parse_screenshot_base64(screenshot_base64: Optional[str]) -> Optional[Tuple[bytes, str]]:
    """
    Decode optional screenshot. Accepts raw base64 or data URLs.
    Returns (bytes, file_extension) or None if absent/invalid.
    """
    if not screenshot_base64 or not isinstance(screenshot_base64, str):
        return None
    s = screenshot_base64.strip()
    if not s:
        return None
    mime = "image/png"
    if s.startswith("data:"):
        try:
            head, b64part = s.split(",", 1)
            mime_match = re.match(r"data:([^;]+)", head)
            if mime_match:
                mime = mime_match.group(1).lower()
        except ValueError:
            return None
    else:
        b64part = s

    try:
        raw = base64.b64decode(b64part, validate=False)
    except (binascii.Error, ValueError):
        return None

    if len(raw) > MAX_SCREENSHOT_BYTES:
        raise ValueError("Screenshot exceeds maximum size (2MB).")

    kind = _detect_image_kind(raw)
    if not kind:
        # Allow if declared mime is image/*
        if mime.startswith("image/"):
            ext = mime.split("/")[-1].split("+")[0]
            if ext not in ("png", "jpeg", "jpg", "gif", "webp"):
                ext = "png"
            if ext == "jpeg":
                ext = "jpg"
            return raw, ext
        raise ValueError("Screenshot must be PNG, JPEG, GIF, or WebP.")

    ext = "jpg" if kind == "jpeg" else kind
    return raw, ext


def _github_request(
    method: str,
    url: str,
    token: str,
    payload: Optional[Dict[str, Any]] = None,
) -> Tuple[int, Dict[str, Any]]:
    data = None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "SikhSituationBot-Feedback/1.0",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            if not body:
                return resp.status, {}
            return resp.status, json.loads(body)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(err_body) if err_body else {}
        except json.JSONDecodeError:
            parsed = {"message": err_body or str(e)}
        logger.warning("GitHub API HTTP %s: %s", e.code, parsed)
        return e.code, parsed


def upload_feedback_screenshot(
    token: str,
    owner: str,
    repo: str,
    branch: str,
    image_bytes: bytes,
    ext: str,
) -> Optional[str]:
    """Upload image via Contents API; return raw.githubusercontent.com URL or None."""
    path = f"user-feedback/screenshots/{uuid.uuid4().hex}.{ext}"
    url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
    b64 = base64.b64encode(image_bytes).decode("ascii")
    status, data = _github_request(
        "PUT",
        url,
        token,
        {
            "message": "chore: user feedback screenshot",
            "content": b64,
            "branch": branch,
        },
    )
    if status not in (200, 201):
        logger.error("Failed to upload screenshot: %s %s", status, data)
        return None
    content = data.get("content") or {}
    download_url = content.get("download_url")
    if download_url:
        return str(download_url)
    # Fallback: build raw URL
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"


def create_feedback_issue(
    token: str,
    owner: str,
    repo: str,
    branch: str,
    feedback_type: str,
    description: str,
    response_snippet: str,
    reporter_user_id: int,
    reporter_email: str,
    screenshot_url: Optional[str],
    chat_id: Optional[int],
) -> Tuple[Optional[str], Optional[str]]:
    """
    Create a GitHub issue. Returns (html_url, error_message).
    """
    ft = (feedback_type or "other").strip().lower()
    if ft not in ("bug", "improvement", "other"):
        ft = "other"

    prefix = {"bug": "[Bug]", "improvement": "[Suggestion]", "other": "[Feedback]"}[ft]
    desc_one_line = description.replace("\n", " ").strip()[:50]
    if len(description.replace("\n", " ").strip()) > 50:
        desc_one_line = desc_one_line.rstrip() + "…"
    title = f"{prefix} {desc_one_line or 'User feedback'}"

    if ft == "bug":
        labels_attempts: List[List[str]] = [["user-feedback", "bug"], ["user-feedback"], []]
    elif ft == "improvement":
        labels_attempts = [["user-feedback", "enhancement"], ["user-feedback"], []]
    else:
        labels_attempts = [["user-feedback"], []]

    body_parts = [
        "### Reporter",
        f"- **User ID:** {reporter_user_id}",
        f"- **Email:** {reporter_email}",
    ]
    if chat_id is not None:
        body_parts.append(f"- **Chat ID:** {chat_id}")
    body_parts.extend(
        [
            "",
            "### Type",
            ft,
            "",
            "### Description",
            description or "_(no description)_",
            "",
            "### Assistant response (reported)",
            "```text",
            response_snippet or "_(empty)_",
            "```",
        ]
    )
    if screenshot_url:
        body_parts.extend(["", "### Screenshot", f"![screenshot]({screenshot_url})"])
    body = "\n".join(body_parts)

    issue_url = f"{GITHUB_API}/repos/{owner}/{repo}/issues"
    last_err: Optional[str] = None
    for labels in labels_attempts:
        status, data = _github_request(
            "POST",
            issue_url,
            token,
            {"title": title[:256], "body": body, "labels": labels},
        )
        if status == 201:
            url = data.get("html_url")
            return (str(url) if url else None), None
        if status == 422:
            msg = data.get("message", "Validation failed")
            last_err = msg
            continue
        last_err = data.get("message", f"HTTP {status}")
        break

    return None, last_err or "Could not create GitHub issue"
