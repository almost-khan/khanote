# khanote.research.start

You are starting a new research session for the user.

## Instructions

1. Read `{vault_path}/.khanote/config.yaml` to find the vault path.
2. Ask the user for the research topic if they have not already provided one.
3. Create the session folder using today's date and a slug derived from the topic:
   - Path: `{vault_path}/khanote/{YYYY-MM-DD}_{topic-slug}/`
   - Example: `khanote/2026-03-25_AI-Agents-Overview/`
4. Create these subdirectories inside the session folder:
   - `sources/` — raw input files and URLs
   - `research/` — structured analysis notes
   - `synthesis/` — final synthesized output
   - `artifacts/` — generated files (audio, PDF, etc.)
5. Create `_session.md` in the session folder with this content:

```markdown
# Session: {topic}
Date: {YYYY-MM-DD}
Status: active

## Sources
(none yet)

## Notes
```

6. Write the session path to `{vault_path}/.khanote/current_session` so other skills know the active session.
7. Update `{vault_path}/khanote/_index.md` — append a line linking to this session.
8. Tell the user: "Session created at `{session_path}`. Use `/khanote.research.ingest` to add sources."
