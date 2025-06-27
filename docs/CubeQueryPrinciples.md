# Cube Query Generation Principles & Capabilities

## 1. Guiding Principles

- **Deterministic, Schema-Driven Translation:**
  - All natural language queries are mapped to Cube.js queries using a dynamic, tenant-aware schema summary and field mapping table.
  - The LLM acts as a deterministic translator, not a guesser—only fields present in the schema summary and mapping table are allowed.
- **Tenant-Specific Relevance:**
  - Only cubes, measures, and dimensions relevant to the current tenant are exposed via JWT authentication.
  - Our CubeService handles JWT token generation with tenant isolation.
- **Concept Model Alignment:**
  - User/LLM phrases are mapped to Cube fields using our ConceptResolver service.
  - EntityResolver handles disambiguation of entity names using trigram similarity search.
  - TimeResolver parses natural language time expressions to Cube.js date ranges.
- **Frame-Based Understanding:**
  - Queries are understood through semantic frames that capture intent, entities, and relationships.
  - The orchestrator uses these principles when constructing Cube.js queries.
- **Comprehensive Feature Utilization:**
  - All advanced Cube.js features (compareDateRange, nested filters, drilldowns, etc.) are supported.
- **Robust Error Handling:**
  - All LLM output is post-processed and validated against the schema; invalid or ambiguous output triggers clarification or fallback.

---

## 2. Cube.js Capabilities Leveraged

- **Measures & Dimensions:**
  - Aggregations (sum, avg, min, max, count) on all available measures.
  - Grouping and slicing by any dimension.
- **Filters:**
  - WHERE-style and HAVING-style filters on dimensions and measures (all in the 'filters' array).
  - Support for all Cube.js operators (equals, notEquals, in, notIn, contains, notContains, startsWith, endsWith, set, notSet, gt, gte, lt, lte, inDateRange, notInDateRange, beforeDate, afterDate).
- **Logical Operators:**
  - AND, OR, and nested logic for complex filter conditions.
- **Time Dimensions & Granularity:**
  - Time series queries with day/week/month/quarter/year granularity.
- **Ordering & Limiting:**
  - Top N, bottom N, custom ordering, and pagination.
- **Compare Date Ranges:**
  - 'compareDateRange' for side-by-side period comparisons (e.g., YOY, MOM).
- **Drilldowns & Data Blending:**
  - Multi-cube joins, drilldown, and cross-dimensional analysis (where supported).
- **Ungrouped Queries:**
  - Raw row output for debugging, exports, or audit trails.

---

## 3. Domain Support, Concept Models, and Tenant Config

- **ConceptResolver Service:**
  - Maps user/LLM phrases to Cube field names (measures, dimensions, filters).
  - Uses cached concept mappings for common terms and LLM for ambiguous cases.
  - Handles normalization, aliasing, and value canonicalization.
- **EntityResolver Service:**
  - Resolves entity names to IDs using PostgreSQL trigram similarity search.
  - Provides disambiguation strings for productions with dates, revenue, and sold_last_30_days.
  - Supports cross-type entity lookup with score discounting.
  - Handles both real entities (productions, venues, customers) and fake entities (city, country, state, currency).
- **TimeResolver Service:**
  - Parses natural language time expressions to Cube.js date ranges.
  - Caches common patterns and uses LLM for complex expressions.
- **Tenant-Specific Config:**
  - JWT tokens include tenant_id for Cube.js data isolation.
  - All services respect tenant boundaries for data access.

---

## 4. Prompt Structure & Best Practices

- **Dynamic Schema Summary:**
  - Inject a token-efficient, tenant-aware schema summary into the prompt.
- **Field Mapping Table:**
  - Show user/LLM phrases mapped to Cube field names for deterministic translation.
- **Supported Query Types & Examples:**
  - Provide JSON examples for all major query types (aggregation, multi-measure, filters, time series, grouping, top N, compare ranges, nested filters, etc.).
- **Advanced Features:**
  - Document and show examples for compareDateRange, nested AND/OR/NOT, drilldown, and data blending.
- **Common Mistakes to Avoid:**
  - Never invent field names; always use canonical IDs/names; never use null/undefined for required fields.
- **Output Format Instructions:**
  - Output a single JSON object compatible with Cube's query schema, using only required keys.

---

## 5. Planner Post-Processing & Validation

- **Field Mapping:**
  - All LLM output is mapped to Cube fields using the field mapping table and schema summary.
- **Schema Validation:**
  - All measures, dimensions, and filters are validated against the loaded schema before query execution.
