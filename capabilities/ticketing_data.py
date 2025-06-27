"""
TicketingData Capability

Smart Cube.js query generator and executor. Uses LLM to generate
sophisticated queries based on orchestrator requests. Handles failures
gracefully and communicates what it can and cannot do.
"""

import os
from typing import Dict, Any, List, Optional
import logging
import json

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from pydantic import BaseModel

from capabilities.base import BaseCapability, CapabilityDescription
from models.capabilities import (
    TicketingDataInputs, TicketingDataResult, DataPoint,
    CubeFilter
)
from services.cube_service import CubeService
from services.cube_meta_service import CubeMetaService

logger = logging.getLogger(__name__)


class CubeQuery(BaseModel):
    """Structured output for generated Cube.js query"""
    measures: List[str]
    dimensions: List[str] = []
    filters: List[Dict[str, Any]] = []
    timeDimensions: Optional[List[Dict[str, Any]]] = None
    order: List[Dict[str, str]] = []
    limit: Optional[int] = None


class TicketingDataCapability(BaseCapability):
    """Smart data access capability with LLM-powered query generation"""
    
    def __init__(self):
        # Initialize CubeService
        cube_url = os.getenv("CUBE_URL")
        cube_secret = os.getenv("CUBE_SECRET")
        
        if not cube_url or not cube_secret:
            raise ValueError("CUBE_URL and CUBE_SECRET environment variables required")
        
        self.cube_service = CubeService(cube_url, cube_secret)
        self.meta_service = CubeMetaService(cube_url, cube_secret)
        
        # Initialize LLM for query generation
        self.llm = ChatOpenAI(
            model=os.getenv("LLM_TIER_STANDARD", "gpt-4o-mini"),
            temperature=0.1  # Low temperature for consistent query generation
        )
    
    def describe(self) -> CapabilityDescription:
        """Describe capability for orchestrator"""
        return CapabilityDescription(
            name="ticketing_data",
            purpose="Execute direct Cube.js queries for ticketing metrics",
            inputs={
                "measures": "List of Cube.js measures (e.g., ticket_line_items.amount)",
                "dimensions": "List of Cube.js dimensions (e.g., productions.name)",
                "filters": "List of CubeFilter objects with member, operator, values",
                "order": "Optional ordering dict",
                "limit": "Optional row limit"
            },
            outputs={
                "data": "List of data points with dimensions and measures",
                "query_metadata": "Query execution details",
                "total_rows": "Number of rows returned",
                "assumptions": "Any query notes"
            },
            examples=[
                "measures=['ticket_line_items.amount'], dimensions=['productions.name']",
                "filters=[{'member': 'productions.name', 'operator': 'equals', 'values': ['Chicago']}]"
            ]
        )
    
    async def execute(self, inputs: TicketingDataInputs) -> TicketingDataResult:
        """Execute data query with intelligent query generation and error handling"""
        
        logger.info(f"Processing data request - Intent: {inputs.measures}")
        
        try:
            # Get available schema for context
            cube_mappings = await self._get_cube_mappings()
            
            # Generate sophisticated Cube.js query using LLM
            query = await self._generate_cube_query(inputs, cube_mappings)
            
            if not query:
                return TicketingDataResult(
                    success=False,
                    data=[],
                    total_rows=0,
                    assumptions=["Could not generate a valid query for this request"],
                    query_metadata={"error": "Query generation failed"}
                )
            
            # Try to execute the generated query
            try:
                result = await self.cube_service.query(
                    measures=query.get("measures", []),
                    dimensions=query.get("dimensions", []),
                    filters=query.get("filters", []),
                    time_dimensions=query.get("timeDimensions"),
                    order=query.get("order", []),
                    limit=query.get("limit", inputs.limit),
                    tenant_id=inputs.tenant_id
                )
            except Exception as e:
                # If query fails, try a simpler version
                logger.warning(f"Initial query failed: {e}. Trying simpler query...")
                
                # Remove problematic dimensions (like sold_datetime)
                simplified_query = await self._simplify_query(query, str(e))
                
                try:
                    result = await self.cube_service.query(
                        measures=simplified_query.get("measures", []),
                        dimensions=simplified_query.get("dimensions", []),
                        filters=simplified_query.get("filters", []),
                        order=simplified_query.get("order", []),
                        limit=simplified_query.get("limit", inputs.limit),
                        tenant_id=inputs.tenant_id
                    )
                except Exception as e2:
                    # Even simplified query failed
                    return TicketingDataResult(
                        success=False,
                        data=[],
                        total_rows=0,
                        assumptions=[
                            f"Unable to fetch data: {str(e2)}",
                            "The requested query combination may not be supported by the data model"
                        ],
                        query_metadata={
                            "error": str(e2),
                            "attempted_query": simplified_query
                        }
                    )
            
            # Transform Cube.js response to our DataPoint format
            data_points = []
            for row in result.get('data', []):
                # Separate dimensions and measures
                dimensions = {}
                measures = {}
                
                for key, value in row.items():
                    if any(key.startswith(m.split('.')[0]) for m in inputs.measures):
                        measures[key] = value
                    else:
                        dimensions[key] = value
                
                data_points.append(DataPoint(
                    dimensions=dimensions,
                    measures=measures
                ))
            
            # Build assumptions list based on query
            assumptions = []
            if not inputs.filters:
                assumptions.append("No filters applied - showing all available data")
            if not inputs.limit:
                assumptions.append("No limit specified - returning all matching rows")
            
            # Add metadata about the query
            query_metadata = {
                "cube_response": {
                    "annotation": result.get('annotation', {}),
                    "query": result.get('query', {})
                },
                "measures_requested": inputs.measures,
                "dimensions_requested": inputs.dimensions,
                "filters_applied": len(inputs.filters)
            }
            
            return TicketingDataResult(
                success=True,
                data=data_points,
                query_metadata=query_metadata,
                total_rows=len(data_points),
                assumptions=assumptions
            )
            
        except Exception as e:
            logger.error(f"Error fetching ticketing data: {e}")
            return TicketingDataResult(
                success=False,
                data=[],
                query_metadata={"error": str(e)},
                total_rows=0,
                assumptions=["Query failed - no data returned"]
            )
    
    async def _get_cube_mappings(self) -> Dict[str, Any]:
        """Get available measures and dimensions from schema"""
        # Use the comprehensive entity type mapping
        entity_mappings = {
            "production": {
                "cube_field": "ticket_line_items.production_id",
                "grouping_field": "productions.name",
                "time_field": "ticket_line_items.created_at_local"
            },
            "venue": {
                "cube_field": "ticket_line_items.venue_id", 
                "time_field": "ticket_line_items.created_at_local"
            },
            "city": {
                "cube_field": "ticket_line_items.city",
                "time_field": "ticket_line_items.created_at_local"
            },
            "retailer": {
                "cube_field": "ticket_line_items.retailer_id",
                "grouping_field": "retailers.name",
                "time_field": "ticket_line_items.created_at_local"
            },
            "priceband": {
                "cube_field": "ticket_line_items.price_band_id",
                "grouping_field": "price_bands.name",
                "time_field": "ticket_line_items.created_at_local"
            },
            "tickettype": {
                "cube_field": "ticket_line_items.ticket_type_id",
                "grouping_field": "ticket_types.name",
                "time_field": "ticket_line_items.created_at_local"
            }
        }
        
        return {
            "metrics": {
                "revenue": "ticket_line_items.amount",
                "attendance": "ticket_line_items.quantity",
                "average_price": "ticket_line_items.amount_average",
                "max_price": "ticket_line_items.amount_max",
                "min_price": "ticket_line_items.amount_min"
            },
            "dimensions": {
                "show": "productions.name",
                "production": "productions.name",
                "venue": "ticket_line_items.venue_id",
                "city": "ticket_line_items.city",
                "retailer": "retailers.name",
                "priceband": "price_bands.name",
                "tickettype": "ticket_types.name",
                "sales_date": "ticket_line_items.created_at_local",
                "event_date": "events.starts_at_local"
            },
            "entity_mappings": entity_mappings,
            "time_field": "ticket_line_items.created_at_local"  # Default time field
        }
    
    async def _generate_cube_query(self, inputs: TicketingDataInputs, cube_mappings: Dict[str, Any]) -> Dict[str, Any]:
        """Generate sophisticated Cube.js query using LLM"""
        
        # Build the request context
        resolved_entities = []
        for f in inputs.filters:
            if hasattr(f, 'member') and hasattr(f, 'values'):
                resolved_entities.append({
                    "field": f.member,
                    "operator": f.operator,
                    "values": f.values
                })
        
        # Build the comprehensive prompt
        system_prompt = """You are an expert at generating sophisticated Cube.js queries for Broadway theater analytics.
Generate queries based on the provided context and schema.

IMPORTANT RULES:
1. Always include "order": [] (even if empty)
2. Use exact field names from the schema
3. For production filters, use "productions.name" with "equals" operator
4. Avoid problematic dimensions like ticket_line_items.sold_datetime unless specifically needed
5. Prefer simpler queries that will work over complex ones that might fail

Available Schema:
- Measures: ticket_line_items.amount, ticket_line_items.quantity, ticket_line_items.amount_average
- Dimensions: productions.name, ticket_line_items.venue_id, ticket_line_items.city
- Time dimensions: ticket_line_items.created_at_local (for time-based analysis)

Respond with ONLY valid JSON, no explanation."""

        user_prompt = f"""Generate a Cube.js query for this request:

Data Intent: {inputs.measures}
Grouping: {inputs.dimensions if inputs.dimensions else "no specific grouping"}
Filters: {resolved_entities}
Order: {inputs.order if inputs.order else "default"}
Limit: {inputs.limit if inputs.limit else "no limit"}

The user is asking about performance data. Generate an appropriate query."""

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            
            # Parse JSON response
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                query = json.loads(json_match.group())
                # Ensure order is always present
                if "order" not in query:
                    query["order"] = []
                return query
            else:
                logger.error("Failed to parse LLM response as JSON")
                return None
                
        except Exception as e:
            logger.error(f"Query generation failed: {e}")
            return None
    
    async def _simplify_query(self, query: Dict[str, Any], error: str) -> Dict[str, Any]:
        """Simplify a query that failed, removing problematic parts"""
        simplified = query.copy()
        
        # If error mentions sold_datetime, remove it from dimensions
        if "sold_datetime" in error.lower():
            simplified["dimensions"] = [d for d in simplified.get("dimensions", []) 
                                      if "sold_datetime" not in d]
        
        # If error mentions time dimensions, remove them
        if "timedimensions" in error.lower():
            simplified.pop("timeDimensions", None)
        
        # If still has issues, go to minimal query
        if not simplified.get("dimensions"):
            simplified["dimensions"] = ["productions.name"]
        
        logger.info(f"Simplified query from {len(query.get('dimensions', []))} to {len(simplified.get('dimensions', []))} dimensions")
        
        return simplified


