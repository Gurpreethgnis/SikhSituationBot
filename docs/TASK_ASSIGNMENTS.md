# 📋 Task Assignments & Role-Based Workflow

This document helps you **assign work** and lets team members **pick up tasks** on their role-specific branches. Update this file as tasks are assigned or completed.

---

## 👥 Team Roles & Branches

| Role | Branch | Owner | Focus Area |
| :--- | :--- | :--- | :--- |
| **AI/Data** | `feature/sbindra-ai` | @sbindra-ai | Data ingestion, LLM integration, embeddings, RAG logic |
| **Design** | `feature/sarnazb-design` | @sarnazb | UI/UX design, visual specs, theme, Gurmukhi typography |
| **UX** | `feature/siddharthchopra-ux` | @siddharthchopra | User flows, persona switching, chat interaction patterns |
| **Ops** | `feature/samisingh-ops` | @samisingh | DevOps, deployment, CI/CD, environment setup, API keys |
| **Vision** | `feature/ekaskohi-vision` | @ekaskohi | Advanced RAG, Semantic Search, Gurbani LLM fine-tuning |
| **AFK** | `feature/suveersabharwal13-afk` | @suveersabharwal13 | Backup / flexible capacity — picks up overflow tasks |

---

## 🔄 How to Pick Up Your Tasks

### Step 1: Make sure you're on your branch
```bash
git checkout main
git pull origin main
git checkout feature/your-role-branch   # e.g. feature/sarnazb-design
git pull origin feature/your-role-branch
```

### Step 2: Find your assigned tasks
- Look at the **Assigned to You** section below for your role.
- Or search this file for your GitHub username or branch name.

### Step 3: Do the work
- Create a sub-branch if you prefer: `git checkout -b task/specific-task-name`
- Or work directly on your role branch.

### Step 4: Submit a PR
- Open a PR from **your branch** → `main`.
- Reference the task in the PR description (e.g., `Fixes: Theme palette`).

---

## 📌 Assigned Tasks (Week 1)

### Assigned to @sbindra-ai (AI/Data)
| Task | Status | Notes |
| :--- | :---: | :--- |
| Create `scripts/clean_data.py` to normalize Gurbani text | ✅ | Done. Used to ensure schema consistency. |
| Expand `data/shabad.json` with more situational Shabads | ✅ | Target hit: 50 situational Shabads vectorized & ready. |
| Validate data against schema in `docs/data-strategy.md` | ✅ | Done. All files use unified JSON schema. |
<| **[MVP]** Script data pipeline to embed SGGS JSON via Gemini | ✅ | COMPLETED: Enhanced `server/seed_db.py` with robust error handling, batch processing, pgvector setup, and progress logging. |
| **[MVP]** Integrate Gemini API in `/ask` for final response synthesis | ✅ | COMPLETED: Updated `/ask` endpoint with Gemini synthesis, persona-aware prompts, and structured responses. |
| **Pointers**: Use `sentence-transformers` in Python if you start on semantic search early. | | |

### Assigned to @sarnazb (Design)
| Task | Status | Notes |
| :--- | :---: | :--- |
| Define CSS color palette (Deep Blues, Gold accents) | ✅ | Sikh-inspired, calming (`client/src/index.css`) |
| Create `docs/design-tokens.md` or design spec | ✅ | Created `docs/design-tokens.md` |
| Design "Perspectives" pills/tabs (Child, Teen, Adult) | ✅ | Integrated into `client/src/index.css` |
| **[MVP]** Standardize rich text/Markdown styling for AI insights | ✅ | COMPLETED: Integrated `MarkdownRenderer.jsx` and standardized `.prose-gurbani` in `globals.css`. |
| **[MVP]** Refine typography layout for dynamically sized AI content | ✅ | COMPLETED: Implemented `clamp()` typography and responsive `shabad-card` layout for dynamic content. |
| **[MVP]** Add comprehensive testing guide and verify suite | ✅ | Created `docs/tests-guide.md` and verified all backend tests |

