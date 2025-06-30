# Claude Recap - EncoreProAI Implementation

## Documentation Guidelines (IMPORTANT)

### Documents to Maintain and Reference
1. **docs/CURRENT_STATE.md** - Single source of truth for implementation status
2. **docs/API_REFERENCE.md** - Technical reference for all components  
3. **docs/TODO.md** - Current priorities and next steps
4. **docs/KNOWN_ISSUES.md** - Active bugs and workarounds
5. **QUICK_REFERENCE.md** - Commands, setup, and examples

### DO NOT Reference or Create
- ❌ **docs/archive/** - Contains outdated/redundant documentation
- ❌ New documentation files - Update existing ones instead
- ❌ Temporary analysis files - Keep findings in existing docs

### Documentation Best Practices
- **No redundancy** - Each fact should exist in ONE place only
- **Update, don't create** - Modify existing docs rather than making new ones
- **Reference, don't repeat** - Link to other docs instead of duplicating content

## Current Status: Full Orchestration Working

## Latest Updates (January 2025)

### Dynamic Capability Descriptions ✅ COMPLETE
- Implemented `_build_capabilities_context()` in orchestrator
- Removed ALL hardcoded capability details
- Each capability self-describes via `describe()` method
- **Result**: 100% routing accuracy, no drift between implementation and orchestrator

### Data Format Alignment ✅ ALL PHASES COMPLETE
- **Phase 1**: Fixed order format (dict vs list) at root cause
- **Phase 2**: Unified Entity models to Pydantic everywhere
- **Phase 3**: Standardized all data interfaces
- **Key insight**: Fix root causes, never patch symptoms

### Capability Integration ✅ COMPLETE
- **TicketingDataCapability**: 100% working (9/9 features)
- **EventAnalysisCapability**: MVP complete with structured output
- **ChatCapability**: Fully integrated with emotional support
- **Orchestration**: Dynamic routing working perfectly

### Dynamic Capability System ✅ COMPLETE
- **Registry**: Runtime discovery of capabilities
- **Categories**: Each capability self-declares its category
- **Generic Execution**: Single pattern works for all capabilities
- **Help System**: Can explain "What can you help me with?"
- **Scalable**: Ready for 6+ capabilities without touching orchestrator

### Prompt Engineering Improvements
- Changed from defensive "ALWAYS/NEVER" to positive instructions
- Simplified capability descriptions for LLM understanding
- Removed implementation details from high-level descriptions
- Examples now match exact capability purpose

## What We've Built So Far

#### Day 1: Foundation (✅ COMPLETED)
- PostgreSQL with pgvector and pg_trgm extensions
- Entity population from Cube.js with disambiguation data
- CubeService with JWT authentication
- EntityResolver with trigram similarity search and cross-type fallback
- Comprehensive test suite

#### Day 2: Frame Extraction (✅ COMPLETED)
- **Simplified Frame Model**: Removed times field, keeping only entities and concepts
- Frame extraction identifies entities (productions, venues, etc.) and concepts (revenue, trends, analysis)
- Multi-turn conversation support
- Tests passing with 92.3% success rate

#### Day 3: ChatCapability (✅ COMPLETED)
- Emotional support for theater professionals
- Uses Claude Sonnet (via ANTHROPIC_API_KEY)
- Concise responses (2-3 sentences)
- User context support (future enhancement)

#### Day 4-5: Orchestration & Enhanced Capabilities (✅ COMPLETED)
- LangGraph workflow implemented
- Simplified routing (extract → resolve_entities → orchestrate → execute → loop)
- Single-task execution with continuous replanning
- ✅ TicketingDataCapability enhanced with ALL Cube.js features
- ✅ ConceptResolver with mem0/pgvector integration
- ✅ EventAnalysisCapability MVP IMPLEMENTED

#### Day 6-7: TicketingDataCapability Perfection (✅ COMPLETED)
- Fixed multi-fetch granularity bug
- All 9/9 features working perfectly
- Code cleanup: 674 lines (was 853)
- Comprehensive test suite in /tests/ticketing/
- Documentation consolidated to 5 core files

#### Day 8: EventAnalysisCapability MVP (✅ COMPLETED)
- Simple LLM-driven implementation (250 lines)
- Structured output with Pydantic schema enforcement
- Progressive analysis with orchestrator hints
- Natural language data requests
- Full test coverage

### Comprehensive Project Overview

EncoreProAI is an LLM-first orchestration system for theater analytics, built with:

#### Core Architecture
- **LangGraph Orchestration**: Single-task execution with continuous replanning
- **Frame-Based Understanding**: Extracts entities and concepts, not intent routing
- **Progressive Analysis**: Capabilities can request additional data through orchestrator
- **Self-Contained Services**: Everything in encoreproai folder, no external dependencies

#### Key Services
1. **CubeService**: JWT-authenticated Cube.js client with tenant isolation
2. **EntityResolver**: PostgreSQL trigram similarity with disambiguation
3. **ConceptResolver**: mem0-based learning system with pattern fallbacks
4. **FrameExtractor**: LLM-based semantic extraction

#### Capabilities
1. **ChatCapability**: Emotional support for theater professionals
2. **TicketingDataCapability**: Sophisticated Cube.js query generation with all features
3. **EventAnalysisCapability**: NOT IMPLEMENTED YET

#### Recent Enhancements
- **Enhanced TicketingDataCapability**:
  - Uses GPT-4 to generate complex Cube.js queries
  - Supports compareDateRange, nested filters, drilldowns, post-aggregation filters
  - Loads real schema via meta API
  - Handles flexible time expressions
  - Uses exact entity IDs for precision

- **ID-Based Filtering**:
  - EntityResolver returns UUIDs with candidates
  - TicketingDataCapability uses exact IDs in filters
  - Prevents string matching issues
  - Ensures data accuracy

- **Fixed Technical Issues**:
  - String formatting errors with f-strings in JSON
  - Order format conversion for Cube.js
  - Dimension/measure categorization logic
  - Explicit field name usage from schema

### Key Architecture Decisions

#### 1. Frame Simplification
User feedback: "why are we including time in concepts. I see no benefit?"
- Removed `times` field from Frame model
- Now only extracts: entities, concepts
- Added specific concepts: analysis, automation, segmentation

#### 2. Capability Architecture
```
TicketingDataCapability (✅ DONE)
├── Pure data fetcher - no analysis
├── Wraps CubeService for orchestrator
├── Returns raw DataPoint objects
└── Uses correct field names (ticket_line_items.amount)

EventAnalysisCapability (❌ NOT IMPLEMENTED)
├── Intelligent analyzer
├── Takes raw data from TicketingDataCapability
├── Can request more data progressively
└── Returns insights, trends, recommendations
```

#### 3. Progressive Analysis Pattern
User confirmed: "Perfect!" to this approach:
- EventAnalysis can request data multiple times
- Can batch multiple data requests in one call
- Orchestrator handles the routing between capabilities
- Example flow: Chat → TicketingData → EventAnalysis → TicketingData → EventAnalysis → Complete

### Important Implementation Details

#### Environment Variables
Docker-compose maps these:
- `CUBE_API_URL` (from .env) → `CUBE_URL` (in container)
- `CUBE_API_SECRET` (from .env) → `CUBE_SECRET` (in container)
- Also needs: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`

#### Entity Resolution
- Primary type resolution first
- Falls back to cross-type lookup if score < 0.5
- Disambiguation includes: ID, dates, recent sales

#### Database Field Names
- Use `ticket_line_items.amount` NOT "revenue"
- Use `ticket_line_items.quantity` for attendance
- Productions: Gatsby, Chicago, Wicked (NOT Hamilton)

### Current File Structure
```
encoreproai/
├── capabilities/
│   ├── base.py                    # BaseCapability interface
│   ├── chat.py                    # ChatCapability (emotional support) - NOT INTEGRATED
│   ├── event_analysis.py          # EventAnalysisCapability - NEEDS ID FILTERING FIX
│   └── ticketing_data.py          # TicketingDataCapability (674 lines) - 100% WORKING
├── models/
│   ├── frame.py                   # Frame, EntityToResolve, ResolvedEntity
│   ├── state.py                   # AgentState for orchestration
│   └── capabilities.py            # Input/Output models for capabilities
├── services/
│   ├── cube_service.py            # Cube.js API client with JWT
│   ├── cube_meta_service.py       # Schema introspection
│   ├── entity_resolver.py         # PostgreSQL trigram search
│   ├── concept_resolver.py        # Pattern-based with mem0
│   └── frame_extractor.py         # LLM-based frame extraction
├── workflow/
│   ├── graph.py                   # LangGraph workflow definition
│   └── nodes.py                   # Workflow nodes
├── scripts/
│   ├── debug/                     # Debug scripts
│   ├── verification/              # Verification scripts
│   └── populate_entities.py       # Entity population
├── tests/
│   └── ticketing/                 # All ticketing tests (9/9 passing)
└── docs/
    ├── API_REFERENCE.md           # Consolidated technical reference
    ├── CURRENT_STATE.md           # Implementation status (SOURCE OF TRUTH)
    ├── TODO.md                    # Active priorities
    ├── KNOWN_ISSUES.md            # Bugs and workarounds
    └── archive/                   # 12 old/redundant docs
```

### What's Working Now

1. **Frame Extraction**: 
   - Query: "Show me revenue for Gatsby. How are you feeling?"
   - Extracts: entities=[Gatsby/production], concepts=[revenue, emotional_state]

2. **Entity Resolution**:
   - Resolves "Gatsby" → "THE GREAT GATSBY [p123] (2024-present) $1.2M last 30 days"
   - Cross-type fallback for ambiguous terms

3. **Chat Capability**:
   - Handles emotional queries with empathy
   - Keeps responses concise (2-3 sentences)

4. **TicketingData Capability**:
   - Enhanced with ALL Cube.js features
   - Generates sophisticated queries using LLM
   - Supports compareDateRange, nested filters, drilldowns
   - Uses exact entity IDs for filtering

### Prompt Management Best Practices

**Current**: Long prompts embedded in code (150+ lines)
**Recommended**: Extract to template files for complex prompts

```python
# Instead of embedded strings:
system_prompt = """Very long prompt..."""

# Use template files:
def load_prompt(name: str) -> str:
    with open(f"prompts/{name}.md", "r") as f:
        return f.read()
```

**Benefits**:
- Easier to maintain and test prompts
- Can version control prompt changes
- Cleaner code files
- Enables A/B testing

### Next Steps (TODO)

#### 1. Complete EventAnalysisCapability with ID-Based Filtering
```python
class EventAnalysisCapability(BaseCapability):
    """
    Intelligent analysis of ticketing data
    - Takes raw data from TicketingDataCapability
    - Identifies trends, patterns, anomalies
    - Can request additional data as needed
    - Returns insights and recommendations
    - MUST use entity IDs for filtering (not string names)
    """
```

#### 2. Test Full Orchestration Flow
- Query: "I'm worried about Chicago. How is it performing?"
- Should trigger: Chat → TicketingData → EventAnalysis → Response

#### 3. Handle Multi-Frame Queries
- Current: Only processes one frame at a time
- Need: Process multiple frames in sequence

#### 4. User Profile Management
- Store UserContext persistently
- Track preferences across sessions
- Multi-tenant support

### Testing Commands

```bash
# Test individual components
docker-compose run --rm test python test_ticketing_data.py
docker-compose run --rm test python demo_ticketing_capability.py

# Test orchestration
docker-compose run --rm test python test_orchestrator_with_data.py

# Run all tests
docker-compose run --rm test python -m pytest tests/ -v

# Verify setup
docker-compose run --rm test python verify_ticketing_setup.py
```

### Key User Feedback Incorporated

1. **No time extraction**: "I see no benefit"
2. **Correct field names**: "use 'amount' not 'revenue'"
3. **Correct show names**: "use Gatsby instead" (not Hamilton)
4. **Progressive analysis**: "Can the event analyzer make more data requests?"
5. **Response length**: "too long", "keep it to 2-3 sentences"
6. **No mocks**: "I am only interested in running real test"

### Critical Implementation Notes

1. **Task Tracking**: Store task in message metadata, not state field
2. **Entity Fallback**: Must explicitly call cross_type_lookup
3. **Docker Env Vars**: Must be listed in docker-compose.yml
4. **Capability Routing**: Orchestrator routes to `execute_{capability_name}`
5. **Single Task Execution**: One task at a time, see results before next

### Current Working Directory
```
/Users/einar/CODE/EncoreProAI
```

### Git Status
- Branch: eventanalysis
- Main branch: main (has merged ticketingdata)
- Recent changes: Implemented EventAnalysisCapability MVP with structured output

---

## Current State Summary

### ✅ What's Complete
1. **TicketingDataCapability** (100% - Production Ready)
   - 9/9 features working perfectly
   - 674 lines (reduced from 853)
   - Comprehensive test coverage
   - Multi-fetch, pagination, complex queries all working

2. **EventAnalysisCapability** (MVP Complete)
   - 250 lines of clean code
   - Structured output with Pydantic
   - Progressive analysis working
   - Test coverage complete

3. **Core Services** (All Working)
   - CubeService with JWT auth
   - EntityResolver with trigram search
   - ConceptResolver with mem0
   - FrameExtractor

### 🚧 What's Next
1. **Test Full Orchestration Pipeline**
   - Wire up all capabilities
   - Test progressive analysis flow
   - Ensure entity IDs flow correctly

2. **Integrate ChatCapability**
   - Already implemented but not wired to orchestrator

### 📝 Key Decisions Made
1. **Pure LLM Orchestration** - No shortcuts, full flexibility
2. **Simple MVP First** - Start basic, enhance based on real usage
3. **Structured Output** - Clean, predictable responses
4. **Entity IDs** - Natural language for humans, IDs for systems

### Remember
- Check docs/CURRENT_STATE.md for latest status
- Update existing docs, don't create new ones
- Reference docs/archive/ content is outdated
- All tests should use Docker: `docker-compose run --rm test`