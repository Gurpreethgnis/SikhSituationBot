import os
import json
from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOCATION = os.getenv("GCP_LOCATION", "us-central1")

def vectorize_shabads(input_path="data/shabads.json", output_path="data/shabads_with_embeddings.json"):
    """
    Reads shabads, generates embeddings using Vertex AI, and saves them.
    """
    if not PROJECT_ID:
        print("Error: GCP_PROJECT_ID not found in environment variables.")
        return

    # Initialize Vertex AI
    aiplatform.init(project=PROJECT_ID, location=LOCATION)
    model = TextEmbeddingModel.from_pretrained("text-embedding-004")

    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        shabads = json.load(f)

    print(f"Generating embeddings for {len(shabads)} shabads...")

    # Extract text for embedding (using English translation for semantic search)
    texts = [s.get("english_translation", "") for s in shabads]
    
    # Vertex AI handles batching, but for a large dataset you'd want to batch manually
    # For PoC, we send all at once or in small batches
    inputs = [TextEmbeddingInput(text, "RETRIEVAL_DOCUMENT") for text in texts]
    embeddings = model.get_embeddings(inputs)

    for i, shabad in enumerate(shabads):
        shabad["embedding"] = embeddings[i].values

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(shabads, f, indent=4, ensure_ascii=False)

    print(f"Successfully vectorized data and saved to {output_path}")

if __name__ == "__main__":
    vectorize_shabads()
