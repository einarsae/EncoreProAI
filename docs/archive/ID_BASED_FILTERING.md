# ID-Based Filtering in EncoreProAI

## Overview

EncoreProAI uses a sophisticated entity resolution system that provides exact database IDs for filtering. However, the ultimate decision of whether to use IDs or names rests with the LLM.

## How It Works

### 1. Entity Resolution
When a user mentions an entity (like "Chicago" or "Gatsby"), the EntityResolver:
- Searches the database using PostgreSQL trigram similarity
- Returns ALL matching candidates with:
  - `id`: The exact database UUID
  - `name`: The display name
  - `disambiguation`: Contextual information (dates, revenue, etc.)
  - `score`: Confidence score (0.0-1.0)

### 2. Orchestrator Context
The orchestrator provides the LLM with complete entity information:
```python
# Example context for "Chicago"
{
    "text": "Chicago",
    "type": "production",
    "candidates": [
        {
            "id": "p456",
            "name": "CHICAGO THE MUSICAL",
            "disambiguation": "CHICAGO THE MUSICAL [p456] (2019-2025) $450,000 last 30 days",
            "score": 0.95
        }
    ]
}
```

### 3. LLM Decision Making
The LLM receives:
- The original entity text
- All candidate matches with IDs
- Disambiguation information

The LLM then decides whether to:
- Use the exact ID for precise filtering: `productions.id = "p456"`
- Use name-based filtering: `productions.name contains "CHICAGO"`
- Select multiple candidates if ambiguous
- Request clarification from the user

### 4. Why This Approach?

**We enable, not enforce:**
- Provides IDs for precision when needed
- Allows fuzzy matching when appropriate
- Handles ambiguity gracefully
- Adapts to query context

**Example scenarios:**
- "Revenue for Chicago" → LLM likely uses ID for exact match
- "Shows like Chicago" → LLM might use name pattern for broader results
- "Chicago venues" → LLM understands this isn't about the show

## Implementation Details

### TicketingDataCapability
The capability receives entities with full candidate information:
```python
entities = [
    {
        "text": "Gatsby",
        "type": "production",
        "candidates": [
            {
                "id": "p123",
                "name": "THE GREAT GATSBY",
                "disambiguation": "THE GREAT GATSBY [p123] (2024-present) $1.2M last 30 days"
            }
        ]
    }
]
```

The LLM prompt includes instructions to:
- Use exact field names from the schema
- Prefer IDs when precision is needed
- Include disambiguation context in query description

### Benefits

1. **Precision**: Exact matches when needed
2. **Flexibility**: Fuzzy matching when appropriate  
3. **Transparency**: Users see which entity was selected
4. **Adaptability**: Context-aware filtering decisions

## Testing

To verify ID-based filtering is working:
```bash
docker-compose run --rm test python -m pytest tests/test_id_based_filtering.py -v
```

This tests that:
- Entity resolution provides IDs
- Orchestrator passes IDs to capabilities
- The system enables (but doesn't force) ID usage