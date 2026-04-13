# SikhSituationBot

--- 🪯

## 🎯 What does this repo do?
This repository contains the code for an AI-powered conversational web application. The bot acts as a specialized search engine and empathetic guide: users type or speak their current emotional state (e.g., "I feel anxious"), and the bot retrieves relevant historical verses (Shabads) from the Siri Guru Granth Sahib (SGGS) to provide comfort and perspective.

## 🔭 What is our focus?
As a development team, our focus is transitioning this application from a basic keyword-search prototype into a context-aware AI. We are focused on:
1. **Semantic Understanding:** Using vector databases (`pgvector`) and Google Gemini embeddings to understand the *meaning* behind user queries, not just exact keywords.
2. **Generative Synthesis:** Using Large Language Models to read the retrieved historical verses and explain them in plain, empathetic English depending on the user's age (Child, Teen, Adult).
3. **Premium Interaction:** Delivering a seamless, rapid, and visually stunning chat interface (Next.js) with Voice Interaction capabilities.

## ✅ Project Progress Tracker

**Current Phase: Stage 2 (MVP) — Final Integration**
`[██████████] Stage 1 (PoC) - 100% Complete & Deployed`
`[██████████] Stage 2 (MVP) - 100% Integrated`

### 🛠️ Recent Completions (MVP)
- [x] **Vector Database Integration (`pgvector`)** (Completed by @Antigravity)
- [x] **Gemini RAG Pipeline (Embeddings & Synthesis)** (Completed by @Antigravity)
- [x] **Persona-Aware AI Insights (Child/Teen/Adult)** (Completed by @Antigravity)
- [x] **Premium Markdown Rendering & UI Polish** (Completed by @Antigravity)
- [x] **Robust Database Seeding Pipeline** (Completed by @sbindra-ai & @Antigravity)

### 📝 Contribution Log
| Task | Contributor | Date | Status |
| :--- | :--- | :--- | :--- |
| Initial UI & Data Foundation | @sbindra-ai | 2026-03-01 | ✅ Done |
| Design Tokens & Theme | @sarnazb | 2026-03-01 | ✅ Done |
| Perspectives UI & Consolidation | @Antigravity | 2026-03-01 | ✅ Done |
| Project Roadmap Setup | @sbindra-ai | 2026-02-08 | ✅ Done |
| Updated Design Tokens and Global CSS | @sarnazb | 2026-03-21 | ✅ Done |
| Testing Guide & Suite Verification | @sarnazb | 2026-03-23 | ✅ Done |
| **MVP RAG Integration & UI Polish** | **@Antigravity** | **2026-03-29** | **✅ Done** |

### 💡 Student Tips
- **Branch Often:** Create feature branches from `main`.
- **Commits Matter:** Use descriptive commit messages (e.g., `feat: add shabad search logic`).
- **Check your tasks:** Your specific tasks are in [docs/TASK_ASSIGNMENTS.md](docs/TASK_ASSIGNMENTS.md). Work at your own pace — there is no fixed weekly deadline.


## 🗺️ Implementation Roadmap

The project is divided into three main stages:

### Stage 1: Proof of Concept (PoC)
**Goal:** A basic functional web interface to test keyword-based Gurbani retrieval.
*   **Features:** Keyword search, basic responses (Gurbani line + simple meaning), minimal chat UI.
*   **Status:** ✅ **Completed & Deployed**
*   **Testing:** See `docs/poc-testing-guide.md` for class testing instructions.

### Stage 2: Minimum Viable Product (MVP)
**Goal:** A smart, context-aware bot with true semantic search and AI synthesis.
*   **Features:** Natural language search, vector embeddings, Gemini AI integration, Voice interaction.
*   **Stack:** Next.js, Flask, PostgreSQL (`pgvector`), Google Gemini API.
*   **Status:** ✅ **Complete & Integrated (PR #21)** - Full RAG pipeline is live.

### Stage 3: Production Version
**Goal:** A scalable, feature-rich platform.
*   **Features:** Audio responses (TTS), user history, personalization, mobile apps, analytics.

## 👥 Team Roles & Task Assignment

We use **role-based branches** so everyone can work in parallel. Each person works on their branch and submits PRs to `main`.

| Role | Branch | Focus |
| :--- | :--- | :--- |
| AI/Data | `feature/sbindra-ai` | Data, LLM, RAG |
| Design | `feature/sarnazb-design` | UI/UX, theme, typography |
| UX | `feature/siddharthchopra-ux` | Chat flows, persona UI |
| Ops | `feature/samisingh-ops` | DevOps, setup, deployment |
| AFK | `feature/suveersabharwal13-afk` | Backup / overflow tasks |

**📋 [docs/TASK_ASSIGNMENTS.md](docs/TASK_ASSIGNMENTS.md)** — Check here for the latest Stage 2 assignments. Team members pick up their tasks and continue on their branch.
**📋 [docs/mvp-plan.md](docs/mvp-plan.md)** — Read the official MVP goals and feature requirements.
**🧪 [docs/poc-testing-guide.md](docs/poc-testing-guide.md)** — Use this in class to interact with the currently deployed PoC.

---

## 🤝 Contribution Workflow

**IMPORTANT:** The `main` branch is protected and should never be pushed to directly.

1.  **Checkout:** Always branch off from `main`.
2.  **Your Branch:** Use your role branch (e.g. `feature/sarnazb-design`). See [docs/TASK_ASSIGNMENTS.md](docs/TASK_ASSIGNMENTS.md).
3.  **Naming Convention:** `feature/your-name-role` or `fix/issue-description`.
4.  **Pull Requests:** Submit PRs from your branch to `main` for review.

## 🚀 Getting Started

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Gurpreethgnis/SikhSituationBot.git
    ```
2.  **Checkout main and pull latest:**
    ```bash
    git checkout main
    git pull origin main
    ```
3.  **Switch to your role branch** (or create it if it doesn't exist):
    ```bash
    git checkout feature/your-name-role    # e.g. feature/sarnazb-design
    # If branch doesn't exist:
    git checkout -b feature/your-name-role
    ```
### 🛠️ Developer Quick Start

| Component | Command | Port | Tech |
| :--- | :--- | :--- | :--- |
| **Backend** | `cd server && pip install -r requirements.txt && python app.py` | `5000` | Flask, PostgreSQL, Gemini SDK |

## 🛡️ Security
SikhSituationBot follows a proactive security posture to protect the Gurbani corpus and user data.
*   **[SECURITY.md](SECURITY.md)** — Secure coding standards and vulnerability reporting.
*   **[THREAT_MODEL.md](THREAT_MODEL.md)** — Attack surface analysis and remediation status.

### Security Testing
Run the automated security suite to verify SQL injection and pattern-matching mitigations:
```bash
pytest server/tests/security/
```

### 📂 Key Folders
- `/client/app`: Next.js frontend application code
- `/server`: Flask backend logic, models, and embedding scripts
- `/docs`: Technical specs, MVP plans, and testing guides
- `/data`: JSON datasets (e.g., `shabad.json`)

---

## 📄 License
[Insert License Information]
