# SikhSituationBot Test Suite

Comprehensive testing framework for the SikhSituationBot MVP application.

## 🏗️ Test Structure

```
tests/
├── __init__.py
├── conftest.py                    # Pytest configuration and fixtures
├── unit/                         # Unit tests
│   ├── test_seed_db.py          # Data pipeline tests
│   ├── test_vector_utils.py     # Embedding tests
│   ├── test_retrieval.py        # Vector search tests
│   ├── test_prompts.py          # Prompt engineering tests
│   └── test_models.py           # Database model tests
├── integration/                 # Integration tests
│   ├── test_api_endpoints.py    # Flask API tests
│   ├── test_database_ops.py     # Database operations
│   └── test_gemini_integration.py # Gemini API integration
├── e2e/                         # End-to-end tests
│   └── test_full_flow.py        # Complete user journey
├── frontend/                    # Frontend tests (Jest)
│   └── components/              # Component tests
└── fixtures/                    # Test data and mocks
    ├── sample_shabads.json
    ├── mock_responses.json
    └── test_database.db
```

## 🚀 Running Tests

### Prerequisites

1. **Install dependencies:**
   ```bash
   # Backend dependencies
   pip install -r server/requirements.txt

   # Frontend dependencies
   cd client && npm install
   ```

2. **Set up test environment:**
   ```bash
   # Copy test environment file
   cp .env.example .env.test

   # Edit .env.test with test-specific values
   # DATABASE_URL=sqlite:///tests/fixtures/test_database.db
   # GEMINI_API_KEY=test-key (for mocked tests)
   ```

### Run All Tests

```bash
# From project root
pytest tests/ -v --tb=short
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# End-to-end tests
pytest tests/e2e/ -v

# Frontend tests
cd client && npm test

# With coverage
pytest tests/ --cov=server --cov-report=html
```

### Run Single Test File

```bash
pytest tests/unit/test_seed_db.py -v
pytest tests/integration/test_api_endpoints.py -v
```

## 🧪 Test Categories

### Unit Tests
- **Purpose**: Test individual functions and modules in isolation
- **Mocking**: External dependencies (APIs, databases) are mocked
- **Coverage**: All utility functions, data processing, validation

### Integration Tests
- **Purpose**: Test component interactions and data flow
- **Scope**: API endpoints, database operations, external service calls
- **Database**: Uses test database with real schema

### End-to-End Tests
- **Purpose**: Test complete user journeys
- **Scope**: Frontend to backend integration
- **Environment**: Full application stack

### Frontend Tests
- **Purpose**: Test React components and user interactions
- **Framework**: Jest + React Testing Library
- **Coverage**: Component rendering, user events, state management

## 📊 Test Coverage Goals

- **Backend**: >90% coverage
- **Frontend**: >80% coverage
- **Integration**: All critical paths
- **E2E**: Happy path + error scenarios

## 🔧 Test Configuration

### Pytest Configuration (`pytest.ini`)

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --strict-markers
    --disable-warnings
    --tb=short
    -ra
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
    api: API-related tests
```

### Environment Variables

```bash
# Test-specific environment
TESTING=true
DATABASE_URL=sqlite:///tests/fixtures/test_database.db
GEMINI_API_KEY=test-key-for-mocking
FLASK_ENV=testing
```

## 🛠️ Writing Tests

### Unit Test Example

```python
import pytest
from unittest.mock import patch, MagicMock

def test_embedding_generation():
    """Test vector embedding generation."""
    with patch('vector_utils.genai') as mock_genai:
        # Arrange
        mock_result = MagicMock()
        mock_result.embedding = [0.1, 0.2, 0.3]
        mock_genai.embed_content.return_value = mock_result

        # Act
        result = get_embedding("test text")

        # Assert
        assert result == [0.1, 0.2, 0.3]
        mock_genai.embed_content.assert_called_once()
```

### Integration Test Example

```python
def test_ask_endpoint_integration(client, mock_db):
    """Test /ask endpoint with mocked database."""
    # Arrange
    test_data = {
        "query": "feeling anxious",
        "persona": "adult"
    }

    # Act
    response = client.post('/ask', json=test_data)
    data = response.get_json()

    # Assert
    assert response.status_code == 200
    assert 'response' in data
    assert 'shabad' in data
    assert data['persona'] == 'adult'
```

### Frontend Test Example

```jsx
import { render, screen, fireEvent } from '@testing-library/react';
import ChatInput from '../components/ChatInput';

test('handles user input and submission', () => {
  const mockOnSend = jest.fn();
  render(<ChatInput onSend={mockOnSend} />);

  const input = screen.getByPlaceholderText(/Share how you're feeling/);
  const button = screen.getByRole('button');

  fireEvent.change(input, { target: { value: 'I feel anxious' } });
  fireEvent.click(button);

  expect(mockOnSend).toHaveBeenCalledWith('I feel anxious');
});
```

## 🔍 Test Fixtures

### Sample Data (`fixtures/sample_shabads.json`)

```json
[
  {
    "shabad_id": "test-1",
    "gurmukhi": "ਤਪਤਿ ਮਾਹਿ ਠਾਢਿ ਵਰਤਾਈ ॥",
    "romanization": "tapat maahi thaadh varataaee ||",
    "english_translation": "In the midst of the burning heat, a cooling breeze has begun to blow.",
    "context_tags": ["anxiety", "peace", "calm"],
    "source": "SGGS Page 1",
    "recommended_persona": "any"
  }
]
```

### Mock Responses (`fixtures/mock_responses.json`)

```json
{
  "gemini_success": {
    "text": "This is a compassionate response about finding peace."
  },
  "gemini_error": {
    "error": "API quota exceeded"
  }
}
```

## 🚨 Common Issues & Solutions

### Database Connection Issues
```bash
# Ensure test database exists
python -c "from server.app import db; db.create_all()"
```

### API Mocking Issues
```python
# Use responses library for HTTP mocking
import responses

@responses.activate
def test_api_call():
    responses.add(responses.POST, 'https://api.example.com', json={'status': 'ok'})
    # Test code here
```

### Async Test Issues
```python
import pytest_asyncio

@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected
```

## 📈 CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r server/requirements.txt
      - name: Run tests
        run: pytest tests/ --cov=server --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## 📋 Test Checklist

### Before Committing
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] No linting errors
- [ ] Test coverage meets targets
- [ ] Documentation updated

### Before Deployment
- [ ] E2E tests pass
- [ ] Performance tests pass
- [ ] Security tests pass
- [ ] Load tests pass (if applicable)

## 🤝 Contributing

1. Write tests for new features
2. Update tests when refactoring
3. Maintain test coverage
4. Document test scenarios
5. Review test quality in PRs