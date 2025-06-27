"""
EventAnalysisCapability - Intelligent Analysis of Ticketing Data

Takes raw data from TicketingDataCapability and provides insights:
- Trend analysis
- Performance comparisons
- Anomaly detection
- Actionable recommendations

Can make progressive data requests through the orchestrator.
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import logging

from capabilities.base import BaseCapability, CapabilityDescription
from models.capabilities import (
    CapabilityInputs, CapabilityResult,
    EventAnalysisInputs, EventAnalysisResult, 
    AnalysisInsight, AnalysisCriteria
)

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.schema import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


class EventAnalysisCapability(BaseCapability):
    """Intelligent analysis of event and ticketing data"""
    
    def __init__(self):
        # Use LLM_TIER_PREMIUM for high-quality analysis
        self.llm = ChatOpenAI(
            model=os.getenv("LLM_TIER_PREMIUM", "gpt-4.1-2025-04-14"),
            temperature=0.3
        )
        logger.info(f"EventAnalysisCapability initialized with model: {self.llm.model_name}")
    
    def describe(self) -> CapabilityDescription:
        """Describe capability for orchestrator"""
        return CapabilityDescription(
            name="event_analysis",
            purpose="Analyze ticketing data to identify trends, patterns, and provide actionable insights",
            inputs={
                "data_context": "Results from previous data queries (from TicketingDataCapability)",
                "analysis_criteria": "What type of analysis to perform (trends, comparison, anomalies)",
                "comparison_entities": "Optional list of entities to compare"
            },
            outputs={
                "insights": "List of discovered patterns and trends",
                "summary": "Executive summary of the analysis",
                "recommendations": "Actionable recommendations based on data",
                "confidence": "Confidence level of the analysis"
            },
            examples=[
                "How is Chicago performing compared to last month?",
                "What are the trends for my top shows?",
                "Are there any concerning patterns in ticket sales?",
                "Which shows should I focus on?",
                "Compare Gatsby with Chicago"
            ]
        )
    
    async def execute(self, inputs: EventAnalysisInputs) -> EventAnalysisResult:
        """Execute analysis on provided data"""
        
        logger.info(f"Executing analysis: {inputs.analysis_criteria.analysis_type}")
        
        # Extract data from context
        data_context = inputs.data_context
        analysis_type = inputs.analysis_criteria.analysis_type
        
        # Build analysis prompt based on type
        if analysis_type == "performance":
            return await self._analyze_performance(data_context, inputs.analysis_criteria)
        elif analysis_type == "trends":
            return await self._analyze_trends(data_context, inputs.analysis_criteria)
        elif analysis_type == "comparison":
            return await self._analyze_comparison(data_context, inputs.comparison_entities)
        elif analysis_type == "anomalies":
            return await self._analyze_anomalies(data_context, inputs.analysis_criteria)
        else:
            # General analysis
            return await self._analyze_general(data_context, inputs.analysis_criteria)
    
    async def _analyze_performance(self, data_context: Dict[str, Any], criteria: AnalysisCriteria) -> EventAnalysisResult:
        """Analyze performance metrics"""
        
        prompt = self._build_performance_prompt(data_context, criteria)
        response = await self._get_llm_analysis(prompt)
        
        return self._parse_analysis_response(response)
    
    async def _analyze_trends(self, data_context: Dict[str, Any], criteria: AnalysisCriteria) -> EventAnalysisResult:
        """Analyze trends over time"""
        
        prompt = self._build_trends_prompt(data_context, criteria)
        response = await self._get_llm_analysis(prompt)
        
        return self._parse_analysis_response(response)
    
    async def _analyze_comparison(self, data_context: Dict[str, Any], entities: List[str]) -> EventAnalysisResult:
        """Compare multiple entities"""
        
        prompt = self._build_comparison_prompt(data_context, entities)
        response = await self._get_llm_analysis(prompt)
        
        return self._parse_analysis_response(response)
    
    async def _analyze_anomalies(self, data_context: Dict[str, Any], criteria: AnalysisCriteria) -> EventAnalysisResult:
        """Detect anomalies in data"""
        
        prompt = self._build_anomaly_prompt(data_context, criteria)
        response = await self._get_llm_analysis(prompt)
        
        return self._parse_analysis_response(response)
    
    async def _analyze_general(self, data_context: Dict[str, Any], criteria: AnalysisCriteria) -> EventAnalysisResult:
        """General analysis when type is not specific"""
        
        prompt = self._build_general_prompt(data_context, criteria)
        response = await self._get_llm_analysis(prompt)
        
        return self._parse_analysis_response(response)
    
    def _build_performance_prompt(self, data_context: Dict[str, Any], criteria: AnalysisCriteria) -> str:
        """Build prompt for performance analysis"""
        
        data_summary = self._summarize_data_context(data_context)
        
        return f"""
