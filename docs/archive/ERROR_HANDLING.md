# EncoreProAI - Error Handling Strategy

## Philosophy: Sparse and Honest

**Fail fast, fail honestly, fail loudly.** Better to see real errors than hide problems behind generic messages.

## What We DON'T Do

❌ **Defensive Programming**
```python
# DON'T:
if frame and frame.entities and len(frame.entities) > 0:
    for entity in frame.entities:
        if entity:
            # Check everything exists

# DO:
for entity in frame.entities:  # Let it fail if None
    resolve(entity)           # Let it fail if missing
```

❌ **Generic Error Messages**
```python
# DON'T:
try:
    result = await some_operation()
except Exception:
    return "An error occurred"  # Useless!

# DO:
result = await some_operation()  # Let the real error bubble up
```

❌ **Silent Failures**
```python
# DON'T:
try:
    entity = await resolve_entity(text)
except:
    entity = None  # Hiding the problem
    
# DO:
entity = await resolve_entity(text)  # Fail loudly
```

## What We DO: Minimal Boundaries

### 1. API Endpoint (Outer Boundary)
```python
@app.post("/query")
async def query(request: QueryRequest):
    request_id = str(uuid.uuid4())[:8]
    logger.info(f"[{request_id}] Query: {request.query[:100]}")
    
    try:
        result = await orchestrator.process(request.query)
        logger.info(f"[{request_id}] Success")
        return {"success": True, "data": result, "request_id": request_id}
    except Exception as e:
        logger.error(f"[{request_id}] Failed: {e}")
        return {"success": False, "error": str(e), "request_id": request_id}
```

### 2. Network Calls (External Boundary)
```python
async def query_cube(self, measures, dimensions, filters, tenant_id):
    """Only catch network-specific timeouts"""
    token = self.generate_token(tenant_id)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{self.cube_url}/cubejs-api/v1/load",
            headers={"Authorization": f"Bearer {token}"},
            json={"measures": measures, "dimensions": dimensions, "filters": filters}
        )
        response.raise_for_status()  # Let HTTP errors bubble up naturally
        return response.json()
```

### 3. Simple Loop Protection (No Try/Catch)
```python
async def orchestrate_node(state: AgentState) -> AgentState:
    # Simple guard - no exception handling
    if state.execution.loop_count > 10:
        state.core.final_response = {
            "error": "Query too complex - took more than 10 steps",
            "partial_results": state.execution.completed_tasks
        }
        state.routing.next_node = END
        return state
    
    # Let everything else fail naturally
    frame = get_current_frame(state)
    decision = await llm.orchestrate(build_context(state, frame))
    # ... rest of orchestration
```

## Benefits

1. **Real Stack Traces**: See exactly what failed and where
2. **Faster Debugging**: No hunting through generic error handlers
3. **Honest System**: Fails when it should, works when it can
4. **Less Code**: Fewer error handling paths to maintain
5. **Better Learning**: Understand actual failure modes from production

## When to Add Error Handling Later

Only add when you see these patterns in production:

- **Specific network issues** that need retry logic
- **LLM rate limiting** that needs backoff
- **Database connection pools** that need circuit breakers
- **User input validation** for security

## Logging Strategy

**Simple and informative:**
```python
import logging

logger = logging.getLogger(__name__)

# Good logging - context without catching
logger.info(f"Extracting frame for query: {query[:50]}...")
logger.info(f"Found {len(mentions)} mentions in frame")
logger.info(f"Orchestration loop {loop_count}: {decision.action}")

# Let errors log themselves through the API boundary
```

## Example: Full Service Implementation

```python
class EntityResolver:
    """Resolve entities with minimal error handling"""
    
    def __init__(self, db_pool):
        self.db_pool = db_pool
    
    async def resolve(self, text: str, entity_type: str) -> List[Entity]:
        """No try/catch - let database errors bubble up"""
        query = """
            SELECT id, name, similarity(name, $1) as score
            FROM entities 
            WHERE type = $2 AND similarity(name, $1) > 0.3
            ORDER BY score DESC
        """
        
        # No error handling - if DB fails, we want to know
        rows = await self.db_pool.fetch(query, text, entity_type)
        
        return [
            Entity(
                id=row['id'],
                name=row['name'],
                confidence=transform_score(row['score'])
            )
            for row in rows
        ]
```

## Summary

- **Two catch points**: API boundary + network calls
- **Everything else fails fast**: No defensive programming
- **Real errors bubble up**: With full stack traces
- **Simple loop protection**: Counter-based, not exception-based
- **Add complexity later**: When you see actual failure patterns

This gives you honest failures you can learn from, not mysterious errors that hide the real problems!