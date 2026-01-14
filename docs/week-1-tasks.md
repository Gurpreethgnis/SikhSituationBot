# 📅 Week 1 Tasks: Infrastructure & Foundation

This checklist is for the student team to establish the core project structure and data baseline.

## 🏗️ Environment Setup
- [ ] **Next.js Initialization:** Scaffold the frontend in `/frontend` using `npx create-next-app@latest`.
- [ ] **FastAPI Backend:** Initialize a Python virtual environment in `/backend` and set up a basic "Hello World" FastAPI server.
- [ ] **Git Workflow:** Ensure everyone is working on feature branches and pulling from `develop`.
- [ ] **API Keys:** Secure access to OpenAI/Gemini/Anthropic API keys in a `.env` file (ensure it's gitignored).

## 📊 Data Ingestion (BaniDB)
- [ ] **Source Research:** Access [BaniDB](https://github.com/shabados/database) or equivalent open Gurbani datasets.
- [ ] **Scripting:** Write a Python script to parse a subset of Gurbani (e.g., Sukhmani Sahib or popular Shabads) into a JSON/SQLITE format.
- [ ] **Basic Embedding:** (Optional/Stretch) Run a small subset through an embedding model (`all-MiniLM-L6-v2`) to test vector storage.

## 🎨 UI/UX Design
- [ ] **Style Guide:** Define a color palette (Golds, Deep Blues, Whites) and typography (Outfit/Inter).
- [ ] **Wireframes:** Design the main chat interface, persona toggle, and response cards (Figma or Pen/Paper).
- [ ] **Landing Page:** Create a simple hero section explaining the bot's purpose.

## 🤖 AI Exploration
- [ ] **System Prompting:** Test different system prompts in a playground (ChatGPT/Claude) to see how well they translate "Situations" to "Advice" based on a provided Shabad.
- [ ] **Persona Definition:** Finalize the tone/voice for 'Child', 'Teen', and 'Adult' personas.

---

### End of week goal:
A "walking skeleton": A frontend that can talk to a backend, which can return a hardcoded Gurbani verse and a formatted explanation.
