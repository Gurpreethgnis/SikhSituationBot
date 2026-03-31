# Privacy Contract — Cross-Session Memory

## What Is Stored

SikhSituationBot stores the following data for authenticated users:

### 1. Conversation Messages (`messages` table)
| Field | Description |
|-------|-------------|
| `content` | Full text of each user and assistant message |
| `role` | `user` or `assistant` |
| `persona` | `child`, `teen`, or `adult` |
| `language` | Response language code (e.g. `en`, `pa`) |
| `llm_provider` / `llm_model` | Which LLM generated the response |
| `was_fallback` | Whether the response was a fallback |
| `created_at` | Timestamp of the message |

### 2. Memory Facts (`user_memories` table)
| Field | Description |
|-------|-------------|
| `fact_type` | One of: `situation`, `preference`, `topic`, `entity` |
| `content` | Short factual sentence (max 500 chars) extracted by LLM |
| `importance` | 1–10 score; higher = more relevant in new conversations |
| `is_pinned` | User-pinned facts are always included in prompt context |
| `source_chat_id` | Which conversation the fact was extracted from |
| `created_at` | When the fact was first stored |

### 3. User Preferences (`users` table)
| Field | Description |
|-------|-------------|
| `memory_enabled` | Whether cross-session memory is active |
| `memory_retention_days` | How long memories and chats are kept (30–365 days) |
| `preferred_language` | Default response language |
| `preferred_persona` | Persona derived from birth year |
| `birth_year` | Year of birth (used for age-appropriate responses) |

---

## Retention Policy

| Default | Range | Notes |
|---------|-------|-------|
| **90 days** | 30 – 365 days | Configurable in Settings |

- **No indefinite storage**: the maximum retention is 365 days.
- **Chat messages** are purged when they exceed the user's retention window (checked on chat list access).
- **Memory facts** outside the retention window are excluded from prompt context (soft expiry).
- Admins cannot override per-user retention settings.

---

## Identity Binding

All stored data is keyed to the authenticated user's `id` (integer primary key in `users` table):

- **Conversations**: `chats.user_id` → `users.id`
- **Messages**: `messages.chat_id` → `chats.id` → `users.id`
- **Memory facts**: `user_memories.user_id` → `users.id`

Authentication is enforced via JWT bearer tokens (issued on login/register/OAuth). The `@require_auth` decorator validates the token and sets `request.user_id` on every protected route.

---

## How Data Is Deleted

### User-initiated deletion
| Action | Effect |
|--------|--------|
| **Delete individual memory** (`DELETE /api/memory/<id>`) | Soft-delete (`is_deleted = true`); excluded from all queries |
| **Clear all memories** (`POST /api/memory/clear`) | Soft-deletes all memory rows for the user |
| **Delete a chat** (`DELETE /api/chats/<id>`) | Hard-deletes the chat and all its messages (CASCADE) |
| **Disable memory** (Settings toggle) | Stops new memory extraction; existing memories remain but are not used in prompts |

### System-initiated deletion
| Trigger | Effect |
|---------|--------|
| **Retention window expiry** | Chats older than the user's `memory_retention_days` are purged on next chat-list access |
| **Account deletion** (admin) | Hard-deletes the user and all associated chats, messages, and memories (CASCADE) |

### What is NOT automatically deleted
- Soft-deleted memory rows (`is_deleted = true`) remain in the database but are excluded from all queries and prompt context. They will be hard-deleted if the user's account is deleted.

---

## No Cross-User Leakage

- Every database query that returns user data filters by `user_id` (enforced by the `@require_auth` decorator).
- There is no endpoint that allows one user to read, modify, or delete another user's data.
- Admin endpoints can view user lists and analytics but do not expose other users' memory facts or conversation content.

---

## Data Flow Summary

```
User sends chat message
       │
       ▼
  /ask endpoint (requires auth)
       │
       ├─► Message stored in messages table (keyed to chat → user)
       │
       ├─► LLM extracts 0–3 memory facts (if memory_enabled)
       │         │
       │         ▼
       │    Dedup check (fingerprint + DB unique constraint)
       │         │
       │         ▼
       │    Stored in user_memories (keyed to user_id)
       │
       ▼
  Next session: /api/threads/active returns latest chat
  Memory facts injected into LLM prompt context (within retention window)
```
