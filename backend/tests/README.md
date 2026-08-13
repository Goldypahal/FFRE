# FFIRE Backend Tests

This directory contains automated tests for the FFIRE backend service.

## Test Structure

- `conftest.py`: Shared test fixtures and configuration
- `test_main.py`: Tests for the main API endpoints
- `test_graph.py`: Tests for the LangGraph reasoning engine
- `test_models.py`: Tests for the database models
- `test_guardrails.py`: Tests for the validation/guardrail logic
- `test_rules.py`: Tests for the rule-based fraud detection
- `test_vector_db.py`: Tests for the vector database integration
- `test_database.py`: Tests for database connectivity and setup

## Running Tests

To run all tests:
```bash
pytest
```

To run tests with coverage:
```bash
pytest --cov=backend --cov-report=html
```

To run specific test files:
```bash
pytest tests/test_main.py
```

To run tests by marker:
```bash
pytest -m unit
```

## Test Environment

The tests use an in-memory SQLite database for isolation, so no external database setup is required.

Mock objects are used for external dependencies like:
- LLM API calls (OpenAPI/Claude)
- External API services (KYC/AML)
- Vector database connections

## Adding New Tests

When adding new tests:
1. Place them in the `tests/` directory with a name starting with `test_`
2. Use the `client` fixture for API endpoint tests
3. Use the `db_session` fixture for database tests
4. Use appropriate mocking for external dependencies
5. Follow the existing test naming and structure conventions