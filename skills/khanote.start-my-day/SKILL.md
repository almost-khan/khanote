# khanote.start-my-day

You are running the daily research briefing or ad-hoc research workflow for the user.

## Instructions

Determine which mode the user wants based on whether they provided a query:

### Mode 1: Daily Briefing (no query)

1. Read the config at `{vault_path}/.khanote/config.yaml` to load all feeds and their researchers.
2. Read `{vault_path}/.khanote/preferences.yaml` to load the user's language, role, interests, depth, and tone.
3. For each feed, check when it last ran (from config or stats file). Run feeds that are due today based on their frequency.
4. For each due feed, use its bound researcher to fetch results. Pass the feed's query and keyword filters.
5. Deduplicate results across all feeds by URL or content hash.
6. Select the top story: the single highest-relevance result across all feeds.
7. Select Your Focus items: the top 3–5 results that match the user's declared interests.
8. Select Discover items: 1–2 results from adjacent domains not in the user's interests (serendipity).
9. Write a briefing file to `{vault_path}/khanote/briefings/{date}-{slug}.md` using this structure:

```markdown
# Daily Briefing — {date}

## Top Story
[Title](url) — one-sentence summary

## Your Focus
1. [Title](url) — one-sentence summary
...

## Your Feeds
### {feed_name}
- [Title](url) — excerpt

## Discover
- [Title](url) — why this is adjacent to your interests

## Sources
All cited URLs listed here.
```

10. Tell the user the briefing is ready and show its path. Offer to open it or summarize it inline.

### Mode 2: Ad-hoc Research (with query)

1. Read `{vault_path}/.khanote/config.yaml` and `preferences.yaml`.
2. Analyze the query complexity. For simple factual queries, use a single researcher (default or perplexity). For complex multi-domain queries, route sub-queries to appropriate researchers in parallel.
3. Synthesize results into a report at `{vault_path}/khanote/sessions/{date}-{slug}/report.md` using this structure:

```markdown
# Research Report — {topic}
Generated: {date}

## Executive Summary
[Key conclusion stated upfront]

## Key Findings
- Finding 1 [HIGH confidence]
- Finding 2 [MEDIUM confidence]

## Dissenting Views
[Counter-evidence or alternative perspectives]

## Methodology
[Which researchers ran which sub-queries]

## References
[All cited sources]
```

4. Tell the user the report is ready and show its path.

## Config Reference

Your config and preferences are at:
- Config: `{vault_path}/.khanote/config.yaml`
- Preferences: `{vault_path}/.khanote/preferences.yaml`

The vault_path is recorded in config.yaml under `vault_path`.
