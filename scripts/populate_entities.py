"""
Entity Population Script - Import entities from Cube.js to PostgreSQL

Fetches all entity types from Cube.js using CubeMetaService and populates:
- entities table - for entity resolution with trigram matching

Usage:
    export CUBE_URL=http://localhost:4000
    export CUBE_SECRET=your-secret
    export DEFAULT_TENANT_ID=your-tenant-id
    python scripts/populate_entities.py

Docker usage:
    docker-compose run --rm app python scripts/populate_entities.py
"""

import asyncio
import asyncpg
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any


from services.cube_service import CubeService
from services.cube_meta_service import CubeMetaService


async def fetch_productions_with_dates(cube_service: CubeService, tenant_id: str) -> List[Dict[str, Any]]:
    """Fetch all productions with their first/last dates using your working query"""
    result = await cube_service.query(
        dimensions=["ticket_line_items.production_id", "productions.name"],
        measures=[
            "ticket_line_items.amount",
            "ticket_line_items.quantity", 
            "events.first_event_starts_at_local",
            "events.last_event_starts_at_local"
        ],
        filters=[],
        tenant_id=tenant_id,
        limit=10000
    )
    
    productions = []
    for row in result.get("data", []):
        if row.get("ticket_line_items.production_id") and row.get("productions.name"):
            productions.append({
                "id": row["ticket_line_items.production_id"],
                "name": row["productions.name"],
                "entity_type": "production",
                "first_date": row.get("events.first_event_starts_at_local", "unknown"),
                "last_date": row.get("events.last_event_starts_at_local", "unknown"),
                "revenue": float(row.get("ticket_line_items.amount", 0) or 0),
                "attendance": int(row.get("ticket_line_items.quantity", 0) or 0)
            })
    
    return productions


async def clear_entities_tables(database_url: str, tenant_id: str):
    """Clear entities and production_info tables for a tenant"""
    conn = await asyncpg.connect(database_url)
    try:
        print(f"🧹 Clearing entity tables for tenant: {tenant_id}")
        
        # Clear existing entities for tenant
        await conn.execute("DELETE FROM entities WHERE tenant_id = $1", tenant_id)
        entities_deleted = await conn.fetchval(
            "SELECT COUNT(*) FROM entities WHERE tenant_id = $1", 
            tenant_id
        )
        
        production_info_deleted = 0
        
        print(f"   Deleted {entities_deleted} entities")
        print(f"   Deleted {production_info_deleted} production_info records")
        
    finally:
        await conn.close()


async def fetch_entities_from_config(cube_service: CubeService, entity_type: str, config: Dict, tenant_id: str) -> List[Dict[str, Any]]:
    """Fetch entities based on CubeMetaService configuration
    
    Config contains:
    - For real entities: id_dimension, name_dimension (e.g., "productions.id", "productions.name")
    - For categorical dimensions: id_dimension only (e.g., "ticket_line_items.city")
    """
    # Determine if this is a categorical dimension (city, country, etc)
    is_categorical = config.get("is_categorical", False)
    
    if is_categorical:
        # Categorical dimensions - get unique values
        result = await cube_service.query(
            dimensions=[config["id_dimension"]],
            measures=[],
            filters=[],
            tenant_id=tenant_id,
            limit=10000
        )
        
        entities = []
        seen_values = set()
        for row in result.get("data", []):
            value = row.get(config["id_dimension"])
            if value and value not in seen_values:
                seen_values.add(value)
                entities.append({
                    "id": value,
                    "name": value,
                    "entity_type": entity_type
                })
        
        return entities
    else:
        # Real entities with separate id and name
        result = await cube_service.query(
            dimensions=[config["id_dimension"], config["name_dimension"]],
            measures=[],
            filters=[],
            tenant_id=tenant_id,
            limit=10000
        )
        
        entities = []
        for row in result.get("data", []):
            entity_id = row.get(config["id_dimension"])
            entity_name = row.get(config["name_dimension"])
            if entity_id and entity_name:
                entities.append({
                    "id": entity_id,
                    "name": entity_name,
                    "entity_type": entity_type
                })
        
        return entities


async def fetch_sold_last_30_days(cube_service: CubeService, tenant_id: str) -> Dict[str, float]:
    """Fetch revenue for last 30 days for all productions using timeDimensions"""
    try:
        result = await cube_service.query(
            measures=["ticket_line_items.amount"],
            dimensions=["ticket_line_items.production_id"],
            filters=[],
            time_dimensions=[{
                "dimension": "ticket_line_items.created_at_local",
                "dateRange": "last 30 days"
            }],
            tenant_id=tenant_id,
            limit=10000
        )
        
        sold_data = {}
        for row in result.get("data", []):
            prod_id = row.get("ticket_line_items.production_id")
            amount = float(row.get("ticket_line_items.amount", 0) or 0)
            if prod_id:
                sold_data[prod_id] = amount
        
        print(f"   Found {len(sold_data)} productions with sales in last 30 days")
        return sold_data
        
    except Exception as e:
        print(f"   Warning: Could not fetch sold_last_30_days: {e}")
        return {}


