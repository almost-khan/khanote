# khanote.research.save

You are finalizing and saving the research session.

## Instructions

1. Read `{vault_path}/.khanote/current_session` to find the active session path.
2. Read all files in the session's `research/` folder to gather the analysis notes.
3. Synthesize the findings into a final output in `synthesis/synthesized.md` using this structure:

```markdown
# {topic} — Synthesis
Date: {YYYY-MM-DD}

## Executive Summary
[Key conclusion in 2–3 sentences]

## Key Findings
1. Finding 1
2. Finding 2

## Supporting Evidence
[Key quotes and references from sources]

## Recommendations
[Actionable next steps, if applicable]

## References
[All cited sources with URLs]
```

4. Update `_session.md` status to `completed` and add a completion timestamp.
5. Append a summary entry to `{vault_path}/khanote/_index.md` linking to this session.
6. Clear `{vault_path}/.khanote/current_session` (no active session).
7. Tell the user: "Session saved at `{session_path}/synthesis/synthesized.md`." Show the executive summary inline.
