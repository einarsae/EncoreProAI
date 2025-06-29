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

## Current Status: TicketingDataCapability 100% Complete

## Latest Updates (December 2024)

### TicketingDataCapability Improvements
- ✅ **Fixed multi-fetch bug**: Updated prompts to handle granularity correctly
- ✅ **All 9/9 features working**: Multi-fetch, pagination, hierarchical data, etc.
- ✅ **Code cleanup**: Reduced from 853 to 674 lines (21% reduction)
  - Removed unused CubeQuery class
  - Removed unused methods (_describe_query, _extract_key_findings)
  - Moved test function to separate file

### Documentation Consolidation
- Reduced from 16 files to 5 core documentation files
- Archived 12 redundant files to docs/archive/
- Created consolidated API_REFERENCE.md
- Cleaned up test files in root directory

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
- ❌ EventAnalysisCapability NOT IMPLEMENTED

#### Current State (main branch)
- Concept resolution moved to orchestrator (on-demand)
- No separate resolve_concepts or resolve_time nodes
- TicketingDataCapability now:
  - Uses LLM to generate sophisticated Cube.js queries
  - Supports ALL Cube features (compareDateRange, nested filters, drilldowns, etc.)
  - Provides query descriptions and key findings
  - Properly aligned with actual Cube.js schema
  - 10/11 tests passing
  - Uses exact entity IDs for filtering

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
- Branch: ticketingdata
- Main branch: main
- Recent changes: Fixed multi-fetch bug, cleaned up code, consolidated docs

---

## Ready to Continue!

### Immediate Priority
Complete EventAnalysisCapability with proper ID-based filtering. The TicketingDataCapability is now 100% complete (all 9/9 features working) and provides the data foundation.

### Remember
- Check docs/CURRENT_STATE.md for latest status
- Update existing docs, don't create new ones
- Reference docs/archive/ content is outdated
- All tests should use Docker: `docker-compose run --rm test`