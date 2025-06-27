# EncoreProAI Test Suite

## Overview

This test suite validates all core services with real connections and data. No mocks are used - tests run against actual PostgreSQL, Cube.js, and OpenAI services.

## Running Tests

### Using Docker Compose (Recommended)

```bash
# Run all tests
./test.sh

# Run only unit tests (fast)
./test.sh unit

# Run only integration tests
./test.sh integration

# Run tests for specific service
./test.sh cube      # CubeService tests
./test.sh entity    # EntityResolver tests
./test.sh concept   # ConceptResolver tests
./test.sh time      # TimeResolver tests

# Run with coverage report
./test.sh coverage
```

### Environment Variables

Set these in your `.env` file or export them:

- `CUBE_URL`: URL to your Cube.js instance (required for Cube tests)
- `CUBE_SECRET`: Cube.js secret for JWT generation (required for Cube tests)
- `OPENAI_API_KEY`: OpenAI API key (required for LLM tests)
- `TENANT_ID`: Tenant ID for testing (defaults to 'test_tenant')

## Test Structure

```
tests/
├── conftest.py              # Pytest fixtures and configuration
├── test_cube_service.py     # CubeService tests
├── test_entity_resolver.py  # EntityResolver tests
├── test_concept_resolver.py # ConceptResolver tests
├── test_time_resolver.py    # TimeResolver tests
└── test_integration.py      # Integration tests
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)
- Fast tests that don't require external services
- Test pure logic like score transformation, caching, etc.

### Integration Tests (`@pytest.mark.integration`)
- Tests that require real database or API connections
- May be slower but test real behavior

### Service-Specific Markers
- `@pytest.mark.requires_cube`: Requires Cube.js connection
- `@pytest.mark.requires_openai`: Requires OpenAI API key
- `@pytest.mark.slow`: Tests that take longer to run

## What's Tested

### CubeService
- JWT token generation
- Real Cube.js connection and queries
- Error propagation (fail fast)
- Time dimension queries

### EntityResolver
- PostgreSQL trigram similarity search
- Score transformation algorithm
- Disambiguation string generation
- Tenant isolation
- Cross-type entity lookup

### ConceptResolver
- Cached concept mappings
- LLM-based concept resolution
- Schema summarization
- High-confidence result caching

### TimeResolver
- Cached time patterns
- LLM-based time parsing
- Date range parsing
- Theater-specific contexts

### Integration Tests
- Database setup verification
- Full query flow (text → entities → concepts → time → Cube.js)
- Ambiguity handling
- Entity population script

## No Mocks Philosophy

Following our "fail fast" approach:
- Tests use real connections
- Errors propagate naturally
- No artificial test scenarios
- Real data from actual services

## Troubleshooting

### PostgreSQL Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose -f docker-compose.test.yml ps

# View PostgreSQL logs
docker-compose -f docker-compose.test.yml logs postgres
```

### Cube.js Connection Issues
- Verify `CUBE_URL` and `CUBE_SECRET` are correct
- Check if Cube.js is running and accessible
- Tests will skip if not configured

### OpenAI API Issues
- Verify `OPENAI_API_KEY` is valid
- Check API quotas and limits
- Tests will skip if not configured