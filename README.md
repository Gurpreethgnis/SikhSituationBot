# SikhSituationBot 🪯

SikhSituationBot is an AI-powered conversational agent designed to provide guidance from Gurbani for modern life's challenges. It helps users find relevant Shabads (verses) based on their emotional state or life situation.

## 🌟 Project Vision
To bridge the gap between historical Sikh scripture and contemporary human experience by making Gurbani's wisdom accessible, age-appropriate, and actionable for the next generation.

## ✅ Project Progress Tracker

**Current Phase: Stage 2 (MVP)**
`[██████████] Stage 1 (PoC) - 100% Complete & Deployed`
`[██░░░░░░░░] Stage 2 (MVP) - 20% In Progress`

### 🛠️ Recent Completions (PoC)
- [x] **Repo Setup & README** (Completed by @sbindra-ai)
- [x] **Frontend Setup (Next.js)** (Completed by @Antigravity)
- [x] **Backend Skeleton (Flask)** (Completed by @samisingh-ops)
- [x] **Mock Data Ingestion** (Completed by @sbindra-ai)
- [x] **Premium UI & Branding** (Completed by @Antigravity)
- [x] **Live Deployment Configuration** (Vercel & Railway)

### 📝 Contribution Log
| Task | Contributor | Date | Status |
| :--- | :--- | :--- | :--- |
| Initial UI & Data Foundation | @sbindra-ai | 2026-03-01 | ✅ Done |
| Design Tokens & Theme | @sarnazb | 2026-03-01 | ✅ Done |
| Perspectives UI & Consolidation | @Antigravity | 2026-03-01 | ✅ Done |
| Project Roadmap Setup | @sbindra-ai | 2026-02-08 | ✅ Done |

## 📅 Weekly Plan (Student View)

| Week | Focus | Main Tasks | Milestone / Deliverable |
| :--- | :--- | :--- | :--- |
| **Week 1** | **Foundations** | Set up environment, Git branches, and basic project structure. Research [BaniDB](https://api.banidb.com) and LLM options. | Repo initialized with a "Hello World" frontend. |
| **Week 2** | **Data & UI** | Build the core Chat UI. Connect to Gurbani data sources and implement basic keyword retrieval. | Searchable Shabad interface with proper formatting. |
| **Week 3** | **AI Integration** | Integrate LLM for generating responses. Design and test prompts for Child, Teen, and Adult personas. | Functional AI chatbot that explains Gurbani contextually. |
| **Week 4** | **Polish & Demo** | Refine UI/UX (animations, responsive design). Conduct user testing and prepare the final demo/presentation. | **Project Demo Ready!** 🚀 |

### 💡 Student Success Tips
- **Branch Often:** Create feature branches from `main`.
- **Commits Matter:** Use descriptive commit messages (e.g., `feat: add shabad search logic`).
- **Ask for Help:** Stuck on Gurbani APIs or AI prompts? Use the `docs/` folder or reach out!
- **Test Small:** Verify your code works in small chunks before moving to the next week's goal.


## 🗺️ Implementation Roadmap

The project is divided into three main stages:

### Stage 1: Proof of Concept (PoC)
**Goal:** A basic functional web interface to test keyword-based Gurbani retrieval.
*   **Features:** Keyword search, basic responses (Gurbani line + simple meaning), minimal chat UI.
*   **Status:** ✅ **Completed & Deployed to `https://sikhsituationbot.sage-school.com`**
*   **Testing:** See `docs/poc-testing-guide.md` for class testing instructions.

### Stage 2: Minimum Viable Product (MVP)
**Goal:** A smart, context-aware bot with true semantic search and AI synthesis.
*   **Features:** Natural language search, vector embeddings, Gemini AI integration, Voice interaction.
*   **Stack:** Next.js, Flask, PostgreSQL (`pgvector`), Google Gemini API.
*   **Status:** 🔄 **In Progress** - See `docs/mvp-plan.md` for full details.

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

**📋 [TASK_ASSIGNMENTS.md](TASK_ASSIGNMENTS.md)** — Check here for the latest Stage 2 assignments. Team members pick up their tasks and continue on their branch.
**📋 [docs/mvp-plan.md](docs/mvp-plan.md)** — Read the official MVP goals and feature requirements.
**🧪 [docs/poc-testing-guide.md](docs/poc-testing-guide.md)** — Use this in class to interact with the currently deployed PoC.

---

## 🤝 Contribution Workflow

**IMPORTANT:** The `main` branch is protected and should never be pushed to directly.

1.  **Checkout:** Always branch off from `main`.
2.  **Your Branch:** Use your role branch (e.g. `feature/sarnazb-design`). See [TASK_ASSIGNMENTS.md](TASK_ASSIGNMENTS.md).
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
| **Frontend** | `cd client && npm install && npm run dev` | `3000` | Next.js, React, CSS Modules |
| **Backend** | `cd server && pip install -r requirements.txt && python app.py` | `5000` | Flask, PostgreSQL, Gemini SDK |

### 📂 Key Folders
- `/client/app`: Next.js frontend application code
- `/server`: Flask backend logic, models, and embedding scripts
- `/docs`: Technical specs, MVP plans, and testing guides
- `/data`: JSON datasets (e.g., `shabad.json`)

---

## 📄 License
[Insert License Information]
