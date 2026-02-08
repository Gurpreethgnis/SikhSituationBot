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

## 🤝 Contribution Workflow

**IMPORTANT:** The `main` branch is protected and should never be pushed to directly.

1.  **Checkout:** Always branch off from `main`.
2.  **Naming Convention:** `feature/your-feature-name` or `fix/issue-description`.
3.  **Pull Requests:** Submit PRs to the `main` branch for review.

## 🚀 Getting Started

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Gurpreethgnis/SikhSituationBot.git
    ```
2.  **Checkout the main branch:**
    ```bash
    git checkout main
    ```
3.  **Create your feature branch:**
    ```bash
    git checkout -b feature/your-name-task
    ```
4.  **Install dependencies:**
    - **Frontend:** `cd client && npm install`
    - **Backend:** `cd server && pip install -r requirements.txt`

## 📄 License
[Insert License Information]
