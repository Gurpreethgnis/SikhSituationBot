from flask import Blueprint, jsonify, request
import logging

from retrieval import find_shabads_by_text_match
from models import Shabad

logger = logging.getLogger(__name__)

search_blueprint = Blueprint("search", __name__)

@search_blueprint.route("/api/search", methods=["GET"])
def search_gurbani():
    """
    Live Gurbani text search endpoint (similar to iGurbani).
    Expects single query parameter 'q'. Requires at least 3 characters.
    """
    query = (request.args.get("q") or "").strip()
    
    if not query or len(query) < 3:
        return jsonify({"results": []}), 200

    try:
        # Retrieve matching shabads. Limit is set to a reasonable number to prevent massive payloads.
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
