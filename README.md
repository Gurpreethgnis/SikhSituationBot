# SikhSituationBot 🪯

SikhSituationBot is an AI-powered conversational agent designed to provide guidance from Gurbani for modern life's challenges. It helps users find relevant Shabads (verses) based on their emotional state or life situation.

## 🌟 Project Vision
To bridge the gap between historical Sikh scripture and contemporary human experience by making Gurbani's wisdom accessible, age-appropriate, and actionable for the next generation.

## ✅ Project Progress Tracker

**Current Phase: Stage 1 (PoC)**
`[████░░░░░░] 40%`

### 🛠️ Active Tasks
- [x] **Repo Setup & README** (Completed by @sbindra-ai)
- [ ] **Frontend Setup (Vite+React)**
    - [ ] Initialize project: `npx create-vite@latest client --template react`
    - [ ] Create basic "Hello World" component in `client/src/App.jsx`
- [ ] **Backend Setup (Flask)**
    - [ ] Initialize Flask app: Create `server/app.py`
    - [ ] Create simple API route: `@app.route('/ask')`
- [ ] **Data Ingestion**
    - [x] Create `data/shabads.json` (Completed by @sbindra-ai)
    - [x] Schema Design (Completed by @sarnazb)
    - [ ] Write `scripts/clean_data.py` to normalize Gurbani text

### 📝 Contribution Log
| Task | Contributor | Date | Status |
| :--- | :--- | :--- | :--- |
| Initial Setup & Data Strategy | @sarnazb | 2026-02-08 | ✅ Done (PR #1) |
| Weekly Plan & Anxiety Data | @sbindra-ai | 2026-02-08 | ✅ Done (PR #2) |
| Added Anxiety Dataset | @sbindra-ai | 2026-02-08 | ✅ Done |
| Initial Repo Setup | @sbindra-ai | 2026-02-08 | ✅ Done |

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
*   **Status:** In Progress

### Stage 2: Minimum Viable Product (MVP)
**Goal:** A smart, context-aware bot with age-appropriate explanations.
*   **Features:** Natural language search, tiered explanations (Child/Teen/Adult), full Gurbani context, FAQ section.
*   **Stack:** React/Vue, Node.js/Python, Vector Search (Pinecone/Milvus), LLM Integration.

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

**📋 [TASK_ASSIGNMENTS.md](TASK_ASSIGNMENTS.md)** — Assign work here. Team members pick up their tasks and continue on their branch.

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
| **Frontend** | `cd client && npm run dev` | `5173` | React, Vite, Tailwind (optional) |
| **Backend** | `cd server && python app.py` | `5000` | Flask, Google Gemini SDK |

### 📂 Key Folders
- `/client/src`: Your React components
- `/server`: Flask API logic and LLM prompts
- `/data`: JSON datasets (e.g., `shabad.json`)
- `/docs`: Visual specs and architecture

---

## 📄 License
[Insert License Information]
