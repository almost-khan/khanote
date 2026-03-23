# khanote.research.pipeline

Run a full research session in one command: start → ingest → analyze → save.

## Usage

```
/khanote.research.pipeline $ARGUMENTS
```

Where `$ARGUMENTS` includes the topic and sources.

## What this does

1. Starts a new session for the topic
2. Ingests all provided sources
3. Runs analysis
4. Saves and finalizes the session
5. Optionally generates additional content (audio, PDF) with `--generate`

## Options

- `--topic <text>`: Research topic (required)
- `--sources <urls/paths>`: One or more sources to ingest
- `--generate <type>`: Generate additional output after save (e.g., audio, summary)

## Example

```
/khanote.research.pipeline --topic "AI Agents" --sources https://arxiv.org/abs/2401.12345
```