# Testing function
async def test_ticketing_data_capability():
    """Test TicketingDataCapability with real queries"""
    
    print("🎫 Testing TicketingDataCapability")
    print("=" * 60)
    
    capability = TicketingDataCapability()
    
    # Test 1: Simple revenue query
    print("\n1️⃣ Simple Revenue Query (Gatsby):")
    inputs = TicketingDataInputs(
        session_id="test_session",
        tenant_id="test_tenant",
        user_id="test_user",
        measures=["ticket_line_items.amount"],
        dimensions=["productions.name"],
        filters=[
            CubeFilter(
                member="productions.name",
                operator="contains",
                values=["GATSBY"]
            )
        ]
    )
    
    result = await capability.execute(inputs)
    print(f"Success: {result.success}")
    print(f"Rows returned: {result.total_rows}")
    
    if result.data:
        for dp in result.data[:3]:  # Show first 3
            print(f"  {dp.dimensions.get('productions.name', 'Unknown')}: ${dp.measures.get('ticket_line_items.amount', 0):,.0f}")
    
    # Test 2: Top productions by revenue
    print("\n2️⃣ Top 5 Productions by Revenue:")
    inputs = TicketingDataInputs(
        session_id="test_session",
        tenant_id="test_tenant",
        user_id="test_user",
        measures=["ticket_line_items.amount"],
        dimensions=["productions.name"],
        filters=[],
        order={"ticket_line_items.amount": "desc"},
        limit=5
    )
    
    result = await capability.execute(inputs)
    if result.success and result.data:
        for i, dp in enumerate(result.data):
            name = dp.dimensions.get('productions.name', 'Unknown')
            revenue = dp.measures.get('ticket_line_items.amount', 0)
            print(f"  {i+1}. {name}: ${revenue:,.0f}")
    
    # Test 3: Multiple measures
    print("\n3️⃣ Revenue and Attendance:")
    inputs = TicketingDataInputs(
        session_id="test_session",
        tenant_id="test_tenant",
        user_id="test_user",
        measures=["ticket_line_items.amount", "ticket_line_items.quantity"],
        dimensions=["productions.name"],
        filters=[],
        order={"ticket_line_items.amount": "desc"},
        limit=3
    )
    
    result = await capability.execute(inputs)
    if result.success and result.data:
        for dp in result.data:
            name = dp.dimensions.get('productions.name', 'Unknown')
            revenue = dp.measures.get('ticket_line_items.amount', 0)
            quantity = dp.measures.get('ticket_line_items.quantity', 0)
            print(f"  {name}:")
            print(f"    Revenue: ${revenue:,.0f}")
            print(f"    Tickets: {quantity:,}")
    
    print("\n✅ TicketingDataCapability test complete!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_ticketing_data_capability())