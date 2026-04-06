import re
from typing import List, Optional, Pattern, Tuple

from gurbani_content_quality import MIN_ENGLISH_CHARS_PARMAAN, MIN_GURMUKHI_CHARS_PARMAAN
from models import Shabad, db
from parmaan_search_normalize import latin_token_search_variants, token_has_gurmukhi
from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError

# STTM-style Gurmukhi ladder keys: user may type ੲ/ੳ instead of full vowel letters.
_GURMUKHI_LADDER_ALTERNATIVES = {
    "\u0a72": ("\u0a07", "\u0a08", "\u0a72"),  # ੲ -> ਇ, ਈ, ੲ
    "\u0a73": ("\u0a09", "\u0a0a", "\u0a73"),  # ੳ -> ਉ, ਊ, ੳ
}

# Between "words" in Gurmukhi / romanization / English lines in the DB
_FIRST_LETTER_SEP = r"(?:[\s\u00a0]+|[,;.:!?\u0964\u0965|]+)+"

_LATIN_WORD_TAIL = r"[a-z\(\)\-]*"
_ENGLISH_WORD_TAIL = r"[a-z'\-]*"
_GURMUKHI_WORD_TAIL = r"[\u0a00-\u0a7f]*"


def sanitize_like_filter(search_term: str) -> str:
    """Escape SQLAlchemy LIKE wildcards (% and _) to avoid 'LIKE injection' (issue audit)."""
    if not isinstance(search_term, str):
        return ""
    # SECURITY: Escape % and _ and \ in user input for LIKE patterns.
    # Note: SQLite and Postgres both treat backslash as escape char by default in SQLAlchemy.
    return search_term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _gurmukhi_char_class(typed: str) -> str:
    """Regex fragment: one Gurmukhi starter matching what the user typed (with STTM ladder alts)."""
    alts = _GURMUKHI_LADDER_ALTERNATIVES.get(typed, (typed,))
    esc = "|".join(re.escape(a) for a in alts)
    return f"(?:{esc})" if len(alts) > 1 else re.escape(alts[0])


def build_latin_first_letter_pattern(letters: List[str]) -> str:
    """
    STTM-style: each Latin letter starts a word in order (romanization or English).
    Words may be separated by spaces, ||, ॥, or light punctuation.
    """
    if not letters:
        return ""
    parts = [re.escape(L.lower()) + _ROMAN_OR_ENGLISH_WORD_TAIL for L in letters]
    return "^" + _FIRST_LETTER_SEP.join(parts)


def build_gurmukhi_first_letter_pattern(letters: List[str]) -> str:
    """Each typed Gurmukhi key starts a Gurmukhi word in order."""
    if not letters:
        return ""
    parts = [_gurmukhi_char_class(L) + _GURMUKHI_WORD_TAIL for L in letters]
    return "^" + _FIRST_LETTER_SEP.join(parts)


def build_english_first_letter_pattern(letters: List[str]) -> str:
    """Same as Latin but allow apostrophes inside English words."""
    if not letters:
        return ""
    parts = [re.escape(L.lower()) + _ROMAN_OR_ENGLISH_WORD_TAIL for L in letters]
    return "^" + _FIRST_LETTER_SEP.join(parts)


def parse_first_letter_query(query: str) -> Optional[Tuple[str, List[str]]]:
    """
    Parse a first-letter ladder query. Returns (script, letters) or None.
    script is 'gurmukhi' or 'latin' (latin patterns apply to romanization + English).
    """
    q = (query or "").strip()
    if not q:
        return None
    if any("\u0a00" <= ch <= "\u0a7f" for ch in q):
        letters = [ch for ch in q if "\u0a00" <= ch <= "\u0a7f"]
        if len(letters) < 2:
            return None
        return ("gurmukhi", letters)
    tokens = q.split()
    if tokens and all(len(t) == 1 and t.isalpha() for t in tokens):
        letters = [t.lower() for t in tokens]
        if len(letters) >= 2:
            return ("latin", letters)
    if " " not in q:
        letters = [c.lower() for c in q if c.isalpha()]
        if 3 <= len(letters) <= 20:
            return ("latin", letters)
    return None


def looks_like_first_letter_query(query: str) -> bool:
    """Heuristic for /api/search?mode=auto — avoid treating short English phrases as ladders."""
    return parse_first_letter_query(query) is not None


def _row_matches_first_letters(
    row: Shabad,
    script: str,
    latin_pat: Pattern[str],
    gurmukhi_pat: Pattern[str],
    english_pat: Pattern[str],
) -> bool:
    if script == "gurmukhi":
        g = (row.gurmukhi or "").strip()
        return bool(gurmukhi_pat.search(g))
    r = (row.romanization or "").strip().lower()
    e = (row.english_translation or "").strip().lower()
    return bool(latin_pat.search(r) or english_pat.search(e))