- **Value Normalization:**
  - Filter values are canonicalized (e.g., entity names/IDs uppercased or mapped as required).
- **Advanced Feature Support:**
  - Planner supports all advanced Cube features, including compareDateRange and nested filters.
- **Clarification Handling:**
  - If output is ambiguous or invalid, set `needs_clarification: true` and provide a `clarification_hint`.

---

## 8. Example: Supported Query Types & JSON Examples

(See prompt for full examples; include aggregation, multi-measure, filters, time series, grouping, top N, compare ranges, nested filters, etc.)

---

## 9. Strategic Value

- **Enables robust, testable, and maintainable analytics workflows.**
- **Reduces LLM hallucination and schema drift.**
- **Supports rapid onboarding and tenant-specific customization.**
- **Maximizes the power and flexibility of Cube.js as a semantic layer.**

---

## 10. Cube.js Query Features, Operators, and Tips & Tricks

### **A. Supported Operators and Features**

- **equals**: Exact match on a field.
- **notEquals**: Field does not match value.
- **in**: Field matches any value in a list.
- **notIn**: Field does not match any value in a list.
- **contains**: Field contains substring/value.
- **notContains**: Field does not contain substring/value.
- **startsWith**: Match beginning of string.
- **endsWith**: Match end of string.
- **set**: Field is set (not null/empty).
- **notSet**: Field is not set (null/empty).
- **gt**: Greater than (numeric/date).
- **gte**: Greater than or equal to.
- **lt**: Less than.
- **lte**: Less than or equal to.
- **inDateRange**: Date/time field is within a range.
- **notInDateRange**: Date outside range.
- **beforeDate**: Date before specified.
- **afterDate**: Date after specified.
- **and**: All conditions must match (nestable).
- **or**: Any condition can match (nestable).
- **compareDateRange**: Compare two or more date ranges in a single query.
- **order**: Sort results by field (asc/desc).
- **limit**: Limit number of results (Top N, pagination).
- **offset**: Skip N results (pagination).
- **total**: Return total count of results (for pagination).
- **drilldown**: Enable drilldown on grouped results.
- **ungrouped queries**: Omit measures/dimensions for raw row output.
- **data blending**: Join data from multiple cubes (where supported).

### **B. Concrete Examples**

#### 1. **Basic Filter** (Array Format)
```json
{
  "dimensions": ["productions.name"],
  "measures": ["ticket_line_items.amount_average"],
  "filters": [
    {
      "member": "productions.name",
      "operator": "equals",
      "values": ["Hamilton"]
    }
  ]
}
```

#### 2. **OR Logic** (Array Format)
```json
{
  "dimensions": ["productions.name"],
  "filters": [
    {
      "or": [
        {
          "member": "productions.name",
          "operator": "equals",
          "values": ["Hamilton"]
        },
        {
          "member": "productions.name",
          "operator": "equals",
          "values": ["Wicked"]
        }
      ]
    }
  ]
}
```

#### 3. **AND Logic** (Array Format)
```json
{
  "dimensions": ["productions.name"],
  "filters": [
    {
      "and": [
        {
          "member": "ticket_line_items.city",
          "operator": "equals",
          "values": ["CHICAGO", "CHICAGO IL"]
        },
        {
          "member": "ticket_line_items.amount",
          "operator": "gt",
          "values": ["100"]
        }
      ]
    }
  ]
}
```

#### 4. **Complex Nested Logic** (Array Format)
```json
{
  "dimensions": ["productions.name"],
  "filters": [
    {
      "or": [
        {
          "and": [
            {
              "member": "ticket_line_items.city",
              "operator": "equals",
              "values": ["CHICAGO"]
            },
            {
              "member": "productions.name",
              "operator": "equals",
              "values": ["Hamilton"]
            }
          ]
        },
        {
          "and": [
            {
              "member": "ticket_line_items.city",
              "operator": "equals",
              "values": ["NEW YORK"]
            },
            {
              "member": "productions.name",
              "operator": "equals",
              "values": ["Wicked"]
            }
          ]
        }
      ]
    }
  ]
}
```

#### 5. **Post-Aggregation (HAVING) Filter** (Array Format)
```json
{
  "measures": ["ticket_line_items.amount_average"],
  "filters": [
    {
      "member": "ticket_line_items.amount_average",
      "operator": "gt",
      "values": ["100"]
    }
  ]
}
```

