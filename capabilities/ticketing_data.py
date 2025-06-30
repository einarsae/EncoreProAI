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
from datetime import datetime
import asyncio

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from pydantic import BaseModel

from capabilities.base import BaseCapability, CapabilityDescription, ResponseContext
from models.capabilities import (
    TicketingDataInputs, TicketingDataResult, DataPoint,
    CubeFilter
)
from services.cube_service import CubeService
from services.cube_meta_service import CubeMetaService

logger = logging.getLogger(__name__)


class QueryPlan(BaseModel):
    """Query execution plan from LLM"""
    strategy: str  # "single" or "multi"
    reasoning: str  # Why this strategy was chosen
    queries: List[Dict[str, Any]]  # One or more Cube.js queries
    metadata: Dict[str, Any] = {}  # Additional context for result combination


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
            purpose="Retrieve ticketing data: revenue, attendance, and sales metrics by production, venue, time period, and other dimensions. Can handle multiple queries in one request - different time periods, separate productions, or any combination of data needs.",
            category="data",
            inputs={
                "description": "Natural language description of what data you need (required)",
                "measures": "List of measures like ['ticket_line_items.amount'] for revenue or ['ticket_line_items.quantity'] for attendance",
                "dimensions": "List of dimensions like ['productions.name'] to group by",
                "filters": "List of filter objects: [{'member': 'productions.id', 'operator': 'equals', 'values': ['prod_id']}]",
                "time_context": "Time period like 'November 2024', 'Q1 2024', '2024'",
                "time_comparison_type": "Optional: year_over_year, month_over_month, etc.",
                "time_granularity": "Optional: day, week, month, quarter, year",
                "entities": "Resolved entities with IDs from orchestrator",
                "limit": "Optional: max rows to return (default 50)",
                "order": "Optional: sort object like {'ticket_line_items.amount': 'desc'}"
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
                "Revenue for Chicago from October to December 2024",
                "Attendance for Gatsby and Wicked this year",  
                "Top 5 venues by average ticket price",
                "Q1 and Q2 revenue data",
                "Daily sales for Chicago and Gatsby events",
                "Monthly revenue breakdown by production",
                "Page 3 of production revenues (50 per page)",
                "All productions with revenue over $1M"
            ]
        )
    
    def build_inputs(self, task: Dict[str, Any], state) -> TicketingDataInputs:
        """Build TicketingDataInputs from task and state"""
        # Get task inputs
        task_inputs = task.get("inputs", {})
        
        return TicketingDataInputs(
            session_id=state.core.session_id,
            tenant_id=state.core.tenant_id,
            user_id=state.core.user_id,
            query_request=task_inputs.get("description", state.core.query),
            measures=task_inputs.get("measures", []),
            dimensions=task_inputs.get("dimensions", []),
            filters=task_inputs.get("filters", []),
            order=task_inputs.get("order", {}),
            limit=task_inputs.get("limit", 50),
            offset=task_inputs.get("offset", 0),
            granularity=task_inputs.get("granularity"),
            time_context=task_inputs.get("time_context"),
            time_comparison_type=task_inputs.get("time_comparison_type"),
            time_granularity=task_inputs.get("time_granularity"),
            entities=task_inputs.get("entities", [])
        )
    
    def summarize_result(self, result: TicketingDataResult) -> str:
        """Summarize data retrieval result"""
        if result.success and result.data:
            if isinstance(result.data, list):
                return f"Retrieved {len(result.data)} data records"
            elif isinstance(result.data, dict) and 'queries' in result.data:
                # Multi-fetch result
                total_records = sum(len(q.get('data', [])) for q in result.data['queries'])
                return f"Retrieved {total_records} records across {len(result.data['queries'])} queries"
            else:
                return "Data retrieved successfully"
        elif result.success:
            return "Query completed but no data found"
        else:
            return "Data retrieval failed"
    
    def prepare_response_context(self, result: TicketingDataResult) -> Dict[str, Any]:
        """
        Prepare condensed context for response generation.
        
        For large datasets, provides summary statistics instead of raw data.
        For small datasets, includes the actual values.
        """
        context = {
            "success": result.success,
            "total_records": len(result.data) if result.data else 0,
        }
        
        if not result.success:
            context["error"] = result.error_message or "Data retrieval failed"
            return context
            
        if not result.data:
            context["summary"] = "No data found matching the query criteria"
            return context
            
        # For small results (1-5 records), include actual data
        if len(result.data) <= 5:
            context["data_points"] = []
            for dp in result.data:
                point = {}
                # Handle both dict and DataPoint objects
                if isinstance(dp, dict):
                    if "measures" in dp:
                        point["measures"] = dp["measures"]
                    if "dimensions" in dp:
                        point["dimensions"] = dp["dimensions"]
                else:
                    if hasattr(dp, "measures") and dp.measures:
                        point["measures"] = dp.measures
                    if hasattr(dp, "dimensions") and dp.dimensions:
                        point["dimensions"] = dp.dimensions
                context["data_points"].append(point)
                
            # Add query description if available
            if hasattr(result, 'query_metadata') and result.query_metadata:
                context["query_description"] = result.query_metadata.get("description", "")
                
        else:
            # For larger results, provide summary
            context["summary"] = f"Retrieved {len(result.data)} records"
            
            # Include sample of first few records
            context["sample_data"] = []
            for dp in result.data[:3]:  # First 3 as examples
                point = {}
                # Handle both dict and DataPoint objects
                if isinstance(dp, dict):
                    if "measures" in dp:
                        point["measures"] = dp["measures"]
                    if "dimensions" in dp:
                        point["dimensions"] = dp["dimensions"]
                else:
                    if hasattr(dp, "measures") and dp.measures:
                        point["measures"] = dp.measures
                    if hasattr(dp, "dimensions") and dp.dimensions:
                        point["dimensions"] = dp.dimensions
                context["sample_data"].append(point)
                
            # Add metadata about the full dataset
            if result.data and result.data[0].measures:
                context["measure_names"] = list(result.data[0].measures.keys())
            if result.data and result.data[0].dimensions:
                context["dimension_names"] = list(result.data[0].dimensions.keys())
                
        # Add any assumptions made
        if hasattr(result, 'assumptions') and result.assumptions:
            context["assumptions"] = result.assumptions
            
        return context
    
    async def execute(self, inputs: TicketingDataInputs) -> TicketingDataResult:
        """Execute data query using all Cube.js capabilities
        
        This method:
        1. Builds context from real Cube.js schema
        2. Uses LLM to generate query plan (single or multi-fetch)
        3. Executes queries based on plan
        4. Returns raw data with clear metadata
        5. Does NOT interpret or analyze results
        """
        
        logger.info(f"Processing data request: {getattr(inputs, 'query_request', 'No description')}")
        
        try:
            # Build comprehensive context for query generation
            context = await self._build_query_context(inputs)
            
            # Generate query plan using LLM - it decides single vs multi-fetch
            query_plan = await self._generate_query_plan(inputs, context)
            
            if not query_plan or not query_plan.queries:
                return TicketingDataResult(
                    success=False,
                    data=[],
                    total_rows=0,
                    total_columns=0,
                    total_measures=0,
                    assumptions=["Could not generate a valid query plan"],
                    query_metadata={"error": "Query planning failed"}
                )
            
            logger.info(f"Query plan: {query_plan.strategy} strategy with {len(query_plan.queries)} queries")
            
            # Execute based on strategy
            if query_plan.strategy == "single":
                # Single query path
                query = query_plan.queries[0]
                result = await self._execute_single_query(query, inputs.tenant_id)
                return self._format_single_result(result, query, query_plan)
            else:
                # Multi-fetch path
                results = await self._execute_multi_fetch(query_plan, inputs.tenant_id)
                return self._format_multi_result(results, query_plan)
            
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
            ]
        }
    
    async def _generate_advanced_query(self, inputs: TicketingDataInputs, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate sophisticated Cube.js query using all available features"""
        
        # Build comprehensive prompt with all Cube.js capabilities
        # Avoid f-string to prevent issues with JSON examples containing braces
        schema_json = json.dumps(context['schema'], indent=2)
        operators_json = json.dumps(context['all_operators'])
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        system_prompt = """You are a Cube.js query generator for a live entertainment ticketing system. Generate queries that fetch the requested data efficiently.

CONTEXT: This is a ticketing analytics system for theaters and live entertainment venues. The data includes ticket sales, productions (shows), events (performances), venues, and customer transactions.

SCHEMA:
""" + schema_json + """

QUERY STRUCTURE:
{
  "measures": ["cube.measure"],      // What to calculate
  "dimensions": ["cube.dimension"],  // How to group
  "timeDimensions": [{              // Time-based grouping
    "dimension": "cube.time_field",
    "dateRange": ["2024-01-01", "2024-12-31"],
    "granularity": "day|week|month|quarter|year"  // REQUIRED if timeDimensions is used!
  }],
  // OR for time filtering without grouping:
  "timeDimensions": [{
    "dimension": "cube.time_field",
    "dateRange": ["2024-01-01", "2024-12-31"]
    // NO granularity field - omit it entirely for filtering only
  }],
  "filters": [{                     // Data filtering
    "member": "cube.field",         // Always use "member" for filters
    "operator": "equals|contains|gt|lt|inDateRange|...",
    "values": ["value1", "value2"]
  }],
  // For complex filters, use AND/OR logic:
  "filters": [
    {"operator": "and", "filters": [
      {"member": "productions.name", "operator": "equals", "values": ["Gatsby"]},
      {"member": "ticket_line_items.amount", "operator": "gt", "values": [100]}
    ]}
  ],
  "order": {"cube.field": "asc|desc"},  // Sort by single field
  "limit": 100,                         // Max rows to return
  "offset": 0,                          // Skip rows (for pagination)
  "total": true                         // Return total count
}

ADDITIONAL FEATURES:
- offset: Skip N rows for pagination (e.g., offset: 100)
- total: Get total count of results (useful for pagination UI)
- Hierarchical data: Use multiple dimensions (e.g., ["retailers.name", "sales_channels.name"])

RULES:
1. Query must have at least one of: measures, dimensions, or timeDimensions with granularity
2. Use exact field names from schema (e.g., "ticket_line_items.amount")
3. When user specifies a limit, use that exact number
4. When adding any limit, also add order by the primary measure descending
5. Use "member" (not "dimension") as the key in filter objects
6. Empty order should be {}
7. Common translations:
   - "revenue" or "sales" → ticket_line_items.amount
   - "attendance" or "tickets" → ticket_line_items.quantity
   - "by show" or "by production" → productions.name
8. For timeDimensions:
   - When grouping by time, include granularity (day, week, month, quarter, year)
   - When filtering by time only, omit the granularity field
   - Valid filter: {"dimension": "...", "dateRange": ["2024-01-01", "2024-12-31"]}
   - Valid grouping: {"dimension": "...", "dateRange": [...], "granularity": "month"}
9. Convert relative dates to YYYY-MM-DD format
   - Example: "last month" → ["2024-11-01", "2024-11-30"]
   - Today is: """ + current_date + """

MEMORY CONSIDERATIONS:
Some dimensions have high cardinality (many unique values):
- ticket_line_items.customer_id: millions of values
- ticket_line_items.city/postcode: 50K+ values  
- events.id with daily data: can be 50K+ rows

When using these:
- Add reasonable limits (100-1000 rows)
- Or use coarser time granularity (weekly/monthly instead of daily)
- Or filter to specific values first

AVAILABLE OPERATORS:
""" + operators_json + """

EXAMPLES:

1. Paginated results:
{
  "measures": ["ticket_line_items.amount"],
  "dimensions": ["productions.name"],
  "order": {"ticket_line_items.amount": "desc"},
  "limit": 50,
  "offset": 100,
  "total": true
}

2. Hierarchical exploration (multiple dimensions):
{
  "measures": ["ticket_line_items.amount"],
  "dimensions": ["retailers.name", "sales_channels.name", "productions.name"],
  "order": {"ticket_line_items.amount": "desc"},
  "limit": 50
}

3. Time filtering WITHOUT grouping (no granularity):
{
  "measures": ["ticket_line_items.amount"],
  "dimensions": ["productions.name"],
  "timeDimensions": [{
    "dimension": "ticket_line_items.created_at_local",
    "dateRange": ["2024-01-01", "2024-03-31"]
    // NO granularity field here!
  }],
  "order": {"ticket_line_items.amount": "desc"},
  "limit": 10
}

4. Time grouping WITH granularity:
{
  "measures": ["ticket_line_items.amount"],
  "timeDimensions": [{
    "dimension": "ticket_line_items.created_at_local",
    "dateRange": ["2024-10-01", "2024-12-31"],
    "granularity": "month"  // REQUIRED for time grouping
  }],
  "order": {"ticket_line_items.created_at_local": "asc"}
}

NOTE: Use multiple dimensions for hierarchical data. NEVER use "granularity": null.

Respond with ONLY the JSON query."""

        user_prompt = f"""Generate a Cube.js query for:

Request: {getattr(inputs, 'query_request', 'Not specified')}
Time context: {getattr(inputs, 'time_context', 'Not specified')}

Provided inputs:
- Measures: {inputs.measures}
- Dimensions: {inputs.dimensions if inputs.dimensions else 'none'}
- Filters: {[f.model_dump() for f in inputs.filters] if inputs.filters else 'none'}
- Order: {inputs.order if inputs.order else 'none'}
- Limit: {inputs.limit if inputs.limit else 'none'}

If a specific limit is provided above, use that exact number."""

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
                query["order"] = {}
            
            # If there's a limit but no order, add default ordering by first measure
            if query.get("limit") and not query.get("order"):
                measures = query.get("measures", [])
                if measures:
                    query["order"] = {measures[0]: "desc"}
                    logger.info(f"Added default ordering by {measures[0]} desc due to limit")
            
            return query
        else:
            raise ValueError("Failed to parse LLM response as JSON")
    
    def _transform_cube_data_to_datapoints(self, cube_data: List[Dict], query: Dict) -> List[DataPoint]:
        """Transform Cube.js response rows to DataPoints"""
        data_points = []
        for row in cube_data:
            dimensions = {}
            measures = {}
            
            for key, value in row.items():
                if key in query.get("measures", []):
                    measures[key] = value
                else:
                    dimensions[key] = value
            
            data_points.append(DataPoint(
                dimensions=dimensions,
                measures=measures
            ))
        return data_points
    
    async def _generate_query_plan(self, inputs: TicketingDataInputs, context: Dict[str, Any]) -> QueryPlan:
        """Generate query execution plan using LLM"""
        
        schema_json = json.dumps(context['schema'], indent=2)
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        system_prompt = f"""You are a Cube.js query planner. Determine if a request needs one query or multiple queries.

SCHEMA:
{schema_json}

NOTE: Cube.js automatically handles joins between cubes. You can use measures and dimensions from different cubes in a single query.

WHEN TO USE MULTIPLE QUERIES:
- Comparing separate time periods (Q1 vs Q2, 2023 vs 2024)
- Keywords like "vs", "compare", "versus" between time periods
- Explicitly stated "per production" or "per event" comparisons

WHEN TO USE SINGLE QUERY:
- Simple aggregations (even across cubes)
- All data in one time range or no time specified
- Basic grouping and filtering
- Top N queries

QUERY STRUCTURE:
{{
  "measures": ["cube.measure"],
  "dimensions": ["cube.dimension"],
  "timeDimensions": [{{
    "dimension": "cube.time_field",
    "dateRange": ["2024-01-01", "2024-12-31"],
    "granularity": "day|week|month|quarter|year"  // Include ONLY if grouping by time
  }}],
  "filters": [{{
    "member": "cube.field",
    "operator": "equals|contains|...",
    "values": ["value"]
  }}],
  "order": {{"cube.field": "asc|desc"}},
  "limit": 100,
  "offset": 0,
  "total": true
}}

IMPORTANT RULES FOR TIME DIMENSIONS:
- If grouping by time: Include "granularity": "day|week|month|quarter|year"
- If just filtering by time: OMIT the granularity field entirely
- NEVER use "granularity": null - this causes errors!
- ALWAYS convert relative dates to explicit YYYY-MM-DD format
  Example: "last month" → ["2024-11-01", "2024-11-30"]
  Today is: """ + current_date + """

MEMORY CONSIDERATIONS (same as query generation):
- ticket_line_items.customer_id: use limits
- ticket_line_items.city/postcode: use limits  
- events.id with daily: use weekly/monthly instead

Return JSON:
{{
    "strategy": "single" or "multi",
    "reasoning": "Why this strategy",
    "queries": [/* array of queries */],
    "metadata": {{}}
}}

EXAMPLE - Multi-fetch for Q1 vs Q2 comparison:
{{
    "strategy": "multi",
    "reasoning": "Comparing two separate quarters",
    "queries": [
        {{
            "measures": ["ticket_line_items.amount"],
            "timeDimensions": [{{
                "dimension": "ticket_line_items.created_at_local",
                "dateRange": ["2024-01-01", "2024-03-31"]
                // No granularity - just filtering
            }}]
        }},
        {{
            "measures": ["ticket_line_items.amount"],
            "timeDimensions": [{{
                "dimension": "ticket_line_items.created_at_local",
                "dateRange": ["2024-04-01", "2024-06-30"]
                // No granularity - just filtering
            }}]
        }}
    ],
    "metadata": {{"comparison": "Q1 vs Q2 2024"}}
}}"""

        user_prompt = f"""Plan queries for:

Request: {getattr(inputs, 'query_request', 'Not specified')}
Time context: {getattr(inputs, 'time_context', 'Not specified')}

Provided inputs:
- Measures: {inputs.measures}
- Dimensions: {inputs.dimensions if inputs.dimensions else 'none'}
- Filters: {[f.model_dump() for f in inputs.filters] if inputs.filters else 'none'}
- Order: {inputs.order if inputs.order else 'none'}
- Limit: {inputs.limit if inputs.limit else 'none'}

If a specific limit is provided, use that exact number in all queries."""

        response = await self.llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        # Parse JSON response
        try:
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                plan_data = json.loads(json_match.group())
                return QueryPlan(**plan_data)
        except Exception as e:
            logger.error(f"Failed to parse query plan: {e}")
            # Fallback to single query with the original approach
            query = await self._generate_advanced_query(inputs, context)
            return QueryPlan(
                strategy="single",
                reasoning="Fallback to single query due to planning error",
                queries=[query] if query else []
            )
    
    async def _execute_single_query(self, query: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        """Execute a single Cube.js query"""
        return await self.cube_service.query(
            measures=query.get("measures", []),
            dimensions=query.get("dimensions", []),
            filters=query.get("filters", []),
            time_dimensions=query.get("timeDimensions"),
            order=query.get("order"),
            limit=query.get("limit"),
            offset=query.get("offset"),
            total=query.get("total"),
            tenant_id=tenant_id
        )
    
    async def _execute_multi_fetch(self, query_plan: QueryPlan, tenant_id: str) -> List[Dict[str, Any]]:
        """Execute multiple queries in parallel with partial result handling"""
        # Limit to 3 parallel queries
        queries_to_execute = query_plan.queries[:3]
        
        # Execute queries in parallel
        tasks = []
        for i, query in enumerate(queries_to_execute):
            task = self._execute_single_query(query, tenant_id)
            tasks.append((i, task))
        
        # Gather results with error handling
        results = []
        failed_queries = []
        
        for i, task in tasks:
            try:
                result = await task
                results.append({
                    "index": i,
                    "success": True,
                    "data": result,
                    "query": queries_to_execute[i]
                })
            except Exception as e:
                logger.error(f"Query {i} failed: {e}")
                failed_queries.append({
                    "index": i,
                    "error": str(e),
                    "query": queries_to_execute[i]
                })
                results.append({
                    "index": i,
                    "success": False,
                    "error": str(e),
                    "query": queries_to_execute[i]
                })
        
        return results
    
    def _format_single_result(self, result: Dict[str, Any], query: Dict[str, Any], query_plan: QueryPlan) -> TicketingDataResult:
        """Format result from single query execution"""
        # Use common transformation
        data_points = self._transform_cube_data_to_datapoints(result.get('data', []), query)
        
        # Calculate totals
        total_columns = 0
        total_measures = 0
        if data_points:
            first_point = data_points[0]
            total_columns = len(first_point.dimensions) + len(first_point.measures)
            total_measures = len(first_point.measures)
        
        return TicketingDataResult(
            success=True,
            data=data_points,
            query_metadata={
                "strategy": "single",
                "cube_response": {
                    "annotation": result.get('annotation', {}),
                    "query": query
                }
            },
            total_rows=len(data_points),
            total_columns=total_columns,
            total_measures=total_measures,
            assumptions=[query_plan.reasoning]
        )
    
    def _format_multi_result(self, results: List[Dict[str, Any]], query_plan: QueryPlan) -> TicketingDataResult:
        """Format and combine results from multi-fetch execution"""
        all_data_points = []
        successful_queries = 0
        failed_queries = []
        query_metadata = {
            "strategy": "multi",
            "total_queries": len(results),
            "fetch_groups": []
        }
        
        # Process each result
        for result_info in results:
            if result_info["success"]:
                successful_queries += 1
                query = result_info["query"]
                result = result_info["data"]
                
                # Extract entity label from query if available
                entity_label = "Unknown"
                if query.get("filters"):
                    for filter in query["filters"]:
                        if filter.get("member") == "productions.name":
                            entity_label = filter.get("values", ["Unknown"])[0]
                            break
                
                # Use common transformation
                entity_data_points = self._transform_cube_data_to_datapoints(
                    result.get('data', []), 
                    query
                )
                all_data_points.extend(entity_data_points)
                
                query_metadata["fetch_groups"].append({
                    "entity": entity_label,
                    "rows": len(entity_data_points),
                    "success": True
                })
            else:
                failed_queries.append({
                    "index": result_info["index"],
                    "error": result_info["error"]
                })
                query_metadata["fetch_groups"].append({
                    "entity": "Failed",
                    "rows": 0,
                    "success": False,
                    "error": result_info["error"]
                })
        
        # Add failed query info if any
        if failed_queries:
            query_metadata["failed_queries"] = failed_queries
            query_metadata["successful_queries"] = successful_queries
        
        # Calculate totals
        total_columns = 0
        total_measures = 0
        if all_data_points:
            first_point = all_data_points[0]
            total_columns = len(first_point.dimensions) + len(first_point.measures)
            total_measures = len(first_point.measures)
        
        # Build assumptions
        assumptions = [query_plan.reasoning]
        if failed_queries:
            assumptions.append(f"Partial results: {successful_queries} of {len(results)} queries succeeded")
        
        return TicketingDataResult(
            success=successful_queries > 0,  # Success if at least one query worked
            data=all_data_points,
            query_metadata=query_metadata,
            total_rows=len(all_data_points),
            total_columns=total_columns,
            total_measures=total_measures,
            assumptions=assumptions
        )