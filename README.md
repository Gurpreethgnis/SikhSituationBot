# SikhSituationBot

SikhSituationBot is an AI-powered chatbot designed to provide guidance from Gurbani (Sikh scripture) for life's challenges. It offers tailored responses suitable for different age groups (children, teens, adults) and spiritual depths, leveraging authentic data sources like BaniDB.

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

## 🛠️ Contribution Workflow

**IMPORTANT:** The `main` branch is protected and should never be pushed to directly.

1.  **Checkout:** Always branch off from `develop` (or your specific feature branch).
2.  **Naming Convention:** `feature/your-feature-name` or `fix/issue-description`.
3.  **Pull Requests:** Submit PRs to the `develop` branch for review.

## 🚀 Getting Started

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    ```
2.  **Checkout the development branch:**
    ```bash
    git checkout develop
    ```
3.  **Install dependencies:**
    *(Instructions to be added based on selected stack)*

## 📄 License
[Insert License Information]
