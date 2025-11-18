# Testing Guide

## Overview

This project uses comprehensive automated testing to ensure code quality and reliability. We have 106 backend tests with 78% code coverage and counting.

## Backend Testing

### Technology Stack
- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting
- **pytest-asyncio**: Async test support
- **FastAPI TestClient**: API endpoint testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest backend/tests/api/test_fighters.py

# Run specific test class
uv run pytest backend/tests/api/test_fighters.py::TestFightersListEndpoint

# Run specific test
uv run pytest backend/tests/api/test_fighters.py::TestFightersListEndpoint::test_list_fighters_success
```

### Test Coverage

```bash
# Run tests with coverage report
uv run pytest --cov=backend

# Generate HTML coverage report
uv run pytest --cov=backend --cov-report=html

# Open coverage report in browser
open htmlcov/index.html
```

### Test Markers

Tests are organized with markers for selective execution:

```bash
# Run only API tests
uv run pytest -m api

# Run only integration tests
uv run pytest -m integration

# Skip slow tests
uv run pytest -m "not slow"

# Run unit tests only
uv run pytest -m unit
```

### Current Test Coverage

**Overall: 78% (1503/1795 statements)**

By Module:
- **Betting API**: 98% ✨
- **Rankings API**: 91% ✨
- **Main API**: 92% ✨
- **Events API**: 85% ✨
- **ESPN API**: 79%
- **Homepage API**: 79%
- **Fighters API**: 74%
- **Wordle API**: 64%
- **Query API**: 8% (needs tests)

### Test Structure

```
backend/tests/
├── __init__.py
├── conftest.py              # Test fixtures and configuration
├── api/
│   ├── __init__.py
│   ├── test_fighters.py     # 16 tests - Fighters API
│   ├── test_events.py       # 18 tests - Events API
│   ├── test_rankings.py     # 6 tests - Rankings API
│   ├── test_espn.py         # 4 tests - ESPN API integration
│   ├── test_betting.py      # 25 tests - Betting API
│   ├── test_homepage.py     # 22 tests - Homepage API
│   └── test_wordle.py       # 16 tests - Wordle API
└── services/                # (Future) Service layer tests
```

### Test Categories

#### Unit Tests
Fast tests that verify individual functions and endpoints work correctly:
- API endpoint responses
- Request parameter validation
- Response structure verification

#### Integration Tests
Tests that verify components work together:
- Data quality validation
- Pagination consistency
- End-to-end API flows

#### Slow Tests
Tests that make external API calls or are time-intensive:
- ESPN API integration
- Response time validation

## Frontend Testing (Coming Soon)

### Planned Technology Stack
- **Jest**: Testing framework
- **React Testing Library**: Component testing
- **Playwright**: E2E testing

### Planned Tests
- Component rendering tests
- User interaction tests
- API integration tests
- E2E user flows

## Continuous Integration

### GitHub Actions

Tests run automatically on:
- Every push to `main` or `develop`
- Every pull request
- Manual workflow dispatch

**Workflow includes:**
1. Backend tests with coverage
2. Frontend linting and build
3. Integration health checks
4. Coverage upload to Codecov

View workflow: `.github/workflows/tests.yml`

### CI Commands

```bash
# Same commands used in CI
uv run pytest backend/tests/ -v --cov=backend --cov-report=xml
cd frontend && npm run lint
cd frontend && npm run build
```

## Writing Tests

### Test Template

```python
"""Tests for [Module] API endpoints."""
import pytest
from fastapi import status


@pytest.mark.api
class Test[Module]Endpoint:
    """Tests for GET /api/[module]/ endpoint."""

    def test_[module]_success(self, client):
        """Test [description] returns 200 with valid data."""
        response = client.get("/api/[module]/")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "key" in data
        assert isinstance(data["key"], list)