def find_shabads_by_first_letters(query: str, limit: int = 20) -> List[Shabad]:
    """
    SikhiToTheMax-style first-letter search: successive words must start with the given letters
    in order (from the start of the line). Gurmukhi ladders match gurmukhi; Latin ladders match
    romanization OR English translation.
    """
    parsed = parse_first_letter_query(query)
    if not parsed:
        return []
    script, letters = parsed
    try:
        if script == "gurmukhi":
            g_pat = re.compile(build_gurmukhi_first_letter_pattern(letters), re.UNICODE)
            latin_pat = re.compile("$^")  # never matches
            english_pat = re.compile("$^")
        else:
            latin_pat = re.compile(build_latin_first_letter_pattern(letters), re.IGNORECASE | re.UNICODE)
            english_pat = re.compile(build_english_first_letter_pattern(letters), re.IGNORECASE | re.UNICODE)
            g_pat = re.compile("$^")

        base = Shabad.query.filter(Shabad.embedding.isnot(None))
        base = _apply_parmaan_quality_filters(base, True)
        base = base.order_by(func.coalesce(Shabad.content_length, 0).desc(), Shabad.id.asc())

        dialect = db.engine.dialect.name
        if dialect == "postgresql":
            if script == "gurmukhi":
                pat = build_gurmukhi_first_letter_pattern(letters)
                col = Shabad.gurmukhi
            else:
                # One regex OR: romanization ~* pat OR english ~* pat_eng
                pat_roman = build_latin_first_letter_pattern(letters)
                pat_eng = build_english_first_letter_pattern(letters)
                
                # SECURITY: Block extremely broad regex patterns (DoS mitigation)
                if pat_roman in ("^.*", ".*") or len(letters) < 2:
                    return []

                rows = (
                    base.filter(
                        or_(
                            Shabad.romanization.op("~*")(pat_roman),
                            Shabad.english_translation.op("~*")(pat_eng),
                        )
                    )
                    .limit(limit)
                    .all()
                )
                return rows
            rows = base.filter(col.op("~*")(pat)).limit(limit).all()
            return rows

        # SQLite and others: stream rows and match in Python (tests / local SQLite).
        matches: List[Shabad] = []
        max_scan = 25000
        scanned = 0
        for row in base.yield_per(400):
            scanned += 1
            if scanned > max_scan:
                break
            if _row_matches_first_letters(row, script, latin_pat, g_pat, english_pat):
                matches.append(row)
                if len(matches) >= limit:
                    break
        return matches
    except SQLAlchemyError as e:
        print(f"[retrieval] first-letter search failure: {e}")
        return []


def _tokenize_search_words(query: str) -> List[str]:
    """Split query into non-trivial tokens for AND-style text match (Latin or Gurmukhi)."""
    q = (query or "").strip()
    if not q:
        return []
    parts = re.split(r"\s+", q)
    out: List[str] = []
    for p in parts:
        p = p.strip('.,;:!?|•·"\'()[]')
        if len(p) >= 2:
            out.append(p)
    return out


def _filter_shabad_matches_token(base, token: str):
    """
    AND-filter step: row must match this token in gurmukhi OR romanization OR english.
    Latin tokens expand via phonetic variants; Gurmukhi tokens match literally.
    """
    if token_has_gurmukhi(token):
        variants = [token]
    else:
        variants = latin_token_search_variants(token)
    token_clauses = []
    for v in variants:
        # SECURITY: sanitize sub-token to prevent LIKE injections
        pattern = f"%{sanitize_like_filter(v)}%"
        token_clauses.append(
            or_(
                Shabad.gurmukhi.ilike(pattern),
                Shabad.romanization.ilike(pattern),
                Shabad.english_translation.ilike(pattern),
            )
        )
    return base.filter(or_(*token_clauses))


def find_shabads_by_text_match(query: str, limit: int = 12) -> List[Shabad]:
    """
    Find shabads whose Gurmukhi, romanization, or English contains the search text.
    Uses AND across tokens when multiple words are present (narrower matches).
    Applies Parmaan quality filters (excludes header-only stubs and very short rows).
    """
    q = (query or "").strip()
    if len(q) < 3:
        return []
    words = _tokenize_search_words(q)
    if not words and len(q.strip()) >= 2:
        words = [q.strip()]
    if not words:
        return []
    try:
        base = Shabad.query.filter(Shabad.embedding.isnot(None))
        base = _apply_parmaan_quality_filters(base, True)
        for w in words:
            base = _filter_shabad_matches_token(base, w)
        rows = (
            base.order_by(func.coalesce(Shabad.content_length, 0).desc(), Shabad.id.asc())
            .limit(limit)
            .all()
        )
        return rows
    except SQLAlchemyError as e:
        print(f"[retrieval] text match failure: {e}")
        return []