You are a theater analytics expert analyzing performance data.

Data provided:
{data_summary}

Analysis requested: {criteria.criteria.get('description', 'General analysis')}

Analyze this data and provide:
1. Key performance metrics and what they mean
2. Whether performance is strong, average, or concerning
3. Specific factors driving the performance
4. Actionable recommendations

Focus on:
- Revenue trends
- Attendance patterns
- Average ticket price changes
- Capacity utilization (if available)

Return JSON:
{{
    "insights": [
        {{
            "type": "performance",
            "description": "Clear insight about performance",
            "confidence": 0.0-1.0,
            "supporting_data": {{}}
        }}
    ],
    "summary": "2-3 sentence executive summary",
    "recommendations": ["Specific actionable recommendations"],
    "confidence": 0.0-1.0,
    "suggested_visualizations": ["line_chart_revenue_trend", "bar_chart_show_comparison"]
}}
"""
    
    def _build_trends_prompt(self, data_context: Dict[str, Any], criteria: AnalysisCriteria) -> str:
        """Build prompt for trends analysis"""
        
        data_summary = self._summarize_data_context(data_context)
        
        return f"""
You are a theater analytics expert analyzing trends in ticketing data.

Data provided:
{data_summary}

Analysis requested: {criteria.criteria.get('description', 'General analysis')}

Identify trends and patterns:
1. Direction of key metrics (increasing/decreasing/stable)
2. Rate of change and acceleration
3. Seasonal or cyclical patterns
4. Emerging opportunities or concerns

Return JSON:
{{
    "insights": [
        {{
            "type": "trend",
            "description": "Clear description of the trend",
            "confidence": 0.0-1.0,
            "supporting_data": {{
                "direction": "up/down/stable",
                "change_rate": "percentage or description"
            }}
        }}
    ],
    "summary": "2-3 sentence executive summary",
    "recommendations": ["Actions based on trends"],
    "confidence": 0.0-1.0,
    "suggested_visualizations": ["time_series_chart", "trend_line_with_forecast"]
}}
"""
    
    def _build_comparison_prompt(self, data_context: Dict[str, Any], entities: List[str]) -> str:
        """Build prompt for comparison analysis"""
        
        data_summary = self._summarize_data_context(data_context)
        
        return f"""
You are a theater analytics expert comparing performance across shows.

Data provided:
{data_summary}

Compare these entities: {', '.join(entities)}

Provide comparative analysis:
1. Relative performance of each entity
2. Key differences in metrics
3. Strengths and weaknesses of each
4. Which is performing best and why

Return JSON:
{{
    "insights": [
        {{
            "type": "comparison",
            "description": "Key comparison finding",
            "confidence": 0.0-1.0,
            "supporting_data": {{
                "entity": "name",
                "metric": "value"
            }}
        }}
    ],
    "summary": "2-3 sentence comparison summary",
    "recommendations": ["Strategic recommendations based on comparison"],
    "confidence": 0.0-1.0,
    "suggested_visualizations": ["grouped_bar_chart", "radar_chart_comparison"]
}}
"""
    
    def _build_anomaly_prompt(self, data_context: Dict[str, Any], criteria: AnalysisCriteria) -> str:
        """Build prompt for anomaly detection"""
        
        data_summary = self._summarize_data_context(data_context)
        
        return f"""
You are a theater analytics expert looking for anomalies and unusual patterns.

Data provided:
{data_summary}

Analysis requested: {criteria.criteria.get('description', 'General analysis')}

Identify anomalies:
1. Unusual spikes or drops in metrics
2. Patterns that deviate from normal
3. Potential data quality issues
4. Concerning trends that need attention

