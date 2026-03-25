# khanote.discover.feedback

You are recording the user's feedback on Discover section items to tune future recommendations.

## Instructions

1. Listen for the user expressing a reaction to a Discover item — they may say things like:
   - "I loved that article about Rust"
   - "Not interested in cryptocurrency"
   - "Never show me tabloid news"

2. Parse their intent:
   - Positive reaction → **like**
   - Negative reaction → **dislike**
   - Block a domain → **block**

3. Extract the topic or domain from their message.

4. Run the appropriate CLI command:
   - Like: `khanote discover like "{topic}"`
   - Dislike: `khanote discover dislike "{topic}"`
   - Block domain: edit `{vault_path}/.khanote/preferences.yaml` and add to `discover.blocked_domains`

5. Confirm the update to the user. For example: "Got it — I've noted your interest in Rust programming. You'll see more like this in future briefings."

## Effect on Future Briefings

- **Liked topics**: Increase the probability of similar adjacent-domain recommendations in the Discover section.
- **Disliked topics**: Reduce or eliminate similar recommendations.
- **Blocked domains**: Never shown in Discover section again.

## Notes

- Your preferences file is at `{vault_path}/.khanote/preferences.yaml`.
- Changes take effect on the next `/khanote.start-my-day`.
