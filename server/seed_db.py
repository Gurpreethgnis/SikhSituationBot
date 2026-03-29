import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from app import app, db
from models import Shabad

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# Configure Gemini API
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

def get_embedding(text):
    """Generate a vector embedding for the given text using Gemini."""
    try:
        # Using text-embedding-004 as it is the recommended model for general text embeddings
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None

def seed_database(json_file_path):
    """Read the SGGS JSON file, generate embeddings, and insert into DB."""
    if not os.path.exists(json_file_path):
        print(f"Data file not found: {json_file_path}")
        return

    with open(json_file_path, 'r', encoding='utf-8') as f:
        shabads_data = json.load(f)
    
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        print(f"Found {len(shabads_data)} shabads. Beginning ingestion...")
        
        for index, item in enumerate(shabads_data):
            # We want to embed the English translation or the theme
            content_to_embed = item.get('translation', '') + " " + item.get('theme', '')
            
            print(f"Processing Shabad {index+1}/{len(shabads_data)}...")
            embedding = get_embedding(content_to_embed)
            
            if embedding:
                new_shabad = Shabad(
                    shabad_id=item.get('shabad_id', f"shabad_{index}"),
                    gurmukhi=item.get('gurmukhi', ''),
                    romanization=item.get('transliteration', ''),
                    english_translation=item.get('translation', ''),
                    source=item.get('source', 'SGGS'),
                    embedding=embedding
                )
                db.session.add(new_shabad)
            
            # Commit in batches
            if (index + 1) % 10 == 0:
                db.session.commit()
                print(f"Committed batch up to {index+1}")
                
        # Final commit
        db.session.commit()
        print("Database seeding complete!")

if __name__ == "__main__":
    # Example usage: python seed_db.py data/shabad.json
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'shabad.json')
    seed_database(data_path)
