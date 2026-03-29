import os
import google.generativeai as genai
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import logging
import sys
from typing import List, Dict, Any

from models import db, Shabad
from vector_utils import get_embedding
from retrieval import search_similar_shabads, get_random_shabads, get_shabad_by_id
from prompts import build_gemini_response_prompt, format_shabad_context, synthesize_gemini_response, FALLBACK_RESPONSE

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini API
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

app = Flask(__name__)
# Enable CORS for the frontend to communicate with the backend
CORS(app, resources={r"/*": {
    "origins": "*",
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"]
}})

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

# Database Configuration
is_testing = (
    os.environ.get('TESTING') == 'true' or 
    os.environ.get('FLASK_ENV') == 'testing' or 
    'pytest' in sys.modules or 
    'unittest' in sys.modules
)

if is_testing:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL_TEST', 'sqlite:///:memory:')
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://localhost/sikhsituationbot')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

@app.route('/health', methods=['GET'])
@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint to verify server is running."""
    import datetime
    return jsonify({
        "status": "healthy",
        "message": "SikhSituationBot backend is running!",
        "timestamp": datetime.datetime.now().isoformat()
    }), 200

@app.route('/ask', methods=['POST'])
def ask():
    """Endpoint for chat queries with semantic search and AI synthesis."""
    try:
        data = request.get_json(silent=True)
        if data is None:
            return jsonify({"error": "Request must be JSON"}), 400
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400

    query_text = data.get('query', '').strip()
    persona_input = data.get('persona', 'adult').lower().strip()

    if not query_text:
        return jsonify({"error": "No query provided"}), 400
        
    # Validate persona
    valid_personas = ['child', 'teen', 'adult']
    persona = persona_input if persona_input in valid_personas else 'adult'

    logger.info(f"Processing query: '{query_text}' for persona: {persona}")

    # 1. Generate Query Embedding
    query_vector = get_embedding(query_text)
    if not query_vector:
        logger.error("Embedding generation failed")
        return jsonify({"error": "Failed to process query embedding"}), 500

    # 2. Perform Semantic Search via pgvector (or search_similar_shabads)
    try:
        similar_shabads = search_similar_shabads(query_embedding=query_vector, limit=1, persona=persona)
        
        if not similar_shabads:
            # Fallback to general search if persona-specific search returns nothing
            similar_shabads = search_similar_shabads(query_embedding=query_vector, limit=1)
            
        if not similar_shabads:
            return jsonify({"error": "No matching wisdom found in database"}), 404
            
        # For MVP compatibility, we use the first (most relevant) shabad
        top_shabad = similar_shabads[0]
        context_dict = top_shabad.to_dict()
        
        # 3. Generate AI Synthesis
        # Convert to list for the synthesis function which expects it
        shabad_list = [context_dict]
        ai_response = synthesize_gemini_response(query_text, shabad_list, persona)
        
        # Return response in format expected by the frontend
        return jsonify({
            "response": ai_response,
            "shabad": {
                "text": context_dict["gurmukhi"],
                "title": context_dict["english_translation"],
                "transliteration": context_dict["romanization"]
            },
            "persona": persona
        }), 200

    except Exception as e:
        logger.error(f"Error during retrieval or synthesis: {e}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/random-shabads', methods=['GET'])
def random_shabads():
    """Endpoint to get random shabads."""
    limit = request.args.get('limit', default=3, type=int)
    shabads = get_random_shabads(limit=limit)
    return jsonify({"shabads": [s.to_dict() for s in shabads]}), 200

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Warning: Could not create tables: {e}")
            
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

if __name__ == '__main__':
    with app.app_context():
        # Ensure tables exist (database must already have pgvector extension)
        try:
            db.create_all()
        except Exception as e:
            print(f"Warning: Could not create tables: {e}")
            
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
