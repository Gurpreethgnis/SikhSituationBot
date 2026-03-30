# Gurbani grounding and SikhiToTheMax (operators)

This note supports [Issue #49](https://github.com/Gurpreethgnis/SikhSituationBot/issues/49): users must see scripture text that matches the database row tied to each `shabad?id=` link, not model-invented pangtis or wrong Ang/Raag prose.

## Source of truth

- **Retrieval**: Shabads are stored with `gurmukhi`, `english_translation`, `romanization`, and `source` (e.g. `SGGS Ang {n}`) from BaniDB during ingest (`server/bulk_ingest_live.py`).
- **Parmaan mode**: The API prepends a **verbatim** markdown section built on the server (`server/gurbani_display.py`). The LLM only adds theme commentary and suggestions—no duplicate scripture lines.
- **Guidance mode**: Prompts require copying the primary shabad verbatim. If checks fail, the pipeline **retries once** with stricter instructions, then **repairs** the reply by inserting the canonical primary shabad before `[SUGGESTIONS]` if needed.

## BaniDB vs SikhiToTheMax

The bot’s English strings come from BaniDB steek fields (bdb/ms/ssk ordering in ingest). **SikhiToTheMax may show different on-page translations** (e.g. other translators). That does **not** mean the response is hallucinated: the **shabad id** in the URL is authoritative, and the text shown in the app is the stored database string. Operators should not assume pixel-perfect match with STTM’s default English line.

## Metadata (Ang, Raag)

- Models must not invent **Ang** numbers. Grounding checks that any `Ang N` mentioned in the reply appears in at least one retrieved shabad’s `source` string.
- Do not present a **Raag/Mehla header alone** as if it were the full shabad when the context only contained that line—prompts instruct the model to say so and point to STTM.

## Re-ingest / bad rows

If a row has suspiciously short `gurmukhi` or `english_translation`, re-run bulk ingest or fix the row in admin. Embeddings and RAG quality depend on full verse text from BaniDB.

## Parmaan search quality (Raag/Mehla headers)

BaniDB shabad ids include **section headers** (e.g. "Aasaa, Fifth Mehla") that are not full hymns. Those rows are flagged at ingest (`is_header_only`, `verse_count`, `content_length` in `server/models.py`) and **skipped on new bulk ingest** when detected. Parmaan discovery (`/api/parmaans/*`, Parmaan chat retrieval) runs vector search with `exclude_parmaan_low_quality=True`: rows with `is_header_only` set, or below minimum Gurmukhi/English length, are filtered out. See `server/gurbani_content_quality.py` and `server/retrieval.py`.

**Existing databases:** run `cd server && python backfill_shabad_quality.py` after deploying the migration so header stubs are flagged. Postgres hosts get new columns via startup migration in `server/app.py` (same pattern as `llm_settings`).

## Related code

- `server/gurbani_display.py` — canonical markdown, substring checks, Ang allow-list.
- `server/prompts.py` — `SYSTEM_PROMPT` Gurbani accuracy section; Parmaan commentary-only instructions.
- `server/llm_synthesis.py` — Parmaan prefix, guidance retry + `ensure_guidance_grounded`.
