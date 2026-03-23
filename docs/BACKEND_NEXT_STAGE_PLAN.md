# 🔧 Backend Next Stage Plan - Data Ingestion & Gemini Integration

**Date Created**: March 23, 2026  
**Current Phase**: Moving from Frontend Design (✅ Complete) → Backend Database Design  
**Team Lead**: @sbindra-ai (AI/Data team)

---

## 📊 ALIGNMENT VERIFICATION

### ✅ Objectives Alignment (MVP Plan vs Current Work)

| Objective | MVP Plan | Current Status | Technology | Aligned? |
|-----------|----------|-----------------|------------|----------|
| Database Foundation (PostgreSQL + pgvector) | Core requirement | ✅ Schema defined (`models.py`) | PostgreSQL + pgvector | ✅ YES |
| Data Pipeline (seed_db.py) | Critical path | 🔄 Partial (exists, untested) | Python JSON → DB | ✅ YES |
| Vector Embeddings | Core RAG requirement | ✅ In place (`vector_utils.py`) | Gemini API + sentence-transformers | ✅ YES |
| Semantic Retrieval | Core RAG requirement | ✅ In place (`retrieval.py`) | pgvector cosine similarity | ✅ YES |
| Gemini Response Synthesis | Critical LLM integration | ⬜ NOT STARTED | google-generativeai library | ✅ YES (planned) |
| Persona-based responses | UX requirement | ✅ Frontend ready | Persona param in /ask endpoint | ✅ YES |

### ✅ Technology Stack Verification

| Layer | Technology | Status | Rationale |
|-------|-----------|--------|-----------|
| **Backend** | Python Flask | ✅ Selected | Native support for AI/ML libraries |
| **Embedding** | Gemini API + sentence-transformers | ✅ Selected | Fallback strategy, scalability |
| **Database** | PostgreSQL + pgvector | ✅ Selected | Vector similarity search, production-ready |
| **LLM** | Google Gemini API | ✅ Selected | Aligned with embedding choice |
| **Frontend** | Next.js React | ✅ Selected | Modern, fast, good for real-time UI |

---

## 📋 SCOPE VERIFICATION

### ✅ In Scope (Per MVP Plan)

1. **Data Pipeline Construction** (`server/seed_db.py`)
   - Read data from `data/shabads_cleaned.json`
   - Generate embeddings for each verse
   - Insert into PostgreSQL database with vectors
   - Status: ⬜ NOT STARTED (needs DB setup, Gemini API key, requirements updates)

2. **Gemini API Integration** (`server/app.py` → `/ask` endpoint)
   - Receive user query + persona
   - Retrieve top-5 semantic matches from DB
   - Construct prompt with retrieved shabads + persona context
   - Call Gemini API to synthesize response
   - Return structured response (shabad + AI guidance)
   - Status: ⬜ NOT STARTED (response synthesis missing)

3. **Vector Utils Enhancement** (`server/vector_utils.py`)
   - ✅ Already supports Gemini embeddings with fallback
   - ✅ Support for both models (`text-embedding-004` and `all-MiniLM-L6-v2`)
   - Status: ✅ COMPLETE

4. **Database Models** (`server/models.py`)
   - ✅ Shabad model with 768-dim vector column
   - ✅ pgvector integration
   - Status: ✅ COMPLETE

5. **Semantic Retrieval** (`server/retrieval.py`)
   - ✅ Cosine similarity search
   - ✅ Persona filtering
   - Status: ✅ COMPLETE

### ⬜ Out of Scope (Not in MVP, Infrastructure/DevOps)

1. **Database Provisioning** (Assigned to @samisingh - Ops)
   - Not AI/Data team responsibility
   - Railway/GCP-SQL setup
   - Production .env management

2. **Frontend Loading States** (Assigned to @siddharthchopra - UX)
   - ✅ Already implemented in current codebase
   - Typing indicators, error states, retry logic

3. **Gurbani Fine-tuning** (Future phase, Vision team)
   - Out of MVP scope
   - Assigned to @ekaskohi for research

---

## 🎯 CURRENT OBJECTIVES (To Start Immediately)

### Objective 1: Construct Data Ingestion Pipeline

**Goal**: Create a robust `server/seed_db.py` that:
- Reads the cleaned Shabad JSON data
- Generates embeddings for each verse
- Persists data to PostgreSQL with vectors
- Handles API rate limiting & fallback models
- Provides clear progress feedback

**Scope**:
- ✅ Data validation against schema
- ✅ Embedding generation (Gemini → fallback)
- ✅ Database insertion with batch commits
- ✅ Error handling & logging
- ✅ pgvector extension setup
- ⬜ Database connection (prerequisite from Ops)

---

### Objective 2: Integrate Gemini API Response Synthesis

