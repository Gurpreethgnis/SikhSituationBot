import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

from server.models import db, Shabad
from server.vector_utils import get_embedding
from server.retrieval import find_similar_shabads

# Load environment variables from the root .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

app = Flask(__name__)
CORS(app)  # Enable CORS for the frontend to communicate with the backend

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://localhost/sikhsituationbot')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint to verify server is running."""
    return jsonify({
        "status": "success",
        "message": "SikhSituationBot backend is running!"
    }), 200

@app.route('/ask', methods=['POST'])
def ask():
    """Endpoint for chat queries. To be implemented by AI team."""
    data = request.json
    query = data.get('query', '').lower()
    persona = data.get('persona', 'adult')
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
        
    # Mock knowledge base / wired responses
    responses = {
        "peace": {
            "child": "Finding peace is like feeling a warm hug from Waheguru. It means being kind and quiet in your heart.",
            "teen": "True peace isn't the absence of noise, but a calm mind amidst the chaos of life and social media. Let Gurbani be your anchor.",
            "adult": "Peace (Shanti) in Gurbani is attained by surrendering the ego and aligning one's consciousness with the Eternal Truth.",
            "shabad": {
                "text": "ਤਪਤਿ ਮਾਹਿ ਠਾਢਿ ਵਰਤਾਈ ॥",
                "title": "In the midst of the heat, a cooling sense has spread.",
                "transliteration": "Tapat Mahe Thadh Varta-ee"
            }
        },
        "stress": {
            "child": "When things feel hard, remember you're never alone. Like a superhero's shield, Waheguru protects you.",
            "teen": "Exam stress or social pressure? Gurbani reminds us that 'Jo Tudh Bhaave Saa-ee Bhalee Kaar'—Whatever pleases You is best. Trust the process.",
            "adult": "Anxiety arises from attachment. Release the burden of control and find solace in the Hukam (Divine Will).",
            "shabad": {
                "text": "ਸਗਲ ਮਨੋਰਥ ਪੂਰਨ ਹੋਏ ਮਨਿ ਤਨਿ ਭਈ ਸੀਤਲਤਾ ॥",
                "title": "All my desires have been fulfilled; my mind and body are cooled and soothed.",
                "transliteration": "Sagal Manorath Pooran Ho-e Man Tan Bha-ee Seetalta"
            }
        }
    }

    # Attempt semantic retrieval via vector search
    query_embedding = get_embedding(query)
    if not query_embedding:
        return jsonify({"error": "Embedding generation failed"}), 503

    similar_shabads = find_similar_shabads(query_embedding=query_embedding, limit=5, persona=persona)

    if similar_shabads:
        response_items = []
        for s in similar_shabads:
            response_items.append({
                "shabad_id": s.shabad_id,
                "gurmukhi": s.gurmukhi,
                "romanization": s.romanization,
                "english_translation": s.english_translation,
                "source": s.source,
                "context_tags": s.context_tags,
            })

        return jsonify({
            "response": f"Found {len(response_items)} relevant shabads for your query.",
            "query": query,
            "shabads": response_items
        }), 200

    # Fallback predefined responses for initial prototype behavior
    result = responses.get("peace") if "peace" in query else responses.get("stress") if any(x in query for x in ["stress", "overwhelmed", "anxious", "scared"]) else None

    if result:
        return jsonify({
            "response": result.get(persona, result["adult"]),
            "shabad": result["shabad"]
        }), 200

    # Generic Placeholder
    return jsonify({
        "response": f"Received your query about '{query}'. I am still learning, but the Guru's wisdom is infinite. AI synthesis coming soon.",
        "shabad": {
            "text": "ੴ ਸਤਿ ਨਾਮੁ ਕਰਤਾ ਪੁਰਖੁ ॥",
            "title": "One Universal Creator God. The Name Is Truth. Creative Being Personified.",
            "transliteration": "Ik Onkar Sat Nam Karta Purakh"
        }
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
