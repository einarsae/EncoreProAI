"""
EventAnalysisCapability - Simple MVP Implementation

Takes raw data from TicketingDataCapability and provides insights using LLM.
Can request additional data through orchestrator hints.

MVP Features:
- Basic LLM-driven analysis
- Progressive data requests
- Natural language insights
- Entity ID-based filtering

Future enhancements tracked in docs/API_REFERENCE.md
"""

import os
from typing import Dict, Any, List
import logging

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from capabilities.base import BaseCapability, CapabilityDescription
from models.capabilities import EventAnalysisInputs, EventAnalysisResult, DataPoint

logger = logging.getLogger(__name__)


# Pydantic model for structured LLM response
class AnalysisResponse(BaseModel):
    """Structured response from LLM analysis"""
    insights: List[str] = Field(description="Key findings from the data")
    recommendations: List[str] = Field(description="Actionable recommendations")
    needs_more_data: bool = Field(default=False, description="Whether additional data is needed")
    additional_data_request: str = Field(default="", description="What additional data is needed")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Confidence in analysis")


class EventAnalysisCapability(BaseCapability):
    """Simple LLM-driven analysis of ticketing data"""
    
    def __init__(self):
        # Use premium tier for analysis
        self.llm = ChatOpenAI(
            model=os.getenv("LLM_TIER_PREMIUM", "gpt-4o"),
            temperature=0.1
        )
        logger.info(f"EventAnalysisCapability initialized with model: {self.llm.model_name}")
    
    def describe(self) -> CapabilityDescription:
        """Describe capability for orchestrator"""
        return CapabilityDescription(
            name="event_analysis",
            purpose="Analyze ticketing data to identify trends, patterns, anomalies, and provide actionable insights. Can progressively request more data to deepen analysis.",
            category="analysis",
            inputs={
                "analysis_request": "What insights or analysis you need",
                "data": "Optional: Pre-fetched data to analyze",
                "entities": "Resolved entities with IDs from orchestrator",
                "time_context": "Period for analysis"
            },
            outputs={
                "insights": "Key findings and patterns",
                "recommendations": "Actionable suggestions",
                "analysis_complete": "Whether analysis is done or needs more data",
                "orchestrator_hints": "Hints for what to do next"
            },
            examples=[
                "How is Chicago performing?",
                "Analyze revenue trends for all shows",
                "Find anomalies in ticket sales",
                "Compare Chicago and Gatsby performance",
                "Which shows are underperforming?"
            ]
        )
    
    def build_inputs(self, task: Dict[str, Any], state) -> EventAnalysisInputs:
        """Build EventAnalysisInputs from task and state"""
        # Get task inputs
        task_inputs = task.get("inputs", {})
        
        return EventAnalysisInputs(
            session_id=state.core.session_id,
            tenant_id=state.core.tenant_id,
            user_id=state.core.user_id,
            analysis_request=task_inputs.get("description", state.core.query),
            data=task_inputs.get("data"),
            entities=task_inputs.get("entities", []),
            time_context=task_inputs.get("time_context")
        )
    
    def summarize_result(self, result: EventAnalysisResult) -> str:
        """Summarize analysis result"""
        if result.summary:
            return f"Analysis complete: {result.summary}"
        elif result.insights:
            return f"Generated {len(result.insights)} insights"
        elif result.analysis_complete:
            return "Analysis completed"
        else:
            return "Analysis in progress - need more data"
    
    async def execute(self, inputs: EventAnalysisInputs) -> EventAnalysisResult:
        """Execute analysis - simple MVP version"""
        
        logger.info(f"Analyzing: {inputs.analysis_request}")
        
        # Check if we have data to analyze
        if not inputs.data:
            # First call - need initial data
            return self._request_initial_data(inputs)
        
        # We have data - analyze it
        return await self._analyze_data(inputs)
    
    def _request_initial_data(self, inputs: EventAnalysisInputs) -> EventAnalysisResult:
        """Create initial data request"""
        
        # Build natural language description for what data we need
        data_description = self._determine_initial_data_needs(inputs)
        
        return EventAnalysisResult(
            success=True,
            insights=[],
            recommendations=[],
            analysis_complete=False,
            confidence=0.0,
            orchestrator_hints={
                "needs_data": True,
                "suggested_capability": "ticketing_data",
                "data_request": {
                    "natural_language": data_description,
                    "analysis_context": inputs.analysis_request,
                    "entities": inputs.entities,
                    "time_context": inputs.time_context
                },
                "reasoning": "Need initial data to begin analysis"
            }
        )
    
    def _determine_initial_data_needs(self, inputs: EventAnalysisInputs) -> str:
        """Figure out what initial data to request
        
        Note: We use entity names in natural language for clarity,
        but the orchestrator should convert these to IDs when building
        the actual TicketingDataInputs.
        """
        
        request = inputs.analysis_request.lower()
        entities_str = ", ".join([e.get("name", "") for e in inputs.entities]) if inputs.entities else ""
        
        # Simple heuristics for common requests
        if "trend" in request:
            time_context = inputs.time_context or "last 6 months"
            return f"Get {entities_str or 'all shows'} revenue and attendance over {time_context} with monthly granularity"
        
        elif "compar" in request:
            return f"Get revenue, attendance, and average ticket price for {entities_str or 'all shows'} for {inputs.time_context or 'last 3 months'}"
        
        elif "anomal" in request or "unusual" in request:
            return f"Get daily revenue and attendance for {entities_str or 'all shows'} for {inputs.time_context or 'last month'}"
        
        elif "underperform" in request or "overperform" in request:
            return f"Get revenue and attendance by show for {inputs.time_context or 'last 3 months'} to identify performance levels"
        
        else:
            # Generic request
            return f"Get revenue and attendance data for {entities_str or inputs.analysis_request} for {inputs.time_context or 'recent period'}"
    
    async def _analyze_data(self, inputs: EventAnalysisInputs) -> EventAnalysisResult:
        """Analyze provided data with LLM using structured output"""
        
        # Format data for LLM
        data_summary = self._format_data_for_analysis(inputs.data)
        
        # Build analysis prompt - no need to specify JSON structure
        analysis_prompt = f"""
        You are analyzing ticketing data for: {inputs.analysis_request}
        
        Entities involved: {inputs.entities}
        Time context: {inputs.time_context}
        
        Data provided:
        {data_summary}
        
        Please analyze this data and provide:
        1. Key insights with specific numbers and percentages
        2. Actionable recommendations based on the data
        3. Whether you need additional data to complete the analysis
        
        Be quantitative and specific. Focus on actionable insights.
        """
        
        # Get structured LLM analysis
        messages = [
            SystemMessage(content="You are a theater analytics expert. Provide clear, data-driven insights."),
            HumanMessage(content=analysis_prompt)
        ]
        
        # Use structured output with enforced schema
        try:
            # Get structured response - it returns the Pydantic object directly
            analysis = await self.llm.with_structured_output(AnalysisResponse).ainvoke(messages)
            
        except Exception as e:
            logger.error(f"Failed to get structured response: {e}")
            # Fallback - use the same Pydantic model
            analysis = AnalysisResponse(
                insights=["Analysis failed - please try again"],
                recommendations=[],
                needs_more_data=False,
                confidence=0.5
            )
        
        # Build result based on structured response
        if analysis.needs_more_data:
            return EventAnalysisResult(
                success=True,
                insights=analysis.insights,
                recommendations=analysis.recommendations,
                analysis_complete=False,
                confidence=analysis.confidence,
                orchestrator_hints={
                    "needs_data": True,
                    "suggested_capability": "ticketing_data",
                    "data_request": {
                        "natural_language": analysis.additional_data_request or "Need more data",
                        "partial_analysis": True,
                        "context": "Additional data for deeper analysis"
                    },
                    "reasoning": "Need more data to complete analysis"
                }
            )
        else:
            return EventAnalysisResult(
                success=True,
                insights=analysis.insights,
                recommendations=analysis.recommendations,
                analysis_complete=True,
                confidence=analysis.confidence,
                orchestrator_hints={
                    "analysis_complete": True,
                    "suggested_action": "present_to_user"
                }
            )
    
    def _format_data_for_analysis(self, data: List[DataPoint]) -> str:
        """Format data into readable summary for LLM"""
        
        if not data:
            return "No data provided"
        
        # Expect List[DataPoint] from TicketingDataCapability
        if not isinstance(data, list):
            raise TypeError(f"Expected List[DataPoint], got {type(data)}")
        
        lines = ["Data points:"]
        for i, point in enumerate(data[:20]):  # First 20 points
            # DataPoint must have dimensions and measures attributes
            dim_str = ", ".join([f"{k}: {v}" for k, v in point.dimensions.items()])
            measure_str = ", ".join([f"{k}: {v}" for k, v in point.measures.items()])
            lines.append(f"{i+1}. {dim_str} → {measure_str}")
        
        if len(data) > 20:
            lines.append(f"... and {len(data) - 20} more rows")
        
        return "\n".join(lines)