# EncoreProAI - Implementation Strategy

## Critical Decision: 100% Self-Contained

**NO references to code outside this folder!** This ensures:
- Clean context for development
- No confusion between architectures
- Clear implementation boundaries
- Easy deployment and testing

## Architecture Overview

### 1. LangGraph Workflow
```
START → extract_frames → resolve_entities → orchestrate → END
                                                   ↑__________|
                                                 (loop until done)
```

- Time resolution: handled by capabilities when they need dates
- Concept resolution: done on-demand during orchestration

### 2. Core Services (Self-Contained)

```python
# services/cube_service.py
- Direct HTTP client to Cube.js
- JWT token generation for tenant isolation (from CUBE_SECRET env var)
- Simple query interface

# services/entity_resolver.py
- PostgreSQL with pg_trgm extension
- Type-aware resolution (production, venue, etc.)
- Score transformation (0.3-0.7 → 0.5-1.0)
- Returns ALL candidates for ambiguity

# services/concept_resolver.py
- mem0 integration with pgvector
- Pattern-based mapping with learning
- Maps business terms → Cube.js measures
- Learns from successful resolutions

# services/time_resolver.py (handled by capabilities)
- Each capability parses time when needed
- No separate time resolver service

# services/memory_service.py (via ConceptResolver)
- PostgreSQL + pgvector through mem0
- Pattern learning and recall
- User-specific corrections
```

### 3. Capabilities

```python
# capabilities/chat.py (CRITICAL)
- Emotional support and companionship
- Warm, empathetic responses
- Follow-up question generation

# capabilities/ticketing_data.py
- Uses CubeService for data access
- LLM decides query structure
- No hardcoded analysis methods

# capabilities/event_analysis.py
- Flexible analysis criteria
- LLM determines thresholds
- Pattern detection
```

### 4. Orchestration Pattern

**Single-Task Execution**: No separate planner!
- Orchestrator creates ONE task at a time
- Sees results and adapts dynamically
- Built-in replanning based on outcomes

## Implementation Order (ONE WEEK)

### Day 1: Foundation & Services
1. Docker environment with PostgreSQL + pgvector
2. Implement core services:
   - CubeService with JWT
   - EntityResolver with trigram
   - ConceptResolver with mapping
3. Test connections and basic queries

### Day 2: Resolution Pipeline
1. Frame extraction (complete semantic understanding with mentions + relations)
2. Entity resolution with ambiguity preservation
3. Concept resolution with SAME_AS handling
4. Time resolution with LLM
5. Test pipeline with real queries

**Remember**: The frame IS the understanding. No separate intent classification!

### Day 3: ChatCapability (CRITICAL)
1. Emotional support implementation
2. Follow-up question generation
3. Warm, empathetic tone
4. Test emotional queries

### Day 4: LangGraph Integration
1. Set up workflow nodes
2. Implement orchestrator (single-task)
3. Connect resolution pipeline
4. Test orchestration loops

### Day 5: Data Capabilities
1. TicketingDataCapability
2. EventAnalysisCapability
3. Test all query types
4. Verify assumptions are shared

### Day 6: Integration & Polish
1. Memory service (if time)
2. End-to-end testing
3. Performance checks
4. Fix critical bugs

### Day 7: Documentation & Demo
1. Update README
2. Create demo scenarios
3. Final testing
4. Client presentation prep

## What We're NOT Doing

1. **No external dependencies** - Everything self-contained
2. **No complex YAML** - Hardcoded mappings for MVP
3. **No separate planner** - Orchestrator handles it
4. **No mocks** - Real data only
5. **No premature optimization** - Make it work first
6. **No complex state** - Simple grouped architecture

## Implementation Philosophy

### Start Simple, Discover Optimal Approach

Instead of prescribing the implementation, we'll:
1. Start with the minimal viable approach
2. See what patterns emerge
3. Refactor to the optimal solution
4. Let the code guide us to the best architecture

### Example: Concept Mapping Evolution

```python
# Phase 1: Start simple
CONCEPT_MAP = {
    "revenue": "ticket_line_items.amount",
    "sales": "ticket_line_items.amount"
}

# Phase 2: If patterns emerge, maybe:
class ConceptMapper:
    def __init__(self, config_path: str = None):
        # Load from JSON/YAML if beneficial
        # Or keep in code if that's cleaner
        
# Phase 3: Let LLM help decide
# Maybe the LLM can even suggest mappings!
```

### Guiding Principles

1. **Minimal viable first** - Get it working
2. **Observe patterns** - What's repeated? What's complex?
3. **Refactor thoughtfully** - Only add complexity if it helps
4. **LLM-first design** - Maybe the LLM can handle more than we think
5. **Pragmatic choices** - What ships in one week?

## Success Metrics

1. ✅ All code in encoreproai/ folder
2. ✅ No imports from parent directory
3. ✅ 100% test success with real data
4. ✅ ChatCapability provides companionship
5. ✅ Delivered in one week

## Emergency Simplifications

If running out of time:
1. Hardcode more mappings
2. Skip memory service initially
3. Basic ambiguity handling only
4. Focus on ChatCapability + TicketingCapability

Remember: The goal is a WORKING system that preserves your key insights, not a perfect reimplementation.