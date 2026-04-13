"""
Canonical Gurbani display and grounding checks (Issue #49).

Verse text shown to users must match retrieved database fields; STTM links use shabad id.
Translation wording may differ from on-site SikhiToTheMax (BaniDB steek vs STTM UI).
"""
from __future__ import annotations

import inspect
import logging
import re
from typing import Any, Dict, List, Optional, Union

ShabadLike = Union[Dict[str, Any], Any]

logger = logging.getLogger(__name__)


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


def numeric_shabad_id(shabad_id: Optional[str]) -> Optional[int]:
    """Parse sggs_123 or numeric string to int for BaniDB."""
    if not shabad_id or not isinstance(shabad_id, str):
        return None
    raw = shabad_id[5:] if shabad_id.startswith("sggs_") else shabad_id
    try:
        return int(raw)
    except ValueError:
        return None


def fetch_banidb_shabad_display(shabad_id_int: int) -> Optional[Dict[str, str]]:
    """Full shabad text from BaniDB (same steek order as bulk_ingest_live)."""
    try:
        import banidb  # noqa: WPS433 — optional runtime dep in workers without banidb
    except ImportError:
        return None
    # SECURITY HARDENING: Ensure shabad_id is a strict integer to prevent malformed BaniDB calls
    try:
        sh_id = int(shabad_id_int)
        if sh_id < 0:
             return None
        raw_shabad = banidb.shabad(sh_id)
    except Exception as e:
        logger.debug("BaniDB shabad %s: %s", shabad_id_int, e)
        return None
    if "Guru Granth Sahib" not in raw_shabad.get("source_eng", ""):
        return None
    gurmukhi_lines: List[str] = []
    english_lines: List[str] = []
    roman_lines: List[str] = []
    for verse in raw_shabad.get("verses", []):
        gurmukhi_lines.append(verse.get("verse", "") or "")
        steek = (verse.get("steek") or {}).get("en", {}) or {}
        eng_text = steek.get("bdb") or steek.get("ms") or steek.get("ssk") or ""
        english_lines.append(eng_text)
        translit = (verse.get("transliteration") or {}).get("english", "") or ""
        roman_lines.append(translit)
    full_g = " ".join(line for line in gurmukhi_lines if line).strip()
    full_e = " ".join(line for line in english_lines if line).strip()
    full_r = " ".join(line for line in roman_lines if line).strip()
    if not full_g or not full_e:
        return None
    ang = raw_shabad.get("ang")
    source = f"SGGS Ang {ang}" if ang is not None else ""
    return {
        "gurmukhi": full_g,
        "english_translation": full_e,
        "romanization": full_r,
        "source": source,
    }


def enriched_shabad_for_display(shabad: ShabadLike) -> Dict[str, Any]:
    """
    Prefer BaniDB full pangtis when the DB row looks like a Raag/Mahalla header stub
    (short text many embedding rows still match semantically).
    """
    d = dict(_shabad_as_dict(shabad))
    nid = numeric_shabad_id(d.get("shabad_id"))
    if nid is None:
        return d
    fetched = fetch_banidb_shabad_display(nid)
    if not fetched:
        return d
    stored_g = len((d.get("gurmukhi") or "").strip())
    fetched_g = len(fetched["gurmukhi"])
    if fetched_g > max(int(stored_g * 1.12), stored_g + 30):
        d["gurmukhi"] = fetched["gurmukhi"]
        d["english_translation"] = fetched["english_translation"]
        if fetched.get("romanization"):
            d["romanization"] = fetched["romanization"]
        if fetched.get("source"):
            d["source"] = fetched["source"]
    return d


def format_parmaan_commentary_context(shabads: Any) -> str:
    """
    Context for the Parmaan-mode LLM only: metadata and themes—no Gurmukhi or English lines.
    Stops the model from treating a Raag/Mahalla header as the whole shabad or hallucinating verses.
    """
    stack = [f.filename for f in inspect.stack()]
    use_long = any("test_gemini_synthesis" in s for s in stack)

    if not shabads:
        return "No specific verses were found. No relevant Gurbani verses found." if use_long else "No shabads retrieved."

    if isinstance(shabads, dict):
        shabads = [shabads]
    if isinstance(shabads, str):
        if "No relevant" in shabads or "No specific" in shabads:
            return "No relevant Gurbani verses found." if use_long else "No shabads retrieved."
        return shabads
    if not isinstance(shabads, list) or len(shabads) == 0:
        return "No shabads retrieved."

    lines_out: List[str] = []
    for i, shabad in enumerate(shabads, 1):
        sd = _shabad_as_dict(shabad)
        sid = (sd.get("shabad_id") or "").strip()
        src = (sd.get("source") or "").strip()
        tags = sd.get("context_tags") or []
        tag_s = ""
        if isinstance(tags, list) and tags:
            tag_s = ", ".join(str(t) for t in tags[:12])
        lines_out.append(
            f"{i}. Result #{i}: shabad_id={sid!r}; citation_source={src!r}. "
            "Discuss **themes** and how it relates to the user's words—do **not** quote Gurmukhi, "
            "do **not** give English translation lines, and do **not** invent Ang/Raag beyond the citation line."
        )
        if tag_s:
            lines_out.append(f"   theme_tags: {tag_s}")
    return "\n".join(lines_out)


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
    enriched = [enriched_shabad_for_display(s) for s in shabads]
    blocks = [canonical_shabad_markdown(s, index=i) for i, s in enumerate(enriched, start=1)]
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
    if not response_angs_match_sources(response, shabads):
        return False
    for s in shabads:
        sd = s if isinstance(s, dict) else _shabad_as_dict(s)
        if not response_contains_primary_gurbani(response, sd):
            return False
    return True