### Assigned to @siddharthchopra (UX)
| Task | Status | Notes |
| :--- | :---: | :--- |
| Build chat input / search bar component | ✅ | `ChatInput.jsx` with premium styling |
| Implement persona toggle (Child/Teen/Adult) UI | ✅ | `Perspectives.jsx` with pill buttons |
| Wire up chat flow: query → display → loading states | ✅ | Full flow wired in `page.jsx` (PR #21) |
| **[MVP]** Implement polished loading skeleton or "Bot is thinking" UI | ✅ | Animated dots loading state (PR #21) |
| **[MVP]** Design failure/error states gracefully | ✅ | Error catch with user-friendly fallback message (PR #21) |

### Assigned to @samisingh (Ops)
| Task | Status | Notes |
| :--- | :---: | :--- |
| Initialize Next.js project in `/client` | ✅ | Done. Running at `localhost:3000` |
| Set up Flask backend in `/server` | ✅ | `server/app.py` with RAG `/ask` route |
| API key setup (Google Gemini) | ✅ | Configured via `.env` |
| **[MVP]** Provision PostgreSQL DB with `pgvector` (e.g., Railway) | 🔄 | Guide created in deployment docs. Needs team to provision. |
| **[MVP]** Manage and secure production `DB_URL` env variables | 🔄 | `.env.example` updated; prod config pending deployment |
| **Pointers**: Check `gh secret set` if we move to GitHub Actions later. | | |

### Assigned to @ekaskohi (Vision)
| Task | Status | Notes |
| :--- | :---: | :--- |
| Semantic Search Research | ⬜ | Explore `sentence-transformers` for Gurbani |
| Advanced RAG Architecture | ⬜ | Design multi-stage retrieval flow |
| Vision: Gurbani fine-tuning plan | ⬜ | Research feasibility of Gurbani-specific LLM |
| **[MVP]** Implement query vectorization using embedding model | ✅ | `text-embedding-004` in `server/app.py` (PR #21) |
| **[MVP]** Write PGVector cosine similarity queries for `/ask` | ✅ | `Shabad.embedding.cosine_distance()` in `server/app.py` (PR #21) |

### Assigned to @suveersabharwal13 (AFK / Backup)
| Task | Status | Notes |
| :--- | :---: | :--- |
| *Available for overflow* | ⬜ | Pick up unassigned tasks or help anyone blocked |
| Hello World page: "Hello SikhSituationBot" | ⬜ | Good first task if nothing else |
| Documentation: Update README or docs as needed | ⬜ | |
| **[MVP]** Pair with Ops to test database connection resilience | ⬜ | Backup support |
| **[MVP]** QA test semantic search responses | ⬜ | Provide feedback on retrieval accuracy |

---

## 📌 Unassigned / Needs Owner

| Task | Status | Notes |
| :--- | :---: | :--- |
| Frontend: Initialize Vite+React or Next.js | ✅ | Initialized Next.js at `http://localhost:3000` |
| Backend: Flask app + `/ask` route | ✅ | Full RAG pipeline in `server/app.py` (PR #21) |
| Data: `scripts/clean_data.py` | ⬜ | Assigned to @sbindra-ai (AI) |

---

## 🛠️ How to Assign Tasks

1. **Assign:** Add the task under the appropriate role in `Assigned Tasks` above.
2. **Use status:** `⬜` = Not started | `🔄` = In progress | `✅` = Done |
3. **Update:** When done, move to `✅` and add to the Contribution Log in `../README.md`.

---

## 🔗 Quick Links

- [README.md](../README.md) — Project overview and progress
- [WEEK_1_TASKS.md](WEEK_1_TASKS.md) — Week 1 priorities
- [docs/weekly-plan.md](docs/weekly-plan.md) — 4-week plan
- [docs/data-strategy.md](docs/data-strategy.md) — Data schema
- [docs/architecture.md](docs/architecture.md) — System design
