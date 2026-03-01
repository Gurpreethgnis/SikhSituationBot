import os
import json
from flask import Flask
from models import db, Shabad
from dotenv import load_dotenv

load_dotenv()

def seed_database(input_path="data/shabads_with_embeddings.json"):
    """
    Reads the vectorized JSON data and uploads it to Google Cloud SQL.
    """
    app = Flask(__name__)
    
    # Database URI should look like: postgresql://user:password@host:port/dbname
    # On GCP, use the public IP or Cloud SQL Proxy address
    db_uri = os.getenv("DATABASE_URL")
    if not db_uri:
        print("Error: DATABASE_URL not found in environment variables.")
        return

    app.config['SQLALCHEMY_DATABASE_HOST'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found. Run scripts/vectorize_data.py first.")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        shabads_data = json.load(f)

    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        print("Database tables created/verified.")

        count = 0
        for item in shabads_data:
            # Check if shabad already exists to avoid duplicates
            existing = Shabad.query.filter_by(shabad_id=item['shabad_id']).first()
            if existing:
                continue

            new_shabad = Shabad(
                shabad_id=item['shabad_id'],
                gurmukhi=item['gurmukhi'],
                romanization=item.get('romanization'),
                english_translation=item['english_translation'],
                source=item.get('source'),
                recommended_persona=item.get('recommended_persona', 'any'),
                context_tags=item.get('context_tags', []),
                embedding=item.get('embedding')
            )
            db.session.add(new_shabad)
            count += 1
        
        db.session.commit()
        print(f"Successfully seeded {count} new shabads to the database.")

if __name__ == "__main__":
    seed_database()
