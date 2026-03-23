# khanote.research.start

Start a new research session for a topic.

## Usage

```
/khanote.research.start $ARGUMENTS
```

Where `$ARGUMENTS` is the research topic (e.g., "AI Agents Overview").

## What this does

1. Creates a dated session folder: `khanote/{YYYY-MM-DD}_{topic}/`
2. Initializes subdirectories: `sources/`, `research/`, `synthesis/`, `artifacts/`
3. Creates `_session.md` with session metadata
4. Updates `.khanote/current_session` pointer
5. Updates `khanote/_index.md` navigation

## Options

- `--session <path>`: Explicitly target an existing session instead of creating a new one

## Example

```
/khanote.research.start AI Agents Overview
```

Creates: `khanote/2026-03-22_AI-Agents-Overview/`
