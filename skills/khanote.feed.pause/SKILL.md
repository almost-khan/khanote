# khanote.feed.pause

Pause an active feed — it will be skipped by start-my-day until resumed.

## When to use

Run this skill when the user wants to temporarily stop a feed without deleting it.

## Guided Flow

1. Run `khanote feed list` to show all feeds.
2. Ask the user which feed to pause (by name).
3. Confirm: "Pause feed '[name]'? (yes/no)"
4. Run `khanote feed pause [name]` — sets `active: false` in config.yaml.
5. Confirm: "Feed '[name]' is now paused. Run /khanote.feed.resume to re-activate it."

## Notes

- Paused feeds remain in config.yaml — they are not deleted
- Use /khanote.feed.remove to permanently delete a feed
- All configuration through conversational prompts — no CLI flags
