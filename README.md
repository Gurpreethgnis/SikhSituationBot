# SikhSituationBot

SikhSituationBot is an AI-powered spiritual companion designed to provide guidance from Gurbani (Sikh scripture) for modern life's challenges. It bridges the gap between ancient wisdom and contemporary stressors by offering tailored, age-appropriate explanations.

---

## 🛠️ System Overview

- **Inputs:** Natural language situations (e.g., "I'm feeling burnt out"), Persona selection (Child, Teen, Adult).
- **Outputs:** Authentic Gurbani verses (Gurmukhi), Translations, and Persona-tailored advice.
- **Core Workflow:** User Query → Contextual Analysis (LLM) → Semantic Retrieval (Vector DB/BaniDB) → Response Synthesis (LLM) → Responsive UI.
- **Constraints:** Verbatim Gurbani text, high cultural sensitivity, low-latency interactions.

---

## 🧩 Component Breakdown

| Component | Technology | Description |
| :--- | :--- | :--- |
| **UI** | Next.js, CSS, Tailwind | Premium, responsive web interface with a focus on ease of use. |
| **Backend** | FastAPI (Python) | High-performance API orchestration for AI tasks. |
| **Data Layer** | BaniDB + SQLite | Source of truth for scriptures and metadata. |
| **Retrieval** | FAISS / ChromaDB | Vector database for semantic search on Shabad embeddings. |
| **AI LLM** | GPT-4o / Gemini | Handles multi-persona explanation generation. |

---

## 🎯 4-Week PoC Definition

**Goal:** A functional web demo showing an end-to-end "Situation-to-Guidance" flow.

- **Week 1:** Infrastructure, Data Ingestion, & UI Foundation.
- **Week 2:** RAG (Retrieval-Augmented Generation) Implementation.
- **Week 3:** Persona-based Prompt Tuning & API Integration.
- **Week 4:** UI Polishing, Deployment, & Demo Video.

---

## ⚠️ Risks & Non-Goals

### Risks
- **Accuracy:** Ensuring the LLM does not hallucinate Gurbani text.
- **Relevance:** Tuning the vector search to find *helpful* shabads, not just keyword-matching ones.

### Non-Goals (Out of Scope for PoC)
- User authentication and saved histories.
- Audio (TTS) or Kirtan player integration.
- Native mobile applications.

---

## 🗺️ Implementation Roadmap

See [Stage 1: PoC](./docs/architecture.md) for more details.

### Stage 2: Minimum Viable Product (MVP)
*   **Features:** Natural language search, tiered explanations (Child/Teen/Adult), full Gurbani context, FAQ section.

### Stage 3: Production Version
*   **Features:** Audio responses (TTS), user history, personalization, mobile apps, analytics.

---

## 🛠️ Contribution Workflow

1.  **Checkout:** Always branch off from `develop`.
2.  **Naming:** `feature/your-feature-name`.
3.  **PRs:** Submit to `develop` for review.

## 📄 License
[MIT](LICENSE)

