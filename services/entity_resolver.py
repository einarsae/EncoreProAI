"""
EntityResolver - Type-aware entity resolution with PostgreSQL trigram similarity

Based on old EntityLookupStore analysis but completely self-contained.
Uses pg_trgm for fuzzy matching with score boosting and ambiguity preservation.
"""

import asyncpg
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class EntityCandidate(BaseModel):
    """Entity candidate with similarity score and metadata"""
    id: str
    name: str
    entity_type: str
    score: float = Field(ge=0.0, le=1.0)  # 0.0 to 1.0
    disambiguation: str  # Human-readable context
    data: Optional[Dict[str, Any]] = Field(default=None, description="Additional entity data")
    # Disambiguation fields from our database
    sold_last_30_days: Optional[float] = None
    first_date: Optional[datetime] = None
    last_date: Optional[datetime] = None


class EntityResolver:
    """PostgreSQL trigram-based entity resolution with score boosting"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Initialize connection pool"""
        self.pool = await asyncpg.create_pool(self.database_url, min_size=2, max_size=10)
        logger.info("EntityResolver connected to PostgreSQL")
    
    async def close(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
    
    def transform_score(self, pg_score: float) -> float:
        """Transform PostgreSQL similarity (0.3-0.7) to usable range (0.5-1.0)"""
        # Based on old system score boosting algorithm
        if pg_score >= 0.7:
            return 1.0
        elif pg_score >= 0.5:
            return 0.8 + (pg_score - 0.5) * 1.0  # 0.8 to 1.0
        elif pg_score >= 0.3:
            return 0.5 + (pg_score - 0.3) * 0.75  # 0.5 to 0.8
        else:
            return pg_score  # Below threshold
    
    async def resolve_entity(
        self,
        text: str,
        entity_type: str,
        tenant_id: str,
        threshold: float = 0.3
    ) -> List[EntityCandidate]:
        """
        Resolve entity with trigram similarity
        Returns ALL candidates above threshold for ambiguity handling
        """
        if not self.pool:
            await self.connect()
        
        query = """
            SELECT 
                id,
                name,
                entity_type,
                data,
                similarity(name, $1) as similarity_score
            FROM entities
            WHERE tenant_id = $2 
              AND entity_type = $3
              AND similarity(name, $1) > $4
            ORDER BY similarity_score DESC
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, text, tenant_id, entity_type, threshold)
        
        candidates = []
        for row in rows:
            # Transform score using old system algorithm
            boosted_score = self.transform_score(row['similarity_score'])
            
            # Parse data field for additional context
            data = json.loads(row['data']) if row['data'] else {}
            
            # Create disambiguation string based on entity type
            if row['entity_type'] == 'production':
                # Build disambiguation with ID, dates and sales
                parts = [row['name'], f"[{row['id']}]", f"(score: {boosted_score:.2f})"]
                
                # Add date range
                first_date = data.get('first_date', 'unknown')
                last_date = data.get('last_date', 'unknown')
                if first_date != 'unknown':
                    if last_date == 'unknown' or last_date > datetime.now().strftime('%Y-%m-%d'):
                        parts.append(f"({first_date[:4]}-present)")
                    else:
                        parts.append(f"({first_date[:4]}-{last_date[:4]})")
                
                # Add sales info
                sold_last_30 = data.get('sold_last_30_days', 0)
                if sold_last_30 > 0:
                    parts.append(f"${sold_last_30:,.0f} last 30 days")
                else:
                    parts.append("no recent sales")
                
                disambiguation = " ".join(parts)
            else:
                disambiguation = f"{row['name']} [{row['id']}] (score: {boosted_score:.2f})"
            
            candidate = EntityCandidate(
                id=row['id'],
                name=row['name'],
                entity_type=row['entity_type'],
                score=boosted_score,
                disambiguation=disambiguation,
                data=data,
                sold_last_30_days=data.get('sold_last_30_days'),
                first_date=datetime.fromisoformat(data['first_date']) if data.get('first_date') and data['first_date'] != 'unknown' else None,
                last_date=datetime.fromisoformat(data['last_date']) if data.get('last_date') and data['last_date'] != 'unknown' else None
            )
            candidates.append(candidate)
        
        logger.info(f"Entity resolution '{text}' -> {len(candidates)} candidates")
        return candidates
    
    def _create_disambiguation(self, row: Dict) -> str:
        """Create human-readable disambiguation string"""
        name = row['name']
        
        # For productions, add date and performance context
        if row['entity_type'] == 'production':
            parts = [name]
            
            # Add date context
            if row['first_date'] and row['first_date'] != 'unknown':
                # Determine if running based on dates
                if row['last_date'] == 'unknown' or (row['last_date'] and row['last_date'] > datetime.now().strftime('%Y-%m-%d')):
                    year = row['first_date'][:4]
                    parts.append(f" ({year}-present")
                else:
                    start_year = row['first_date'][:4]
                    end_year = row['last_date'][:4] if row['last_date'] else 'unknown'
                    parts.append(f" ({start_year}-{end_year}")
            
            # Add revenue context if available
            if row['total_revenue'] and row['total_revenue'] > 0:
                revenue_m = row['total_revenue'] / 1000000  # Convert to millions
                parts.append(f", ${revenue_m:.1f}M total")
            
            parts.append(")")
            return "".join(parts)
        
        return name
    
    async def cross_type_lookup(
        self,
        text: str,
        tenant_id: str,
        threshold: float = 0.3
    ) -> List[EntityCandidate]:
        """Search across all entity types with score discounting"""
        if not self.pool:
            await self.connect()
        
        query = """
            SELECT 
                id,
                name,
                entity_type,
                data,
                similarity(name, $1) as similarity_score
            FROM entities
            WHERE tenant_id = $2 
              AND similarity(name, $1) > $3
            ORDER BY similarity_score DESC
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, text, tenant_id, threshold)
        
        candidates = []
        for row in rows:
            # Discount score for cross-type matches
            base_score = self.transform_score(row['similarity_score'])
            discounted_score = base_score * 0.85  # 15% penalty for cross-type
            
            # Parse data field
            data = json.loads(row['data']) if row['data'] else {}
            
            # Create type-specific disambiguation
            if row['entity_type'] == 'production':
                # Build disambiguation with ID, dates and sales
                parts = [row['name'], f"[{row['id']}]", f"(score: {discounted_score:.2f})", f"({row['entity_type']})"]
                
                # Add date range
                first_date = data.get('first_date', 'unknown')
                last_date = data.get('last_date', 'unknown')
                if first_date != 'unknown':
                    if last_date == 'unknown' or last_date > datetime.now().strftime('%Y-%m-%d'):
                        parts.append(f"{first_date[:4]}-present")
                    else:
                        parts.append(f"{first_date[:4]}-{last_date[:4]}")
                
                # Add sales info
                sold_last_30 = data.get('sold_last_30_days', 0)
                if sold_last_30 > 0:
                    parts.append(f"${sold_last_30:,.0f} last 30 days")
                else:
                    parts.append("no recent sales")
                
                disambiguation = " ".join(parts)
            else:
                disambiguation = f"{row['name']} [{row['id']}] (score: {discounted_score:.2f}) ({row['entity_type']})"
            
            candidate = EntityCandidate(
                id=row['id'],
                name=row['name'],
                entity_type=row['entity_type'],
                score=discounted_score,
                disambiguation=disambiguation,
                data=data,
                sold_last_30_days=data.get('sold_last_30_days'),
                first_date=datetime.fromisoformat(data['first_date']) if data.get('first_date') and data['first_date'] != 'unknown' else None,
                last_date=datetime.fromisoformat(data['last_date']) if data.get('last_date') and data['last_date'] != 'unknown' else None
            )
            candidates.append(candidate)
        
        logger.info(f"Cross-type lookup '{text}' -> {len(candidates)} candidates")
        return candidates


# Testing functions
async def test_entity_resolution(database_url: str):
    """Test entity resolution with real database"""
    resolver = EntityResolver(database_url)
    
    try:
        await resolver.connect()
        
        # Test with no entities (empty database)
        candidates = await resolver.resolve_entity(
            text="chicago", 
            entity_type="production", 
            tenant_id="test_tenant"
        )
        print(f"✅ Entity resolution test: {len(candidates)} candidates found")
        
        # Test cross-type lookup
        cross_candidates = await resolver.cross_type_lookup(
            text="chicago",
            tenant_id="test_tenant"
        )
        print(f"✅ Cross-type lookup test: {len(cross_candidates)} candidates found")
        
        return True
        
    except Exception as e:
        print(f"❌ Entity resolution test failed: {e}")
        return False
    finally:
        await resolver.close()


if __name__ == "__main__":
    import asyncio
    import os
    
    database_url = os.getenv("DATABASE_URL", "postgresql://encore:secure_password@localhost:5432/encoreproai")
    asyncio.run(test_entity_resolution(database_url))