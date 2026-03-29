import os
from app import app, db
from models import Shabad
from vector_utils import get_embedding
from retrieval import search_similar_shabads

# Use the DATABASE_URL from environment
# os.environ['DATABASE_URL'] should be set in .env

with app.app_context():
    query = "I am feeling happy and blessed"
    print(f"\nSearching for: {query}")
    v = get_embedding(query)
    
    # Get top 5
    results = search_similar_shabads(query_embedding=v, limit=5)
    
    print(f"\nFound {len(results)} results:")
    for i, s in enumerate(results):
        print(f"{i+1}. [{s.shabad_id}] {s.english_translation[:100]}...")
