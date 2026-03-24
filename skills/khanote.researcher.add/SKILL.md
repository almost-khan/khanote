# khanote.researcher.add

Add a custom HTTP researcher to khanote — no code required. All configuration through conversational prompts.

## When to use

Run this skill when the user wants to connect a new data source (API) to khanote without writing code. Examples:
- "I want to use the Exa Search API for research"
- "Can I add a custom API to khanote?"
- "I need to search using [some API]"

## Guided Flow (9 steps)

Follow these steps in order. Use natural language prompts — NO CLI flags.

### Step 1: Intent
Ask: "Describe the data source you want to connect. For example: 'I want to use Exa Search API to find research papers.'"

→ Extract: API name, likely capabilities, domain

### Step 2: Persistence
Ask: "Would you like to save this researcher permanently, or use it just for this session?"
- Permanent → will write to config.yaml at the end
- Session only → will write to `.khanote/sessions/<slug>/researcher.yaml`

### Step 3: API Configuration
Ask:
1. "What's the API endpoint URL?"
2. "How does this API authenticate? (API key in header, Bearer token, or no auth)"
3. "Do you have an API key? (You can also set it as an environment variable like `${EXA_API_KEY}`)"

→ Configure headers accordingly

### Step 4: Capabilities
Ask: "What can this API do? Select all that apply:
- Search for information
- Ingest/index documents
- Analyze content
- Generate content"

→ Populates `capabilities` list. Require at least one.

### Step 5: Response Mapping
For each declared capability with an endpoint:
Ask: "When you call this API, what does the response look like? Paste a sample response if you have one."

→ Auto-generate `response_mapping` from sample JSON. If no sample: "I'll use sensible defaults."

### Step 6: SOP Templates
For capabilities WITHOUT an endpoint:
Ask: "This researcher doesn't have a direct [capability] endpoint. Want to customize the prompt template, or use the default?"

- Default → use built-in SOP template from `templates/sop/`
- Custom → ask user to describe what it should produce, generate SOP prompt

### Step 7: Connectivity Test
Run `khanote researcher add` internally or use `ConfigResearcher.test_connectivity()`.
Report: success (latency) or failure (error details).

If failed: "The API test failed. Check your URL/key. Save anyway (marked unavailable)? (yes/no)"

### Step 8: Confirmation
Show summary:
```
Researcher: [name]
Type: http
Capabilities: [list]
Endpoints: [caps with endpoints]
SOP fallbacks: [caps with SOP only]
API key: [masked]
```
Ask: "Save this researcher? (yes/no)"

→ Yes: call `add_researcher_to_config()` or `add_researcher_to_session()`
→ No: discard, clean exit

### Step 9: Feed Prompt (permanent researchers only)
Ask: "Would you like to create a feed based on this researcher? A feed runs recurring searches automatically. (yes/no)"

→ Yes: proceed with `/khanote.feed.add` (researcher pre-selected)
→ No: done

## Implementation

The underlying logic is in `src/khanote/cli/researcher_add.py`:
- `add_researcher_to_config(config_path, name, researcher_config)` — permanent
- `add_researcher_to_session(session_dir, name, researcher_config)` — session-scoped
- `promote_session_researcher(session_dir, config_path)` — post-session promotion
- `discard_session_researcher(session_dir)` — decline cleanup

## Error Handling

- Invalid URL → retry the URL prompt with error message
- No capabilities selected → explain that at least one is required, re-prompt
- User cancels at any step → clean exit, no partial config written
- Connectivity test fails → offer to save as unavailable

## Notes

- All configuration through conversational prompts — no CLI flags ever
- SOP prompt templates only execute inside vibe coding tools (skill mode)
- Running analysis via a SOP-backed researcher through standalone CLI will show a message directing to skill mode
