# khanote.feed.add

You are helping the user add a new recurring research feed.

## Instructions

Walk the user through these steps conversationally — ask one question at a time.

### Step 1: New or copy?
Ask: "Would you like to create a new feed, or copy settings from an existing one?"
- If copy: Read `{vault_path}/.khanote/config.yaml`, list the existing feeds, let the user choose one, pre-fill all fields, and skip to Step 5.

### Step 2: Choose a researcher
Read `{vault_path}/.khanote/config.yaml` to find available researchers. Show the list and ask which one to use. Built-in options include: `arxiv`, `perplexity`, `newsapi`, `hackernews`, `rss`, `producthunt`, `pubmed`, `notebooklm`.

### Step 3: Set the query
Ask: "What topic or question should this feed search for?" Accept natural language.

### Step 4: Add filters (optional)
Ask: "Any keyword filters to narrow results? (comma-separated, or press Enter to skip)"

### Step 5: Review and confirm
Show a summary:
```
Name: [auto-suggested from topic]
Researcher: [selected]
Query: [query text]
Keywords: [keywords or none]
Frequency: daily
```
Ask: "Does this look right? (yes / edit)"

### Step 6: Confirm the name
Ask: "What would you like to name this feed? (e.g., 'ai-papers')" — must be alphanumeric with hyphens.

### Step 7: Save
Run: `khanote feed add` with the collected parameters, or write directly to the `feeds` section of `config.yaml`.
Tell the user: "Feed '{name}' added. Run `/khanote.feed.list` to see all your feeds."
