import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from server.app import app, db
from server.models import Shabad
from server.vector_utils import get_embedding

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# Configure Gemini API
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# get_embedding imported from vector_utils, ensuring use of shared embedding behavior

def seed_database(json_file_path):
    """Read the SGGS JSON file, generate embeddings, and insert into DB."""
    if not os.path.exists(json_file_path):
        print(f"Data file not found: {json_file_path}")
        return

    with open(json_file_path, 'r', encoding='utf-8') as f:
        shabads_data = json.load(f)
    
    with app.app_context():
        # Ensure pgvector extension & index exist for fast similarity queries
        db.session.execute("CREATE EXTENSION IF NOT EXISTS vector")
        db.session.execute("CREATE INDEX IF NOT EXISTS shabads_embedding_idx ON shabads USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)")
        db.session.commit()

        # Optional: db.drop_all() if you want a clean slate every run, though usually not desired in prod
        print(f"Found {len(shabads_data)} shabads. Beginning ingestion...")
        
        for index, item in enumerate(shabads_data):
            # We want to embed the English translation or the transliteration
            # as that's what the AI will semantically match against the user's english query
            content_to_embed = item.get('translation', '') + " " + item.get('theme', '')
            
            print(f"Processing Shabad {index+1}/{len(shabads_data)}...")
            embedding = get_embedding(content_to_embed)
            
            if embedding:
                new_shabad = Shabad(
                    shabad_id=item.get('shabad_id') or f"shabad-{index+1}",
                    gurmukhi=item.get('gurmukhi', ''),
                    romanization=item.get('romanization', item.get('transliteration', '')),
                    english_translation=item.get('english_translation', item.get('translation', '')),
                    source=item.get('source', ''),
                    context_tags=item.get('context_tags', []),
                    embedding=embedding
                )
                db.session.add(new_shabad)
            
            # Commit in batches to prevent memory overflow
            if (index + 1) % 50 == 0:
                db.session.commit()
                print(f"Committed batch up to {index+1}")
                
        # Final commit for any remaining items
        db.session.commit()
        print("Database seeding complete!")

if __name__ == "__main__":
    # Example usage: python seed_db.py data/shabad.json
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'shabad.json')
    seed_database(data_path)
