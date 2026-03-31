# khanote.research.pipeline

You are running a full research pipeline: start → ingest → analyze → save.

## Instructions

1. Ask the user for the research topic if not already provided.
2. Ask the user for sources to ingest (URLs, files, or text). Accept multiple sources.
3. Run `/khanote.research.start` to create the session folder.
4. Run `/khanote.research.ingest` to add all provided sources to the session.
5. Run `/khanote.research.analyze` to extract findings and write structured notes.
6. Run `/khanote.research.save` to synthesize and finalize the session.
7. Show the user the executive summary from the synthesis and the path to the full report.
   - The executive summary must follow the Pyramid Principle: conclusion first, supporting evidence second.
   - Every finding heading must be an action title (insight stated as a verb-driven sentence).
   - Every finding must answer "so what?" with an actionable implication.
   - All factual claims must cite sources inline.

## Notes

- You can run each step individually if the user prefers fine-grained control.
- If any step fails, tell the user which step failed and suggest how to recover.
- Your config is at `{vault_path}/.khanote/config.yaml`.