async def populate_database(
    database_url: str,
    cube_url: str,
    cube_secret: str,
    tenant_id: str
):
    """Main population function using CubeMetaService"""
    
    # Initialize services
    cube_service = CubeService(cube_url, cube_secret)
    meta_service = CubeMetaService(cube_url, cube_secret)
    
    # Connect to PostgreSQL
    conn = await asyncpg.connect(database_url)
    
    try:
        print(f"🔄 Starting entity population for tenant: {tenant_id}")
        
        # Clear existing data
        await clear_entities_tables(database_url, tenant_id)
        
        # Fetch productions with all their data in one query
        print("📊 Fetching productions with dates...")
        productions = await fetch_productions_with_dates(cube_service, tenant_id)
        print(f"  Found {len(productions)} productions")
        
        # Fetch sold_last_30_days data
        print("📊 Fetching sold_last_30_days data...")
        sold_last_30_days_data = await fetch_sold_last_30_days(cube_service, tenant_id)
        
        # Start with production entities
        all_entities = productions
        
        # Discover other entity types using CubeMetaService
        print("🔍 Discovering other entity types from Cube.js schema...")
        entity_types = await meta_service.get_entity_types()
        
        # Skip productions (already fetched) and problematic types
        skip_types = {'productions', 'production', 'venues', 'venue', 'customers', 'customer'}
        
        for entity_type in entity_types:
            if entity_type in skip_types:
                continue
                
            print(f"📊 Fetching {entity_type} entities...")
            config = await meta_service.get_entity_config(entity_type)
            
            if not config:
                print(f"  ❌ No config found for {entity_type}")
                continue
            
            try:
                entities = await fetch_entities_from_config(cube_service, entity_type, config, tenant_id)
                print(f"  Found {len(entities)} {entity_type} entities")
                all_entities.extend(entities)
            except Exception as e:
                print(f"  ❌ Failed to fetch {entity_type}: {e}")
        
        # Insert all entities
        print(f"\n💾 Inserting {len(all_entities)} entities...")
        for entity in all_entities:
            # Build data field
            entity_data = {}
            if entity["entity_type"] == "production":
                entity_data["sold_last_30_days"] = sold_last_30_days_data.get(entity["id"], 0.0)
                entity_data["first_date"] = entity.get("first_date", "unknown")
                entity_data["last_date"] = entity.get("last_date", "unknown")
            
            await conn.execute("""
                INSERT INTO entities (tenant_id, id, name, entity_type, data, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $6)
                ON CONFLICT (tenant_id, entity_type, id) DO UPDATE 
                SET name = EXCLUDED.name, data = EXCLUDED.data, updated_at = EXCLUDED.updated_at
            """, 
                tenant_id, 
                entity["id"], 
                entity["name"], 
                entity["entity_type"],
                json.dumps(entity_data),
                datetime.utcnow()
            )
        
        
        # Verify counts by entity type
        entity_count = await conn.fetchval(
            "SELECT COUNT(*) FROM entities WHERE tenant_id = $1",
            tenant_id
        )
        
        entity_type_counts = await conn.fetch("""
            SELECT entity_type, COUNT(*) as count 
            FROM entities 
            WHERE tenant_id = $1 
            GROUP BY entity_type
        """, tenant_id)
        
        # Count productions specifically
        prod_count = await conn.fetchval(
            "SELECT COUNT(*) FROM entities WHERE tenant_id = $1 AND entity_type = 'production'",
            tenant_id
        )
        
        print(f"\n✅ Population complete!")
        print(f"   Total entities: {entity_count}")
        for row in entity_type_counts:
            print(f"   - {row['entity_type']}: {row['count']}")
        print(f"   Productions with data: {prod_count}")
        print(f"   Productions with sold_last_30_days > 0: {len([k for k, v in sold_last_30_days_data.items() if v > 0])}")
        
    except Exception as e:
        print(f"❌ Population failed: {e}")
        raise
    finally:
        await conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Populate entities from Cube.js to PostgreSQL")
    parser.add_argument("--clear-only", action="store_true", help="Only clear tables, don't populate")
    args = parser.parse_args()
    
    # Get configuration from environment
    database_url = os.getenv("DATABASE_URL", "postgresql://encore:secure_password@localhost:5433/encoreproai")
    cube_url = os.getenv("CUBE_URL")
    cube_secret = os.getenv("CUBE_SECRET")
    tenant_id = os.getenv("DEFAULT_TENANT_ID", os.getenv("TENANT_ID", "default"))
    
    if args.clear_only:
        # Just clear tables
        asyncio.run(clear_entities_tables(database_url, tenant_id))
    else:
        if not cube_url or not cube_secret:
            print("❌ Error: CUBE_URL and CUBE_SECRET environment variables required")
            print("\nUsage:")
            print("  CUBE_URL=http://localhost:4000 CUBE_SECRET=your-secret DEFAULT_TENANT_ID=your-tenant python populate_entities.py")
            print("  python populate_entities.py --clear-only  # Just clear tables")
            sys.exit(1)
        
        # Run population
        asyncio.run(populate_database(database_url, cube_url, cube_secret, tenant_id))