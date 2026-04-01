from flask import Blueprint, jsonify, request
import logging

from retrieval import find_shabads_by_first_letters, find_shabads_by_text_match, looks_like_first_letter_query
from models import Shabad

logger = logging.getLogger(__name__)

search_blueprint = Blueprint("search", __name__)

@search_blueprint.route("/api/search", methods=["GET"])
def search_gurbani():
    """
    Live Gurbani text search endpoint (similar to iGurbani / STTM).
    Query parameter 'q' is required.
    Optional 'mode': 'auto' (default), 'first_letter', or 'text'.
    First-letter mode accepts short ladders (e.g. Gurmukhi keys or Latin "stmp").
    """
    query = (request.args.get("q") or "").strip()
    mode = (request.args.get("mode") or "auto").strip().lower()

    if not query:
        return jsonify({"results": []}), 200

    try:
        rows = []
        if mode == "first_letter":
            rows = find_shabads_by_first_letters(query, limit=50)
        elif mode == "text":
            if len(query) < 3:
                return jsonify({"results": []}), 200
            rows = find_shabads_by_text_match(query, limit=50)
        else:
            # auto
            if looks_like_first_letter_query(query):
                rows = find_shabads_by_first_letters(query, limit=50)
            if not rows:
                if len(query) < 3:
                    return jsonify({"results": []}), 200
                rows = find_shabads_by_text_match(query, limit=50)
        
        # Serialize the rows for the frontend.
        # We include id, shabad_id, gurmukhi, romanization, english_translation, source, and verse_count.
        results = []
        for row in rows:
            results.append({
                "id": row.id,
                "shabad_id": row.shabad_id,
                "gurmukhi": row.gurmukhi,
                "transliteration": row.romanization,
                "translation": row.english_translation,
                "source": row.source,
                "verse_count": row.verse_count,
            })
            
        return jsonify({"results": results}), 200

    except Exception as e:
        logger.error(f"Error during Gurbani search: {e}", exc_info=True)
        return jsonify({"error": "Failed to perform search"}), 500
