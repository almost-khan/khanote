# khanote.researcher.add

You are helping the user connect a new data source (API) to khanote.

## Instructions

Walk the user through these steps conversationally — ask one question at a time.

### Step 1: Describe the data source
Ask: "Describe the data source you want to connect. For example: 'I want to use Exa Search API to find research papers.'"
Extract: API name, likely capabilities, and domain.

### Step 2: Permanent or session-only?
Ask: "Save this researcher permanently for all future sessions, or just for this session?"
- Permanent → write to `config.yaml`
- Session only → write to `.khanote/sessions/{slug}/researcher.yaml`

### Step 3: API configuration
Ask these three questions:
1. "What is the API endpoint URL?"
2. "How does this API authenticate? (API key in header, Bearer token, or no auth)"
3. "Do you have an API key? You can also use an environment variable like `${MY_API_KEY}`."

### Step 4: Capabilities
Ask: "What can this API do? Select all that apply: search, ingest, analyze, generate."
Require at least one capability.

### Step 5: Test the connection
Run `khanote researcher add` or call the API with a test request to verify the key and URL.
- Success: tell the user the connection works and show the response latency.
- Failure: show the error and ask: "Save anyway as unavailable? (yes/no)"

### Step 6: Confirm and save
Show a summary of the researcher configuration and ask: "Save this researcher? (yes/no)"
- Yes: write to `config.yaml` (permanent) or session file.
- No: discard and exit cleanly.

### Step 7: Offer to create a feed (permanent researchers only)
Ask: "Would you like to create a recurring feed using this researcher? (yes/no)"
- Yes: proceed with `/khanote.feed.add` with this researcher pre-selected.
- No: done.

## Notes

- All configuration is done through this conversation — no CLI flags required.
- Your config is at `{vault_path}/.khanote/config.yaml`.
