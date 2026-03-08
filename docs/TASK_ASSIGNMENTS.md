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
| **[MVP]** Script data pipeline to embed SGGS JSON via Gemini | ⬜ | See `docs/mvp-plan.md` |
| **[MVP]** Integrate Gemini API in `/ask` for final response synthesis | ⬜ | RAG combination phase |
| **Pointers**: Use `sentence-transformers` in Python if you start on semantic search early. | | |

### Assigned to @sarnazb (Design)
| Task | Status | Notes |
| :--- | :---: | :--- |
| Define CSS color palette (Deep Blues, Gold accents) | ✅ | Sikh-inspired, calming (`client/src/index.css`) |
| Create `docs/design-tokens.md` or design spec | ✅ | Created `docs/design-tokens.md` |
| Design "Perspectives" pills/tabs (Child, Teen, Adult) | ✅ | Integrated into `client/src/index.css` |
| **[MVP]** Standardize rich text/Markdown styling for AI insights | ⬜ | Make paragraphs and lists look clean |
| **[MVP]** Refine typography layout for dynamically sized AI content | ⬜ | Ensure long verses map well on mobile |

### Assigned to @siddharthchopra (UX)
| Task | Status | Notes |
| :--- | :---: | :--- |
| Build chat input / search bar component | ⬜ | Premium feel |
| Implement persona toggle (Child/Teen/Adult) UI | ⬜ | Pills or tabs |
| Wire up chat flow: query → display → loading states | ⬜ | |
| **[MVP]** Implement polished loading skeleton or "Bot is thinking" UI | ⬜ | Essential for AI latency |
| **[MVP]** Design failure/error states gracefully | ⬜ | Fallback UI when LLM times out |

### Assigned to @samisingh (Ops)
| Task | Status | Notes |
| :--- | :---: | :--- |
| Initialize Next.js project in `/client` | ⬜ | Per `WEEK_1_TASKS.md` |
| Set up Flask backend in `/server` | ⬜ | `server/app.py`, basic route |
| API key setup (Google Gemini) | ⬜ | Use `.env` file (see `.env.example`) |
| **[MVP]** Provision PostgreSQL DB with `pgvector` (e.g., Railway) | ⬜ | Critical path for MVP |
| **[MVP]** Manage and secure production `DB_URL` env variables | ⬜ | Vercel & Railway Config |
| **Pointers**: Check `gh secret set` if we move to GitHub Actions later. | | |

### Assigned to @ekaskohi (Vision)
| Task | Status | Notes |
| :--- | :---: | :--- |
| Semantic Search Research | ⬜ | Explore `sentence-transformers` for Gurbani |
| Advanced RAG Architecture | ⬜ | Design multi-stage retrieval flow |
| Vision: Gurbani fine-tuning plan | ⬜ | Research feasibility of Gurbani-specific LLM |
| **[MVP]** Implement query vectorization using embedding model | ⬜ | Convert user text to vector in backend |
| **[MVP]** Write PGVector cosine similarity queries for `/ask` | ⬜ | Link user vector to DB Shabad vectors |

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
| Backend: Flask app + `/ask` route | ⬜ | Assign to Ops |
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
