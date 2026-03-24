# khanote.feed.list

List all configured feeds with their status, researcher, and query.

## When to use

Run this skill when the user wants to:
- See all configured feeds
- Check which feeds are active vs paused
- Verify a feed was added correctly
- Check for orphaned feeds

## Behavior

Run `khanote feed list` which displays a Rich table:

```
┌──────────────┬────────────┬──────────────────┬───────────┬────────┬────────┐
│ Feed         │ Researcher │ Query            │ Frequency │ Active │ Status │
├──────────────┼────────────┼──────────────────┼───────────┼────────┼────────┤
│ llm-papers   │ arxiv      │ large language…  │ daily     │ ✓      │        │
│ ai-industry  │ perplexity │ AI startup fu…   │ daily     │ ✓      │        │
│ agent-papers │ arxiv      │ AI agents        │ daily     │ ✗      │        │
│ old-feed     │ deleted    │ old topic        │ daily     │ ✓      │ orphaned│
└──────────────┴────────────┴──────────────────┴───────────┴────────┴────────┘
```

- `✓` = active, `✗` = paused
- `orphaned` = researcher no longer exists or is disabled

## Implementation

Uses `FeedManager.list_feeds()` and `FeedManager.detect_orphans()` from `src/khanote/feeds/manager.py`.

## Related skills

- `khanote.feed.add` — Add a new feed
- `khanote.feed.pause` — Pause an active feed
- `khanote.feed.resume` — Resume a paused feed
- `khanote.feed.remove` — Remove a feed