```

### Best Practices

1. **Test Naming**: Use descriptive names that explain what is being tested
   - Good: `test_list_fighters_with_pagination`
   - Bad: `test_fighters`

2. **Arrange-Act-Assert**: Structure tests clearly
   ```python
   def test_example(self, client):
       # Arrange: Set up test data
       fighter_id = 123

       # Act: Perform action
       response = client.get(f"/api/fighters/{fighter_id}")

       # Assert: Verify results
       assert response.status_code == 200
   ```

3. **Test One Thing**: Each test should verify one specific behavior

4. **Use Fixtures**: Share common test data via conftest.py

5. **Mark Tests**: Use appropriate markers (@pytest.mark.api, @pytest.mark.slow)

6. **Handle Edge Cases**: Test error conditions, empty results, invalid inputs

7. **Don't Test Implementation**: Test behavior, not internal details

## Test Data

### Using Real Database
Tests currently use the production database (`data/mma.db`) which means:
- ✅ Tests verify actual data structure
- ✅ No mocking required
- ⚠️  Tests depend on database content
- ⚠️  Cannot run in CI without database

### Future: Test Fixtures
Consider creating test fixture database for CI:
```bash
# Create minimal test database
sqlite3 data/test.db < tests/fixtures/test_schema.sql
```

## Debugging Tests

### Run with Debug Output

```bash
# Show print statements
uv run pytest -s

# Show local variables on failure
uv run pytest -l

# Stop on first failure
uv run pytest -x

# Show detailed traceback
uv run pytest --tb=long
```

### Interactive Debugging

```python
# Add breakpoint in test
def test_example(self, client):
    response = client.get("/api/fighters/")
    import pdb; pdb.set_trace()  # Debugger will stop here
    assert response.status_code == 200
```

## Coverage Goals

### Current Progress
- ✅ Test infrastructure: Complete
- ✅ Core API tests: 78% coverage - Near 80% goal! ✨
- ✅ Betting API: Complete (98% coverage)
- ✅ Homepage API: Complete (79% coverage)
- ✅ Wordle API: Complete (64% coverage)
- ⬜ Remaining APIs: 2% to reach 80%
- ⬜ Frontend tests: Not started
- ⬜ E2E tests: Not started

### Next Steps to 80%+ Coverage

1. **Add Query API tests** (~10-15 tests, +10% coverage) - Would reach 88%+ ✨
2. **Improve Wordle/Fighters coverage** (~5-10 tests, +5% coverage) - Would reach 83%+

Estimated effort: 3-4 hours

## Troubleshooting

### Common Issues

**Import Errors**
```bash
# Ensure you're in project root
cd /path/to/mmaWebsite

# Install dependencies
uv sync
```

**Database Not Found**
```bash
# Verify database exists
ls -lh data/mma.db

# Create if missing
uv run python scripts/create_seed_db.py
```

**Tests Hanging**
```bash
# Kill any running servers
pkill -f "uvicorn"
pkill -f "run.py"

# Run tests with timeout
uv run pytest --timeout=60
```

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [GitHub Actions](https://docs.github.com/en/actions)

## Contributing

When adding new features:
1. ✅ Write tests first (TDD) or alongside code
2. ✅ Ensure tests pass locally before committing
3. ✅ Maintain or improve coverage percentage
4. ✅ Use appropriate test markers
5. ✅ Document complex test scenarios

## Test Results

```bash
# Latest test run
============================= test session starts ==============================
collected 106 items

backend/tests/api/test_betting.py .........................  [ 23%]
backend/tests/api/test_espn.py ....                          [ 27%]
backend/tests/api/test_events.py ..................          [ 44%]
backend/tests/api/test_fighters.py ................          [ 59%]
backend/tests/api/test_homepage.py ......................     [ 80%]
backend/tests/api/test_rankings.py ......                    [ 85%]
backend/tests/api/test_wordle.py ................            [100%]

======================= 106 passed in 113.52s (0:01:53) ========================
Coverage: 78% (1503/1795 statements)
```

---

**Last Updated**: November 17, 2025
**Status**: ✅ Backend testing infrastructure complete
