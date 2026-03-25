# khanote.discover.feedback

Give feedback on Discover section items to tune future recommendations.

## Overview

After reading your daily briefing's Discover section, use this skill to tell khanote whether you liked or disliked a discovered topic. This updates your `preferences.yaml` to influence future serendipity recommendations.

## Usage

Express your feedback naturally:

- "I loved that article about Rust programming" → `khanote discover like "rust programming"`
- "Not interested in cryptocurrency" → `khanote discover dislike "cryptocurrency"`
- "Block anything about tabloid news" → adds to `discover.blocked_domains`

## Direct CLI Commands

```bash
khanote discover like "<topic>"
khanote discover dislike "<topic>"
```

## How to Use This Skill

When the user expresses feedback about a Discover item:

1. Parse their intent: like / dislike / block
2. Extract the topic name from their message
3. Run the appropriate CLI command:
   - Like: `khanote discover like "<topic>"`
   - Dislike: `khanote discover dislike "<topic>"`
   - Block domain: Edit `preferences.yaml` directly under `discover.blocked_domains`
4. Confirm the update to the user

## Examples

User says: "That article about quantum computing in the Discover section was really interesting"
→ Run: `khanote discover like "quantum computing"`

User says: "I don't want to see anything about NFTs"
→ Run: `khanote discover dislike "NFTs"`

User says: "Please block tabloid-news.com from appearing"
→ Edit preferences.yaml: `discover.blocked_domains: [tabloid-news.com]`

## Effect on Future Briefings

- **Liked topics**: Increase probability of similar adjacent-domain recommendations
- **Disliked topics**: Reduce or eliminate similar recommendations
- **Blocked domains**: Never shown in Discover section

Changes take effect on the next `khanote start-my-day` run.

## View Current Preferences

```bash
khanote preferences show
```

This displays all preferences including liked/disliked topics and blocked domains.
