## Summary

This PR improves Parmaan text matching and disambiguation, adds **cross-session user memory** (issue #42), and ships related onboarding/auth and settings updates.

## Parmaan search and disambiguation

- **Phonetic / spelling normalization** for Latin queries vs STTM-style romanization (`server/parmaan_search_normalize.py`), wired into `find_shabads_by_text_match` with OR-per-token variants and AND across tokens.
- **Single text hit** automatically becomes the similarity anchor; **multiple hits** return a disambiguation response with candidate buttons (existing flow).
- **Gurmukhi** tokens are matched literally (no Latin variant expansion).

## Cross-session memory (#42)

- New **`UserMemory`** model and **`users.memory_enabled` / `memory_retention_days`**.
- Guidance-mode prompts receive a short **stored context** block from recent memories; **Parmaan** mode does not inject memory (discovery stays neutral).
- After successful Guidance turns (with persisted chat messages), a **Gemini flash-lite** pass may append 0–3 new facts (deduped).
- **API**: `GET/DELETE /api/memory`, `POST /api/memory/<id>/pin`, `POST /api/memory/clear`; `PATCH /api/auth/me` accepts memory fields.
- **Settings** UI: toggle memory, retention days, list/remove/clear memories.
- **Production**: run the migration script (see below) before or immediately after deploy.

## Onboarding / `/ask` gate

- Users without **`birth_year`** receive **403** with `code: birth_year_required` on `/ask` (enforced in `server/app.py`).
- Register/onboarding and test helpers updated accordingly.

## Ops: database migration

**Required on PostgreSQL** (Railway, Cloud SQL, etc.):

```bash
export DATABASE_URL='postgresql://USER:PASS@HOST:5432/DBNAME'
bash server/scripts/apply_postgres_migrations.sh
```

Or on Windows PowerShell:

```powershell
$env:DATABASE_URL = "postgresql://..."
.\server\scripts\apply_postgres_migrations.ps1
```

SQLite dev: new tables/columns appear on fresh `create_all()`; existing file DBs may need manual migration or recreate.

## Testing

- `PYTHONPATH=server python -m unittest tests.unit.test_parmaan_search_normalize tests.unit.test_user_memory tests.unit.test_prompts tests.unit.test_retrieval tests.unit.test_llm_synthesis_grounding`
- Integration / e2e: `tests/integration/test_app.py`, `tests/e2e/test_complete_workflow.py`, `tests/helpers/flask_test_auth.py`

## Checklist

- [ ] Run Postgres migration on staging/production
- [ ] Confirm `NEXT_PUBLIC_API_URL` or rewrites include `/api/memory` (see `client/next.config.mjs`)

Refs: #42
