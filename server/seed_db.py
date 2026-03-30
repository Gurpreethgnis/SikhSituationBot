import os
import json
import time
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import google.generativeai as genai
from dotenv import load_dotenv
from sqlalchemy import text

from vector_utils import (
    get_embedding,
    load_local_model,
    calculate_backoff_delay
)
from models import Shabad
from app import db, app

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# Configure Gemini API
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

@dataclass
class SeedingStats:
    """Track seeding progress and statistics."""
    total_processed: int = 0
    successful_embeddings: int = 0
    failed_embeddings: int = 0
    duplicates_skipped: int = 0
    start_time: float = 0.0

    def get_elapsed_time(self) -> float:
        return time.time() - self.start_time

    def get_success_rate(self) -> float:
        if self.total_processed == 0:
            return 0.0
        return (self.successful_embeddings / self.total_processed) * 100

def validate_shabad_data(item: Dict[str, Any]) -> bool:
    """Validate that shabad data has required fields."""
    # Support both 'english_translation' and 'english' for test compatibility
    gurmukhi = item.get('gurmukhi', '').strip()
    english = (item.get('english_translation') or item.get('english') or '').strip()
    
    if not gurmukhi or not english:
        return False
    return True

def get_embedding_content(item: Dict[str, Any]) -> str:
    """Extract the best content for embedding generation."""
    # Primary: English translation (what users will query in)
    content = (item.get('english_translation') or item.get('english') or '').strip()

    # Secondary: Add context tags for better semantic matching
    context_tags = item.get('context_tags', [])
    if context_tags:
        content += " " + " ".join(context_tags)

    # Tertiary: Add romanization if translation is short
    if len(content.split()) < 10:
        romanization = item.get('romanization', '').strip()
        if romanization:
            content += " " + romanization

    return content

def check_duplicate_shabad(shabad_id: str, gurmukhi: str) -> bool:
    """Check if shabad already exists in database."""
    try:
        with app.app_context():
            existing = Shabad.query.filter(
                (Shabad.shabad_id == shabad_id) |
                (Shabad.gurmukhi == gurmukhi)
            ).first()
            return existing is not None
    except Exception as e:
        logger.error(f"Error checking for duplicate shabad: {e}")
        return False

def seed_database(json_file_path: str, batch_size: int = 10, skip_duplicates: bool = True) -> SeedingStats:
    """Read the SGGS JSON file, generate embeddings, and insert into DB with robust error handling."""
    stats = SeedingStats()
    stats.start_time = time.time()

    if not os.path.exists(json_file_path):
        logger.error(f"Data file not found: {json_file_path}")
        return stats

    try:
        # Use standard open for mock compatibility and encoding support
        with open(json_file_path, 'r') as f:
            shabads_data = json.load(f)
            logger.info(f"Loaded {len(shabads_data)} items from {json_file_path}")
            if not shabads_data:
                logger.warning(f"No data found in {json_file_path}")
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load JSON data: {e}")
        return stats

    if not isinstance(shabads_data, list):
        logger.error("JSON data is not a list")
        return stats

    logger.info(f"Loaded {len(shabads_data)} shabads from {json_file_path}")

    # Setup database within app context
    try:
        with app.app_context():
            # Try to setup pgvector extension if it doesn't exist (if on Postgres)
            from sqlalchemy import text
            try:
                db.session.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
                db.session.commit()
            except Exception as e:
                logger.warning(f"Failed to setup pgvector: {e}")
                db.session.rollback()

            # Ensure tables exist AFTER extension is created
            db.create_all()

            # Ensure the embedding column is unconstrained (in case it was created with a specific dimension previously)
            try:
                db.session.execute(text('ALTER TABLE shabads ALTER COLUMN embedding TYPE vector'))
                db.session.commit()
            except Exception as e:
                logger.warning(f"Failed to alter embedding column: {e}")
                db.session.rollback()

            batch_items = []
            for index, item in enumerate(shabads_data):
                stats.total_processed += 1

                # Validate data
                if not validate_shabad_data(item):
                    logger.warning(f"Skipping invalid shabad at index {index}")
                    continue

                shabad_id = str(item.get('shabad_id') or item.get('id') or (index + 1))
                gurmukhi = item.get('gurmukhi')

                # Check for duplicates
                if skip_duplicates and check_duplicate_shabad(shabad_id, gurmukhi):
                    stats.duplicates_skipped += 1
                    continue

                # Generate content to embed
                content_to_embed = get_embedding_content(item)
                if not content_to_embed:
                    logger.warning(f"Could not generate embedding content for shabad: {shabad_id}")
                    continue

                # Generate embedding
                embedding = get_embedding(content_to_embed)

                if embedding:
                    stats.successful_embeddings += 1
                    shabad = Shabad(
                        shabad_id=shabad_id,
                        gurmukhi=gurmukhi,
                        english_translation=item.get('english_translation') or item.get('english'),
                        romanization=item.get('romanization') or item.get('roman'),
                        embedding=embedding,
                        context_tags=item.get('context_tags', [])
                    )
                    batch_items.append(shabad)

                    # Periodically commit batches
                    if len(batch_items) >= batch_size:
                        try:
                            db.session.add_all(batch_items)
                            db.session.commit()
                            logger.info(f"Committed batch of {len(batch_items)} shabads")
                            batch_items = []
                        except Exception as e:
                            logger.error(f"Failed to commit batch: {e}")
                            db.session.rollback()
                            stats.successful_embeddings -= len(batch_items)
                            batch_items = []
                else:
                    stats.failed_embeddings += 1
                    logger.warning(f"Failed to generate embedding for shabad: {shabad_id}")

            # Final commit for remaining items
            if batch_items:
                try:
                    db.session.add_all(batch_items)
                    db.session.commit()
                    logger.info(f"Committed final batch of {len(batch_items)} shabads")
                except Exception as e:
                    logger.error(f"Failed to commit final batch: {e}")
                    db.session.rollback()
                    stats.successful_embeddings -= len(batch_items)

    except Exception as e:
        logger.error(f"Seeding process failed: {e}")

    # Log final statistics
    elapsed = stats.get_elapsed_time()
    success_rate = stats.get_success_rate()

    logger.info("=" * 50)
    logger.info("DATABASE SEEDING COMPLETE")
    logger.info("=" * 50)
    logger.info(f"Total processed: {stats.total_processed}")
    logger.info(f"Successfully embedded: {stats.successful_embeddings}")
    logger.info(f"Failed embeddings: {stats.failed_embeddings}")
    logger.info(f"Duplicates skipped: {stats.duplicates_skipped}")
    logger.info(f"Elapsed time: {elapsed:.2f} seconds")
    logger.info(f"Success rate: {success_rate:.1f}%")
    logger.info("=" * 50)

    return stats

if __name__ == "__main__":
    # Default usage: python seed_db.py
    # Uses the cleaned data file by default
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'shabads_cleaned.json')

    # Allow override via command line argument
    import sys
    if len(sys.argv) > 1:
        data_path = sys.argv[1]

    logger.info(f"Seeding database from: {data_path}")
    stats = seed_database(data_path, batch_size=5)  # Smaller batch for testing

    # Exit with error code if seeding failed
    if stats.successful_embeddings == 0:
        logger.error("Seeding failed - no shabads were successfully processed")
        sys.exit(1)
