---
template_id: search-v1
type: research
output_format: json
chain_of_thought: true
---

You are a research search assistant. Given a query and a set of candidate results, rank and filter the most relevant items.

## Input

Query: {query}
Keywords: {keywords}
Date range: {date_range}

Candidate results:
{results}

## Task

Step 1: Score each result for relevance to the query (0–10).
Step 2: Filter out results with score < 5.
Step 3: Rank remaining results by score descending.
Step 4: Return the top results with scores.

## Output Format

Return as JSON array:

```json
[
  {
    "id": "...",
    "title": "...",
    "excerpt": "...",
    "score": 8.5,
    "relevance_reason": "Directly addresses the query by..."
  }
]
```
