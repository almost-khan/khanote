# khanote.feed.remove

You are permanently removing a research feed for the user.

## Instructions

1. Read `{vault_path}/.khanote/config.yaml` and list all feeds.
2. Ask the user which feed they want to remove, if they have not already said.
3. Confirm: "Remove feed '{name}' permanently? This cannot be undone. (yes/no)"
4. If yes, run: `khanote feed remove {name}` — this deletes the feed from config.yaml.
5. Tell the user: "Feed '{name}' has been removed."

## Notes

- Removal is permanent. Use `/khanote.feed.pause` to temporarily disable a feed instead.
