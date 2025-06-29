# TicketingDataCapability - Advanced Features

## Overview

TicketingDataCapability is a sophisticated data retrieval service that leverages ALL Cube.js features. It uses an LLM to translate natural language requests into complex Cube.js queries.

## Key Capabilities

### 1. Time Period Comparisons (compareDateRange)
The capability can compare multiple time periods in a single query:
- **Year-over-Year (YOY)**: Compare this year vs last year
- **Month-over-Month (MOM)**: Compare consecutive months
- **Quarter-over-Quarter (QOQ)**: Compare quarters
- **Week-over-Week (WOW)**: Compare weeks
- **Custom periods**: Any two date ranges

Example queries:
- "Compare Q1 vs Q2 revenue"
- "Show YOY growth for Chicago"
- "Compare this month to same month last year"

### 2. Time Series Analysis
Supports various time granularities:
- Hour, day, week, month, quarter, year
- Custom date ranges
- Rolling windows

Example queries:
- "Show daily revenue for last 30 days"
- "Monthly trends for 2024"
- "Weekly attendance patterns"

### 3. Complex Filtering
Supports nested AND/OR logic:
```json
{
  "or": [
    {
      "and": [
        {"member": "city", "operator": "equals", "values": ["Chicago"]},
        {"member": "amount", "operator": "gt", "values": [100]}
      ]
    },
    {
      "member": "productions.name", "operator": "contains", "values": ["GATSBY"]
    }
  ]
}
```

### 4. Post-Aggregation Filters
Filter on calculated measures (HAVING clause):
- "Shows with average ticket price > $100"
- "Venues with total revenue > $1M"
- "Productions with attendance < 1000"

### 5. Advanced Operators
All Cube.js operators are supported:
- **Comparison**: equals, notEquals, gt, gte, lt, lte
- **List**: in, notIn
- **String**: contains, notContains, startsWith, endsWith
- **Null**: set, notSet
- **Date**: inDateRange, notInDateRange, beforeDate, afterDate

### 6. Multi-Dimensional Analysis
- Multiple measures in one query
- Multiple dimensions for grouping
- Drilldown capabilities
- Cross-dimensional filtering

### 7. Ordering and Limiting
- Sort by multiple fields
- Top N / Bottom N queries
- Pagination support
- Custom result limits

## How the Orchestrator Should Use This

The orchestrator passes queries to TicketingDataCapability using the standard inputs:
- `measures`: List of metrics to retrieve (or empty for LLM to decide)
- `dimensions`: How to group the data (or empty for LLM to decide)
- `filters`: Specific filter criteria with entity IDs
- `entities`: Resolved entities with candidates and IDs
- `order`: Sort criteria (optional)
- `limit`: Maximum results (optional)

The LLM inside TicketingDataCapability will:
1. Parse the natural language context
2. Identify if it needs compareDateRange, trends, or other features
3. Generate the optimal Cube.js query using all available features

## Examples for Orchestrator

### Example 1: Year-over-Year Comparison
```python
User: "Compare this year's revenue to last year"
Orchestrator should call TicketingDataCapability with:
{
    "measures": ["ticket_line_items.amount"],
    "dimensions": [],
    "filters": [],
    # The time comparison intent is understood from the natural language
    # The LLM will generate a compareDateRange query
}
```

### Example 2: Top Shows with Trends
```python
User: "Show me top 5 shows with their monthly trends"
Orchestrator should call TicketingDataCapability with:
{
    "query_request": "Top 5 productions with monthly revenue trends",
    "analysis_type": "trend",
    "time_granularity": "month",
    "measures": ["ticket_line_items.amount"],
    "dimensions": ["productions.name"],
    "limit": 5
}
```

### Example 3: Complex Filter with Comparison
```python
User: "Compare Chicago venues Q1 vs Q2 for shows over $50"
Orchestrator should call TicketingDataCapability with:
{
    "query_request": "Compare Q1 vs Q2 for Chicago venues with tickets over $50",
    "comparison_type": "quarter_over_quarter",
    "time_context": "Q1 vs Q2",
    "filters": [
        {"member": "city", "operator": "equals", "values": ["Chicago"]},
        {"member": "amount", "operator": "gt", "values": [50]}
    ]
}
```

## Important Notes

1. **TicketingDataCapability handles ALL data retrieval** - including complex comparisons
2. **EventAnalysisCapability is for interpretation** - when you need insights, not just data
3. **The LLM generates optimal queries** - using schema context and Cube.js best practices
4. **Entity IDs are preferred** - for precise filtering when available