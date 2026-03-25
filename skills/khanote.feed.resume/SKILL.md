# khanote.feed.resume

You are resuming a paused research feed for the user.

## Instructions

1. Read `{vault_path}/.khanote/config.yaml` and list all paused feeds (where `active: false`).
2. Ask the user which feed they want to resume, if they have not already said.
3. Confirm: "Resume feed '{name}'? (yes/no)"
4. If yes, run: `khanote feed resume {name}` — this sets `active: true` in config.yaml.
5. Tell the user: "Feed '{name}' is now active. It will run on your next `/khanote.start-my-day`."

## Notes

- If no feeds are paused, tell the user all feeds are already active.
