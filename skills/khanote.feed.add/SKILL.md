# khanote.feed.add

Add a recurring research feed to khanote — no code required. All configuration through conversational prompts.

## When to use

Run this skill when the user wants to:
- Set up a daily research feed for a topic (e.g., "I want daily updates on AI agents")
- Copy an existing feed with different parameters
- Create a feed after adding a new researcher

## Guided Flow (7 steps)

Follow these steps in order. Use natural language prompts — NO CLI flags.

### Step 1: New or Copy?
Ask: "Would you like to create a new feed, or copy settings from an existing one?"

- New → proceed to Step 2
- Copy → show list of existing feeds, user selects one, pre-fill all fields, jump to Step 5 for review

### Step 2: Select Researcher
Ask: "Which researcher should this feed use?"
Show the list of available researchers from `config.yaml`.

**Built-in researchers available:**
| Researcher | Best for | Key required? |
|-----------|----------|--------------|
| `perplexity` | General queries, current events, Q&A | Yes (PERPLEXITY_API_KEY) |
| `arxiv` | Academic papers (CS, AI, math, physics) | No |
| `pubmed` | Medical/biomedical literature | No |
| `github` | Open-source repositories and tools | No (optional GITHUB_TOKEN) |
| `hackernews` | Tech community discussions, startups | No |
| `newsapi` | News articles from thousands of sources | Yes (NEWSAPI_KEY) |
| `rss` | Any RSS/Atom feed by URL | No |
| `producthunt` | New products and startup launches | Yes (PRODUCTHUNT_TOKEN) |
| `notebooklm` | Document ingestion and synthesis | Yes (GOOGLE_API_KEY) |

### Step 3: Query
Ask: "What topic or query should this feed search for?"
Free text — user describes their interest in natural language.

### Step 4: Filters (optional)
Ask: "Any keyword filters? (comma-separated, or skip)"
These narrow results — e.g., "llm, transformer, agent"

### Step 5: Review
Show a summary:
```
Feed name: [auto-suggested from query]
Researcher: [selected]
Query: [query text]
Keywords: [keywords or none]
Frequency: daily
```

Ask: "Does this look right? (yes/edit)"

### Step 6: Confirm Name
Ask: "What would you like to name this feed? (e.g., 'llm-papers')"
Name must be alphanumeric with hyphens only.

### Step 7: Save
Call `FeedManager.add_feed()` and write to config.yaml.
Report: "Feed 'llm-papers' added. Run /khanote.feed.list to see all feeds."

## Implementation

The underlying logic is in `src/khanote/feeds/manager.py`:
- `FeedManager.add_feed(name, researcher, query, keywords, max_age_days)` — writes to config.yaml
- `FeedManager.clone_feed(source_name, new_name)` — clone for "copy" flow
- `FeedManager.list_feeds()` — returns all feeds for review/selection

## Error Handling

- Duplicate feed name → explain and suggest a different name
- Researcher not found → suggest running /khanote.researcher.add first
- No feeds exist when "copy" selected → fall back to new feed flow

## Notes

- All configuration through conversational prompts — no CLI flags ever
- Feed frequency is `daily` for now (weekly/custom coming later)
- After adding, consider running /khanote.feed.list to verify
