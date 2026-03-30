"""
One-off backfill: set is_header_only, verse_count, content_length on all shabad rows.

Run from the server directory with DATABASE_URL set (same as the Flask app):

  cd server && python backfill_shabad_quality.py
"""
from __future__ import annotations

import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Allow running as script from server/
_SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
if _SERVER_DIR not in sys.path:
    sys.path.insert(0, _SERVER_DIR)

from app import app  # noqa: E402
from gurbani_content_quality import recompute_quality_for_stored_row  # noqa: E402
from models import Shabad, db  # noqa: E402


def main() -> None:
    with app.app_context():
        total = Shabad.query.count()
        logger.info("Backfilling content quality fields for %s shabads...", total)
        processed = 0
        for s in Shabad.query.order_by(Shabad.id).all():
            q = recompute_quality_for_stored_row(
                s.gurmukhi or "",
                s.english_translation or "",
                s.verse_count,
            )
            s.is_header_only = q["is_header_only"]
            s.verse_count = q["verse_count"]
            s.content_length = q["content_length"]
            processed += 1
            if processed % 500 == 0:
                db.session.commit()
                logger.info("  committed %s / %s", processed, total)
        db.session.commit()
        logger.info("Done. Updated %s rows.", processed)


if __name__ == "__main__":
    main()
