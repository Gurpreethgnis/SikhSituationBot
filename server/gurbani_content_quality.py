"""
Detect Raag/Mehla header stubs vs substantive shabad rows for Parmaan retrieval.

BaniDB assigns a shabad id to section headers (e.g. "Aasaa, Fifth Mehla") as well as
full hymns. Those headers should not appear in semantic "pramaan" search results.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional

# Minimum text length for a row to be eligible for Parmaan-style vector search.
MIN_GURMUKHI_CHARS_PARMAAN = 50
MIN_ENGLISH_CHARS_PARMAAN = 30

# English ordinals used in SGGS section headers (word form, 1st–19th).
_EN_MEHLA_ORDINAL_WORDS = (
    r"first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|"
    r"eleventh|twelfth|thirteenth|fourteenth|fifteenth|sixteenth|seventeenth|"
    r"eighteenth|nineteenth"
)
# Numeric ordinals: 1st–19th + mehl / mehla (e.g. "11th Mehl").
_EN_MEHLA_NUMERIC = re.compile(
    r"\b((?:1[1-9]th|10th|[1-9](?:st|nd|rd|th)))\s+mehla?\b",
    re.IGNORECASE,
)
# English steek lines that are only Raag / Mehla metadata.
_EN_MEHLA_LINE = re.compile(
    rf"(?:{_EN_MEHLA_ORDINAL_WORDS})\s+mehl",
    re.IGNORECASE,
)
_EN_MAHALLA_LINE = re.compile(
    rf"(?:{_EN_MEHLA_ORDINAL_WORDS})\s+mahal",
    re.IGNORECASE,
)
_EN_RAAG_PREFIX = re.compile(r"^\s*raag\s+", re.IGNORECASE)
# "Aasaa, Fifth Mehla" / "Asa, First Mehl"
_EN_RAAG_COMMA_MEHLA = re.compile(
    rf"^[A-Za-z][A-Za-z\s\-–]{{0,48}},\s*(?:{_EN_MEHLA_ORDINAL_WORDS})\s+mehl",
    re.IGNORECASE,
)
# Structural section labels (not hymn text), e.g. "Seventeen Ashtpadheeyaa Of The First Mehla".
_EN_ASHTPADI_HEADER = re.compile(
    r"ashtpad[iey]+|ashtapad[iey]+|ashtpadee",
    re.IGNORECASE,
)
_SUBSTANTIVE_ENGLISH = re.compile(
    r"\b(the|you|your|thy|thou|god|lord|waheguru|guru|true|one|mind|soul|hope|fear|love|peace|"
    r"death|life|sin|virtue|faith|naam|meditate|sings?|speaks?|says?|obtain|"
    r"eternal|divine|human|world)\b",
    re.IGNORECASE,
)


def infer_verse_count_from_banidb_verses(verses: list) -> int:
    """Count verses that carry Gurmukhi text from a BaniDB shabad payload."""
    if not verses:
        return 0
    n = 0
    for v in verses:
        if not isinstance(v, dict):
            continue
        if (v.get("verse") or "").strip():
            n += 1
    return n


def infer_verse_count_from_gurmukhi(gurmukhi: Optional[str]) -> int:
    """Fallback when DB row has no verse_count: approximate from double-danda line breaks."""
    g = (gurmukhi or "").strip()
    if not g:
        return 0
    # Each complete line in Gurbani often ends with ॥
    breaks = g.count("॥")
    return max(1, breaks) if breaks else 1


def _english_looks_like_raag_mehla_only(english: str) -> bool:
    e = (english or "").strip()
    if not e:
        return True
    if _EN_RAAG_PREFIX.match(e):
        return True
    if _EN_RAAG_COMMA_MEHLA.match(e):
        return True
    if _EN_MEHLA_NUMERIC.search(e):
        if len(e) >= 160 and _SUBSTANTIVE_ENGLISH.search(e):
            return False
        return True
    if _EN_ASHTPADI_HEADER.search(e):
        # Section headers like "Seventeen Ashtpadheeyaa Of The First Mehla" are metadata.
        if len(e) >= 200 and _SUBSTANTIVE_ENGLISH.search(e):
            return False
        return True
    if _EN_MEHLA_LINE.search(e) or _EN_MAHALLA_LINE.search(e):
        # Long text with "mehla" might still be a real translation mentioning Mehla — check substance
        if len(e) >= 160 and _SUBSTANTIVE_ENGLISH.search(e):
            return False
        return True
    return False


def is_raag_header_only(gurmukhi: str, english: str, verse_count: int) -> bool:
    """
    True if this row is (likely) only a Raag/Mehla heading, not a hymn users want as pramaan.

    verse_count should be the number of BaniDB verses with non-empty Gurmukhi (>=1 for real shabads).
    """
    g = (gurmukhi or "").strip()
    e = (english or "").strip()

    if verse_count < 1:
        return True
    if verse_count >= 2:
        return False

    # Single-verse: almost always a header or a very short slok; long single-verse shabads exist.
    if len(g) >= MIN_GURMUKHI_CHARS_PARMAAN and len(e) >= MIN_ENGLISH_CHARS_PARMAAN:
        if _english_looks_like_raag_mehla_only(e) and len(e) < 100:
            return True
        if _SUBSTANTIVE_ENGLISH.search(e):
            return False

    if _english_looks_like_raag_mehla_only(e) and len(e) < 180:
        return True

    if "ਮਹਲਾ" in g and len(g) < 85:
        if len(e) < 120 or _english_looks_like_raag_mehla_only(e):
            return True

    return False


def compute_shabad_quality_fields(
    gurmukhi: str,
    english: str,
    verse_count: int,
) -> Dict[str, Any]:
    """Fields to persist on Shabad rows from ingest or backfill."""
    g = (gurmukhi or "").strip()
    content_length = len(g)
    return {
        "is_header_only": is_raag_header_only(g, english, verse_count),
        "verse_count": max(verse_count, 0),
        "content_length": content_length,
    }


def recompute_quality_for_stored_row(
    gurmukhi: str,
    english: str,
    verse_count: Optional[int] = None,
) -> Dict[str, Any]:
    """For backfill/admin: infer verse_count when missing."""
    vc = verse_count
    if vc is None:
        vc = infer_verse_count_from_gurmukhi(gurmukhi)
    return compute_shabad_quality_fields(gurmukhi, english, vc)


def passes_parmaan_minimum_length(gurmukhi: str, english: str) -> bool:
    """Length gate used alongside is_header_only in vector search."""
    g = (gurmukhi or "").strip()
    e = (english or "").strip()
    return len(g) >= MIN_GURMUKHI_CHARS_PARMAAN and len(e) >= MIN_ENGLISH_CHARS_PARMAAN
