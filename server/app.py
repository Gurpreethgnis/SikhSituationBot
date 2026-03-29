import os
import google.generativeai as genai
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from models import db, Shabad

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

app = Flask(__name__)
CORS(app)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Configure Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

def get_embedding(text):
    """Generate a vector embedding for the given text using Gemini."""
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_query"
        )
        return result['embedding']
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None

def generate_ai_response(query, context, persona):
    """Synthesize an empathetic response using Gemini based on Gurbani context."""
    prompt = f"""
    You are the SikhSituationBot, a wise and empathetic companion that provides guidance based on the Sri Guru Granth Sahib (SGGS).
    
    User Query: "{query}"
    User Persona: {persona} (Tailor your tone for this audience: Child, Teen, or Adult)
    
    Relevant Wisdom from SGGS:
    - Gurmukhi: "{context['gurmukhi']}"
    - English Translation: "{context['translation']}"
    
    Task:
    1. Acknowledge the user's situation with deep empathy.
    2. Explain the meaning of the provided Gurmukhi verse in the context of their query.
    3. Provide actionable, spiritual advice aligned with Gurmat (Guru's teachings).
    4. Keep the tone respectful, calming, and appropriate for a {persona}.
    
    Response format: Markdown (use bullet points or short paragraphs for readability).
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"I am reflecting on the Guru's wisdom for you. (Error: {str(e)})"

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "success", "message": "SikhSituationBot RAG backend is active!"}), 200

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    query = data.get('query', '')
    persona = data.get('persona', 'adult').capitalize()
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
        
    # 1. Generate Query Embedding
    query_vector = get_embedding(query)
    if not query_vector:
        return jsonify({"error": "Failed to process query embedding"}), 500

    # 2. Perform Semantic Search via pgvector
    try:
        # Get the single most relevant verse
        shabad = Shabad.query.order_by(Shabad.embedding.cosine_distance(query_vector)).first()
        
        if not shabad:
            return jsonify({"error": "No matching wisdom found in database"}), 404
            
        context = {
            "gurmukhi": shabad.gurmukhi,
            "translation": shabad.english_translation,
            "transliteration": shabad.romanization
        }
        
        # 3. Generate AI Synthesis
        ai_response = generate_ai_response(query, context, persona)
        
        return jsonify({
            "response": ai_response,
            "shabad": {
                "text": context["gurmukhi"],
                "title": context["translation"],
                "transliteration": context["transliteration"]
            }
        }), 200

    except Exception as e:
        print(f"Database error: {e}")
        return jsonify({"error": "A database error occurred. Please ensure pgvector is enabled."}), 500

if __name__ == '__main__':
    with app.app_context():
        # Ensure tables exist (database must already have pgvector extension)
        try:
            db.create_all()
        except Exception as e:
            print(f"Warning: Could not create tables: {e}")
            
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
