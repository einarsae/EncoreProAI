#!/usr/bin/env python3
"""
Test just the dynamic capability description functionality
"""

import asyncio
from workflow.nodes import WorkflowNodes
from models.state import AgentState, CoreState

async def main():
    """Test dynamic capability descriptions without full orchestration"""
    
    print("Testing Dynamic Capability Descriptions")
    print("=" * 80)
    
    # Initialize workflow nodes
    nodes = WorkflowNodes()
    
    print("\n1. Loaded Capabilities:")
    print("-" * 40)
    for name, cap in nodes.capabilities.items():
        print(f"  ✓ {name}: {type(cap).__name__}")
    
    print("\n2. Capability Descriptions:")
    print("-" * 40)
    
    for name, cap in nodes.capabilities.items():
        desc = cap.describe()
        print(f"\n{name.upper()}:")
        print(f"  Purpose: {desc.purpose}")
        print(f"  Inputs:")
        for field, description in desc.inputs.items():
            print(f"    - {field}: {description}")
        print(f"  Outputs:")
        for field, description in desc.outputs.items():
            print(f"    - {field}: {description}")
        if desc.examples:
            print(f"  Examples:")
            for i, example in enumerate(desc.examples[:2], 1):  # Show first 2 examples
                print(f"    {i}. {example}")
    
    print("\n3. Dynamic Context Generation:")
    print("-" * 40)
    
    # Test the _build_capabilities_context method
    capabilities_context = nodes._build_capabilities_context()
    print("\nGenerated Context (first 1000 chars):")
    print("-" * 40)
    print(capabilities_context[:1000])
    if len(capabilities_context) > 1000:
        print(f"\n... (truncated, total length: {len(capabilities_context)} chars)")
    
    print("\n4. Sample Orchestration Context:")
    print("-" * 40)
    
    # Create a test state
    state = AgentState(
        core=CoreState(
            session_id="test-session",
            user_id="test-user",
            tenant_id="test-tenant",
            query="Show me Hamilton revenue"
        )
    )
    
    # Build orchestration context
    context = nodes._build_orchestration_context(state)
    
    # Show the capabilities section
    cap_section_start = context.find("Available Capabilities:")
    if cap_section_start != -1:
        cap_section = context[cap_section_start:cap_section_start + 800]
        print("\nCapabilities Section in Context:")
        print("-" * 40)
        print(cap_section)
        print("...")
    
    print("\n✅ Test Complete!")
    print(f"\nSummary:")
    print(f"  - {len(nodes.capabilities)} capabilities loaded")
    print(f"  - All capabilities have describe() method")
    print(f"  - Dynamic context generated successfully")
    print(f"  - Context length: {len(capabilities_context)} characters")

if __name__ == "__main__":
    asyncio.run(main())