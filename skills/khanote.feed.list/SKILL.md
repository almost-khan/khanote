# khanote.feed.list

You are listing the user's configured research feeds.

## Instructions

1. Read `{vault_path}/.khanote/config.yaml` and find the `feeds` section.
2. For each feed, collect: name, researcher, query, frequency, and active status.
3. Check for orphaned feeds — feeds whose researcher no longer exists or is disabled in config.
4. Display the feeds as a formatted table:

```
| Feed         | Researcher | Query               | Frequency | Active | Notes   |
|--------------|------------|---------------------|-----------|--------|---------|
| ai-papers    | arxiv      | AI agents           | daily     | ✓      |         |
| market-news  | newsapi    | startup funding     | daily     | ✓      |         |
| old-feed     | deleted    | old topic           | daily     | ✓      | orphaned|
```

5. If there are no feeds, tell the user: "No feeds configured yet. Run `/khanote.feed.add` to add your first feed."
6. If there are orphaned feeds, note: "Orphaned feeds reference researchers that no longer exist. Run `/khanote.feed.remove` to clean them up."
