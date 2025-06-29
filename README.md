# EncoreProAI - Frame-Based AI Companion

## 🎭 Vision

An empathetic AI companion for live entertainment professionals that provides emotional support, data insights, and intelligent analysis through natural conversation.

## 🏗️ Architecture: Frame-Based Understanding

### Core Innovation: No Intent Routing

Instead of classifying queries into intent categories, we extract **semantic frames** containing:
- **Mentions**: Entities, concepts, time expressions, emotional context
- **Relations**: How mentions connect (same_as, applies_to, measured_in)
- **Metadata**: Confidence, emotional tone, complexity

The orchestrator makes intelligent decisions based on this rich semantic understanding.

### Single-Task Execution with Replanning

```
Query → Extract Frame → Resolve → Orchestrate → Execute ONE Task → Loop
        (complete understanding)      (uses frame)                    |
                                         ↑                           |
                                         |___________________________|
```

**Key Insight**: One task at a time, see results, adapt strategy. No predetermined plans!

## 📁 Project Structure

```
encoreproai/
├── docker-compose.yml     # PostgreSQL + pgvector only
├── .env.example          # CUBE_URL, CUBE_SECRET, OPENAI_API_KEY
├── services/             # Self-contained data access
│   ├── cube_service.py      # Direct HTTP to Cube.js with JWT
│   ├── entity_resolver.py   # PostgreSQL trigram similarity
│   ├── concept_resolver.py  # Hardcoded mappings for MVP
│   ├── time_resolver.py     # LLM-based parsing
│   └── memory_service.py    # PostgreSQL + pgvector
├── capabilities/         # Business logic wrappers
│   ├── base.py            # BaseCapability interface
│   ├── chat.py            # ChatCapability (CRITICAL!)
│   ├── ticketing_data.py  # TicketingDataCapability
│   └── event_analysis.py  # EventAnalysisCapability
├── workflow/             # LangGraph implementation
│   ├── nodes.py           # All workflow nodes
│   ├── state.py           # State definitions
│   └── graph.py           # Workflow definition
├── models/               # Pydantic v2 models
│   ├── frame.py          # Frame, Mention, Relation
│   ├── state.py          # AgentState and sub-states
│   └── capabilities.py   # Input/output models
└── tests/                # Real data tests ONLY
```

## 🚀 Key Features

### 1. Advanced Data Retrieval (WORKING ✅)
- **TicketingDataCapability**: Production-ready with 8/9 features
- LLM generates sophisticated Cube.js queries
- Multi-fetch for time comparisons
- Natural language understanding
- Pagination and hierarchical data support

### 2. Frame-Based Understanding (IMPLEMENTED ✅)
```python
Query: "Show me Chicago revenue trends"
Frame:
  entities: [{"text": "Chicago", "type": "production"}]
  concepts: ["revenue", "trends"]
  resolved_entities: [  # After resolution
    {"id": "prod_chicago_broadway", "name": "Chicago (Broadway)"},
    {"id": "prod_chicago_tour", "name": "Chicago (Tour)"}
  ]
```

### 3. Entity Resolution (WORKING ✅)
- PostgreSQL trigram similarity search
- Preserves ambiguity for orchestrator
- Real entity data from Cube.js
- Score-based ranking

### 4. In Development 🚧
- **EventAnalysisCapability**: Needs ID-based filtering
- **ChatCapability**: Emotional support implementation
- **Full Orchestration**: LangGraph workflow integration
- **Memory Learning**: Pattern recognition and adaptation

## 🛠️ Technology Stack

- **PostgreSQL + pgvector**: Entity resolution + vector memory
- **LangGraph**: Proven workflow orchestration  
- **Pydantic v2**: Typed data models
- **httpx**: Direct HTTP to Cube.js
- **OpenAI**: Frame extraction + orchestration + analysis
- **Docker Compose**: Local development

**What We DON'T Use:**
- ❌ Intent classification (using frames directly)
- ❌ Temporal workflows (future feature)
- ❌ Complex routing rules (orchestrator decides)

## 📊 Available Data