def _apply_parmaan_quality_filters(query, exclude_parmaan_low_quality: bool):
    """
    Drop Raag/Mehla header stubs and overly short rows from Parmaan / discovery search.
    Rows with is_header_only IS NULL are kept (pre-backfill compatibility) unless
    they fail the length gate (headers are almost always short).
    """
    if not exclude_parmaan_low_quality:
        return query
    query = query.filter(Shabad.is_header_only.isnot(True))
    query = query.filter(func.length(Shabad.gurmukhi) >= MIN_GURMUKHI_CHARS_PARMAAN)
    query = query.filter(func.length(Shabad.english_translation) >= MIN_ENGLISH_CHARS_PARMAAN)
    return query


def find_similar_shabads(
    query_embedding: List[float],
    limit: int = 5,
    persona: Optional[str] = None,
    exclude_parmaan_low_quality: bool = False,
):
    """Return top-k most similar Shabad rows by cosine similarity."""
    if not query_embedding:
        return []

    try:
        query = Shabad.query

        if persona:
            query = query.filter(Shabad.recommended_persona.in_([persona, "any"]))

        query = _apply_parmaan_quality_filters(query, exclude_parmaan_low_quality)

        fetch_n = limit
        if exclude_parmaan_low_quality:
            # Nearest neighbors may be mostly header stubs; fetch extra then trim.
            fetch_n = min(max(limit * 8, 24), 120)

        rows = query.order_by(Shabad.embedding.cosine_distance(query_embedding)).limit(fetch_n).all()
        return rows[:limit]
    except SQLAlchemyError as e:
        print(f"[retrieval] DB query failure: {e}")
        return []


def search_similar_shabads(
    query_embedding: List[float],
    limit: int = 5,
    persona: Optional[str] = None,
    exclude_parmaan_low_quality: bool = False,
):
    """Alias for find_similar_shabads to match test expectations."""
    return find_similar_shabads(query_embedding, limit, persona, exclude_parmaan_low_quality)


def get_random_shabads(limit: int = 3):
    """Return a random selection of shabads."""
    try:
        from sqlalchemy.sql import func

        return Shabad.query.order_by(func.random()).limit(limit).all()
    except SQLAlchemyError as e:
        print(f"[retrieval] DB random query failure: {e}")
        return []


def get_shabad_by_id(shabad_id: str):
    """Return a shabad by its string shabad_id."""
    try:
        return Shabad.query.filter_by(shabad_id=shabad_id).first()
    except SQLAlchemyError as e:
        print(f"[retrieval] DB ID query failure: {e}")
        return None


def get_shabad_by_pk(pk: int):
    """Return a shabad by primary key."""
    try:
        return db.session.get(Shabad, pk)
    except SQLAlchemyError as e:
        print(f"[retrieval] DB pk query failure: {e}")
        return None


def browse_shabads(
    page: int = 1,
    per_page: int = 20,
    source: Optional[str] = None,
    search: Optional[str] = None,
    persona: Optional[str] = None,
) -> Tuple[List[Shabad], int]:
    """Paginated list with optional filters. Returns (items, total_count)."""
    try:
        q = Shabad.query
        if source:
            # SECURITY: sanitize user-provided source for LIKE
            s_val = f"%{sanitize_like_filter(source)}%"
            q = q.filter(Shabad.source.ilike(s_val))
        if persona:
            q = q.filter(Shabad.recommended_persona.in_([persona, "any"]))
        if search:
            # SECURITY: sanitize user-provided search term for LIKE
            term = f"%{sanitize_like_filter(search)}%"
            q = q.filter(
                or_(
                    Shabad.gurmukhi.ilike(term),
                    Shabad.english_translation.ilike(term),
                    Shabad.romanization.ilike(term),
                    Shabad.shabad_id.ilike(term),
                )
            )
        total = q.count()
        items = (
            q.order_by(Shabad.id.asc())
            .offset(max(0, (page - 1) * per_page))
            .limit(per_page)
            .all()
        )
        return items, total
    except SQLAlchemyError as e:
        print(f"[retrieval] browse failure: {e}")
        return [], 0


def find_similar_to_shabad(
    shabad: Shabad,
    limit: int = 6,
    exclude_self: bool = True,
    exclude_parmaan_low_quality: bool = False,
    persona: Optional[str] = None,
) -> List[Shabad]:
    """Neighbors in embedding space (excluding same row)."""
    # embedding may be a numpy vector from pgvector; never use `not embedding` (ambiguous truth value).
    if shabad is None or shabad.embedding is None:
        return []
    try:
        q = Shabad.query.filter(Shabad.embedding.isnot(None))
        if persona:
            q = q.filter(Shabad.recommended_persona.in_([persona, "any"]))
        if exclude_self:
            q = q.filter(Shabad.id != shabad.id)
        q = _apply_parmaan_quality_filters(q, exclude_parmaan_low_quality)
        fetch_n = limit
        if exclude_parmaan_low_quality:
            fetch_n = min(max(limit * 8, 24), 120)
        rows = q.order_by(Shabad.embedding.cosine_distance(shabad.embedding)).limit(fetch_n).all()
        return rows[:limit]
    except SQLAlchemyError as e:
        print(f"[retrieval] similar failure: {e}")
        return []
