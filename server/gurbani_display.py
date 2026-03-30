"""
Canonical Gurbani display and grounding checks (Issue #49).

Verse text shown to users must match retrieved database fields; STTM links use shabad id.
Translation wording may differ from on-site SikhiToTheMax (BaniDB steek vs STTM UI).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Union

ShabadLike = Union[Dict[str, Any], Any]


def _sttm_link_from_shabad_id(shabad_id: Optional[str]) -> str:
    if not shabad_id or not isinstance(shabad_id, str):
        return ""
    numeric_id = shabad_id[5:] if shabad_id.startswith("sggs_") else shabad_id
    return f"https://www.sikhitothemax.org/shabad?id={numeric_id}"


def _shabad_as_dict(shabad: ShabadLike) -> Dict[str, Any]:
    if isinstance(shabad, dict):
        return shabad
    return {
        "gurmukhi": getattr(shabad, "gurmukhi", None),
        "romanization": getattr(shabad, "romanization", None),
        "english_translation": getattr(shabad, "english_translation", None),
        "source": getattr(shabad, "source", None),
        "shabad_id": getattr(shabad, "shabad_id", None),
        "sttm_link": getattr(
            shabad, "sttm_link", None
        ),  # may be missing on ORM object
    }


def _sttm_for_dict(d: Dict[str, Any]) -> str:
    link = (d.get("sttm_link") or "").strip()
    if link:
        return link
    return _sttm_link_from_shabad_id(d.get("shabad_id"))


def canonical_shabad_markdown(shabad: ShabadLike, index: Optional[int] = None) -> str:
    """Fixed markdown for one shabad from DB fields (verbatim)."""
    d = _shabad_as_dict(shabad)
    g = (d.get("gurmukhi") or "").strip()
    en = (d.get("english_translation") or d.get("english") or "").strip()
    ro = (d.get("romanization") or d.get("roman") or "").strip()
    src = (d.get("source") or "").strip()
    sid = (d.get("shabad_id") or "").strip()
    sttm = _sttm_for_dict(d)

    title_parts = []
    if index is not None:
        title_parts.append(f"Shabad {index}")
    if src:
        title_parts.append(src)
    heading = " — ".join(title_parts) if title_parts else (sid or "Shabad")

    lines = [f"### ☬ {heading}"]
    if g:
        lines.append(f"**Gurmukhi:** {g}")
    if en:
        lines.append(f"**English:** {en}")
    if ro:
        lines.append(f"**Roman:** {ro}")
    if sid:
        lines.append(f"**Shabad ID:** {sid}")
    if sttm:
        lines.append(f"**SikhiToTheMax:** [Open on SikhiToTheMax]({sttm})")
    return "\n\n".join(lines)


def parmaan_canonical_section(shabads: List[ShabadLike]) -> str:
    """All retrieved shabads as verbatim blocks (prepended in Parmaan mode)."""
    if not shabads:
        return ""
    blocks = [canonical_shabad_markdown(s, index=i) for i, s in enumerate(shabads, start=1)]
    intro = (
        "## Retrieved Gurbani (verbatim from database)\n\n"
        "The text below is copied exactly from our scripture database for each link. "
        "On SikhiToTheMax, visible translation may use different wording; the shabad id in the link is authoritative.\n\n"
    )
    return intro + "\n\n---\n\n".join(blocks)


def normalize_ws(text: str) -> str:
    return " ".join((text or "").split())


def _gurmukhi_english_chunks(shabad: Dict[str, Any]) -> tuple[str, str]:
    g = normalize_ws(shabad.get("gurmukhi") or "")
    e = normalize_ws(
        shabad.get("english_translation") or shabad.get("english") or ""
    )
    chunk_g = g[: min(120, len(g))] if g else ""
    chunk_e = e[: min(160, len(e))] if e else ""
    return chunk_g, chunk_e


def response_contains_primary_gurbani(response: str, primary: Dict[str, Any]) -> bool:
    """True if normalized response embeds a substantial prefix of primary Gurmukhi and English."""
    r = normalize_ws(response)
    chunk_g, chunk_e = _gurmukhi_english_chunks(primary)
    if len(chunk_g) < 12:
        return True
    if chunk_g not in r:
        return False
    if chunk_e and len(chunk_e) >= 20 and chunk_e not in r:
        return False
    return True


def allowed_angs_from_shabads(shabads: List[Dict[str, Any]]) -> Optional[set]:
    found: set = set()
    for s in shabads:
        src = s.get("source") or ""
        for m in re.finditer(r"Ang\s*(\d+)", str(src), re.I):
            found.add(int(m.group(1)))
    return found if found else None


def response_angs_match_sources(response: str, shabads: List[Dict[str, Any]]) -> bool:
    """Every 'Ang N' mention in the response must appear in at least one shabad source line."""
    allowed = allowed_angs_from_shabads(shabads)
    if not allowed:
        return True
    for m in re.finditer(r"\bAng\s*(\d+)\b", response, re.I):
        n = int(m.group(1))
        if n not in allowed:
            return False
    return True


def guidance_grounding_ok(response: str, shabads: Optional[List[Dict[str, Any]]]) -> bool:
    if not shabads:
        return True
    primary = shabads[0]
    if not response_contains_primary_gurbani(response, primary):
        return False
    if not response_angs_match_sources(response, shabads):
        return False
    return True


def repair_guidance_with_canonical(response: str, shabads: List[Dict[str, Any]]) -> str:
    """Append verbatim primary (and note) before [SUGGESTIONS] so scripture matches DB."""
    note = (
        "\n\n### ☬ Timeless Shabad (Reference) — verbatim from database\n\n"
        "_The following is repeated exactly from our retrieval so it matches the SikhiToTheMax link "
        "and source line; do not rely on paraphrased text above for scripture wording._\n\n"
    )
    primary_block = canonical_shabad_markdown(shabads[0], index=1)
    insert = note + primary_block
    if "[SUGGESTIONS]" in response:
        pre, sep, post = response.partition("[SUGGESTIONS]")
        return pre.rstrip() + insert + "\n\n[SUGGESTIONS]" + post
    return (response.rstrip() + insert + "\n\n[SUGGESTIONS]\n- Continue reflecting on this shabad\n"
            "- Explore related themes in Gurbani\n- Open the link above on SikhiToTheMax\n")


def ensure_guidance_grounded(
    response: str,
    shabads: Optional[List[Dict[str, Any]]],
) -> str:
    if not shabads or not str(response).strip():
        return response
    if guidance_grounding_ok(response, shabads):
        return response
    return repair_guidance_with_canonical(response, shabads)
