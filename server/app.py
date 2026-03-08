import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from the root .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

app = Flask(__name__)
CORS(app)  # Enable CORS for the frontend to communicate with the backend

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
    query = data.get('query', '')
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
        
    # Placeholder response
    return jsonify({
        "response": f"Received query: '{query}'. AI synthesis coming soon.",
        "shabad": {
            "id": 1,
            "title": "Sample Shabad",
            "text": "This is placeholder text for the shabad."
        }
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
