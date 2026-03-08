# 📋 Week 1: Foundation & Setup

Welcome team! Our goal this week is to set up the "skeleton" of SikhSituationBot. Use **Cursor/Antigravity** to help you move fast, even if you are unfamiliar with some of these tools.

**📋 [TASK_ASSIGNMENTS.md](TASK_ASSIGNMENTS.md)** — Check here for your assigned tasks and your role branch. Pick up work and continue on your branch.

## 🚀 Priority Tasks

### 1. Environment & Repo Setup
- [x] **Clone & Branch**: Done. Team is using feature branches and merging to main.
- [ ] **Next.js Init**: Initialize a Next.js project in the `/client` folder (Changed from `/src` to align with repo structure).
- [ ] **API Keys**: Set up shared keys for Gemini and Supabase.
- [ ] **Hello World**: Deploy a basic "Hello SikhSituationBot" page.

### 2. Data Sourcing (The Core)
- [x] **Locate Data**: Done. Initial `data/shabad.json` created by @sbindra-ai.
- [x] **Data Cleaning**: Done. Created `scripts/clean_data.py`.
- [x] **Schema Design**: Done. Proposed in `docs/data-strategy.md` by @sarnazb.

### 3. Basic UI Scaffolding
- [ ] **Chat Input**: Create a search bar/input field that feels premium.
- [ ] **Perspectives UI**: Build a "pills" or "tabs" component to select 'Child', 'Teen', or 'Adult'.
- [ ] **Theme**: Define a CSS color palette that is calming (Deep Blues, Gold accents - *Sikh color palette*).

---

## 💡 Tips for using AI Tools (Cursor/Antigravity)
- **Frontend**: Ask: *"Design a modern, glassmorphic chat interface using Next.js and vanilla CSS with a gold and deep blue theme."*
- **Scripting**: Highlight your data JSON and ask: *"Write a Python script to extract all 'English' fields and save them to a new CSV for embedding."*
- **Learning**: If you don't understand RAG, ask: *"Explain how Vector Databases work in the context of this project as if I am a beginner."*

## 🏁 Friday Milestone
**Goal**: We should be able to type a query, see it logged in the console, and see a hardcoded Shabad display on a beautiful UI.
