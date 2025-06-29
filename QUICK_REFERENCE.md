# EncoreProAI - Quick Reference Guide

Your one-stop guide for everything that actually works, including setup, commands, and troubleshooting.

## 🚀 Setup

```bash
# 1. Clone and navigate
cd encoreproai

# 2. Create .env file with required variables
cp .env.example .env
# Edit .env and add:
CUBE_URL=https://ivory-wren.aws-us-east-2.cubecloudapp.dev
CUBE_SECRET=<your-secret>
OPENAI_API_KEY=<your-key>
DEFAULT_TENANT_ID=yesplan

# 3. Start services
docker-compose up -d

# 4. Verify PostgreSQL is healthy
docker-compose ps
```

## 💻 What's Actually Working Right Now

### 1. TicketingDataCapability ✅
```python
# This works great!
from capabilities.ticketing_data import TicketingDataCapability
from models.capabilities import TicketingDataInputs

capability = TicketingDataCapability()
result = await capability.execute(TicketingDataInputs(
    session_id="test",
    tenant_id="yesplan",
    user_id="user123",
    query_request="Show me top 5 productions by revenue",
    measures=["ticket_line_items.amount"],
    dimensions=["productions.name"],
    limit=5
))
```

**Features that work**:
- Basic queries ✅
- Pagination (offset/limit) ✅
- Total count ✅
- Hierarchical data (multiple dimensions) ✅
- High cardinality handling ✅
- Natural language translation ✅
- Complex filters ✅
- Time intelligence ✅
- Multi-fetch ❌ (has granularity bug)

### 2. Entity Resolution ✅
```python
from services.entity_resolver import EntityResolver

resolver = EntityResolver()
candidates = await resolver.resolve("Chicago", "production", "yesplan")
# Returns both Broadway and Tour versions
```

### 3. Docker Setup ✅
```bash
# Start database
docker-compose up -d postgres

# Run tests
docker-compose run --rm test python -m pytest tests/ticketing/test_all_features.py -v

# Test individual capability
docker-compose run --rm test python capabilities/ticketing_data.py
```

## What's NOT Working

### 1. EventAnalysisCapability ❌
- Code exists but doesn't use entity IDs properly
- Not integrated with orchestrator

### 2. Full Orchestration ❌
- LangGraph structure exists
- Not fully connected or tested

### 3. ChatCapability ❌
- Implementation exists
- Not integrated or tested

## 🔧 Troubleshooting

### Tests Timing Out?
```bash
# Run specific test file instead
docker-compose run --rm test python -m pytest tests/ticketing/test_all_features.py -v
```

### PostgreSQL Connection Issues?
```bash
# Check if PostgreSQL is running
docker-compose ps

# Note: PostgreSQL runs on port 5433 (not 5432)
psql -h localhost -p 5433 -U encore -d encoreproai
```

### Multi-fetch Failing?
See [KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md#1-multi-fetch-granularity-error) for the granularity bug workaround.

## 🎯 Common Tasks

### Running Tests
```bash
# Best approach - run specific test file
docker-compose run --rm test python -m pytest tests/ticketing/test_all_features.py -v

# Run all tests (warning: may timeout)
docker-compose run --rm test python -m pytest tests/ -v

# Test individual capability directly
docker-compose run --rm test python capabilities/ticketing_data.py
```

### Debugging
```bash
# Check logs
docker-compose logs -f postgres
docker-compose logs test

# Access PostgreSQL
docker-compose exec postgres psql -U encore -d encoreproai

# Check entity counts
docker-compose exec postgres psql -U encore -d encoreproai -c "SELECT entity_type, COUNT(*) FROM entities GROUP BY entity_type;"

# Test Cube.js connection
curl -H "Authorization: Bearer YOUR_TOKEN" https://ivory-wren.aws-us-east-2.cubecloudapp.dev/cubejs-api/v1/meta
```

## 📦 Code Examples

### Query Production Revenue
```python
from capabilities.ticketing_data import TicketingDataCapability
from models.capabilities import TicketingDataInputs

capability = TicketingDataCapability()
result = await capability.execute(TicketingDataInputs(
    session_id="test",
    tenant_id="yesplan",
    user_id="user123",
    query_request="Show revenue for Chicago productions",
    measures=["ticket_line_items.amount"],
    dimensions=["productions.name"],
    filters=[{
        "member": "productions.name",
        "operator": "contains",
        "values": ["Chicago"]
    }]
))

for data_point in result.data:
    print(f"{data_point.dimensions['productions.name']}: ${data_point.measures['ticket_line_items.amount']:,.0f}")
```

### Resolve Ambiguous Entities
```python
from services.entity_resolver import EntityResolver

resolver = EntityResolver()
candidates = await resolver.resolve("Chicago", "production", "yesplan")
# Returns: [Chicago (Broadway), Chicago (Tour)]
```

## 📝 Notes

- **Status Details**: See [CURRENT_STATE.md](docs/CURRENT_STATE.md)
- **Known Issues**: See [KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md) 
- **Architecture**: See [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Development**: See [TODO.md](docs/TODO.md)