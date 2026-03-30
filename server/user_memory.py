"""
Cross-session user memory: load facts for prompts, extract new facts after guidance turns.
"""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

import google.generativeai as genai

from models import User, UserMemory, db
from prompts import _RELAXED_SAFETY, _safe_response_text

logger = logging.getLogger(__name__)

ALLOWED_FACT_TYPES = frozenset({"situation", "preference", "topic", "entity"})
MAX_NEW_MEMORIES_PER_TURN = 3
MAX_MEMORIES_IN_PROMPT = 10
MAX_CONTENT_LEN = 500
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

_extraction_model = None


def _get_extraction_model():
    global _extraction_model
    if not GEMINI_API_KEY:
        return None
    if _extraction_model is None:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            _extraction_model = genai.GenerativeModel("models/gemini-2.5-flash-lite")
        except Exception as e:
            logger.warning("user_memory: could not init extraction model: %s", e)
            return None
    return _extraction_model


def _normalize_content(s: str) -> str:
    return " ".join((s or "").lower().strip().split())


def load_active_memories_for_user(user: User) -> List[UserMemory]:
    """Return non-deleted memories within retention window, ordered for prompt injection."""
    if not user or not getattr(user, "memory_enabled", True):
        return []
    q = UserMemory.query.filter_by(user_id=user.id, is_deleted=False)
    days = int(getattr(user, "memory_retention_days", 90) or 90)
    if days > 0:
        cutoff = datetime.utcnow() - timedelta(days=days)
        q = q.filter(UserMemory.created_at >= cutoff)
    rows = q.order_by(
        UserMemory.is_pinned.desc(),
        UserMemory.importance.desc(),
        UserMemory.created_at.desc(),
    ).limit(40).all()
    return rows


def format_memory_context_for_prompt(memories: List[UserMemory]) -> str:
    """Plain-text block for the synthesis prompt (empty if none)."""
    if not memories:
        return ""
    lines: List[str] = []
    for m in memories[:MAX_MEMORIES_IN_PROMPT]:
        ft = (m.fact_type or "topic").strip()
        ct = (m.content or "").strip()
        if not ct:
            continue
        lines.append(f"- ({ft}) {ct}")
    if not lines:
        return ""
    return (
        "STORED CONTEXT from earlier signed-in conversations (use only when clearly relevant; "
        "do not recite this list; do not assume facts are current without checking the latest message):\n"
        + "\n".join(lines)
    )


def _recent_content_fingerprints(user_id: int, limit: int = 150) -> Set[str]:
    rows = (
        UserMemory.query.filter_by(user_id=user_id, is_deleted=False)
        .order_by(UserMemory.created_at.desc())
        .limit(limit)
        .all()
    )
    return {_normalize_content(r.content) for r in rows if r.content}


def _parse_extraction_json(text: str) -> List[Dict[str, Any]]:
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t
        t = t.rsplit("```", 1)[0] if "```" in t else t
        t = t.strip()
    try:
        data = json.loads(t)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    out: List[Dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        ft = str(item.get("fact_type") or "").strip().lower()
        if ft not in ALLOWED_FACT_TYPES:
            continue
        content = str(item.get("content") or "").strip()
        content = re.sub(r"\s+", " ", content)[:MAX_CONTENT_LEN]
        if len(content) < 8:
            continue
        imp = item.get("importance", 5)
        try:
            imp_i = max(1, min(10, int(imp)))
        except (TypeError, ValueError):
            imp_i = 5
        out.append({"fact_type": ft, "content": content, "importance": imp_i})
    return out[:MAX_NEW_MEMORIES_PER_TURN]


def extract_new_memory_facts(
    user_message: str,
    assistant_response: str,
    existing_fingerprints: Set[str],
) -> List[Dict[str, Any]]:
    """
    Call a small Gemini model to propose 0–3 new memories. Returns validated dicts.
    """
    model = _get_extraction_model()
    if not model:
        return []
    um = (user_message or "").strip()
    ar = (assistant_response or "").strip()
    if len(um) < 12 or len(ar) < 40:
        return []
    preview = list(existing_fingerprints)[:25]
    existing_block = "\n".join(f"- {x[:200]}" for x in preview if x) or "(none yet)"

    prompt = f"""You extract durable personal context for a spiritual-guidance chat app (Sikh / Gurbani).
Only extract facts the USER revealed or clearly implied about themselves — not generic scripture summaries.

EXISTING STORED FACTS (fingerprints — do not repeat or paraphrase these closely):
{existing_block}

USER MESSAGE:
{um[:4000]}

ASSISTANT REPLY:
{ar[:6000]}

Return ONLY a JSON array of 0 to {MAX_NEW_MEMORIES_PER_TURN} objects. Each object:
{{"fact_type": "situation"|"preference"|"topic"|"entity", "content": "one short neutral sentence", "importance": 1-10}}
Use importance 8+ only for major life events. Empty array [] if nothing new worth storing.
No markdown, no commentary outside the JSON."""

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(temperature=0.1, max_output_tokens=400),
            safety_settings=_RELAXED_SAFETY,
        )
        raw = _safe_response_text(response).strip()
    except Exception as e:
        logger.warning("Memory extraction LLM failed: %s", e)
        return []
    candidates = _parse_extraction_json(raw)
    deduped: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    for c in candidates:
        fp = _normalize_content(c["content"])
        if not fp or fp in existing_fingerprints or fp in seen:
            continue
        seen.add(fp)
        deduped.append(c)
    return deduped


def save_memory_facts(
    user_id: int,
    facts: List[Dict[str, Any]],
    chat_id: Optional[int] = None,
    user_message_id: Optional[int] = None,
    assistant_message_id: Optional[int] = None,
) -> int:
    """Insert facts; returns count saved."""
    if not facts:
        return 0
    n = 0
    fingerprints = _recent_content_fingerprints(user_id, limit=200)
    for f in facts:
        fp = _normalize_content(f["content"])
        if fp in fingerprints:
            continue
        row = UserMemory(
            user_id=user_id,
            fact_type=f["fact_type"],
            content=f["content"],
            importance=int(f.get("importance", 5)),
            source_chat_id=chat_id,
            source_user_message_id=user_message_id,
            source_assistant_message_id=assistant_message_id,
        )
        db.session.add(row)
        fingerprints.add(fp)
        n += 1
    if n:
        try:
            db.session.commit()
        except Exception as e:
            logger.warning("save_memory_facts commit failed: %s", e)
            db.session.rollback()
            return 0
    return n


def maybe_extract_and_save_after_guidance_turn(
    user: User,
    chat_id: Optional[int],
    user_message: str,
    assistant_message: str,
    user_message_id: Optional[int],
    assistant_message_id: Optional[int],
) -> None:
    """Fire-and-forget style: errors logged, never raises to caller."""
    if not user or not getattr(user, "memory_enabled", True):
        return
    try:
        fps = _recent_content_fingerprints(user.id, limit=200)
        facts = extract_new_memory_facts(user_message, assistant_message, fps)
        if facts:
            save_memory_facts(
                user.id,
                facts,
                chat_id=chat_id,
                user_message_id=user_message_id,
                assistant_message_id=assistant_message_id,
            )
    except Exception as e:
        logger.warning("maybe_extract_and_save_after_guidance_turn: %s", e)
