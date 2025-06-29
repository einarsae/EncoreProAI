"""
Debug natural language query generation
"""
import asyncio
import os
import json
from capabilities.ticketing_data import TicketingDataCapability
from models.capabilities import TicketingDataInputs


async def debug_nl_query():
    """Debug why Chicago filter isn't being added"""
    
    capability = TicketingDataCapability()
    tenant_id = os.getenv("DEFAULT_TENANT_ID", "yesplan")
    
    inputs = TicketingDataInputs(
        session_id="debug",
        tenant_id=tenant_id,
        user_id="test",
        query_request="What were the sales trends for Chicago last month broken down by week?",
        measures=["ticket_line_items.amount"],
        time_context="last month"
    )
    
    context = await capability._build_query_context(inputs)
    query_plan = await capability._generate_query_plan(inputs, context)
    
    print("Query Plan:")
    print(f"Strategy: {query_plan.strategy}")
    print(f"Reasoning: {query_plan.reasoning}")
    print(f"\nGenerated Queries:")
    for i, query in enumerate(query_plan.queries):
        print(f"\nQuery {i+1}:")
        print(json.dumps(query, indent=2))


if __name__ == "__main__":
    asyncio.run(debug_nl_query())