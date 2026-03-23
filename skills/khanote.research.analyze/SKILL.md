# khanote.research.analyze

Trigger analysis of ingested sources and write structured notes.

## Usage

```
/khanote.research.analyze $ARGUMENTS
```

Where `$ARGUMENTS` is an optional query to guide analysis.

## What this does

1. Resolves active session via `.khanote/current_session` pointer
2. Triggers `researcher.analyze()` with optional query
3. Writes structured notes to `research/` using the fixed-layer template
4. Updates `_session.md` status

## Options

- `--session <path>`: Target a specific session
- `--query <text>`: Guide the analysis with a specific question

## Example

```
/khanote.research.analyze
/khanote.research.analyze --query "What are the key limitations?"
```
