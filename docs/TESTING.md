# 🧪 Testing Guide

We prioritize high code quality through rigorous testing.

## 🛠️ Testing Stack

- **Framework**: `pytest`
- **Async Support**: `pytest-asyncio`
- **Mocks**: `pytest-mock`
- **Coverage**: `pytest-cov`

## 🏃 Running Tests

### Run All Tests
```bash
python -m pytest tests/ -v
```

### Run with Coverage
Generate a coverage report to see what lines are missed.
```bash
python -m pytest tests/ --cov=server --cov-report=term-missing
```

### Run Specific Module
```bash
python -m pytest tests/test_api/test_auth.py
```

---

## 📝 Writing Tests

### Test Structure
Tests are located in `tests/` and mirror the `server/` structure.

- `tests/conftest.py`: Global fixtures (DB session, Test Client).
- `tests/test_api/`: API endpoint tests.
- `tests/test_workers/`: Background worker logic tests.

### Example Test Case

```python
import pytest

@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

## 🔄 CI/CD Integration

Tests run automatically on every Pull Request via GitHub Actions.
Ensure all tests pass before merging!
