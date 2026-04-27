# SikhSituationBot — Security Policy & Secure Coding Standards

This document outlines the security procedures and secure coding standards for the SikhSituationBot codebase.

## 1. Vulnerability Reporting
If you find a security vulnerability, please do NOT open a public issue. Instead, email the maintainers at `security@sikhbot.example.com` (placeholder) or open a private security advisory on GitHub.

## 2. Secure Coding Standards — Data Access

### A. Mandatory Use of SQLAlchemy ORM / Core
All database interactions MUST use SQLAlchemy's ORM or Core expression language. These tools provide built-in protection against SQL injection via automatic parameter binding.

*   **CORRECT**: `Shabad.query.filter_by(shabad_id=q).first()`
*   **CORRECT**: `Session.get(User, user_id)`
*   **FORBIDDEN**: Hand-rolling raw strings inside `db.session.execute("SELECT ...")`.

### B. Raw SQL & `text()` Blocks
If raw SQL is absolutely necessary (e.g., for schema extensions or complex performance tuning), you MUST use bound parameters. **NEVER** use f-strings or `.format()` inside `text()` calls.

*   **CORRECT**:
    ```python
    db.session.execute(text("SELECT * FROM shabads WHERE id = :id"), {"id": some_id})
    ```
*   **FORBIDDEN**:
    ```python
    # DO NOT DO THIS
    db.session.execute(text(f"SELECT * FROM shabads WHERE id = {some_id}")) # SQL INJECTION RISK
    ```

### C. LIKE-Injection Protection
When using `ilike` or `like` filters with user-provided search terms, the terms must be escaped to prevent Denial-of-Service or pattern-matching bypass.

*   **Mandatory Helper**: Use `retrieval.sanitize_like_filter()` before building the pattern.
*   Example:
    ```python
    from retrieval import sanitize_like_filter
    pattern = f"%{sanitize_like_filter(user_input)}%"
    query = Shabad.query.filter(Shabad.gurmukhi.ilike(pattern))
    ```

## 3. Input Validation
*   **Search Routes**: All `/api/search` queries are validated to ensure they are not purely wildcards.
*   **Admin Routes**: Any administrative lookups (emails, user IDs) must be strictly typed or sanitized before database lookup.
*   **BaniDB Integration**: All external IDs must be cast to strict integers via `int()` before being passed to library calls.

## 4. Automated Security Testing
The repo contains a dedicated security test suite in `server/tests/security/test_sql_injection.py`.
Run these tests regularly:
```bash
pytest server/tests/security/
```
These tests simulate common injection payloads (wildcards, regex complexity, auth bypass) to ensure no regressions are introduced.
