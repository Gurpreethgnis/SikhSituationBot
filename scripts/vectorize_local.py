import os
import json
from sentence_transformers import SentenceTransformer

def vectorize_local(input_path="data/shabads.json", output_path="data/shabads_local_embeddings.json"):
    """
    Reads shabads, generates embeddings using a LOCAL model (all-MiniLM-L6-v2),
    and saves them. No GCP project required for this.
    """
    print("Loading local embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        shabads = json.load(f)

    print(f"Generating local embeddings for {len(shabads)} shabads...")

    # Extract text for embedding
    texts = [s.get("english_translation", "") for s in shabads]
    
    # Generate embeddings
    embeddings = model.encode(texts)

    for i, shabad in enumerate(shabads):
        shabad["embedding"] = embeddings[i].tolist()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(shabads, f, indent=4, ensure_ascii=False)

    print(f"Successfully vectorized data locally and saved to {output_path}")

if __name__ == "__main__":
    vectorize_local()
