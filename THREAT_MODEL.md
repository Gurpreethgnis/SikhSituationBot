# SikhSituationBot — Security Threat Model

This document maps the entry points and database touchpoints in SikhSituationBot, providing an analysis of the primary attack vectors and their current remediations.

## 1. Asset Inventory
*   **Primary Data**: Gurbani Corpus (PostgreSQL, ~25,000 Shabad rows).
*   **User Data**: Identity (Email, Name, Hash), Chat History, User Memories.
*   **Access Control**: JWT-based authentication (HS256) for regular and admin users.

## 2. External Entry Points
| Point | Input | Method | Potential Impact | Status |
| :--- | :--- | :--- | :--- | :--- |
| `/api/search` | `q` (query), `mode` | `GET` | SQLi / DoS | **SECURED** |
| `/api/admin/interactions` | `user_email` | `GET` | Info Leakage / SQLi | **SECURED** |
| `/api/shabad/<id>` | `shabad_id` (string) | `GET` | Blind SQLi | **LOW RISK (ORM)** |
| `/api/banidb/display` | `shabad_id` (int) | `GET` | External Auth Bypass | **SECURED** |

## 3. Attack Vector Analysis

### Vector A: "LIKE-Injection" via Search
*   **Threat**: An attacker uses `%` or `_` or `\` in Gurbani search queries to bypass filters or force broad scans (DoS).
*   **Remediation**: 
    1.  Recursive escaping via `sanitize_like_filter()` in `retrieval.py`.
    2.  Length and alphanumeric gate in `search_routes.py`.
    3.  ORM-only text matching (no raw strings).

### Vector B: SQLi via Admin Filter
*   **Threat**: An administrator account (compromised or malicious) uses the user-search filter to extract DB data via union or bypass.
*   **Remediation**:
    1.  Strict use of SQLAlchemy `ilike()` which uses bound parameters.
    2.  Escaping wildcards in `app.interactions`.

### Vector C: Malformed BaniDB Lookups
*   **Threat**: Injecting strings into library calls that interact with external DB providers.
*   **Remediation**: 
    1.  Explicit `int()` casting in `gurbani_display.py` before passing to library.

## 4. Current Risk Posture
*   **Critical SQL Injection**: **NONE**. All database queries use SQLAlchemy's parameter binding.
*   **Pattern Injection (LIKE)**: **Mitigated**. Patterns are escaped before execution.
*   **Denial of Service (Search)**: **Minimized**. Broad patterns are rejected at the route level.
