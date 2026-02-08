# SikhSituationBot 🪯

SikhSituationBot is an AI-powered conversational agent designed to provide guidance from Gurbani for modern life's challenges. It helps users find relevant Shabads (verses) based on their emotional state or life situation.

## 🌟 Project Vision
To bridge the gap between historical Sikh scripture and contemporary human experience by making Gurbani's wisdom accessible, age-appropriate, and actionable for the next generation.

## ✅ Project Progress Tracker

**Current Phase: Stage 1 (PoC)**
`[██░░░░░░░░] 20%`

### 🛠️ Active Tasks
- [x] **Repo Setup & README** (Completed by @sbindra-ai on 2026-02-08)
- [ ] **Frontend Setup (Vite+React)**
    - [ ] Initialize project
    - [ ] Create basic "Hello World" component
- [ ] **Backend Setup (Flask)**
    - [ ] Initialize Flask app
    - [ ] Create simple API route
- [ ] **Data Ingestion**
    - [ ] Create `data/shabads.json` (Partial: Anxiety dataset added)
    - [ ] Write `scripts/clean_data.py`

### 📝 Contribution Log
| Task | Contributor | Date | Status |
| :--- | :--- | :--- | :--- |
| Added Anxiety Dataset | @Gurpreethgnis | 2026-02-08 | ✅ Done |
| Initial Repo Setup | @sbindra-ai | 2026-02-08 | ✅ Done |

## 📅 Weekly Plan (Student View)

| Week | Focus | Main Tasks | Milestone / Deliverable |
| :--- | :--- | :--- | :--- |
| **Week 1** | **Foundations** | Set up environment, Git branches, and basic project structure. Research [BaniDB](https://api.banidb.com) and LLM options. | Repo initialized with a "Hello World" frontend. |
| **Week 2** | **Data & UI** | Build the core Chat UI. Connect to Gurbani data sources and implement basic keyword retrieval. | Searchable Shabad interface with proper formatting. |
| **Week 3** | **AI Integration** | Integrate LLM for generating responses. Design and test prompts for Child, Teen, and Adult personas. | Functional AI chatbot that explains Gurbani contextually. |
| **Week 4** | **Polish & Demo** | Refine UI/UX (animations, responsive design). Conduct user testing and prepare the final demo/presentation. | **Project Demo Ready!** 🚀 |

### 💡 Student Success Tips
- **Branch Often:** Don't work on `develop` directly. Create feature branches for every task.
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
    git clone <repository-url>
    ```
2.  **Checkout the main branch:**
    ```bash
    git checkout main
    ```
3.  **Install dependencies:**
    *(Instructions to be added based on selected stack)*

## 📄 License
[Insert License Information]
