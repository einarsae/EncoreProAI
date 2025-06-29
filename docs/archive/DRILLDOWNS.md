# Drilldowns in EncoreProAI

## What are Drilldowns?

Drilldowns allow you to explore hierarchical data by expanding grouped results into more detailed breakdowns. In Cube.js, this enables interactive data exploration where users can "drill down" from summary to detail.

## How Drilldowns Work in EncoreProAI

### 1. Enabling Drilldowns
The LLM can add drilldown support to any query by including:
```json
{
  "measures": ["ticket_line_items.amount"],
  "dimensions": ["productions.name", "sales_channels.name"],
  "drilldown": true
}
```

### 2. What Drilldowns Provide
When enabled, the response includes:
- Aggregated data at the requested level
- Ability to expand each row for more detail
- Hierarchical navigation through dimensions

### 3. Example Use Cases

**Production → Sales Channel Breakdown:**
```
Query: "Show revenue by production with ability to see sales channels"
Result:
  Chicago: $1.5M [+]
    └── Web: $800K
    └── Box Office: $500K
    └── Phone: $200K
  Gatsby: $1.2M [+]
    └── Web: $900K
    └── Box Office: $300K
```

**Time-Based Drilldowns:**
```
Query: "Monthly revenue with daily breakdown capability"
Result:
  March 2024: $5.2M [+]
    └── March 1: $180K
    └── March 2: $165K
    └── ...
```

**Geographic Drilldowns:**
```
Query: "Sales by state with city breakdown"
Result:
  New York: $10M [+]
    └── New York City: $8M
    └── Buffalo: $1.5M
    └── Albany: $500K
```

## When to Use Drilldowns

The LLM determines when drilldowns are appropriate based on:

1. **Hierarchical Queries**: When users ask for multi-level breakdowns
2. **Exploratory Analysis**: "Show me X broken down by Y"
3. **Progressive Detail**: Starting with summary, allowing detail on demand

## Implementation

### In TicketingDataCapability
The LLM can generate queries with drilldown support:
```python
# The LLM might generate:
cube_query = {
    "measures": ["ticket_line_items.amount", "ticket_line_items.quantity"],
    "dimensions": ["productions.name", "venues.name", "price_bands.name"],
    "drilldown": true,
    "order": [["ticket_line_items.amount", "desc"]]
}
```

### Current Status
- ✅ Drilldown capability is available in the LLM prompt
- ✅ CubeService passes drilldown parameter correctly
- ✅ The LLM can enable drilldowns when appropriate

### Limitations
- The current UI/response format doesn't visualize the hierarchical nature
- Drilldown interactions require client-side implementation
- Best suited for BI tools or interactive dashboards

## Examples of Drilldown Queries

1. **"Show me revenue by production with venue breakdown"**
   - Primary dimension: productions.name
   - Drilldown dimension: venues.name

2. **"Display monthly sales with weekly and daily drilldowns"**
   - Primary: month granularity
   - Drilldown: week, then day

3. **"Analyze customer segments with geographic breakdown"**
   - Primary: customer type
   - Drilldown: country → state → city

## Testing Drilldowns

To see if a query uses drilldowns, check the generated Cube.js query:
```python
# In test or logs, look for:
"drilldown": true
```

The LLM will add this when it recognizes a hierarchical analysis need.