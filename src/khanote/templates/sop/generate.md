---
template_id: generate-v1
type: research
output_format: markdown
chain_of_thought: true
---

You are a senior research writer. Generate a structured research report from the provided analysis.

## Context

Domain: {domain_name}
Query: {query}
Date: {date}

## Input

Analysis:
{analysis}

Sources:
{sources}

## Task

Step 1: Review the analysis and identify the 3 most important findings to highlight.
Step 2: Structure the report with a clear executive summary, key findings, and recommendations.
Step 3: Write in clear, professional language suitable for a research briefing.
Step 4: Cite sources inline.

## Output Format

Return as markdown:

# Research Report: {query}

**Date**: {date}
**Domain**: {domain_name}

## Executive Summary
[2–3 paragraphs summarizing key findings and their significance]

## Key Findings

### Finding 1: [Title]
[2–3 sentences with source citation]

### Finding 2: [Title]
[2–3 sentences with source citation]

### Finding 3: [Title]
[2–3 sentences with source citation]

## Recommendations
- [Actionable recommendation 1]
- [Actionable recommendation 2]

## References
- [Source 1]
- [Source 2]
