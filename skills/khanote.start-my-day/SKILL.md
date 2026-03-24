# khanote.start-my-day

**Coming Soon** — Daily research briefing based on your configured feeds.

## Intended Behavior (Planned)

1. Reads your `feeds` configuration from `config.yaml`
2. For each active feed, runs the bound researcher's search with the feed query and filters
3. Analyzes results using the researcher's analyze capability (API or SOP prompt)
4. Creates a dated briefing session in `khanote/{YYYY-MM-DD}_daily-briefing/`
5. Generates a structured digest of new findings across all feeds

## Feed Integration (Available Now)

Feeds power start-my-day. Set up feeds first:

- **Add a feed**: Run `/khanote.feed.add` — guided flow to configure query, filters, and researcher
- **List feeds**: Run `/khanote.feed.list` — see all configured feeds and their status
- **Pause/resume feeds**: Run `/khanote.feed.pause` or `/khanote.feed.resume`

### Example Feed Config (in config.yaml)

```yaml
feeds:
  llm-papers:
    researcher: arxiv
    query: "large language models"
    keywords: [llm, transformer, agent]
    frequency: daily
    active: true
```

## Status

The daily briefing orchestration is planned for spec-003 (start-my-day). Feed management (adding, listing, pausing, removing feeds) is fully available now.

To track progress, see: `specs/` for the planned spec.
