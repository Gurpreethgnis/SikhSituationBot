# 📋 Week 1: Foundation & Setup

Welcome team! Our goal this week is to set up the "skeleton" of SikhSituationBot. Use **Cursor/Antigravity** to help you move fast, even if you are unfamiliar with some of these tools.

## 🚀 Priority Tasks

### 1. Environment & Repo Setup
- [ ] **Clone & Branch**: Ensure everyone has the repo and is working on a `feature/` branch.
- [ ] **Next.js Init**: Initialize a Next.js project in the `/src` folder.
- [ ] **API Keys**: Set up shared keys for:
    - Google AI Studio (Gemini)
    - Supabase (for Database)
- [ ] **Hello World**: Deploy a basic "Hello SikhSituationBot" page to Vercel/Netlify.

### 2. Data Sourcing (The Core)
- [ ] **Locate Data**: Download a JSON export of common situational Shabads from [BaniDB](https://banidb.com).
- [ ] **Data Cleaning**: Create a small script `scripts/clean_data.py` to extract just the Gurmukhi and English translation for 50-100 Shabads.
- [ ] **Schema Design**: Define what a "Shabad object" looks like in our DB (id, gurmukhi, english, tags like 'stress').

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
