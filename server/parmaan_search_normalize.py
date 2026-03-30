"""
Phonetic / spelling variants for Parmaan text search (user Latin input vs DB romanization).

STTM-style romanization often uses explicit short vowels (e.g. satigur, teree, aasaiaa) while
users may type informal spellings (satgur, teri, aasya). We expand each Latin token to a small
set of ILIKE patterns, OR-ed per token, AND-ed across tokens.
"""
from __future__ import annotations

import re
from typing import List, Set

# Gurmukhi block (Gurmukhi / Gurmukhi supplement used in SGGS text)
GURMUKHI_RE = re.compile(r"[\u0a00-\u0a7f]")

# Do not explode SQL OR clauses
MAX_VARIANTS_PER_TOKEN = 14


def token_has_gurmukhi(token: str) -> bool:
    return bool(GURMUKHI_RE.search(token or ""))


def _add_variant(out: Set[str], s: str) -> None:
    s = (s or "").strip()
    if len(s) >= 1:
        out.add(s)


def latin_token_search_variants(token: str) -> List[str]:
    """
    Generate alternative spellings for one whitespace token (Latin / informal Roman).
    Gurmukhi tokens should use token_has_gurmukhi and skip this — pass [token] only.
    """
    t = (token or "").lower().strip()
    out: Set[str] = set()
    if not t:
        return []

    _add_variant(out, t)
    variants = set(out)

    def expand_once(bucket: Set[str]) -> Set[str]:
        nxt = set(bucket)
        for s in bucket:
            # satgur ↔ satigur (common user vs STTM)
            if "satgur" in s:
                _add_variant(nxt, s.replace("satgur", "satigur"))
            if "satigur" in s:
                _add_variant(nxt, s.replace("satigur", "satgur"))
            # va / wa interchange (waheguru / vaheguru, etc.)
            if s.startswith("wahe") and len(s) >= 5:
                _add_variant(nxt, "vahe" + s[4:])
            if s.startswith("vahe") and len(s) >= 5:
                _add_variant(nxt, "wahe" + s[4:])
            # prabhu ↔ prabh (substring — avoids over-broad full-word rules)
            if "prabhu" in s:
                _add_variant(nxt, s.replace("prabhu", "prabh"))
            if "prabh" in s and "prabhu" not in s and len(s) < 40:
                _add_variant(nxt, s.replace("prabh", "prabhu", 1))
            # Nanak / Naanak style
            if re.search(r"nanak", s) and "naanak" not in s:
                _add_variant(nxt, re.sub(r"nanak", "naanak", s, count=1))
            if "naanak" in s:
                _add_variant(nxt, s.replace("naanak", "nanak", 1))
            # Double vowels often typed as singles for -ee / -oo
            if "ee" in s:
                _add_variant(nxt, s.replace("ee", "i"))
            if re.search(r"(?<![eo])i(?![eo])", s) and "ee" not in s and len(s) <= 24:
                if re.search(r"\bteri\b", s):
                    _add_variant(nxt, re.sub(r"\bteri\b", "teree", s))
                if re.search(r"\bteree\b", s):
                    _add_variant(nxt, re.sub(r"\bteree\b", "teri", s))
            if "oo" in s:
                _add_variant(nxt, s.replace("oo", "u"))
            # aasya ↔ aasaiaa (satgur teri aasya vs aasaiaa)
            if "aasya" in s:
                _add_variant(nxt, s.replace("aasya", "aasaiaa"))
                _add_variant(nxt, s.replace("aasya", "aasiaa"))
            if "aasaiaa" in s:
                _add_variant(nxt, s.replace("aasaiaa", "aasya"))
            if "aasiaa" in s:
                _add_variant(nxt, s.replace("aasiaa", "aasya"))
            # guru ↔ gur (common endings)
            if s.endswith("guru") and len(s) >= 5:
                _add_variant(nxt, s[:-1])
            if s.endswith("gur") and not s.endswith("guru") and len(s) >= 4:
                _add_variant(nxt, s + "u")
            # naam ↔ nam (doubled 'a')
            if "naam" in s:
                _add_variant(nxt, s.replace("naam", "nam"))
            if "nam" in s and "naam" not in s:
                _add_variant(nxt, s.replace("nam", "naam", 1))
            # har ↔ hari (common shortening)
            if re.search(r"\bhari\b", s):
                _add_variant(nxt, re.sub(r"\bhari\b", "har", s))
            if re.search(r"\bhar\b", s) and not re.search(r"\bhari\b", s):
                _add_variant(nxt, re.sub(r"\bhar\b", "hari", s))
            # sikh ↔ sikh (no change, but sikhi ↔ sikh)
            if re.search(r"\bsikhi\b", s):
                _add_variant(nxt, re.sub(r"\bsikhi\b", "sikh", s))
            if re.search(r"\bsikh\b", s) and not re.search(r"\bsikhi\b", s):
                _add_variant(nxt, re.sub(r"\bsikh\b", "sikhi", s))
            # ji suffix (waheguru ji ↔ waheguruji, etc.)
            if " ji" in s:
                _add_variant(nxt, s.replace(" ji", "ji"))
            if re.search(r"[a-z]ji\b", s):
                _add_variant(nxt, re.sub(r"([a-z])ji\b", r"\1 ji", s))
        return nxt

    # Run two passes so satgur→satigur can combine with other rules
    for _ in range(2):
        variants = expand_once(variants)
        if len(variants) >= MAX_VARIANTS_PER_TOKEN:
            break

    # Stable order: shortest first can help planner slightly; prefer original first
    lst = sorted(variants, key=lambda x: (0 if x == t else 1, len(x), x))
    return lst[:MAX_VARIANTS_PER_TOKEN]