### Entity Types (Discovered via CubeMetaService)
- **Real Entities with data**: productions (495), payment_methods (138), price_bands (377), retailers (35), sales_channels (3), seating_plans (377), ticket_types (999)
- **Categorical Entities**: city (999), country (439), state (434), currency (1) - geographical/categorical dimensions
- **Empty Entities**: delivery_methods, performers
- **Disambiguation**: sold_last_30_days data, first/last dates for productions

### Cube.js Metrics
- **Revenue**: ticket_line_items.amount
- **Attendance**: ticket_line_items.quantity  
- **Dimensions**: productions.name, venues.name, ticket_line_items.city, etc.

## 📊 Current Implementation Status

### ✅ What's Working
- **TicketingDataCapability**: 🎉 ALL 9/9 features operational!
  - LLM-driven Cube.js query generation
  - Multi-fetch (fixed!), pagination, hierarchical data
  - Natural language understanding
- **Core Services**: 
  - CubeService with JWT auth
  - EntityResolver with ambiguity preservation
  - ConceptResolver with pattern matching
- **Infrastructure**: Docker, PostgreSQL + pgvector
- **Data Models**: Pydantic v2 with proper typing

### 🚧 In Progress
- **EventAnalysisCapability**: Needs ID-based filtering fix
- **Orchestration**: LangGraph structure exists, needs integration
- **ChatCapability**: Implementation exists, needs testing

### ❌ Not Yet Implemented
- Full memory learning system
- Multi-frame query handling  
- Production features (caching, retry, monitoring)

### 🐛 Known Issues
- ~~Multi-fetch fails when LLM generates `"granularity": null`~~ ✅ FIXED!
- Some integration tests timeout
- EventAnalysisCapability not using entity IDs properly

For detailed status, see [CURRENT_STATE.md](docs/CURRENT_STATE.md)

## 🎯 Project Goals

1. ✅ **Real data queries** - Works with actual Cube.js data
2. ✅ **Advanced query capabilities** - TicketingDataCapability with all features
3. 🚧 **Empathetic chat support** - Implementation exists, needs integration
4. 🚧 **Adaptive orchestration** - Structure built, needs completion
5. ❌ **Full system integration** - Components work individually, not together yet

## 🚀 Getting Started

```bash
# Setup
cd encoreproai
cp .env.example .env
# Add: CUBE_URL, CUBE_SECRET, OPENAI_API_KEY, DATABASE_URL

# Start PostgreSQL + pgvector
docker-compose up -d

# Install dependencies (use Docker for consistency)
docker-compose build test

# Run tests with Docker
docker-compose run --rm test python -m pytest tests/ticketing/test_all_features.py -v

# Check specific capability
docker-compose run --rm test python capabilities/ticketing_data.py
```

## 💬 Example Conversations

### Emotional + Data Query
```
User: "I'm feeling overwhelmed - which shows are underperforming?"

AI: "I understand this can feel overwhelming when you're trying to make 
    sense of all the data. Let me help break this down for you.
    
    Looking at the numbers, I can see that Chicago (Tour) and Hell's Kitchen 
    are currently performing below their venue capacity targets - Chicago Tour 
    is at 65% capacity vs the 80% benchmark, and Hell's Kitchen has seen a 
    15% decline in revenue over the past month.
    
    Would it help if I explained what specific factors might be contributing 
    to these trends?"

*Assumptions: Used 80% capacity as "good performance" benchmark, 
compared last 30 days of data*
```

### Ambiguous Query
```
User: "Show me Chicago numbers"

Frame Analysis:
- "Chicago" → Multiple candidates (Broadway, Tour)
- System preserves both options for orchestrator

AI: "I found data for both Chicago productions:
    - Chicago (Broadway): $2.1M revenue, 89% capacity 
    - Chicago (Tour): $485K revenue, 65% capacity
    
    The Broadway production is performing strongly while the tour 
    needs attention. Which would you like me to focus on?"
```

