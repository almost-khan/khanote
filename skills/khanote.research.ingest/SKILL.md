# khanote.research.ingest

You are ingesting sources into the active research session.

## Instructions

1. Read `{vault_path}/.khanote/current_session` to find the active session path. If it does not exist, ask the user to run `/khanote.research.start` first.
2. Collect sources from the user — accept any combination of:
   - URLs (web pages, arXiv links, etc.)
   - Local file paths (PDF, Markdown, text)
   - Inline text pasted directly into the conversation
3. For each source:
   - Copy files to the session's `sources/` directory.
   - Download URLs to `sources/` as `.html` or `.pdf` where possible.
   - Record the source in `_session.md` under `## Sources` with its type and timestamp.
4. Send each source to the active researcher for indexing. Use the default researcher from `config.yaml` unless the user specifies otherwise.
5. If a researcher is unavailable (no API key or network error), record the source with status `pending` — do not fail.
6. Tell the user how many sources were ingested and any that are pending. Suggest running `/khanote.research.analyze` next.