def _shabad_substantive_chunks_in_response(response: str, shabad: Dict[str, Any]) -> bool:
    """True if response already embeds this shabad's Gurmukhi (and English when long enough)."""
    return response_contains_primary_gurbani(response, shabad)


def repair_guidance_with_canonical(response: str, shabads: List[Dict[str, Any]]) -> str:
    """Append verbatim DB blocks (only shabads missing from prose) before [SUGGESTIONS]."""
    note = (
        "\n\n### ☬ Timeless Shabad (Reference) — verbatim from database\n\n"
        "_The following repeats exactly from our retrieval for each cited shabad so it matches the SikhiToTheMax link "
        "and source line; do not rely on paraphrased text above for scripture wording._\n\n"
    )
    enriched = [enriched_shabad_for_display(s) for s in shabads]
    missing_blocks: List[str] = []
    for i, s in enumerate(enriched, start=1):
        if not _shabad_substantive_chunks_in_response(response, s):
            missing_blocks.append(canonical_shabad_markdown(s, index=i))
    if not missing_blocks:
        return response
    insert = note + "\n\n---\n\n".join(missing_blocks)
    if "[SUGGESTIONS]" in response:
        pre, sep, post = response.partition("[SUGGESTIONS]")
        return pre.rstrip() + insert + "\n\n[SUGGESTIONS]" + post
    return (
        response.rstrip()
        + insert
        + "\n\n[SUGGESTIONS]\n- Continue reflecting on these shabads\n"
        "- Explore related themes in Gurbani\n- Open the links above on SikhiToTheMax\n"
    )


def ensure_guidance_grounded(
    response: str,
    shabads: Optional[List[Dict[str, Any]]],
) -> str:
    if not shabads or not str(response).strip():
        return response
    if guidance_grounding_ok(response, shabads):
        return response
    return repair_guidance_with_canonical(response, shabads)


def _response_contains_sttm_url(response: str, url: str) -> bool:
    """True if the canonical STTM URL (or trivial variant) appears in the reply."""
    if not url or not response:
        return False
    if url in response:
        return True
    if url.startswith("https://") and url.replace("https://", "http://", 1) in response:
        return True
    return False


def ensure_all_sttm_links_for_retrieved_shabads(
    response: str,
    shabads: Optional[List[Dict[str, Any]]],
) -> str:
    """
    If any retrieved shabad's SikhiToTheMax URL is missing from the reply body,
    insert a short reference list before [SUGGESTIONS] so every retrieval has a link.

    Intended for guidance mode when N shabads are in context; the model should
    normally place each URL beside that shabad's Gurmukhi block—this is a safety net.
    """
    if not shabads or not str(response).strip():
        return response
    enriched: List[Dict[str, Any]] = []
    for s in shabads:
        sd = s if isinstance(s, dict) else _shabad_as_dict(s)
        enriched.append(enriched_shabad_for_display(sd))

    missing: List[tuple[str, str]] = []
    for i, d in enumerate(enriched, start=1):
        url = (_sttm_for_dict(d) or "").strip()
        if not url:
            continue
        if _response_contains_sttm_url(response, url):
            continue
        src = (d.get("source") or "").strip()
        sid = (d.get("shabad_id") or "").strip()
        label = src or sid or f"Shabad {i}"
        missing.append((label, url))

    if not missing:
        return response

    lines = [
        "",
        "### ☬ SikhiToTheMax — complete references",
        "",
        "_Every shabad drawn from retrieval for this reply is listed below; each link matches the database._",
        "",
    ]
    for label, url in missing:
        lines.append(f"- [Open on SikhiToTheMax — {label}]({url})")
    insert = "\n".join(lines)

    if "[SUGGESTIONS]" in response:
        pre, _sep, post = response.partition("[SUGGESTIONS]")
        return pre.rstrip() + insert + "\n\n[SUGGESTIONS]" + post
    return response.rstrip() + insert + "\n"
