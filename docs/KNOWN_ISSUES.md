# Known Issues and Workarounds

## 🐛 Current Bugs

### 1. ~~Multi-fetch Granularity Error~~ ✅ FIXED
**Previous Issue**: LLM generated `"granularity": null` causing 400 errors

**Solution Implemented**: Updated prompts in `capabilities/ticketing_data.py` to clarify:
- For time grouping: Must include valid granularity ("day", "week", "month", etc.)
- For time filtering only: Omit granularity field entirely
- Never use `"granularity": null`

**Status**: RESOLVED - All multi-fetch tests passing

---

### 2. Test Timeouts
**Issue**: Many integration tests timeout after 2 minutes

**Affected Tests**:
- Full test suite (`pytest tests/`)
- Some orchestration tests

**Workaround**: Run specific test files instead:
```bash
docker-compose run --rm test python -m pytest tests/ticketing/test_all_features.py -v
```

---

### 3. ~~EventAnalysisCapability Implementation~~ ✅ COMPLETED
**Previous Issue**: Needed MVP implementation

**Solution**: Built simple 250-line implementation with:
- Structured output using Pydantic
- Progressive data requests
- Clear orchestrator hints

**Status**: MVP complete and tested

---

## ⚠️ Limitations

### 1. No Drilldown Support
**Issue**: Cube.js instance returns "drilldown is not allowed"

**Solution**: Use multiple dimensions instead:
```python
# Instead of drilldown
dimensions=["retailers.name", "sales_channels.name"]  # Hierarchical data
```

---

### 2. Memory Constraints
**High Cardinality Dimensions**:
- `ticket_line_items.customer_id`: Millions of values
- `ticket_line_items.city`: 50K+ values
- `ticket_line_items.postcode`: 50K+ values

**Impact**: Queries without limits can cause memory issues

**Solution**: LLM automatically adds limits when using these dimensions

---

## 🔧 Configuration Issues

### 1. Docker PostgreSQL Port
**Issue**: PostgreSQL exposed on port 5433 (not default 5432)

**Fix**: Use correct connection string:
```bash
postgresql://encore:secure_password@localhost:5433/encoreproai
```

---

### 2. Missing Environment Variables
**Common Missing Variables**:
- `CUBE_SECRET`: Required for JWT generation
- `DEFAULT_TENANT_ID`: Defaults to "yesplan"

**Check**: Run this to see what's missing:
```bash
docker-compose run --rm test env | grep -E "(CUBE|OPENAI|TENANT)"
```