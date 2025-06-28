"""
TicketingData Capability

Translates high-level data requests into sophisticated Cube.js queries and returns raw data.

Key responsibilities:
1. Uses real Cube.js schema to ensure valid field names
2. Leverages LLM to generate complex queries with advanced features
3. Returns raw data without interpretation (that's EventAnalysisCapability's job)
4. Fails fast - no retries or query simplification
5. Provides query metadata and assumptions made

This capability is purely for data retrieval. Analysis, insights, and recommendations
are handled by EventAnalysisCapability.
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
    """Data access capability that translates high-level requests to sophisticated Cube.js queries"""
    
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
        """Describe capability for orchestrator
        
        This capability fetches raw ticketing transaction data from Cube.js.
        It translates natural language requests into sophisticated Cube.js queries
        but does NOT interpret or analyze the data - that's EventAnalysisCapability's job.
        """
        return CapabilityDescription(
            name="ticketing_data",
            purpose="Fetch raw ticketing transaction data with advanced Cube.js features. Can retrieve data from multiple time periods (2 or more) in a single query for comparison. Supports trends, complex filtering, and all Cube.js features. No interpretation or analysis - just data retrieval. For insights and recommendations, use event_analysis capability.",
            inputs={
                "query_request": "Natural language description of what data you need",
                "measures": "What to measure (revenue, attendance, prices ['min', 'max', 'avg'], count, show dates, sales dates)",
                "dimensions": "How to group data (by show, venue, time, retailers/outlets, ticket types, price, location, sales channels, etc.)",
                "filters": "What to filter by (specific entities, time ranges, sales channels, ticket types, price bands, cities, postcode, customer, event, sales channels)",
                "time_context": "Time period for data (e.g., 'last month', 'Q1 2024', 'this year')",
                "time_comparison_type": "Optional: year_over_year, month_over_month, quarter_over_quarter, week_over_week",
                "time_granularity": "Optional: day, week, month, quarter, year",
                "entities": "Resolved entities with IDs from orchestrator",
                "limit": "Optional: max number of results",
                "order": "Optional: how to sort results"
            },
            outputs={
                "data": "Requested data points",
                "query_description": "What the query did",
                "key_findings": "Notable patterns or insights in the data",
                "total_rows": "Number of rows returned",
                "total_columns": "Number of columns returned",
                "total_measures": "Number of measures returned"
            },
            examples=[
                "Get revenue trends for Chicago over the last 3 months",
                "Compare attendance between Gatsby and Wicked this year",
                "Show top 5 venues by average ticket price",
                "Compare Q1 vs Q2 vs Q3 vs Q4 revenue this year",
                "Show year-over-year growth for all productions",
                "Compare this month's sales to same month last year",
                "Compare revenue across all 4 quarters of 2024"
            ]
        )
    
    async def execute(self, inputs: TicketingDataInputs) -> TicketingDataResult:
        """Execute data query using all Cube.js capabilities
        
        This method:
        1. Builds context from real Cube.js schema
        2. Uses LLM to generate sophisticated queries
        3. Executes the query and returns raw data
        4. Does NOT interpret or analyze results
        """
        
        logger.info(f"Processing data request: {inputs.measures}")
        
        try:
            # Build comprehensive context for query generation
            context = await self._build_query_context(inputs)
            
            # Generate sophisticated Cube.js query using LLM with full feature set
            query = await self._generate_advanced_query(inputs, context)
            
            if not query:
                return TicketingDataResult(
                    success=False,
                    data=[],
                    total_rows=0,
                    total_columns=0,
                    total_measures=0,
                    assumptions=["Could not generate a valid query for this request"],
                    query_metadata={"error": "Query generation failed"}
                )
            
            # Log the generated query for debugging
            logger.info(f"Generated query: {json.dumps(query, indent=2)}")
            
            # Log the actual query being sent
            logger.info(f"Sending query to Cube.js: {json.dumps(query, indent=2)}")
            
            # Execute the query - fail fast, no retries
            result = await self.cube_service.query(
                measures=query.get("measures", []),
                dimensions=query.get("dimensions", []),
                filters=query.get("filters", []),
                time_dimensions=query.get("timeDimensions"),
                order=query.get("order", []),
                limit=query.get("limit", inputs.limit),
                tenant_id=inputs.tenant_id
            )
            
            # Transform Cube.js response to our DataPoint format
            data_points = []
            for row in result.get('data', []):
                # Separate dimensions and measures
                dimensions = {}
                measures = {}
                
                for key, value in row.items():
                    # Check if this exact key is in the measures list
                    if key in query.get("measures", []):
                        measures[key] = value
                    else:
                        dimensions[key] = value
                
                data_points.append(DataPoint(
                    dimensions=dimensions,
                    measures=measures
                ))
            
            # Build query description and key findings
            query_description = await self._describe_query(query, len(data_points))
            key_findings = self._extract_key_findings(data_points, query)
            
            # Calculate total columns and measures
            total_columns = 0
            total_measures = 0
            if data_points:
                first_point = data_points[0]
                total_columns = len(first_point.dimensions) + len(first_point.measures)
                total_measures = len(first_point.measures)
            
            # Add metadata about the query
            query_metadata = {
                "cube_response": {
                    "annotation": result.get('annotation', {}),
                    "query": query
                }
            }
            
            return TicketingDataResult(
                success=True,
                data=data_points,
                query_metadata=query_metadata,
                total_rows=len(data_points),
                total_columns=total_columns,
                total_measures=total_measures,
                assumptions=[query_description] + key_findings
            )
            
        except Exception as e:
            logger.error(f"Error fetching ticketing data: {e}", exc_info=True)
            return TicketingDataResult(
                success=False,
                data=[],
                query_metadata={"error": str(e)},
                total_rows=0,
                total_columns=0,
                total_measures=0,
                assumptions=[f"Query failed: {str(e)}"]
            )
    
    async def _build_query_context(self, inputs: TicketingDataInputs) -> Dict[str, Any]:
        """Build comprehensive context from real Cube.js schema"""
        # Get full schema information
        try:
            schema = await self.meta_service.get_meta()
            available_cubes = schema.get('cubes', [])
            
            # Get all dimensions and measures from real schema
            all_dimensions = await self.meta_service.get_all_dimensions()
            all_measures = await self.meta_service.get_all_measures()
            
            # Build structured schema for LLM
            structured_schema = {
                "cubes": [],
                "all_dimensions": all_dimensions,
                "all_measures": all_measures
            }
            
            # Add cube details
            for cube in available_cubes:
                cube_info = {
                    "name": cube.get("name"),
                    "measures": [m.get("name") for m in cube.get("measures", [])],
                    "dimensions": [d.get("name") for d in cube.get("dimensions", [])],
                    "timeDimensions": [d.get("name") for d in cube.get("dimensions", []) 
                                       if d.get("type") == "time"]
                }
                structured_schema["cubes"].append(cube_info)
            
        except Exception as e:
            logger.warning(f"Failed to get real schema: {e}. Using empty schema.")
            structured_schema = {
                "cubes": [],
                "all_dimensions": [],
                "all_measures": []
            }
        
        return {
            "schema": structured_schema,
            "all_operators": [
                "equals", "notEquals", "contains", "notContains",
                "startsWith", "endsWith", "in", "notIn",
                "gt", "gte", "lt", "lte",
                "set", "notSet",
                "inDateRange", "notInDateRange", "beforeDate", "afterDate"
            ],
            "advanced_features": [
                "compareDateRange", "drilldown", "total",
                "nested AND/OR filters", "post-aggregation filters",
                "multi-cube joins", "ungrouped queries"
            ]
        }
    
    async def _generate_advanced_query(self, inputs: TicketingDataInputs, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate sophisticated Cube.js query using all available features"""
        
        # Build comprehensive prompt with all Cube.js capabilities
        # Avoid f-string to prevent issues with JSON examples containing braces
        schema_json = json.dumps(context['schema'], indent=2)
        operators_json = json.dumps(context['all_operators'])
        
        system_prompt = """You are an expert at generating sophisticated Cube.js queries.

AVAILABLE SCHEMA:
""" + schema_json + """

CRITICAL RULES:
1. Use EXACT field names from the schema above
2. NEVER use shortcuts - always use full qualified names (e.g., "ticket_line_items.amount" not "revenue")
3. Only use dimensions and measures that exist in the schema
4. Match the exact case and spelling from the schema

AVAILABLE OPERATORS:
""" + operators_json + """

ADVANCED FEATURES YOU CAN USE:
1. compareDateRange - for YOY, MOM comparisons
2. Nested AND/OR filters - for complex logic
3. Post-aggregation filters - filter on calculated measures
4. Time granularity - day, week, month, quarter, year
5. Multiple orderings - sort by multiple fields
6. Drilldown - for hierarchical analysis
7. Total - get total count with results

QUERY PATTERNS:
- Trends: Use timeDimensions with granularity
- Comparisons: Use compareDateRange or filters
- Top N: Use order + limit
- Distribution: Use dimensions without limit
- Cohort analysis: Use nested filters

QUERY FORMAT:
1. Use array format for filters (not object format)
2. Include "order": [] even if empty  
3. For time ranges, use inDateRange operator
4. order should be an object like {"field": "asc"} for simple ordering

EXAMPLE QUERIES:

Basic aggregation:
{
  "measures": ["ticket_line_items.amount"],
  "dimensions": ["productions.name"],
  "filters": [
    {
      "member": "productions.name",
      "operator": "contains",
      "values": ["GATSBY"]
    }
  ],
  "order": []
}

Top N with ordering:
{
  "measures": ["ticket_line_items.amount"],
  "dimensions": ["productions.name"],
  "filters": [],
  "order": {"ticket_line_items.amount": "desc"},
  "limit": 5
}

Time series with granularity:
{
  "measures": ["ticket_line_items.amount"],
  "timeDimensions": [{
    "dimension": "ticket_line_items.created_at_local",
    "granularity": "month",
    "dateRange": ["2024-01-01", "2024-12-31"]
  }],
  "order": []
}

Comparing multiple time periods (compareDateRange):
{
  "measures": ["ticket_line_items.amount"],
  "dimensions": ["productions.name"],
  "timeDimensions": [{
    "dimension": "ticket_line_items.created_at_local",
    "compareDateRange": [
      ["2024-01-01", "2024-03-31"],
      ["2024-04-01", "2024-06-30"],
      ["2024-07-01", "2024-09-30"],
      ["2024-10-01", "2024-12-31"]
    ]
  }],
  "order": []
}

IMPORTANT: When user asks to compare multiple time periods (Q1 vs Q2, this year vs last year, etc), use compareDateRange instead of dateRange. compareDateRange supports 2 or more date ranges.

Respond with ONLY valid JSON."""

        user_prompt = f"""Generate a Cube.js query for this request:

Query request: {getattr(inputs, 'query_request', 'Not specified')}
Time context: {getattr(inputs, 'time_context', 'Not specified')}
Time comparison type: {getattr(inputs, 'time_comparison_type', 'Not specified')}

Measures requested: {inputs.measures}
Dimensions requested: {inputs.dimensions if inputs.dimensions else 'none'}
Filters: {[f.model_dump() for f in inputs.filters] if inputs.filters else 'none'}
Order: {inputs.order if inputs.order else 'auto-determine based on query'}
Limit: {inputs.limit if inputs.limit else 'auto-determine based on query type'}

Analyze the request and determine the best query approach:
- If comparing time periods, use compareDateRange
- If showing trends over time, use timeDimensions with appropriate granularity
- If finding top/bottom performers, use order and limit
- If complex filtering is needed, use nested AND/OR filters
- If filtering on calculated values, use post-aggregation filters

Generate the most sophisticated query that answers this request using the exact field names from the schema."""

        # Log the user prompt for debugging
        logger.info(f"User prompt: {user_prompt}")
        
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
            raise ValueError("Failed to parse LLM response as JSON")
    
    async def _describe_query(self, query: Dict[str, Any], row_count: int) -> str:
        """Generate a description of what the query did"""
        parts = []
        
        if query.get("measures"):
            parts.append(f"Retrieved {', '.join(query['measures'])}")
        
        if query.get("dimensions"):
            parts.append(f"grouped by {', '.join(query['dimensions'])}")
            
        if query.get("filters"):
            parts.append(f"with {len(query['filters'])} filter(s) applied")
            
        if query.get("timeDimensions"):
            for td in query["timeDimensions"]:
                if "compareDateRange" in td:
                    parts.append("comparing time periods")
                elif "granularity" in td:
                    parts.append(f"at {td['granularity']} granularity")
                    
        if query.get("order"):
            # Order might be in different formats after LLM generation
            order_info = query['order']
            if isinstance(order_info, dict):
                parts.append("sorted by " + ', '.join(order_info.keys()))
            elif isinstance(order_info, list) and order_info:
                # Could be [["field", "asc"]] or [{"field": "asc"}]
                if isinstance(order_info[0], list):
                    fields = [item[0] for item in order_info]
                    parts.append("sorted by " + ', '.join(fields))
                elif isinstance(order_info[0], dict):
                    fields = [k for item in order_info for k in item.keys()]
                    parts.append("sorted by " + ', '.join(fields))
            else:
                parts.append("with ordering")
            
        if query.get("limit"):
            parts.append(f"limited to {query['limit']} results")
            
        return f"{' '.join(parts)}. Found {row_count} records."
    
    def _extract_key_findings(self, data_points: List[DataPoint], query: Dict[str, Any]) -> List[str]:
        """Extract key findings from the data"""
        findings = []
        
        if not data_points:
            return ["No data found matching the criteria"]
            
        # For top N queries, highlight the top performer
        if query.get("limit") and query.get("order") and data_points:
            first_point = data_points[0]
            measure_key = list(first_point.measures.keys())[0] if first_point.measures else None
            if measure_key:
                dim_key = list(first_point.dimensions.keys())[0] if first_point.dimensions else None
                if dim_key:
                    try:
                        value = float(first_point.measures[measure_key])
                        findings.append(
                            f"Top performer: {first_point.dimensions[dim_key]} "
                            f"with {measure_key}: {value:,.0f}"
                        )
                    except (ValueError, TypeError):
                        # If conversion fails, show the value as-is
                        findings.append(
                            f"Top performer: {first_point.dimensions[dim_key]} "
                            f"with {measure_key}: {first_point.measures[measure_key]}"
                        )
        
        # For time series, note if there's a trend
        if query.get("timeDimensions") and len(data_points) > 2:
            findings.append(f"Time series data with {len(data_points)} data points")
            
        return findings


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