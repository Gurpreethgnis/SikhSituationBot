# 🚀 Stage 2: Minimum Viable Product (MVP) Plan

This document outlines the goals, outcomes, and task assignments for transitioning our SikhSituationBot from a hardcoded Proof of Concept (PoC) to a fully functional, AI-driven MVP.

## 🎯 Overall Outcome
The primary objective of the MVP is to replace the mock keyword-matching system with true **Semantic Search** and **AI Synthesis**. The bot will understand the nuance of a user's emotional query, retrieve relevant wisdom from the Siri Guru Granth Sahib (SGGS) using vector embeddings, and generate a customized, empathetic response using the Gemini API—all while respecting the selected user persona (Child, Teen, Adult).

## 🪜 Step Goals
1. **Database Foundation:** Establish a PostgreSQL database with the `pgvector` extension to store SGGS verses and their multi-dimensional embeddings.
2. **Data Pipeline:** Create a script to run our curated Gurbani data through an embedding model and populate the database.
3. **Intelligence (RAG):** Upgrade the `/ask` endpoint to convert user queries to vectors, query the database for the nearest semantic matches, and pass the results to a Large Language Model (LLM) for response generation.
4. **UX & Polish:** Refine the frontend to handle potential AI latency with elegant loading states (e.g., streaming text, typing indicators) and ensure error handling is robust.
5. **Secure Operations:** Provision the production database and securely manage all necessary secrets (DB connection strings, LLM API keys) across our deployment platforms.

---

## 📋 Task Assignments by Persona

### 🧠 AI/Data (@sbindra-ai)
**Focus:** Data pipeline and LLM orchestration.
- **Goal:** Drive the intelligence of the bot.
- **Tasks:** 
  - Construct the data ingestion pipeline (`server/seed_db.py`).
  - Integrate the Gemini API inside `server/app.py` to synthesize the final response combining the retrieved Shabad and the user's situation.

### 👁️ Vision (@ekaskohi-vision)
**Focus:** Semantic search and advanced RAG (Retrieval-Augmented Generation).
- **Goal:** Ensure the bot finds the *right* Gurbani verse based on emotional meaning, not just keywords.
- **Tasks:**
  - Implement vector embedding generation for the user's incoming query.
  - Write the SQLAlchemy/pgvector queries to perform cosine similarity searches in the database.

### 🎨 Design (@sarnazb)
**Focus:** Typography, theme polish, and visual communication.
- **Goal:** Ensure the new AI responses are presented beautifully and respectfully.
- **Tasks:**
  - Standardize Markdown or rich text rendering for the AI-generated insight.
  - Refine spacing and sizing for multi-paragraph responses.

### 📱 UX (@siddharthchopra)
**Focus:** Interaction patterns and perceived performance.
- **Goal:** Keep the user engaged while waiting for the AI and provide frictionless input.
- **Tasks:**
  - Implement a refined loading skeleton or "typing..." indicator in the chat UI.
  - Design failure/error states gracefully (e.g., if the LLM times out).

### ⚙️ Ops (@samisingh)
**Focus:** Infrastructure, database setup, and CI/CD.
- **Goal:** Provide a stable, secure foundation for the new features.
- **Tasks:**
  - Provision a remote PostgreSQL database (with `pgvector` support) on Railway or equivalent.
  - Update `.env` templates and securely inject the new connection variables into Vercel and Railway production environments.

### 🦸‍♂️ AFK/Backup (@suveersabharwal13)
**Focus:** Flexible support.
- **Goal:** Unblock the team.
- **Tasks:**
  - Assist Ops with database deployment and testing.
  - Review PRs from other branches to ensure fast merges.
