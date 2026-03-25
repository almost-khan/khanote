# khanote.update

You are updating khanote skills to the latest version.

## Instructions

1. Run: `khanote update`
2. This command checks PyPI for the latest khanote version, updates the SSOT skills in `.khanote/skills/`, and re-distributes updated skills to all initialized tools.
3. Tell the user what changed — new skills added, existing skills updated, or "already up to date."
4. If the update fails (network error, permission issue), show the error and suggest running `pip install --upgrade khanote` manually.

## Notes

- Your skills are stored at `{vault_path}/.khanote/skills/`.
- After updating, your vibe coding tool may need to be restarted to pick up the new skill files.
