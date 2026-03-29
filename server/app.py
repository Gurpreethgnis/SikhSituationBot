import os
import json
import google.generativeai as genai
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import logging
import sys
from typing import List, Dict, Any, Tuple

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

# LLM model for query assessment (lightweight, fast)
query_assessment_model = None

def get_assessment_model():
    """Get or create the query assessment model."""
    global query_assessment_model
    if query_assessment_model is None and GEMINI_API_KEY:
        query_assessment_model = genai.GenerativeModel('models/gemini-2.0-flash-lite')
    return query_assessment_model

def assess_query_clarity(query: str, persona: str = "adult") -> Tuple[bool, str]:
    """
    Use LLM to assess if a query has enough context to provide meaningful Gurbani guidance.
    
    Returns:
        Tuple of (needs_clarification: bool, reason: str)
    """
    model = get_assessment_model()
    if not model:
        return (False, "")
    
    assessment_prompt = f"""You are assessing whether a user's query has enough context to provide meaningful spiritual guidance from Sikh scripture (Guru Granth Sahib).

USER'S QUERY: "{query}"
USER TYPE: {persona}

Analyze if this query:
1. Expresses a clear situation, problem, or question that can be addressed with scriptural wisdom
2. Has enough context to find relevant Gurbani verses
3. Or is too vague/ambiguous and would benefit from clarification

Examples that NEED clarification:
- "I am scared" (scared of what? situation unclear)
- "Help me" (with what?)
- "I'm feeling down" (why? what happened?)
- "What should I do?" (about what?)
- "I can't anymore" (can't do what?)
- "Life is hard" (in what way specifically?)

Examples that are CLEAR enough:
- "I am scared about my upcoming job interview" (clear situation)
- "How do I deal with anger towards my parents?" (clear emotion + context)
- "I lost my father recently and feel lost" (clear life event)
- "What does Gurbani say about forgiveness?" (clear topic)
- "I'm struggling with my faith after a tragedy" (clear spiritual challenge)

Respond with ONLY valid JSON (no markdown, no code blocks):
{{"needs_clarification": true/false, "reason": "brief explanation"}}"""

    try:
        response = model.generate_content(
            assessment_prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.1,
                max_output_tokens=150
            )
        )
        
        result_text = response.text.strip()
        # Clean up any markdown formatting that might slip through
        if result_text.startswith('```'):
            result_text = result_text.split('\n', 1)[1] if '\n' in result_text else result_text
            result_text = result_text.rsplit('```', 1)[0] if '```' in result_text else result_text
        result_text = result_text.strip()
        
        result = json.loads(result_text)
        return (result.get("needs_clarification", False), result.get("reason", ""))
        
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse query assessment JSON: {e}, response: {response.text if response else 'None'}")
        return (False, "")
    except Exception as e:
        logger.warning(f"Query assessment failed, proceeding with full response: {e}")
        return (False, "")

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
# Narrower testing check to avoid accidental fallbacks during seeding
is_testing = (
    os.environ.get('TESTING') == 'true' or 
    os.environ.get('FLASK_ENV') == 'testing'
)

db_url = os.environ.get('DATABASE_URL')

# SQLAlchemy 1.4/2.0+ requires postgresql+psycopg2:// instead of postgresql:// 
# for some environments, though many drivers handle both.
if db_url and db_url.startswith("postgresql://") and not db_url.startswith("postgresql+psycopg2://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

if is_testing:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL_TEST', 'sqlite:///:memory:')
else:
    # Use provided URL or default to local postgres
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'postgresql+psycopg2://localhost/sikhsituationbot'

# Log the connection target (safely)
if "sqlite" in app.config['SQLALCHEMY_DATABASE_URI']:
    logger.info("Database configured for LOCAL SQLITE")
else:
    target = app.config['SQLALCHEMY_DATABASE_URI'].split('@')[-1] if '@' in app.config['SQLALCHEMY_DATABASE_URI'] else 'local/postgres'
    logger.info(f"Database configured for POSTGRES: {target}")

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

    # Use LLM to assess if query needs clarification
    needs_clarification, clarification_reason = assess_query_clarity(query_text, persona)
    
    if needs_clarification:
        logger.info(f"Query needs clarification: '{query_text}' - Reason: {clarification_reason}")
        ai_response = synthesize_gemini_response(query_text, None, persona)
        
        return jsonify({
            "response": ai_response,
            "shabad": None,
            "persona": persona,
            "is_clarification": True
        }), 200

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
            "persona": persona,
            "is_clarification": False
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
