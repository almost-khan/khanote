# khanote.research.save

Save and finalize the research session with structured synthesis notes.

## Usage

```
/khanote.research.save $ARGUMENTS
```

Where `$ARGUMENTS` is an optional note or tag to attach to the session.

## What this does

1. Structures notes per research-note template
2. Writes synthesis to `synthesis/`
3. Updates `_session.md` status to `completed`
4. Updates `khanote/_index.md` with session summary
5. Triggers knowledge graph update

## Options

- `--session <path>`: Target a specific session

## Example

```
/khanote.research.save
/khanote.research.save --session khanote/2026-03-22_AI-Agents-Overview
```
