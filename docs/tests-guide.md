# SikhSituationBot Testing Guide 🧪

This document serves as a comprehensive guide for running and understanding the test suite of the SikhSituationBot project. It is designed to help new developers and agents quickly pick up the testing workflow.

## 📂 Test Locations

The project maintains two main test directories:

1.  **`/tests`**: The primary test suite containing:
    -   `unit/`: Backend logic tests (Models, Prompts, RAG).
    -   `integration/`: Flask API and Database interaction tests.
    -   `e2e/`: End-to-end application workflow tests.
    -   `frontend/`: Component-level UI tests (currently requiring path resolution fixes).
2.  **`/server/tests`**: Backend-specific tests often co-located with server logic.
3.  **`/client/app/__tests__`**: Frontend application-level tests.

---

## 🚀 Test Execution Strategy

The tests are divided into two main categories to balance speed and coverage.

### 1. Critical Tests (Minimum Viability)
**Purpose:** To quickly ensure the application is functional at a basic level. These tests verify core connectivity (API endpoints) and ensure there are no catastrophic UI or logic errors that would prevent basic use.

- **Check Backend Health & Connectivity**:
  ```bash
  pytest tests/integration/test_app.py::test_health_check
  ```
- **Ensure Core Conversational Flow**:
  ```bash
  pytest tests/integration/test_app.py::test_ask_endpoint_success
  ```
- **Verify End-to-End Workflow**:
  ```bash
  pytest tests/e2e/test_complete_workflow.py
  ```
- **Basic UI Rendering**:
  ```bash
  cd client && npx jest ProseGurbaniSpacing.test.jsx
  ```

### 2. Full Scale Tests (Complete Coverage)
**Purpose:** Comprehensive verification of all edge cases, persona-specific logic, database seeding, and vector utility resilience. Run these before significant merges or releases.

#### Execution Order:
1.  **Backend Unit Tests**:
    ```bash
    pytest tests/unit/
    ```
2.  **Backend Integration & E2E**:
    ```bash
    pytest tests/integration/ tests/e2e/
    ```
3.  **Server-Specific Logic**:
    ```bash
    pytest server/tests/
    ```
4.  **Complete Frontend Suite**:
    ```bash
    cd client && npx jest
    ```

---

## 📝 Test Descriptions

| Category | Suite | Description |
| :--- | :--- | :--- |
| **Backend Unit** | `test_models.py` | Validates database schema and Shabad model methods. |
| **Backend Unit** | `test_prompts.py` | Ensures AI prompts are built correctly for different personas. |
| **Backend Unit** | `test_retrieval.py` | Tests the semantic search and vector retrieval logic. |
| **Backend Unit** | `test_gemini_synthesis.py` | Mocks Gemini API to verify response synthesis logic. |
| **Backend Integration** | `test_app.py` | Tests Flask endpoints, CORS, and response structures. |
| **Backend E2E** | `test_complete_workflow.py`| Simulates full user stories from query to AI response. |
| **Frontend** | `ProseGurbaniSpacing.test.jsx` | Verifies UI styling and spacing for Gurbani text. |
| **Frontend** | `Logo.test.jsx` | (Needs Fix) Validates Logo component rendering. |

---

## ⚠️ Known Issues

- **Import Paths in `tests/frontend`**: The tests in `tests/frontend/components` currently have incorrect relative import paths and may fail if not run from a specific context or updated.
- **Vector Utils Imports**: `tests/unit/test_vector_utils.py` may fail due to a function naming discrepancy (`_calculate_backoff_delay` vs `calculate_backoff_delay`) in the source.
- **Seed DB Failure**: Some tests in `test_seed_db.py` currently fail and require investigation into the seeding logic consistency.

---

> [!TIP]
> Always run tests with the `--tb=short` flag for cleaner output, and use `--maxfail=1` if you want to stop at the first internal error.
