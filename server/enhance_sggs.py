import os
import json
import time
import re
import argparse
import sys
import logging
from typing import List

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

try:
    import banidb
    import google.generativeai as genai
except ImportError as e:
    logger.error(f"Missing dependency: {e}. Please run: pip3 install banidb google-generativeai")
    sys.exit(1)

# Configuration
SGGS_MAX_SHABADS = 5867
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'sggs_enhanced.json')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Model auto-selection (similar to prompts.py)
GENERATION_MODEL = None

def get_best_generation_model():
    """Detect the best available generation model from the API."""
    global GENERATION_MODEL
    if GENERATION_MODEL:
        return GENERATION_MODEL
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        best_models = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
        for best in best_models:
            if best in available_models:
                GENERATION_MODEL = best
                return GENERATION_MODEL
        GENERATION_MODEL = available_models[0] if available_models else 'gemini-1.5-flash'
        return GENERATION_MODEL
    except Exception:
        GENERATION_MODEL = 'gemini-1.5-flash'
        return GENERATION_MODEL

def load_checkpoint() -> List[dict]:
    """Load existing processed shabads from disk to allow resuming."""
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip():
                    return []
                return json.loads(content)
        except json.JSONDecodeError:
            logger.warning(f"Warning: {OUTPUT_FILE} is corrupted. Starting fresh.")
    return []

def save_checkpoint(data: List[dict]):
    """Save the progress to disk."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def fetch_shabad_text(shabad_id: int):
    """Fetch Gurmukhi, Romanization, and English translation for a specific Shabad."""
    try:
        raw_shabad = banidb.shabad(shabad_id)
    except Exception as e:
        logger.error(f"Failed to fetch Shabad {shabad_id} from BaniDB API: {e}")
        return None

    gurmukhi_lines = []
    english_lines = []
    roman_lines = []
    
    # We only want Sri Guru Granth Sahib Ji (source_eng usually matches)
    if "Guru Granth Sahib" not in raw_shabad.get("source_eng", ""):
        return None # Skip Dasam Granth, Bhai Gurdas, etc if they overlap.

    for verse in raw_shabad.get("verses", []):
        gurmukhi_lines.append(verse.get("verse", ""))
        
        # Get english translation (fallback from bdb to ms to ssk)
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
    """Use Gemini to generate 5 emotional context tags based on the English translation."""
    prompt = (
        f"Read the following English translation of a 15th-century Sikh verse.\n"
        f"Provide exactly 5 modern emotional context tags (like 'anxiety', 'grief', 'joy', 'family', 'courage') "
        f"that summarize the themes, pain points, or emotional states this verse addresses or provides comfort for.\n"
        f"Return ONLY a valid JSON array of 5 lowercase strings, nothing else.\n\n"
        f"Verse Translation:\n{english_text}"
    )
    
    # Max retries
    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            # Clean possible markdown formatting
            clean_text = response.text.strip().replace("```json", "").replace("```", "").strip()
            tags = json.loads(clean_text)
            if isinstance(tags, list) and len(tags) > 0:
                # Limit to 5
                return [str(t).lower() for t in tags[:5]]
        except Exception as e:
            time.sleep(2) # Backoff
            
    # Fallback generic tags if AI fails
    return ["spiritual", "meditation", "wisdom", "divine", "peace"]

def main(limit: int = 5):
    """Main pipeline loop."""
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY environment variable is required.")
        sys.exit(1)
        
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model_name = get_best_generation_model()
    model = genai.GenerativeModel(ai_model_name)
    logger.info(f"Using Gemini Model: {ai_model_name}")

    existing_data = load_checkpoint()
    processed_ids = {item.get("raw_id") for item in existing_data if "raw_id" in item}
    
    logger.info(f"Loaded {len(existing_data)} previously processed Shabads.")
    
    count = 0
    # Process sequentially up to limit for testing (or SGGS_MAX_SHABADS for full)
    target_limit = min(SGGS_MAX_SHABADS, limit) if limit > 0 else SGGS_MAX_SHABADS
    
    for shabad_id in range(1, SGGS_MAX_SHABADS + 1):
        if count >= target_limit and limit > 0:
            break
            
        if shabad_id in processed_ids:
            continue
            
        logger.info(f"Processing Shabad {shabad_id}...")
        
        # 1. Fetch from BaniDB
        shabad_data = fetch_shabad_text(shabad_id)
        if not shabad_data:
            logger.warning(f"Skipping Shabad {shabad_id} (empty or not SGGS)")
            processed_ids.add(shabad_id)
            continue
            
        # 2. Enrich with Gemini
        tags = generate_context_tags(shabad_data["english_translation"], model)
        shabad_data["context_tags"] = tags
        shabad_data["recommended_persona"] = "any" # Default
        
        # 3. Save directly to existing_data
        existing_data.append(shabad_data)
        processed_ids.add(shabad_id)
        count += 1
        
        # Save checkpoint every 10 shabads
        if count % 10 == 0:
            save_checkpoint(existing_data)
            logger.info(f"Checkpoint saved. Processed {count} items.")
            
        # Optional sleep to avoid Google AI Studio strict rate limits on free tier
        time.sleep(2)

    # Final save
    if count > 0:
        save_checkpoint(existing_data)
        logger.info(f"Pipeline finished! Saved {len(existing_data)} enriched Shabads to {OUTPUT_FILE}")
    else:
        logger.info("No new Shabads were processed (all already complete or limit reached).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bulk SGGS Enrichment Pipeline")
    parser.add_argument("--limit", type=int, default=5, help="Number of shabads to process (0 for all)")
    args = parser.parse_args()
    main(limit=args.limit)