Return JSON:
{{
    "insights": [
        {{
            "type": "anomaly",
            "description": "Description of the anomaly",
            "confidence": 0.0-1.0,
            "supporting_data": {{
                "metric": "what is unusual",
                "deviation": "how much it deviates"
            }}
        }}
    ],
    "summary": "2-3 sentence summary of findings",
    "recommendations": ["How to investigate or address anomalies"],
    "confidence": 0.0-1.0,
    "suggested_visualizations": ["scatter_plot_outliers", "control_chart"]
}}
"""
    
    def _build_general_prompt(self, data_context: Dict[str, Any], criteria: AnalysisCriteria) -> str:
        """Build prompt for general analysis"""
        
        data_summary = self._summarize_data_context(data_context)
        context_str = json.dumps(criteria.context) if criteria.context else "No additional context"
        
        return f"""
You are a theater analytics expert providing insights on ticketing data.

Data provided:
{data_summary}

Analysis requested: {criteria.criteria.get('description', 'General analysis')}
Context: {context_str}

Provide comprehensive analysis including:
1. Key insights from the data
2. What's working well
3. Areas of concern
4. Opportunities for improvement

Keep insights concise and actionable.

Return JSON:
{{
    "insights": [
        {{
            "type": "general",
            "description": "Clear, actionable insight",
            "confidence": 0.0-1.0,
            "supporting_data": {{}}
        }}
    ],
    "summary": "2-3 sentence executive summary",
    "recommendations": ["Specific actions to take"],
    "confidence": 0.0-1.0,
    "suggested_visualizations": ["appropriate chart types based on data"]
}}
"""
    
    def _summarize_data_context(self, data_context: Dict[str, Any]) -> str:
        """Convert data context into readable summary"""
        
        summary_parts = []
        
        # Look for task results from previous capability executions
        for key, value in data_context.items():
            if isinstance(value, dict) and "data" in value:
                summary_parts.append(f"\nData from {key}:")
                
                # If it has the structure of a TicketingDataResult
                if "total_rows" in value:
                    summary_parts.append(f"Total rows: {value['total_rows']}")
                
                # Summarize the data points
                data_points = value.get("data", [])[:10]  # First 10 rows
                for dp in data_points:
                    if isinstance(dp, dict):
                        # Handle our DataPoint structure
                        dims = dp.get("dimensions", {})
                        measures = dp.get("measures", {})
                        
                        dim_str = ", ".join([f"{k}: {v}" for k, v in dims.items() if v])
                        measure_str = ", ".join([f"{k}: {v}" for k, v in measures.items() if v])
                        
                        if dim_str and measure_str:
                            summary_parts.append(f"  {dim_str} → {measure_str}")
                        elif measure_str:
                            summary_parts.append(f"  {measure_str}")
                
                if len(data_points) > 10:
                    summary_parts.append(f"  ... and {len(data_points) - 10} more rows")
        
        return "\n".join(summary_parts) if summary_parts else "No data provided"
    
    async def _get_llm_analysis(self, prompt: str) -> Dict[str, Any]:
        """Get analysis from LLM"""
        
        messages = [
            SystemMessage(content="""You are a theater industry analytics expert. 
Provide data-driven insights that are actionable and specific. 
Be concise but thorough. 
Always include confidence scores based on data quality and completeness.
Suggest visualizations that would help communicate the insights."""),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        # Parse JSON response
        try:
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
        
        # Fallback response
        return {
            "insights": [{
                "type": "general",
                "description": "Analysis completed but response parsing failed",
                "confidence": 0.5,
                "supporting_data": {}
            }],
            "summary": response.content[:200] if response.content else "Analysis error",
            "recommendations": ["Review the raw data for patterns"],
            "confidence": 0.5,
            "suggested_visualizations": []
        }
    
    def _parse_analysis_response(self, response: Dict[str, Any]) -> EventAnalysisResult:
        """Parse LLM response into EventAnalysisResult"""
        
        # Convert insights
        insights = []
        for insight_data in response.get("insights", []):
            insights.append(AnalysisInsight(
                type=insight_data.get("type", "general"),
                description=insight_data.get("description", ""),
                confidence=float(insight_data.get("confidence", 0.7)),
                supporting_data=insight_data.get("supporting_data", {})
            ))
        
        return EventAnalysisResult(
            success=True,
            insights=insights,
            summary=response.get("summary", "Analysis complete"),
            recommendations=response.get("recommendations", []),
            confidence=float(response.get("confidence", 0.7)),
            metadata={
                "llm_used": self.llm.model_name,
                "analysis_timestamp": datetime.now().isoformat(),
                "suggested_visualizations": response.get("suggested_visualizations", [])
            }
        )