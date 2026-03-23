# khanote.research.ingest

Ingest sources into the active research session.

## Usage

```
/khanote.research.ingest $ARGUMENTS
```

Where `$ARGUMENTS` is one or more sources (URLs, file paths, or text).

## What this does

1. Accepts URLs, local file paths, or inline text
2. Copies files to `sources/` directory
3. Records sources in `_session.md` under `## Sources`
4. Sends sources to the active researcher for indexing
5. If researcher is unavailable, records source with `pending` status

## Options

- `--session <path>`: Target a specific session (default: current session)

## Example

```
/khanote.research.ingest https://arxiv.org/abs/2401.12345
/khanote.research.ingest ./my-paper.pdf https://example.com/article
```
