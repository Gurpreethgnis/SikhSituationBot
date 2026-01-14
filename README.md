# SikhSituationBot 🪯

SikhSituationBot is an AI-powered spiritual companion designed to provide guidance from Gurbani (Sikh scripture) for modern life challenges. It bridges the gap between historical wisdom and contemporary situations using advanced Retrieval-Augmented Generation (RAG).

## 🌟 System Overview

### Core Workflow
1. **Input**: User describes a situation or emotion (e.g., "Feeling anxious about exams") and selects a perspective (Child, Teen, or Adult).
2. **Contextual Retrieval**: The system queries a specialized Vector Database containing Gurbani, translations, and historical context.
3. **AI Generation**: A Large Language Model (LLM) synthesizes the retrieved verses into a compassionate, age-appropriate explanation.
4. **Output**: A structured response featuring the Shabad (Gurmukhi/Romanized), its literal meaning, and a "Situation Guide" explaining how to apply it.

### Constraints
- **Theological Accuracy**: Responses must be grounded in authentic sources (BaniDB/Shabad OS).
- **Tone & Sensitivity**: Guidance must remain respectful and avoid "hallucinating" religious mandates.
- **Accessibility**: Support for various levels of Gurmukhi proficiency.

---

## 🏗️ 4-Week PoC Definition (The "Hero" Demo)

The goal for the 4-week Proof of Concept is to deliver a functional web-based chatbot that can answer **Stress & Anxiety** related queries with 80% accuracy in verse retrieval.

- **Demo Goal**: A user enters "I am feeling lonely," and the bot returns a relevant Shabad (e.g., *Tu Mera Pita Tu Hai Mera Mata*) with an explanation suitable for a 10-year-old child.

### Roadmap
- **Week 1**: **Foundation** - Tech stack setup, Data sourcing (top 100 most common situational Shabads), and UI scaffolding.
- **Week 2**: **The Brain** - Vector database ingestion and basic semantic search implementation.
- **Week 3**: **The Voice** - LLM integration for tiered explanations (Adult/Child modes).
- **Week 4**: **The Look** - UI/UX polish, micro-animations, and deployment.

---

## ⚠️ Risks & Non-Goals

### Risks
- **LLM Hallucinations**: The AI might misinterpret a verse or invent spiritual advice.
- **Data Quality**: Ensuring translations capture the nuance of Gurbani.
- **Varying Student Skills**: Some students may struggle with RAG concepts vs. frontend tasks.

### Non-Goals
- **Full Gurbani Search**: We will not index all 1430 pages of SGGS for the PoC; we'll focus on a situational subset.
- **Account System**: No user logins or history for the PoC.
- **Audio/Kirtan Integration**: No audio playback in Week 4.

---

## 📂 Project Structure
- `/src`: Application source code.
- `/docs`: Technical documentation and architecture.
- `/scripts`: Data ingestion and processing utilities.

---
*Developed for the Sikh community with ❤️ and AI.*
