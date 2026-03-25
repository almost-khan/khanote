# khanote.research.analyze

You are analyzing ingested sources in the active research session.

## Instructions

1. Read `{vault_path}/.khanote/current_session` to find the active session path.
2. Read `_session.md` in the session folder to see all ingested sources.
3. If the user provided an analysis query or question, use it to focus the analysis. Otherwise, derive the key question from the session topic.
4. For each ingested source, extract key claims, findings, and supporting evidence.
5. Identify themes, contradictions, and gaps across all sources.
6. Write structured analysis notes to the session's `research/` folder using this template:

```markdown
# Analysis — {topic}
Date: {YYYY-MM-DD}
Query: {analysis_question}

## Key Findings
- Finding 1 [HIGH confidence]
- Finding 2 [MEDIUM confidence]

## Themes
- Theme 1: description

## Contradictions
- Source A says X, Source B says Y

## Gaps
- What is still unknown or missing

## Source Notes
### {source_name}
Key claims: ...
```

7. Update `_session.md` status to `analyzed`.
8. Tell the user analysis is complete and suggest running `/khanote.research.save` to finalize.
