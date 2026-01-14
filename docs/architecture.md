# System Architecture: SikhSituationBot

## 1. System Overview
SikhSituationBot is an intelligent retrieval system that maps modern life situations to relevant Gurbani (Sikh scripture) guidance.

### Core Workflow
1. **User Input:** Modern-day stressor or question (e.g., "I feel anxious about my exams").
2. **Contextual Analysis:** LLM interprets the emotional and situational context of the query.
3. **Retrieval (RAG):** Search in a vectorized Gurbani database (BaniDB) for Shabads addressing specific themes (anxiety, patience, focus).
4. **Tailored Generation:** LLM synthesizes the Shabad, translation, and a persona-based explanation (Child/Adult/Deep Learner).
5. **Output:** A formatted response with Gurmukhi, English, and situational advice.

### Constraints
- **Authenticity:** Gurbani text must be retrieved verbatim from trusted sources (BaniDB).
- **Sensitivity:** Explanations must align with Sikh ethics and Gurmat.
- **Latency:** Prompt responses (<3s) for a modern chat experience.

---

## 2. Component Breakdown

### UI (Frontend)
- **Framework:** Next.js + Tailwind CSS.
- **Features:** Responsive chat interface, Persona selector (Toggle), Quick-action "Situation" buttons.
- **Esthetics:** Modern, "Premium" look with glassmorphic elements and soothing color palettes.

### Backend (API Layer)
- **Framework:** Python (FastAPI).
- **Responsibilities:** API endpoints for chat, persona management, and session handling.

### Data Layer
- **Source:** BaniDB (Shabad, Pauri, Line data).
- **Format:** SQLite for metadata, JSON for cached responses.

### Retrieval Engine
- **Strategy:** Hybrid Search (Semantic Vector Search + Keyword matching).
- **Vector DB:** ChromaDB or FAISS (local/lightweight for PoC).
- **Embedding Model:** `sentence-transformers` or OpenAI `text-embedding-3-small`.

### Explanation Generator
- **LLM:** GPT-4o or Gemini 1.5 Pro.
- **Prompt Engineering:** Stage-managed system prompts specifically tuned for different age groups.

---

## 3. 4-Week PoC Definition

### Goal
Demonstrate a "Situation-to-Shabad" loop where a user picks a persona, enters a life problem, and receives a relevant, accurate Gurbani-based response.

- **Scope:** 5-10 common "Situations" pre-optimized, or open-ended if RAG is stable.
- **Deliverable:** Hosted web app (Vercel/Rail) with basic streaming responses.

---

## 4. Risks & Non-Goals

### Risks
- **Hallucinations:** LLM might "invent" verses if not strictly constrained to the retrieved context.
- **Data Quality:** BaniDB subsets might need cleaning for vectorization.
- **Complexity:** Over-engineering the UI before the retrieval logic is solid.

### Non-Goals
- **User Accounts/Auth:** Not needed for PoC.
- **Audio/Kirtan Integration:** Deferred to Stage 2/3.
- **Mobile Apps (Native):** Web-only for PoC.
- **Full Scripture Search:** Initial focus only on popular Shabads or specific themes.
