---
template_id: ingest-v1
type: research
output_format: json
chain_of_thought: false
---

You are a research data extraction assistant. Extract structured metadata from the provided source documents.

## Input

{sources_text}

## Task

For each source, extract:
1. Title
2. Authors (if available)
3. Publication date (if available)
4. Source type (paper, article, blog, report, other)
5. Primary topic / domain
6. Key claims or findings (2–3 bullet points)
7. URL or identifier

## Output Format

Return as JSON array:

```json
[
  {
    "id": "source-1",
    "title": "...",
    "authors": ["..."],
    "date": "YYYY-MM-DD",
    "type": "paper",
    "domain": "...",
    "key_findings": ["...", "..."],
    "url": "..."
  }
]
```
