# khanote.feed.resume

Resume a paused feed — it will be included in start-my-day again.

## When to use

Run this skill when the user wants to re-activate a paused feed.

## Guided Flow

1. Run `khanote feed list` to show all feeds (including paused ones).
2. Ask the user which feed to resume (by name).
3. Confirm: "Resume feed '[name]'? (yes/no)"
4. Run `khanote feed resume [name]` — sets `active: true` in config.yaml.
5. Confirm: "Feed '[name]' is now active."

## Notes

- All configuration through conversational prompts — no CLI flags
