"""
LangGraph Workflow Definition

Defines the orchestration graph with frame-based routing.
Single-task execution with continuous replanning.
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage

from models.state import AgentState, CoreState
from workflow.nodes import WorkflowNodes


def create_workflow():
    """Create the LangGraph workflow"""
    
    # Initialize nodes
    nodes = WorkflowNodes()
    
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("extract_frames", nodes.extract_frames_node)
    workflow.add_node("resolve_entities", nodes.resolve_entities_node)
    workflow.add_node("orchestrate", nodes.orchestrate_node)
    workflow.add_node("execute_chat", nodes.execute_chat_node)
    workflow.add_node("execute_ticketing_data", nodes.execute_ticketing_data_node)
    workflow.add_node("execute_event_analysis", nodes.execute_event_analysis_node)
    
    # Define routing function
    def route_by_next_node(state: AgentState) -> str:
        """Route based on next_node in state"""
        next_node = state.routing.next_node
        
        # Map "end" to LangGraph's END
        if next_node == "end":
            return END
            
        return next_node
    
    # Add conditional edges
    workflow.add_conditional_edges("extract_frames", route_by_next_node)
    workflow.add_conditional_edges("resolve_entities", route_by_next_node)
    workflow.add_conditional_edges("orchestrate", route_by_next_node)
    workflow.add_conditional_edges("execute_chat", route_by_next_node)
    workflow.add_conditional_edges("execute_ticketing_data", route_by_next_node)
    workflow.add_conditional_edges("execute_event_analysis", route_by_next_node)
    
    # Set entry point
    workflow.set_entry_point("extract_frames")
    
    # Compile
    return workflow.compile()


async def process_query(
    query: str,
    session_id: str,
    user_id: str,
    tenant_id: str,
    debug: bool = False
) -> Dict[str, Any]:
    """Process a user query through the workflow"""
    
    # Create initial state
    initial_state = AgentState(
        core=CoreState(
            session_id=session_id,
            user_id=user_id,
            tenant_id=tenant_id,
            query=query
        )
    )
    
    # Add user message
    initial_state.add_message("user", query)
    
    # Enable debug if requested
    if debug:
        from models.state import DebugState
        initial_state.debug = DebugState(trace_enabled=True)
    
    # Create and run workflow
    workflow = create_workflow()
    
    # Run with streaming to see progress (optional)
    if debug:
        async for chunk in workflow.astream(initial_state, {"recursion_limit": 15}):
            node_name = list(chunk.keys())[0] if chunk else "unknown"
            print(f"Processing: {node_name}")
    
    # Get final state using ainvoke
    try:
        final_state_dict = await workflow.ainvoke(initial_state, {"recursion_limit": 15})
        
        # Extract state components
        if isinstance(final_state_dict, dict) and 'core' in final_state_dict:
            core = final_state_dict['core']
            return {
                "success": core.status == "complete",
                "response": core.final_response,
                "messages": [msg.model_dump() for msg in core.messages] if hasattr(core, 'messages') else [],
                "debug": final_state_dict.get('debug').model_dump() if final_state_dict.get('debug') else None
            }
        else:
            return {
                "success": False,
                "error": "Unexpected workflow result format",
                "response": None
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "response": None
        }