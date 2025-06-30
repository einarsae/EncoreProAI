# EncoreProAI API Reference

This document consolidates all technical implementation details for services, capabilities, and orchestration.

## Table of Contents
1. [Services](#services)
2. [Capabilities](#capabilities)
3. [Orchestration](#orchestration)
4. [Query Types](#query-types)
5. [Error Handling](#error-handling)

---

## Services

### CubeService
**Status**: ✅ Working  
**Purpose**: Direct HTTP client to Cube.js with JWT authentication

```python
from services.cube_service import CubeService

service = CubeService(cube_url, cube_secret)
result = await service.query(
    measures=["ticket_line_items.amount"],
    dimensions=["productions.name"],
    filters=[],
    tenant_id="yesplan"
)
```

**Features**:
- JWT token generation with tenant isolation
- 30-second timeout
- Supports all Cube.js query parameters
- No retry logic (planned improvement)

### EntityResolver
**Status**: ✅ Working  
**Purpose**: PostgreSQL-based entity resolution with trigram similarity

```python
from services.entity_resolver import EntityResolver

resolver = EntityResolver()
candidates = await resolver.resolve("Chicago", "production", "yesplan")
# Returns: [
#   {"id": "prod_chicago_broadway", "name": "Chicago (Broadway)", "score": 0.85},
#   {"id": "prod_chicago_tour", "name": "Chicago (Tour)", "score": 0.82}
# ]
```

**Features**:
- Trigram similarity search
- Score transformation (0.3-0.7 → 0.5-1.0)
- Preserves ambiguity for orchestrator
- Includes metadata from Cube.js

### ConceptResolver
**Status**: ✅ Working  
**Purpose**: Pattern-based concept resolution with mem0 learning

```python
from services.concept_resolver import ConceptResolver

resolver = ConceptResolver()
result = await resolver.resolve("revenue", context)
# Returns: "ticket_line_items.amount"
```

**Features**:
- Base patterns for common concepts
- Memory integration for learned patterns
- LLM fallback for ambiguous cases

### CubeMetaService
**Status**: ✅ Working  
**Purpose**: Schema introspection and validation

```python
from services.cube_meta_service import CubeMetaService

meta = CubeMetaService(cube_url, cube_secret)
measures = await meta.get_all_measures()
dimensions = await meta.get_all_dimensions()
```

---

## Capabilities

All capabilities are self-contained, self-describing, and discovered dynamically at runtime.

### Capability System Features
- **Dynamic Discovery**: Capabilities are found and loaded at runtime
- **Self-Describing**: Each capability describes its purpose, inputs, outputs, and category
- **Generic Execution**: Single execution pattern works with all capabilities
- **Categories**: data, analysis, communication, planning, action
- **Help System**: Can generate user-friendly explanations of available capabilities

### TicketingDataCapability
**Status**: ✅ Working (9/9 features)  
**Category**: data
**Purpose**: Advanced data retrieval with LLM-driven query generation

```python
from capabilities.ticketing_data import TicketingDataCapability
from models.capabilities import TicketingDataInputs

capability = TicketingDataCapability()
result = await capability.execute(TicketingDataInputs(
    session_id="test",
    tenant_id="yesplan",
    user_id="user123",
    query_request="Show top 5 productions by revenue",
    measures=["revenue"],
    dimensions=["by show"],
    limit=5
))
```

**Working Features**:
1. ✅ Basic queries with measures/dimensions
2. ✅ Multi-fetch strategy (with granularity bug)
3. ✅ Pagination (offset/limit)
4. ✅ Total count for UI
5. ✅ Hierarchical data (multiple dimensions)
6. ✅ High cardinality handling
7. ✅ Natural language understanding
8. ✅ Complex filters (nested AND/OR)
9. ✅ Time intelligence

**Known Issues**:
- Multi-fetch generates `"granularity": null` causing errors

### EventAnalysisCapability
**Status**: ✅ MVP Complete  
**Category**: analysis
**Purpose**: Analyze data from TicketingDataCapability to provide insights

#### Current Implementation (MVP)
```python
from capabilities.event_analysis import EventAnalysisCapability
from models.capabilities import EventAnalysisInputs

capability = EventAnalysisCapability()
result = await capability.execute(EventAnalysisInputs(
    session_id="test",
    tenant_id="yesplan", 
    user_id="user123",
    analysis_request="How is Chicago performing?",
    data=data_from_tdc,  # Optional: pre-fetched data
    entities=[{"id": "prod_chicago_broadway", "name": "Chicago"}]
))
```

**Simple Version Features**:
- Basic LLM-driven analysis
- Progressive data requests (can ask for more data)
- Natural language insights
- Uses entity IDs for filtering

**Implementation Approach**:
```python
class EventAnalysisCapability(BaseCapability):
    """Minimal viable analysis - let LLM do the work"""
    
    async def execute(self, inputs: EventAnalysisInputs) -> EventAnalysisResult:
        if not inputs.data:
            # Need data first
            return EventAnalysisResult(
                analysis_complete=False,
                insights=[],
                orchestrator_hints={
                    "needs_data": True,
                    "description": f"Get data for {inputs.analysis_request}"
                }
            )
        
        # Simple prompt-based analysis
        analysis_prompt = f"""
        Analyze this data for: {inputs.analysis_request}
        Entities: {inputs.entities}
        Data: {inputs.data}
        
        Provide:
        1. Key insights (be specific and quantitative)
        2. Any concerns or anomalies
        3. Do you need more data? If yes, what specifically?
        """
        
        response = await self.llm.ainvoke(analysis_prompt)
        
        # Basic parsing
        needs_more = "need more data" in response.content.lower()
        
        return EventAnalysisResult(
            insights=[response.content],
            analysis_complete=not needs_more,
            orchestrator_hints={
                "needs_data": needs_more,
                "description": "Extract what data needed from response"
            }
        )
```

#### Future Enhancements (Add When Needed)

**Phase 2: Context Tools** (Add if seeing data request loops)
```python
# Pre-calculated summaries to prevent asking for non-existent data
class DataContextTool:
    async def get_top_values(dimension, measure, tenant_id):
        # Returns top 10 values for any dimension
        
class TimeRangeContextTool:
    async def get_range(tenant_id, entity_id=None):
        # Returns available date ranges
```

**Phase 3: Structured Analysis** (Add if LLM analysis too variable)
```python
# Structured prompts and response parsing
- Specific analysis types (trend, anomaly, comparison)
- Calculated metrics (growth rates, averages)
- Confidence scores
```

**Phase 4: Memory Integration** (Add if seeing repeated patterns)
```python
# Learn from successful analyses
- Store analysis patterns
- User preferences
- Common insights for entities
```

**Phase 5: Advanced Tools** (Add for sophisticated analysis)
```python
# Statistical analysis tools
- Anomaly detection algorithms
- Trend analysis
- Segmentation
- Predictive insights
```

**When to Add Each Enhancement**:
1. **Context Tools**: When you see >3 rounds of "no data exists" loops
2. **Structured Analysis**: When insights vary too much between runs
3. **Memory**: When same questions asked repeatedly (>10 times)
4. **Advanced Tools**: When LLM calculations prove inaccurate

**Key Design Principles**:
- Start simple, enhance based on real usage
- Let LLM do heavy lifting initially
- Add structure only when randomness hurts
- Every enhancement should solve a specific observed problem

### ChatCapability
**Status**: ✅ Fully Integrated  
**Category**: communication
**Purpose**: Emotional support and conversation

```python
from capabilities.chat import ChatCapability
from models.capabilities import ChatInputs, EmotionalContext

capability = ChatCapability()
result = await capability.execute(ChatInputs(
    message="I'm feeling overwhelmed with these numbers",
    emotional_context=EmotionalContext(
        support_needed=True,
        stress_level="high"
    ),
    conversation_history=[],
    user_context=UserContext(
        role="producer",
        organization="Broadway Theater"
    )
))
```

**Working Features**:
- ✅ Emotional support detection and response
- ✅ Context-aware conversation (theater industry)
- ✅ Claude Sonnet for nuanced responses
- ✅ Follow-up question generation
- ✅ Proper orchestrator routing
- ✅ Concise responses (2-3 sentences)

### Capability Registry
**Status**: ✅ Implemented  
**Purpose**: Dynamic capability discovery and management

```python
from capabilities.registry import get_registry

# Get registry instance
registry = get_registry()

# Get all capabilities
capabilities = registry.get_all_instances()

# Get capabilities by category
data_capabilities = registry.get_capabilities_by_category()["data"]

# Generate help text for users
help_text = registry.get_help_text()
print(help_text)
# Output:
# I can help you with:
# 
# **Analysis** - Analyze data to find patterns...
#   • Analyze ticketing data to identify trends...
#     For example: "How is Chicago performing?"
# 
# **Communication** - Chat, get support...
#   • Provide companionship, emotional support...
#     For example: "I'm feeling overwhelmed"
# ...

# Get structured summary
summary = registry.get_capabilities_summary()
```

**Adding New Capabilities**:
1. Create a new file in `capabilities/` directory
2. Inherit from `BaseCapability`
3. Implement `describe()`, `execute()`, `build_inputs()`, and `summarize_result()`
4. Declare its category in `describe()`
5. The registry will automatically discover it!

---

## Orchestration

**Status**: ✅ Fully integrated with dynamic capability discovery

### Workflow Structure
```
START → extract_frame → resolve_entities → orchestrate → execute → orchestrate → END
                                                   ↑                      |
                                                   |______________________|
```

### Dynamic Capability Discovery
The orchestrator discovers capabilities at runtime using `_build_capabilities_context()`:

```python
def _build_capabilities_context(self) -> str:
    """Build capabilities context dynamically"""
    capabilities_text = "\n\nAvailable Capabilities:"
    
    for name, capability in self.capabilities.items():
        description = capability.describe()
        capabilities_text += f"\n\n- {description.name}: {description.purpose}"
        # Add inputs, outputs, examples...
    
    return capabilities_text
```

**Benefits**:
- ✅ No hardcoded capability knowledge
- ✅ 100% routing accuracy
- ✅ Easy to add new capabilities
- ✅ Self-documenting system

### Key Concepts

#### Frame Extraction
Extracts semantic meaning from queries:
```python
Frame:
  entities: [{"text": "Chicago", "type": "production"}]
  concepts: ["revenue", "trends"]
  resolved_entities: [...]  # After resolution
```

#### Single-Task Execution
One capability at a time with continuous replanning:
```python
while not complete:
    task = decide_next_task(state)
    result = execute_capability(task)
    update_state(result)
```

---

## Query Types

### 1. Data Queries
**Examples**: "Show revenue for all productions"  
**Capability**: TicketingDataCapability  
**Status**: ✅ Working

### 2. Comparison Queries  
**Examples**: "Compare Q1 vs Q2"  
**Capability**: TicketingDataCapability (multi-fetch)  
**Status**: 🐛 Has granularity bug

### 3. Analysis Queries
**Examples**: "Which shows are underperforming?"  
**Capability**: EventAnalysisCapability  
**Status**: 🚧 Needs implementation

### 4. Support Queries
**Examples**: "I'm overwhelmed with these numbers"  
**Capability**: ChatCapability  
**Status**: 🚧 Not integrated

---

## Error Handling

### Philosophy: Fail Fast
- Only catch errors at API boundaries and network calls
- Let errors bubble up with full stack traces
- No defensive programming
- Simple loop protection (max 10 iterations)

### Error Locations
1. **Network Boundaries**: HTTP requests to Cube.js
2. **API Endpoints**: Top-level request handlers
3. **Database Operations**: Connection failures only

### What NOT to Catch
- Logic errors
- Validation failures  
- Missing data
- Type errors

```python
# Good - catch at boundary
try:
    response = await httpx.post(url, json=data)
    response.raise_for_status()
except httpx.HTTPError as e:
    logger.error(f"Cube.js request failed: {e}")
    raise

# Bad - defensive programming
if data and data.get('measures') and len(data['measures']) > 0:  # NO!
    # Just use the data directly
```

---

## Common Patterns

### Entity ID Filtering
Always use entity IDs, not names:
```python
# Good
filters = [{
    "member": "productions.id",
    "operator": "equals",
    "values": ["prod_chicago_broadway"]
}]

# Bad
filters = [{
    "member": "productions.name",
    "operator": "contains",
    "values": ["Chicago"]
}]
```

### Natural Language Translation
The LLM translates common terms:
- "revenue" → "ticket_line_items.amount"
- "attendance" → "ticket_line_items.quantity"
- "by show" → "productions.name"

### High Cardinality Protection
Automatically limit queries on:
- customer_id (millions of values)
- city/postcode (50K+ values)
- events with daily granularity

---

## Prompt Engineering Best Practices

### Current Approach
TicketingDataCapability has embedded prompts (~150 lines each) that work well.

### When to Extract Prompts
- **Complex prompts (>50 lines)**: Consider extraction to templates
- **Simple prompts (<50 lines)**: Keep embedded
- **Shared prompts**: Always extract

### Recommended Structure (Future)
```
prompts/
├── ticketing_data/
│   ├── query_generation.md
│   └── query_planning.md
└── shared/
    └── common_rules.md
```

### Loading Pattern
```python
def load_prompt(name: str) -> str:
    with open(f"prompts/{name}.md", "r") as f:
        return f.read()
```

### Recommendation
1. **Now**: Keep embedded (working fine)
2. **Later**: Extract when iterating on quality or sharing across capabilities
3. **Benefits**: Easier testing, version control, non-engineer access