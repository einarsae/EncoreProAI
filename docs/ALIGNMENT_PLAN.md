# Data Format Alignment Plan

## Current Issues

### 1. Order Field Format Chaos
- **Orchestrator generates**: Sometimes dict, sometimes list
- **TicketingDataInputs expects**: Dict format `{"field": "asc|desc"}`
- **CubeService converts to**: List format `[["field", "asc"]]` for Cube.js
- **Default values**: Inconsistent (None vs [])

### 2. Entity Resolution Format Mismatch
- **EntityResolver returns**: Dataclass `EntityCandidate`
- **Workflow expects**: Pydantic `EntityCandidate`
- **Conversion happens**: Every single request in workflow/nodes.py

### 3. Data Structure Inconsistencies
- **TicketingData returns**: List[DataPoint]
- **EventAnalysis expects**: Various formats (list, dict, string)
- **Multiple handlers**: For the same data

## Proposed Solutions

### Phase 1: Standardize Order Field (Immediate)
1. **Single source of truth**: Dict format `{"field": "direction"}`
2. **Conversion only at boundary**: CubeService converts to Cube.js format
3. **Clear documentation**: In orchestrator prompt and capability description
4. **Consistent defaults**: Always None, not empty list

### Phase 2: Unify Entity Models (Short-term)
1. **Use Pydantic everywhere**: Remove dataclass EntityCandidate
2. **Single model definition**: In models/frame.py
3. **Update EntityResolver**: Return Pydantic models directly
4. **Remove conversion code**: In workflow/nodes.py

### Phase 3: Standardize Data Flow (Medium-term)
1. **Define clear interfaces**: Between each component
2. **Single data format**: For capability outputs
3. **Remove adaptation layers**: Fix at source, not symptoms
4. **Type safety**: Enforce with Pydantic throughout

## Implementation Order

### 1. Fix Order Field (NOW)
```python
# In capabilities/ticketing_data.py line 541
order=query.get("order"),  # Remove default []

# In workflow/nodes.py - remove any order conversion
# Let CubeService handle Cube.js format conversion
```

### 2. Fix Entity Models (NEXT)
```python
# In services/entity_resolver.py
# Change return type to use Pydantic EntityCandidate
# Remove dataclass import and definition

# In workflow/nodes.py
# Remove the entire conversion loop (lines 137-150)
```

### 3. Document Expected Formats
```python
# In each capability's describe() method
# Be explicit about format expectations
# Show examples of exact format needed
```

## Benefits
1. **Reduced complexity**: Remove conversion code
2. **Better performance**: No repeated conversions
3. **Clearer errors**: Format issues caught at source
4. **Easier maintenance**: Single place to update formats

## Risks
1. **Breaking changes**: Need to update all tests
2. **Hidden dependencies**: Other code may rely on current formats
3. **Migration effort**: Need careful coordination

## Success Metrics
1. Zero format conversion functions
2. All components use same model classes
3. Clear error messages for format issues
4. No try-except blocks for format handling