**Goal**: Upgrade `server/app.py` `/ask` endpoint to:
- Accept query + persona
- Retrieve relevant shabads (already working via `retrieval.py`)
- Construct intelligent prompt combining:
  - Retrieved shabads (context)
  - User's emotional query (persona-specific phrasing)
  - Persona-specific guidance tone (Child/Teen/Adult)
- Call Gemini API for final synthesis
- Return structured response

**Scope**:
- ✅ Prompt engineering (persona-aware)
- ✅ Gemini API call with error handling
- ✅ Response parsing & formatting
- ✅ Fallback if API fails
- ⬜ Streaming response (optional, future enhancement)

---

## 📁 FILES TO CREATE / MODIFY

### ✅ NEW FILES (To Create)

| File Path | Purpose | Complexity | Owner |
|-----------|---------|-----------|-------|
| `server/prompts.py` | Centralized prompt templates for each persona | Low | @sbindra-ai |
| `server/seed_db.py` | ENHANCED - Full data ingestion pipeline | Medium | @sbindra-ai |
| `.env.example` | Updated with new env vars for DB + Gemini | Low | @sbindra-ai |
| `docs/VECTOR_SEEDING_GUIDE.md` | Instructions for running seed_db.py | Low | @sbindra-ai |
| `tests/test_seed_db.py` | Unit tests for seeding pipeline | Medium | @sbindra-ai |
| `tests/test_gemini_synthesis.py` | Unit tests for Gemini response generation | Medium | @sbindra-ai |

### 🔄 MODIFIED FILES (To Update)

| File Path | Changes | Complexity | Owner |
|-----------|---------|-----------|-------|
| `server/app.py` | Add Gemini synthesis to `/ask` endpoint | Medium | @sbindra-ai |
| `server/vector_utils.py` | Add retry logic + rate limit handling | Low | @sbindra-ai |
| `server/requirements.txt` | Add: pgvector, sqlalchemy, sentence-transformers | Low | @sbindra-ai |
| `docs/architecture.md` | Update data flow diagram with Gemini integration | Low | @sbindra-ai |
| `docs/TASK_ASSIGNMENTS.md` | Mark Objective 1 & 2 as IN PROGRESS | Low | @sbindra-ai |

---

## 🛠️ IMPLEMENTATION BREAKDOWN

### Phase 1: Data Ingestion Pipeline (Objective 1)

#### Step 1.1: Create `server/prompts.py`
**Purpose**: Centralized persona-specific prompt templates  
**Content**:
```
- PERSONA_CONTEXTS: dict mapping 'child' → 'teen' → 'adult' guidance tones
- SYSTEM_PROMPT: Base instruction for Gemini
- PROMPT_TEMPLATES: f-string templates for each persona combining shabads + query
```

#### Step 1.2: Enhanced `server/seed_db.py`
**Purpose**: Robust data pipeline with error handling  
**Key Features**:
- Load JSON from data/shabads_cleaned.json
- Batch embedding generation (50 items per batch)
- Rate limit handling for Gemini API
- Progress logging (current/total)
- pgvector extension & index creation
- Duplicate detection (skip already-seeded shabads)
- Atomic commits (rollback on error)

#### Step 1.3: Update `server/requirements.txt`
**Add**:
- `pgvector` (PostgreSQL vector type)
- `sqlalchemy>=2.0` (ORM with vector support)
- `sentence-transformers>=2.2` (local embedding fallback)

#### Step 1.4: Create `docs/VECTOR_SEEDING_GUIDE.md`
**Content**:
- Prerequisites (DB connection, env variables)
- Step-by-step execution guide
- Expected output format
- Troubleshooting common errors

#### Step 1.5: Create Unit Tests
**File**: `tests/test_seed_db.py`
- Mock database context
- Test JSON loading
- Test embedding generation
- Test batch insertion logic

---

### Phase 2: Gemini Response Synthesis (Objective 2)

#### Step 2.1: Create `server/prompts.py` (Continued)
**Add Synthesis Functions**:
```python
def build_synthesis_prompt(query, shabads, persona) → str
def format_shabad_context(shabads_list) → str
```

#### Step 2.2: Update `server/app.py` → `/ask` endpoint
**Current Flow**:
1. Receive query + persona ✅
2. Generate query embedding ✅
3. Retrieve shabads from DB ✅
4. Return mock response ❌ (REPLACE THIS)

**New Flow**:
1. Receive query + persona ✅
2. Generate query embedding ✅
3. Retrieve shabads from DB ✅
4. **[NEW]** Build synthesis prompt using `prompts.build_synthesis_prompt()`
5. **[NEW]** Call Gemini API with prompt
6. **[NEW]** Parse + structure response
7. Return `{"response": ai_synthesis, "shabad": shabad_dict, "query": query}`

