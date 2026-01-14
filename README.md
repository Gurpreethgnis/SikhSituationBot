# SikhSituationBot 🪯

SikhSituationBot is an AI-powered conversational agent designed to provide guidance from Gurbani for modern life's challenges. It helps users find relevant Shabads (verses) based on their emotional state or life situation.

## 🌟 Project Vision
To bridge the gap between historical Sikh scripture and contemporary human experience by making Gurbani's wisdom accessible, age-appropriate, and actionable for the next generation.

## 🎯 PoC Success Criteria (The "Week 4" Bar)
To consider the PoC a success, the bot must achieve the following by the final demo:
1.  **Relevance**: In a test of 20 common queries (e.g., "I feel stressed," "Help with grief"), the bot must retrieve a contextually relevant Shabad 100% of the time.
2.  **Persona Accuracy**: The LLM's explanation must pass a "vibe check" for the selected persona (e.g., Child mode must not use words like "metaphysical" or "existential").
3.  **Performance**: The time from "Query Sent" to "Response Displayed" must be under **4 seconds**.
4.  **Visual Fidelity**: Gurmukhi text must be rendered using a proper Gurbani font (Akhar/Anmol) with correct vowel placements.
5.  **Robustness**: The app must handle empty searches or "gibberish" queries without crashing or throwing unhandled errors.


## 🚀 How to Run

### Backend (Python/Flask)
1. Navigate to `/server`.
2. Install dependencies: `pip install -r requirements.txt`.
3. Start server: `python app.py`.

### Frontend (React/Vite)
1. Navigate to `/client`.
2. Install dependencies: `npm install`.
3. Start dev server: `npm run dev`.

---

## 📂 Repository Structure
```text
SikhSituationBot/
├── client/          # React (Vite) frontend application
├── server/          # Python/Flask backend and AI logic
├── data/            # Local JSON files containing Shabad data
├── docs/            # Project documentation and weekly plans
└── scripts/         # Data ingestion and cleaning utilities
```
