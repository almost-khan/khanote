# khanote

*Your research was almost Khan-worthy. Now it is. You're welcome.*

A workflow kit for vibe coding tools — skills and SOPs for daily research briefings, feed management, and structured notes. Output is plain Markdown; works with Obsidian, any note app, or just a folder.

> **Requires a vibe coding tool**: Claude Code, Cursor, Codex, Gemini CLI, or OpenCode. khanote adds intelligence to the tool you already use — it has no standalone AI of its own.

[中文文档](README_zh.md)

---

## What is khanote?

khanote installs a set of **skills** (SOPs) into your vibe coding tool. When you type `/khanote.start-my-day` in Claude Code, the AI follows the instructions in that skill to fetch your feeds, synthesize a briefing, and save structured Markdown to your output folder. You never leave your coding tool.

```
┌─────────────────────────────────────────────────────────────┐
│  You type: /khanote.start-my-day                            │
│                                                             │
│  Claude Code reads khanote skills → fetches your feeds     │
│  → synthesizes findings → saves Markdown briefing          │
└─────────────────────────────────────────────────────────────┘
```

**The terminal CLI (`khanote`) is only for setup and config management.** All research intelligence runs inside your vibe coding tool.

---

## Quick Start

**Step 1 — Install**

```bash
pip install khanote
# or: brew install khanote  |  pipx install khanote
```

**Step 2 — Set up (from your vault / project folder)**

```bash
cd ~/your-obsidian-vault   # or any folder
khanote init
```

The setup wizard asks for your language, tool, role, and interests. Everything installs in the current directory — just like speckit. Takes about 2 minutes.

**Step 3 — Restart your tool and run your first briefing**

Restart Claude Code (or your chosen tool), then type:

```
/khanote.start-my-day
```

That's it. Your first daily briefing is saved to your output folder.

---

## Sample Output

```markdown
# Daily Briefing — 2026-03-25

## Top Story
[Gemini 2.0 Flash outperforms GPT-4o on coding benchmarks](https://...) — Google's
latest model shows 23% improvement on HumanEval vs prior generation.

## Your Focus
1. [Mixture-of-Experts scaling laws updated](https://arxiv.org/...) — New paper
   revises MoE efficiency estimates for 100B+ parameter models.
2. [Cursor raises $900M Series C](https://...) — Vibe coding valuations continue
   to surge as developer tools market consolidates.

## Your Feeds
### ai-papers (arxiv)
- [Attention-free transformers revisited](https://arxiv.org/...) — RWKV-v6 benchmarks

## Discover
- [DeepMind's AlphaFold 3 applied to drug discovery](https://...) — Adjacent to your
  AI interest: protein structure prediction is now powering pharma pipelines.

## Sources
[all cited URLs]
```

---

## How It Works

```
cd ~/your-vault
khanote init
    └─▶ copies skills to .claude/commands/ (or .cursor/rules/, etc.)
    └─▶ writes config + preferences to .khanote/
    └─▶ everything lives in the current directory

/khanote.start-my-day  (inside Claude Code)
    └─▶ Claude reads your config and feeds
    └─▶ fetches results from configured researchers
    └─▶ synthesizes briefing per your preferences
    └─▶ saves Markdown to the same directory
```

Your config lives in `.khanote/` inside the folder where you ran `khanote init`:
- `config.yaml` — feeds, researchers, vault path
- `preferences.yaml` — language, role, interests, depth, tone

---

## Available Skills

Run these inside your vibe coding tool (Claude Code, Cursor, etc.):

| Skill | What it does |
|-------|-------------|
| `/khanote.start-my-day` | Daily briefing from your feeds, or ad-hoc research on any topic |
| `/khanote.research.start` | Start a new research session (creates dated folder) |
| `/khanote.research.ingest` | Add sources (URLs, PDFs, text) to the active session |
| `/khanote.research.analyze` | Extract findings from ingested sources |
| `/khanote.research.save` | Finalize and synthesize the session |
| `/khanote.research.pipeline` | Full pipeline: start → ingest → analyze → save |
| `/khanote.feed.add` | Add a recurring research feed |
| `/khanote.feed.list` | List all feeds with status |
| `/khanote.feed.pause` | Pause a feed temporarily |
| `/khanote.feed.resume` | Resume a paused feed |
| `/khanote.feed.remove` | Delete a feed permanently |
| `/khanote.discover.feedback` | Like/dislike Discover items to tune recommendations |
| `/khanote.researcher.add` | Connect a new API as a researcher (no code required) |
| `/khanote.update` | Update skills to the latest version |

---

## Built-in Researchers

| Researcher | Best for | Key required? |
|-----------|----------|--------------|
| `arxiv` | Academic papers (CS, AI, math, physics) | No |
| `perplexity` | General queries, current events, Q&A | Yes (`PERPLEXITY_API_KEY`) |
| `newsapi` | News from 70k+ sources | Yes (`NEWSAPI_KEY`) |
| `hackernews` | Tech discussions, startups, tools | No |
| `pubmed` | Medical and biomedical literature | No |
| `github` | Open-source repositories | No (optional `GITHUB_TOKEN`) |
| `rss` | Any RSS/Atom feed by URL | No |
| `producthunt` | New products and launches | Yes (`PRODUCTHUNT_TOKEN`) |
| `notebooklm` | Document synthesis | Yes (`GOOGLE_API_KEY`) |

Add any HTTP REST API as a custom researcher via `/khanote.researcher.add` — no code, guided prompts only.

---

## Multi-Tool Support

Initialize once per tool; all tools share the same config:

| Tool | Entry File | Skills Directory |
|------|-----------|-----------------|
| Claude Code | `CLAUDE.md` | `.claude/commands/` |
| Cursor | `.cursorrules` | `.cursor/rules/` |
| Codex | `AGENTS.md` | `.codex/` |
| Gemini CLI | `GEMINI.md` | `.gemini/` |
| OpenCode | `OPENCODE.md` | `.opencode/` |

```bash
cd ~/my-research && khanote init --tool cursor
```

---

## Preferences

Personalize all output by running `khanote init` or editing `preferences.yaml` directly:

```yaml
language: en-US               # BCP-47 tag (zh-CN, fr-FR, ja-JP, ...)
role: developer               # developer | pm | researcher | operations | mixed
interests: [ai, product]      # drives starter feeds and focus selection
depth: summary                # headlines | summary | detailed | deep_dive
expertise: intermediate       # beginner | intermediate | expert
tone: professional_briefing   # formal_report | professional_briefing | casual_notes
discover:
  enabled: true
  serendipity: 0.15           # 0.0 = off, 1.0 = maximum exploration
```

---

## Design Principles

1. **Requires a vibe coding tool** — khanote adds skills to Claude Code, Cursor, etc. It does not run standalone AI.
2. **SOP as skills** — research workflows live in SKILL.md files, not in your head.
3. **Zero-code for everyone** — all operations via guided prompts; no CLI flags needed after setup.
4. **Session-driven** — each research run = an independent date-prefixed folder.
5. **Progressive disclosure** — simple by default, powerful when you need it.

---

## Name

**Khan** (from AlmostKhan) + **note** — Khan's notes / notes that conquer knowledge.

## Status

Active development. 14 skills, 9 built-in researchers, feed management, daily briefing, preference system, and serendipity Discover are all implemented.

## License

TBD