#### Step 2.3: Enhance `server/vector_utils.py`
**Add**:
- Retry logic (exponential backoff for rate limits)
- Timeout handling
- API key validation

#### Step 2.4: Create Unit Tests
**File**: `tests/test_gemini_synthesis.py`
- Mock Gemini API responses
- Test prompt construction
- Test persona-specific responses
- Test error handling (API timeout, invalid key)

#### Step 2.5: Update `docs/architecture.md`
**Clarify**:
- Updated data flow with Gemini integration
- Prompt engineering strategy
- Error handling paths
- Performance considerations

---

## 📊 EXECUTION PLAN

### Week 1 (This Week): Setup & Phase 1

| Day | Task | Owner | Status |
|-----|------|-------|--------|
| **Mon** | 1.1: Create `prompts.py` | @sbindra-ai | ⬜ |
| **Tue** | 1.2: Enhance `seed_db.py` | @sbindra-ai | ⬜ |
| **Wed** | 1.3: Update requirements.txt | @sbindra-ai | ⬜ |
| **Thu** | 1.4: Create seeding guide | @sbindra-ai | ⬜ |
| **Fri** | 1.5: Unit tests for seed_db | @sbindra-ai | ⬜ |

### Week 2: Phase 2

| Day | Task | Owner | Status |
|-----|------|-------|--------|
| **Mon** | 2.1: Extend `prompts.py` | @sbindra-ai | ⬜ |
| **Tue** | 2.2: Update `/ask` endpoint | @sbindra-ai | ⬜ |
| **Wed** | 2.3: Enhance `vector_utils.py` | @sbindra-ai | ⬜ |
| **Thu** | 2.4: Unit tests for Gemini | @sbindra-ai | ⬜ |
| **Fri** | 2.5: Update architecture docs | @sbindra-ai | ⬜ |

---

## 🔗 DEPENDENCIES & BLOCKERS

### Prerequisites (Blocking)
- ❌ **Database Connection String** (DATABASE_URL)
  - Assigned to: @samisingh (Ops)
  - Impact: Seed_db.py cannot run without DB
  - Workaround: Local PostgreSQL + pgvector for dev testing

- ❌ **GEMINI_API_KEY** in `.env`
  - Status: May already be present (check .env file)
  - Impact: Embedding generation and Gemini synthesis
  - Workaround: Can use local embeddings only (reduced quality)

### Nice-to-Have (Non-blocking)
- ✅ pgvector Python library (can add to requirements)
- ✅ Additional Shabad data (can use existing 3 shabads for MVP demo)

---

## ✅ SUCCESS CRITERIA

### Objective 1: Data Pipeline
- [ ] `seed_db.py` successfully reads JSON with zero errors
- [ ] All 3 test shabads get embeddings (Gemini or fallback)
- [ ] Database table `shabads` contains 3 rows with vectors
- [ ] No data loss during insertion
- [ ] Execution time logged & reasonable (< 5 min for 3 items)

### Objective 2: Gemini Synthesis
- [ ] `/ask` endpoint returns structured JSON response
- [ ] Response includes: `response` (AI text), `shabad`, `query`
- [ ] Persona-specific guidance tone evident in response
- [ ] Error cases handled gracefully (API timeout, rate limit)
- [ ] Integration tests pass with mock Gemini responses

---

## 📝 NOTES & CONVENTIONS

### Code Organization
- All prompts centralized in `server/prompts.py`
- Environment variables documented in `.env.example`
- Error messages logged with context (`[module_name]`)
- Database operations use batch commits (performance)

### Persona Implementation
- **Child**: Simple, reassuring, metaphor-based language
- **Teen**: Relatable, direct, acknowledges modern challenges
- **Adult**: Philosophical, nuanced, scripture-based reasoning

### Testing Strategy
- Unit tests for each new function
- Mock external APIs (Gemini, DB) in tests
- Test data fixtures in `tests/fixtures/`

---

## 🚀 NEXT IMMEDIATE ACTIONS

1. **Confirm** DATABASE_URL with @samisingh (or setup local dev DB)
2. **Create** `server/prompts.py` with persona templates
3. **Enhance** existing `seed_db.py` with error handling & logging
4. **Update** `requirements.txt` with missing dependencies
5. **Test** seed_db.py locally with test data
6. **Create** Gemini synthesis function in `server/app.py`
7. **Test** end-to-end flow: query → retrieval → synthesis

---

## 📞 COMMUNICATION

**Team Sync**:
- Daily standup: 10 AM (share blocking issues)
- PR review: 24-hour turnaround
- Document updates: After each significant change

**Document Updates**:
- Update [TASK_ASSIGNMENTS.md](TASK_ASSIGNMENTS.md) status daily
- Update this plan weekly with new findings
- Link to test results in PR descriptions

