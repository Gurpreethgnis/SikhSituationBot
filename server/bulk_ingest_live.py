import os
import json
import time
import logging
from typing import List

import google.generativeai as genai
from sqlalchemy import text
from dotenv import load_dotenv

import banidb

# Make sure we can import local modules
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Shabad
from vector_utils import get_embedding, get_best_embedding_model

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load local .env just in case it's run locally (Railway ignores this and uses its own)
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
# BaniDB v2 GET /shabads/{id} returns error (no shabadInfo) for id > 5540 for SGGS.
# Do not raise the loop limit without re-checking https://api.banidb.com/v2/shabads/{id}
SGGS_MAX_SHABADS = 5540

def get_best_generation_model():
    """Detect the best available generation model from the API."""
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for best in ['models/gemini-2.5-flash-lite', 'models/gemini-2.5-flash', 'models/gemini-2.5-pro']:
            if best in available_models:
                return best
        return available_models[0] if available_models else 'models/gemini-2.5-flash-lite'
    except Exception:
        return 'models/gemini-2.5-flash-lite'

def fetch_shabad_text(shabad_id: int):
    """Fetch Gurmukhi, Romanization, and English translation for a specific Shabad."""
    try:
        raw_shabad = banidb.shabad(shabad_id)
    except KeyError as e:
        # banidb.shabad() indexes json['shabadInfo']; API error payloads omit it.
        if e.args and e.args[0] == "shabadInfo":
            logger.warning(
                "Skipping Shabad %s: not in BaniDB (invalid id or past max SGGS shabad id %s).",
                shabad_id,
                SGGS_MAX_SHABADS,
            )
        else:
            logger.error("Failed to fetch Shabad %s from BaniDB API: %s", shabad_id, e)
        return None
    except Exception as e:
        logger.error(f"Failed to fetch Shabad {shabad_id} from BaniDB API: {e}")
        return None

    if "Guru Granth Sahib" not in raw_shabad.get("source_eng", ""):
        return None # Only process SGGS shabads

    gurmukhi_lines = []
    english_lines = []
    roman_lines = []

    for verse in raw_shabad.get("verses", []):
        gurmukhi_lines.append(verse.get("verse", ""))
        
        steek = verse.get("steek", {}).get("en", {})
        eng_text = steek.get("bdb") or steek.get("ms") or steek.get("ssk") or ""
        english_lines.append(eng_text)
        
        translit = verse.get("transliteration", {}).get("english", "")
        roman_lines.append(translit)

    full_gurmukhi = " ".join([line for line in gurmukhi_lines if line]).strip()
    full_english = " ".join([line for line in english_lines if line]).strip()
    full_roman = " ".join([line for line in roman_lines if line]).strip()
    
    if not full_gurmukhi or not full_english:
        return None

    return {
        "shabad_id": f"sggs_{shabad_id}",
        "raw_id": shabad_id,
        "gurmukhi": full_gurmukhi,
        "romanization": full_roman,
        "english_translation": full_english,
        "source": f"SGGS Ang {raw_shabad.get('ang')}",
        "writer": raw_shabad.get('writer', 'Unknown')
    }

def generate_context_tags(english_text: str, model) -> List[str]:
    """Use Gemini to generate 5 emotional context tags."""
    prompt = (
        f"Read the following English translation of a 15th-century Sikh verse.\n"
        f"Provide exactly 5 modern emotional context tags (like 'anxiety', 'grief', 'joy', 'family', 'courage') "
        f"that summarize the themes or pain points this verse addresses.\n"
        f"Return ONLY a valid JSON array of 5 lowercase strings.\n\n"
        f"Verse Translation:\n{english_text}"
    )
    for _ in range(3):
        try:
            response = model.generate_content(prompt)
            clean_text = response.text.strip().replace("```json", "").replace("```", "").strip()
            tags = json.loads(clean_text)
            if isinstance(tags, list) and len(tags) > 0:
                return [str(t).lower() for t in tags[:5]]
        except Exception:
            time.sleep(2)
    return ["spiritual", "meditation", "wisdom", "divine", "peace"]

def setup_database():
    """Ensure the Shabad table has the unconstrained Vector column."""
    with app.app_context():
        try:
            db.session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            # Alter table to unrestrained vector if it exists with constrained dims
            db.session.execute(text("ALTER TABLE shabads ALTER COLUMN embedding TYPE vector"))
            db.session.commit()
            db.create_all()
        except Exception as e:
            logger.warning(f"Note: pgvector setup note: {e}")
            db.session.rollback()

def main():
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY environment variable is required.")
        sys.exit(1)
        
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model_name = get_best_generation_model()
    model = genai.GenerativeModel(ai_model_name)
    logger.info(f"Using Gemini Generation Model: {ai_model_name}")
    
    embed_model_name = get_best_embedding_model()
    logger.info(f"Using Gemini Embedding Model: {embed_model_name}")

    setup_database()

    with app.app_context():
        count = 0
        for raw_id in range(1, SGGS_MAX_SHABADS + 1):
            
            # Check if this Shabad is already safely inside Postgres!
            existing = Shabad.query.filter_by(shabad_id=f"sggs_{raw_id}").first()
            if existing:
                if raw_id % 100 == 0:
                    logger.info(f"Skipping {raw_id} (Already securely inside Postgres)")
                continue
                
            logger.info(f"Processing Shabad {raw_id}...")
            
            # 1. Fetch from BaniDB
            shabad_data = fetch_shabad_text(raw_id)
            if not shabad_data:
                logger.warning(f"Skipping Shabad {raw_id} (empty or not SGGS)")
                continue
                
            # 2. Add AI Context Tags
            tags = generate_context_tags(shabad_data["english_translation"], model)
            
            # 3. Create the compound text for the Vector Embedding
            text_to_embed = (
                f"Translation: {shabad_data['english_translation']}\n"
                f"Themes and Context: {', '.join(tags)}"
            )
            
            # 4. Generate 3072D Vector Profile
            try:
                embedding = get_embedding(text_to_embed)
                if not embedding:
                    logger.error(f"Skipping Shabad {raw_id} (Embedding generation returned None)")
                    continue
            except Exception as e:
                logger.error(f"Skipping Shabad {raw_id} (Embedding API Error): {e}")
                time.sleep(10)
                continue

            # 5. Insert to Railway Postgres
            try:
                new_shabad = Shabad(
                    shabad_id=shabad_data["shabad_id"],
                    gurmukhi=shabad_data["gurmukhi"],
                    romanization=shabad_data["romanization"],
                    english_translation=shabad_data["english_translation"],
                    context_tags=json.dumps(tags),
                    source=shabad_data["source"],
                    recommended_persona="any",
                    embedding=embedding
                )
                db.session.add(new_shabad)
                db.session.commit()
                count += 1
                logger.info(f"✅ Successfully inserted Shabad {raw_id} into PostgreSQL!")
            except Exception as e:
                logger.error(f"Database insertion failed for Shabad {raw_id}: {e}")
                db.session.rollback()

            # Sleep to strictly respect Gemini free tier limits
            time.sleep(3)

        logger.info(f"✅ Bulk Ingestion Script fully completed! Processed {count} new items today.")

if __name__ == "__main__":
    main()
