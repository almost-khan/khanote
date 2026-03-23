# khanote Context

khanote is a research workflow kit that connects your AI coding tool with Obsidian.

## What khanote does

- **Start sessions**: Create organized research folders in your Obsidian vault
- **Ingest sources**: Capture URLs, files, and text for analysis
- **Analyze**: Use pluggable researchers (Perplexity, arXiv, NotebookLM) for deep analysis
- **Save**: Generate structured Markdown notes in your vault
- **Pipeline**: Run the full workflow in one command

## Session structure

All sessions live under `khanote/` in your vault:

```
khanote/
├── _index.md                          # Navigation index (auto-generated)
└── {YYYY-MM-DD}_{topic}/
    ├── _session.md                    # Session metadata and source list
    ├── sources/                       # Ingested files
    ├── research/                      # Researcher analysis output
    ├── synthesis/                     # Your structured notes
    └── artifacts/                     # Generated content (audio, PDFs)
```

## Available commands

| Command | Description |
|---------|-------------|
| `/khanote.research.start <topic>` | Start a new research session |
| `/khanote.research.ingest <sources>` | Ingest sources into active session |
| `/khanote.research.analyze` | Analyze ingested sources |
| `/khanote.research.save` | Save and finalize session |
| `/khanote.research.pipeline` | Full pipeline in one command |
| `/khanote.update` | Update khanote skills |
| `/khanote.start-my-day` | Daily briefing (coming soon) |

## Configuration

Edit `.khanote/config.yaml` in your vault to configure researchers, domains, and tools.
