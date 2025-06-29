# EncoreProAI - Services (Not Tools!)

## Overview

Services provide self-contained data access. Everything is in the encoreproai folder with NO external dependencies.

## Environment Configuration

All services use environment variables for configuration:
```bash
# .env file
CUBE_URL=https://your-cube-instance.com
CUBE_SECRET=your-secret-key
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://user:pass@localhost:5433/encoreproai
DEFAULT_TENANT_ID=your-tenant-id
```

## Core Services

### 1. CubeService

**Purpose**: Self-contained Cube.js integration with JWT security

```python
class CubeService:
    """Direct Cube.js client with JWT authentication"""
    
    def __init__(self, cube_url: str, cube_secret: str):
        self.cube_url = cube_url
        self.cube_secret = cube_secret
    
    def generate_token(self, tenant_id: str) -> str:
        """JWT with tenant isolation"""
        payload = {
            "sub": tenant_id,
            "tenant_id": tenant_id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=30)
        }
        return jwt.encode(payload, self.cube_secret, algorithm="HS256")
    
    async def query(self, measures, dimensions, filters, tenant_id, order=None, limit=None):
        """Execute Cube.js query with array-format filters"""
        # All filters use array format per our implementation
```

**Key Features**:
- JWT-based tenant isolation
- Array format for filters (not object format)
- Direct HTTP calls with httpx
- Error propagation without wrapping

### 2. EntityResolver  

**Purpose**: Type-aware entity resolution with PostgreSQL trigram similarity

```python
class EntityResolver:
    """PostgreSQL trigram similarity resolution with disambiguation"""
    
    async def resolve_entity(
        self,
        text: str,
        entity_type: str,
        tenant_id: str,
        threshold: float = 0.3
    ) -> List[EntityCandidate]:
        """Resolve entity with trigram similarity"""
        # Returns ALL candidates above threshold for ambiguity handling
        # Score transformation: 0.3-0.7 → 0.5-1.0
        
    async def cross_type_lookup(
        self,
        text: str,
        tenant_id: str,
        threshold: float = 0.3
    ) -> List[EntityCandidate]:
        """Search across all entity types with score discounting"""
        # 10% penalty for cross-type matches
```

**Disambiguation Format**:
- Productions: `"Hamilton [PROD123] (score: 0.95) (2015-present) $125,000 last 30 days"`
- Cities: `"NEW YORK [NEW YORK] (score: 1.00)"`
- Other entities: `"Payment Method Name [ID] (score: 0.88)"`

**Key Features**:
- Single flat entities table (no joins!)
- JSONB data field with sold_last_30_days, first_date, last_date
- Score transformation algorithm from old system
- Support for both real and categorical entities

### 3. CubeMetaService

**Purpose**: Discover entity types and dimensions from Cube.js schema

```python
class CubeMetaService:
    """Discover entity configuration from Cube.js meta schema"""
    
    async def get_entity_types(self) -> List[str]:
        """Get list of entity types (cube names + fake entities)"""
        # Returns: ['productions', 'city', 'country', etc.]
        
    async def get_entity_config(self, entity_type: str) -> Optional[Dict[str, str]]:
        """Get ID and name dimensions for an entity type"""
        # Real entities: {"id_dimension": "productions.id", "name_dimension": "productions.name"}
        # Categorical entities: {"id_dimension": "ticket_line_items.city", "name_dimension": "ticket_line_items.city"}
```

**Entity Types Found**:
- Real entities: productions, payment_methods, price_bands, retailers, sales_channels, seating_plans, ticket_types
- Categorical entities: city, country, state, currency
- Empty entities: delivery_methods, performers

### 4. ConceptResolver

**Purpose**: Memory-based concept resolution using mem0

```python
class ConceptResolver:
    """Memory-based concept resolution with mem0 integration"""
    
    def resolve(self, concept_text: str, user_id: str = "system") -> Dict[str, Any]:
        """Resolve a concept to memory context using mem0 or fallback mappings"""
        # 1. Query mem0 for related memories
        # 2. If no memory found, use pattern-based mappings
        # 3. Return enriched memory context with confidence scores
        
    def learn_from_success(self, concept_text: str, successful_mapping: str, user_id: str):
        """Learn from successful concept mappings by storing in mem0"""
        
    def learn_from_correction(self, concept_text: str, corrected_mapping: str, user_id: str):
        """Learn from user corrections by storing in mem0"""
```

**Key Features**:
- Memory-based learning with mem0/pgvector
- Pattern matching for common concepts (revenue → financial_performance)
- Learns from successful mappings
- User-specific corrections
- Fallback to basic mappings when mem0 unavailable

**Pattern Categories**:
- Financial: revenue, sales, income → financial_performance
- Audience: attendance, tickets, people → audience_metrics
- Performance: performing, "how did" → general_analysis
- Analysis: trends, comparison, vs → trend_analysis/comparative_analysis
- Emotional: overwhelmed, stressed → emotional_support

### 5. TimeResolver

**Purpose**: Parse natural language time expressions

**Current Status**: Handled directly by capabilities when they need date ranges. Each capability that requires time resolution (like TicketingDataCapability) uses its LLM to parse time expressions in context.

```python
# Capabilities parse time expressions like:
# "last month" → date range with start/end dates
# "Q3 2023" → quarterly date range
# "since June" → date range from June to present
# "yesterday vs last week" → comparison date ranges
```

## Database Schema

### entities table
```sql
CREATE TABLE entities (
    tenant_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    id TEXT NOT NULL,
    name TEXT NOT NULL,
    data JSONB,  -- {sold_last_30_days, first_date, last_date}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (tenant_id, entity_type, id)
);

-- Trigram index for fuzzy matching
CREATE INDEX idx_entities_trigram ON entities USING gin(name gin_trgm_ops);
```

## Testing Philosophy

**NO MOCKS!** All tests use real connections:
- Real PostgreSQL with test data
- Real Cube.js queries (when API keys provided)
- Real OpenAI API calls (when needed)

Tests skip honestly when services unavailable:
```python
if not cube_url:
    pytest.skip("CUBE_URL not set")
```

## Population Script

`scripts/populate_entities.py`:
- Fetches productions with dates in a single query
- Uses timeDimensions for sold_last_30_days calculation
- Discovers other entity types via CubeMetaService
- Skips problematic entity types (venues, customers)
- Handles categorical dimensions (city, country, state)
- Supports --clear-only flag for cleanup