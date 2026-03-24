# khanote.feed.remove

Permanently remove a feed from config.yaml.

## When to use

Run this skill when the user wants to delete a feed entirely (not just pause it).

## Guided Flow

1. Run `khanote feed list` to show all feeds.
2. Ask the user which feed to remove (by name).
3. Confirm: "Remove feed '[name]' permanently? This cannot be undone. (yes/no)"
4. If yes: Run `khanote feed remove [name]` — deletes the feed from config.yaml.
5. Confirm: "Feed '[name]' removed."

## Notes

- Removal is permanent — use /khanote.feed.pause to temporarily disable
- All configuration through conversational prompts — no CLI flags
