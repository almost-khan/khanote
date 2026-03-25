# khanote.start-my-day

Daily research briefing or ad-hoc research query.

## Two Modes

### Mode 1: Daily Briefing (no arguments)

Run with no arguments to get your personalized daily briefing:

```
khanote start-my-day
```

**What happens**:
1. Loads your configured feeds from `config.yaml`
2. Checks which feeds are due (based on frequency and last run time)
3. Executes due feeds via their bound researchers
4. Deduplicates results across feeds
5. Selects top "Focus" items weighted by your preferences
6. Generates a briefing file: `{vault}/khanote/briefings/{date}-{slug}.md`

**Briefing sections**:
- **Top Story**: Single most important item
- **Your Focus**: Top 3-5 items matching your interests
- **Your Feeds**: Per-feed result summaries
- **Discover**: 1-2 items from adjacent domains (serendipity)
- **Sources**: All cited sources

### Mode 2: Ad-hoc Research (with query)

Run with a query to research any topic:

```
khanote start-my-day "What are the latest advances in AI agents?"
```

**What happens**:
1. Analyzes query complexity (simple vs complex)
2. For complex queries: routes to multiple researchers by domain
3. Executes research in parallel where possible
4. Synthesizes a report: `{vault}/khanote/sessions/{date}-{slug}/report.md`

**Report sections** (McKinsey pyramid):
- **Executive Summary**: Key conclusion stated upfront
- **Key Findings**: With confidence levels (HIGH/MEDIUM/LOW)
- **Dissenting Views**: Counter-evidence
- **Methodology**: Which researchers ran which sub-queries
- **References**: All cited sources

## Preferences

Customize output via `khanote init` or by editing `preferences.yaml`:

```yaml
language: en-US          # BCP 47 language tag
role: developer          # developer | pm | researcher | mixed
interests: [ai, web]     # Used for focus selection and starter feeds
depth: summary           # headlines | summary | detailed | deep_dive
expertise: intermediate  # beginner | intermediate | expert
tone: professional_briefing  # formal_report | professional_briefing | casual_notes
discover:
  enabled: true
  serendipity: 0.15      # 0.0 = disable, 1.0 = maximum exploration
  blocked_domains: []    # never show in Discover
```

## Available Researchers

| Researcher | Domains | Requires Key |
|-----------|---------|-------------|
| perplexity | general, news, q-and-a | Yes (PERPLEXITY_API_KEY) |
| arxiv | academic, CS, AI/ML | No |
| pubmed | medical, biomedical | No |
| github | software, open-source | No (optional GITHUB_TOKEN) |
| hackernews | tech, startups, programming | No |
| newsapi | news, current-events | Yes (NEWSAPI_KEY) |
| rss | blogs, custom feeds | No |
| producthunt | products, startups | Yes (PRODUCTHUNT_TOKEN) |
| notebooklm | documents, synthesis | Yes (GOOGLE_API_KEY) |

## Discover Feedback

React to Discover items to tune future recommendations:

```
khanote discover like "rust programming"
khanote discover dislike "cryptocurrency"
```

Or naturally: `/khanote.discover.feedback`

## Related Commands

- `khanote feed add` — add a new research feed
- `khanote feed list` — list configured feeds
- `khanote preferences show` — view current preferences
- `khanote init` — (re)run onboarding to update preferences + starter feeds