### Multi-Step Analysis
```
User: "Compare our top 3 shows by revenue and analyze their trends"

Orchestration Loop:
1. Frame: Need revenue data for ranking
2. Task 1: Get revenue for all shows
3. Frame + Results: Can now identify top 3  
4. Task 2: Get trend data for top 3 specifically
5. Frame + All Data: Ready for analysis
6. Task 3: Provide comparative trend analysis

AI: "Your top 3 shows by revenue are:
    1. Gatsby: $3.2M (↑ 12% month-over-month)
    2. Hell's Kitchen: $2.8M (↓ 8% month-over-month) 
    3. Chicago (Broadway): $2.1M (→ steady)
    
    Gatsby is your growth leader, Hell's Kitchen needs attention, 
    and Chicago Broadway provides reliable baseline revenue."
```

## 📚 Documentation

### Core Documentation
- [Architecture](docs/ARCHITECTURE.md) - System design and workflow
- [Services](docs/SERVICES.md) - Core service implementations
- [Capabilities](docs/CAPABILITIES.md) - Business logic components
- [Orchestration](docs/ORCHESTRATION.md) - Single-task execution pattern
- [Error Handling](docs/ERROR_HANDLING.md) - Fail-fast philosophy

### Key Features
- [TicketingData Features](docs/TICKETING_DATA_FEATURES.md) - Advanced Cube.js capabilities
- [ID-Based Filtering](docs/ID_BASED_FILTERING.md) - How entity IDs enable precision
- [Drilldowns](docs/DRILLDOWNS.md) - Hierarchical data exploration
- [Cube Query Principles](docs/CubeQueryPrinciples.md) - Query generation guide

### Implementation Guides
- [TODO](docs/TODO.md) - Implementation roadmap
- [Query Types](docs/QUERY_TYPES.md) - Understanding different queries
- [Glossary](docs/GLOSSARY.md) - Key terminology

## ⚠️ Critical Architecture Decisions

### Why Frame-Based Over Intent Routing?

**Intent Routing** (traditional):
```python
if intent == "DATA":
    route_to_data_capability()
elif intent == "ANALYSIS": 
    route_to_analysis_capability()
```
**Problems**: Rigid categories, can't handle nuanced queries, predetermined flows

**Frame-Based** (our approach):
```python
frame = extract_complete_semantic_understanding(query)
decision = orchestrator.decide_based_on_frame(frame)
```
**Benefits**: Handles any query naturally, adaptive behavior, no maintenance overhead

### Why Single-Task Execution?

**Multi-Step Planning** (traditional):
```python
plan = ["get_revenue", "identify_top_3", "analyze_trends"]
for task in plan:
    execute(task)  # Hope the plan was right
```

**Single-Task with Replanning** (our approach):
```python
while not complete:
    next_task = decide_based_on_current_state()
    result = execute(next_task)
    adapt_strategy_based_on_result()
```
**Benefits**: Adapts to unexpected results, more intelligent, simpler to debug

## 🛡️ Error Handling Philosophy

**Fail Fast, Fail Honestly:**
- Only catch at API boundaries and network calls
- Let real errors bubble up with stack traces
- No defensive programming or generic error messages
- Simple loop protection (max 10 steps)

```python
# Good:
@app.post("/query")
async def query(request):
    try:
        return await orchestrator.process(request.query)
    except Exception as e:
        return {"error": str(e)}  # Real error message

# Bad:
try:
    if frame and frame.mentions:
        for mention in frame.mentions:
            if mention:  # Defensive checks everywhere
                # ...
except:
    return "Something went wrong"  # Useless
```

## 📚 Documentation Structure

- **README.md** - This overview
- **ARCHITECTURE.md** - Detailed technical architecture
- **TODO.md** - Comprehensive 7-day implementation plan
- **ORCHESTRATION.md** - Single-task execution patterns
- **CAPABILITIES.md** - Capability specifications
- **SERVICES.md** - Self-contained service implementations
- **ERROR_HANDLING.md** - Sparse error handling strategy
- **QUERY_TYPES.md** - Query categories (descriptive, not routing)
- **TEST_QUERIES.md** - Real test scenarios
- **GLOSSARY.md** - Terminology definitions

---

**Built for live entertainment professionals who need both emotional support and data insights. Ships in one week. Working code > perfect architecture.**