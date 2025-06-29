"""Test only natural language"""
import asyncio
import os
import json
from capabilities.ticketing_data import TicketingDataCapability
from models.capabilities import TicketingDataInputs


async def test_nl():
    capability = TicketingDataCapability()
    tenant_id = os.getenv("DEFAULT_TENANT_ID", "yesplan")
    
    inputs = TicketingDataInputs(
        session_id="verify",
        tenant_id=tenant_id,
        user_id="test",
        query_request="What were the sales trends for Chicago last month broken down by week?",
        measures=["ticket_line_items.amount"],
        time_context="last month"
    )
    
    context = await capability._build_query_context(inputs)
    query_plan = await capability._generate_query_plan(inputs, context)
    
    print(f"Query plan queries:")
    for i, query in enumerate(query_plan.queries):
        print(f"\nQuery {i}:")
        print(json.dumps(query, indent=2))

if __name__ == "__main__":
    asyncio.run(test_nl())