#### 6. **Compare Date Range** (Array Format)
```json
{
  "measures": ["ticket_line_items.quantity"],
  "timeDimensions": [
    {
      "dimension": "ticket_line_items.created_at_local",
      "compareDateRange": [["2025-04-01", "2025-04-30"], ["2025-03-01", "2025-03-31"]]
    }
  ]
}
```

#### 7. **Multi-Measure, Multi-Dimension, Nested Filters, HAVING, Ordering, Limit** (Array Format)
```json
{
  "measures": [
    "ticket_line_items.amount_max",
    "ticket_line_items.amount_average",
    "ticket_line_items.amount_min",
    "ticket_line_items.quantity"
  ],
  "dimensions": ["productions.name"],
  "filters": [
    { "member": "productions.name", "operator": "notEquals", "values": ["Hamilton"] },
    { "member": "ticket_line_items.city", "operator": "equals", "values": ["CHICAGO", "CHICAGO IL"] },
    { "member": "ticket_line_items.customer_id", "operator": "set" },
    { "member": "ticket_line_items.amount_max", "operator": "lte", "values": [100] }
  ],
  "order": { "ticket_line_items.amount_max": "desc" },
  "limit": 100,
  "rowLimit": 2000
}
```

#### 8. **Distinct List (No Measures)** (Array Format)
```json
{
  "dimensions": ["payment_methods.name"]
}
```

#### 9. **Drilldown Example** (Array Format)
```json
{
  "measures": ["ticket_line_items.amount"],
  "dimensions": ["productions.name", "sales_channels.name"],
  "drilldown": true
}
```

#### 10. **Ungrouped Query (Raw Rows)** (Array Format)
```json
{
  "filters": [
    { "member": "ticket_line_items.city", "operator": "equals", "values": ["CHICAGO"] }
  ]
}
```

#### 11. **Example: Customers in Chicago Who Saw Hamilton But Not Wicked** (Array Format)
```json
{
  "dimensions": ["ticket_line_items.customer_id"],
  "filters": [
    { "member": "ticket_line_items.city", "operator": "equals", "values": ["CHICAGO", "CHICAGO IL"] },
    {
      "or": [
        {
          "and": [
            { "member": "productions.name", "operator": "equals", "values": ["Hamilton"] },
            {
              "or": [
                { "member": "productions.name", "operator": "notEquals", "values": ["Wicked"] }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

#### 12. **Example: Shows Seen by Customers Who Saw Hamilton** (Array Format)
```json
{
  "dimensions": ["productions.name"],
  "measures": ["ticket_line_items.amount_average"],
  "filters": [
    { "member": "productions.name", "operator": "notEquals", "values": ["Hamilton"] },
    {
      "or": [
        { "member": "ticket_line_items.customer_id", "operator": "equals", "values": ["*"] }
      ]
    }
  ],
  "order": { "ticket_line_items.amount_average": "desc" },
  "limit": 100
}
```

### **C. Tips & Tricks**

- **All filter logic (including HAVING/post-aggregation) goes in the 'filters' array.**
- **Filters are ALWAYS an array, not an object (per our CubeService implementation).**
- **Use nested AND/OR/NOT for complex cohort/segment logic.**
- **Use 'set'/'notSet' for null checks.**
- **Use 'inDateRange', 'beforeDate', 'afterDate' for time filtering.**
- **For Top N, use 'order' + 'limit'.**
- **For distinct lists, use only 'dimensions'.**
- **For raw data, omit measures/dimensions.**
- **For multi-step plans, use output of one query as filter in the next.**
- **Always use canonical field names and values.**
- **Validate all fields and values before query execution.**

### **D. Integration with EncoreProAI Services**

- **CubeService**: Handles JWT authentication and query execution
  - Generates tenant-specific JWT tokens
  - Executes queries with proper error propagation
  - Supports all Cube.js query features

- **ConceptResolver**: Maps natural language to Cube.js fields
  - Caches common concept mappings
  - Uses LLM for ambiguous terms
  - Returns mapped Cube.js field names

- **EntityResolver**: Disambiguates entity references
  - Uses PostgreSQL trigram search with score transformation
  - Provides disambiguation strings with sold_last_30_days data
  - Handles both real entities and fake entities (geographical dimensions)
  - Supports cross-type lookups with score discounting

- **TimeResolver**: Parses time expressions
  - Converts "last month", "Q3 2023" to date ranges
  - Caches common patterns
  - Returns Cube.js compatible date formats

---

This document serves as the definitive reference for Cube.js query construction in EncoreProAI. The orchestrator and frame-based system use these principles to generate accurate, tenant-isolated queries.