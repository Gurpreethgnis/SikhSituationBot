# Architecture & Data Flow

## 🏛️ System Overview
The SikhSituationBot uses a **RAG (Retrieval-Augmented Generation)** architecture to ensure that the AI's responses are grounded in actual scripture rather than hallucinated text.

### Tech Stack Choice: Python/Flask
We have selected **Python/Flask** for the backend because Python is the native language of AI and LLM development. It provides the best libraries (`langchain`, `sentence-transformers`, `openai`) for semantic search and prompt orchestration, which are critical for this project.

## 🔄 Core Data Flow

1. **User Request**: User selects a persona (e.g., "Child") and types: "I'm feeling afraid of the dark."
2. **Preprocessing**: The Flask backend receives the query and converts it into a numerical vector (embedding).
3. **Retrieval**: The system searches our `data/shabads.json` file for verses that are semantically close to "fear" and "protection" (e.g., *Tati Vao Na Lagi*).
4. **Augmentation**: The backend constructs a prompt:
   > "Using these Gurbani verses: [Verse 1, Verse 2], explain to a 10-year-old child how Guru's wisdom addresses their fear of the dark."
5. **Generation**: An LLM (Gemini or OpenAI) generates a compassionate, age-appropriate response.
6. **Delivery**: The React frontend displays the Shabad in high-quality typography alongside the AI's explanation.

## � Component Breakdown
- **Frontend (Client)**: Manages state, handles "Persona" selection, and renders Gurbani with proper spacing and fonts.
- **Backend (Server)**: Acts as the "Brain". It handles the logic for searching the local JSON data and communicating with the LLM API.
- **Local Database (Data)**: A structured JSON file containing:
    - `id`: Unique identifier.
    - `gurmukhi`: The original verse.
    - `translation`: Primary English meaning.
    - `keywords`: Tags like 'courage', 'peace', 'anxiety' for simple matching.
