# khanote.feed.pause

You are pausing an active research feed for the user.

## Instructions

1. Read `{vault_path}/.khanote/config.yaml` and list all active feeds.
2. Ask the user which feed they want to pause, if they have not already said.
3. Confirm: "Pause feed '{name}'? It will be skipped until you resume it. (yes/no)"
4. If yes, run: `khanote feed pause {name}` — this sets `active: false` in config.yaml.
5. Tell the user: "Feed '{name}' is now paused. Run `/khanote.feed.resume` to re-activate it."

## Notes

- Paused feeds stay in config and can be resumed at any time.
- Use `/khanote.feed.remove` to permanently delete a feed.
