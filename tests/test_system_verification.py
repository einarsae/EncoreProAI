#!/usr/bin/env python3
"""
Final verification test with real populated data

Run: docker-compose run --rm test python test_final_verification.py
"""

import asyncio
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.entity_resolver import EntityResolver
from services.cube_service import CubeService
from services.cube_meta_service import CubeMetaService


async def main():
    print("🔍 Final Verification Test")
    print("=" * 60)
    
    database_url = os.getenv("DATABASE_URL", "postgresql://encore:secure_password@localhost:5433/encoreproai")
    cube_url = os.getenv("CUBE_URL")
    cube_secret = os.getenv("CUBE_SECRET")
    
    if not cube_url or not cube_secret:
        print("❌ CUBE_URL and CUBE_SECRET required")
        return
    
    # Initialize services
    resolver = EntityResolver(database_url)
    await resolver.connect()
    cube_service = CubeService(cube_url, cube_secret)
    meta_service = CubeMetaService(cube_url, cube_secret)
    
    try:
        # Get tenant_id from database
        async with resolver.pool.acquire() as conn:
            tenant_id = await conn.fetchval("SELECT DISTINCT tenant_id FROM entities LIMIT 1")
            
        print(f"Using tenant_id: {tenant_id}\n")
        
        # Test 1: Verify entity counts
        print("📊 Test 1: Entity Counts")
        async with resolver.pool.acquire() as conn:
            counts = await conn.fetch("""
                SELECT entity_type, COUNT(*) as count
                FROM entities
                WHERE tenant_id = $1
                GROUP BY entity_type
                ORDER BY count DESC
            """, tenant_id)
            
            total = 0
            for row in counts:
                print(f"  {row['entity_type']:20} {row['count']:5,}")
                total += row['count']
            print(f"  {'TOTAL':20} {total:5,}")
        
        # Test 2: Production disambiguation
        print("\n🎭 Test 2: Production Disambiguation")
        test_productions = ["chicago", "hamilton", "wicked", "gatsby"]
        
        for prod_name in test_productions:
            candidates = await resolver.resolve_entity(
                text=prod_name,
                entity_type="production",
                tenant_id=tenant_id,
                threshold=0.3
            )
            
            if candidates:
                top = candidates[0]
                print(f"\n  Query: '{prod_name}'")
                print(f"  Found: {top.disambiguation}")
                
                # Verify all parts are present
                checks = {
                    "Has ID": "[" in top.disambiguation and "]" in top.disambiguation,
                    "Has score": "score:" in top.disambiguation,
                    "Has dates": "present" in top.disambiguation or "-20" in top.disambiguation,
                    "Has sales": "$" in top.disambiguation or "no recent sales" in top.disambiguation
                }
                
                for check, passed in checks.items():
                    print(f"    ✓ {check}" if passed else f"    ✗ {check}")
            else:
                print(f"\n  Query: '{prod_name}' - NOT FOUND")
        
        # Test 3: Categorical entity resolution
        print("\n🌆 Test 3: Categorical Entity Resolution")
        test_cities = ["new york", "chicago", "los angeles", "london"]
        
        for city_name in test_cities:
            candidates = await resolver.resolve_entity(
                text=city_name,
                entity_type="city",
                tenant_id=tenant_id,
                threshold=0.3
            )
            
            print(f"\n  Query: '{city_name}' -> {len(candidates)} matches")
            for i, candidate in enumerate(candidates[:3]):
                print(f"    {i+1}. {candidate.disambiguation}")
        
        # Test 4: Cross-type ambiguity
        print("\n🔀 Test 4: Cross-Type Ambiguity")
        ambiguous_terms = ["chicago", "paris", "brooklyn"]
        
        for term in ambiguous_terms:
            candidates = await resolver.cross_type_lookup(
                text=term,
                tenant_id=tenant_id,
                threshold=0.3
            )
            
            print(f"\n  Query: '{term}' -> {len(candidates)} total matches")
            
            # Group by type
            by_type = {}
            for c in candidates:
                by_type.setdefault(c.entity_type, []).append(c)
            
            for entity_type, items in sorted(by_type.items()):
                print(f"    {entity_type}: {len(items)} matches")
                if items:
                    print(f"      Top: {items[0].disambiguation}")
        
        # Test 5: Data quality check
        print("\n🔍 Test 5: Data Quality Check")
        async with resolver.pool.acquire() as conn:
            # Check productions with complete data
            complete_prods = await conn.fetchval("""
                SELECT COUNT(*)
                FROM entities
                WHERE tenant_id = $1
                  AND entity_type = 'production'
                  AND data->>'first_date' != 'unknown'
                  AND data->>'last_date' != 'unknown'
                  AND data->>'sold_last_30_days' IS NOT NULL
            """, tenant_id)
            
            total_prods = await conn.fetchval("""
                SELECT COUNT(*)
                FROM entities
                WHERE tenant_id = $1 AND entity_type = 'production'
            """, tenant_id)
            
            print(f"  Productions with complete data: {complete_prods}/{total_prods}")
            
            # Sample production data
            sample_prod = await conn.fetchrow("""
                SELECT name, data
                FROM entities
                WHERE tenant_id = $1
                  AND entity_type = 'production'
                  AND (data->>'sold_last_30_days')::float > 0
                ORDER BY (data->>'sold_last_30_days')::float DESC
                LIMIT 1
            """, tenant_id)
            
            if sample_prod:
                print(f"\n  Top selling production: {sample_prod['name']}")
                data = json.loads(sample_prod['data'])
                for key, value in data.items():
                    print(f"    {key}: {value}")
        
        # Test 6: Cube.js integration
        print("\n📊 Test 6: Cube.js Integration")
        
        # Test a simple query
        result = await cube_service.query(
            measures=["ticket_line_items.amount"],
            dimensions=["productions.name"],
            filters=[],
            tenant_id=tenant_id,
            order={"ticket_line_items.amount": "desc"},
            limit=5
        )
        
        print("  Top 5 productions by revenue:")
        for row in result.get('data', []):
            name = row.get('productions.name', 'Unknown')
            revenue = row.get('ticket_line_items.amount', 0)
            try:
                revenue_num = float(revenue) if revenue else 0
                print(f"    {name}: ${revenue_num:,.0f}")
            except:
                print(f"    {name}: {revenue}")
        
        # Test 7: CubeMetaService
        print("\n🔧 Test 7: CubeMetaService")
        entity_types = await meta_service.get_entity_types()
        print(f"  Discovered {len(entity_types)} entity types")
        
        # Test a few configs
        for et in ['productions', 'city', 'venues']:
            config = await meta_service.get_entity_config(et)
            if config:
                print(f"    {et}: {config.get('id_dimension', 'N/A')}")
            else:
                print(f"    {et}: No config found")
        
        print("\n✅ All verification tests completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await resolver.close()


if __name__ == "__main__":
    asyncio.run(main())