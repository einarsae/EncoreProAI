"""Debug assumptions"""
import asyncio
import os
from capabilities.ticketing_data import TicketingDataCapability
from models.capabilities import TicketingDataInputs

async def debug():
    capability = TicketingDataCapability()
    inputs = TicketingDataInputs(
        session_id="test",
        tenant_id=os.getenv("DEFAULT_TENANT_ID", "yesplan"),
        user_id="test",
        measures=["ticket_line_items.amount"],
        dimensions=["productions.name"],
        order={"ticket_line_items.amount": "desc"},
        limit=5
    )
    
    result = await capability.execute(inputs)
    print(f"Success: {result.success}")
    print(f"Rows: {result.total_rows}")
    print(f"Assumptions: {result.assumptions}")

if __name__ == "__main__":
    asyncio.run(debug())