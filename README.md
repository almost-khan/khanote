# khanote

*Your research was almost Khan-worthy. Now it is. You're welcome.*

A workflow kit for vibe coding tools — skills and SOPs for daily research briefings, feed management, and structured research sessions. Output is plain Markdown, best experienced with **[Obsidian](https://obsidian.md)**.

> **Requires a vibe coding tool**: Claude Code, Cursor, Codex, Gemini CLI, or OpenCode. khanote adds intelligence to the tool you already use — it has no standalone AI of its own.

> **Strongly recommended: [Obsidian](https://obsidian.md)** as your vault. khanote generates interlinked Markdown files — Obsidian's graph view, backlinks, and search make your research knowledge base come alive. Any note app or plain folder works too, but Obsidian is the best experience.

[中文文档](README_zh.md)

---

## What is khanote?

khanote installs a set of **skills** (SOPs) into your vibe coding tool. When you type `/khanote.start-my-day` in Claude Code, the AI follows the instructions in that skill to fetch your feeds, synthesize a briefing, and save structured Markdown to your Obsidian vault. You never leave your coding tool.

```
┌─────────────────────────────────────────────────────────────┐
│  You type: /khanote.start-my-day                            │
│                                                             │
│  Claude Code reads khanote skills → fetches your feeds     │
│  → synthesizes findings → saves Markdown to your vault     │
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

**Step 2 — Set up (from your Obsidian vault)**

```bash
cd ~/your-obsidian-vault
khanote init
```

The setup wizard asks 5 questions: language, tool, role, interests, and optional API keys. Everything installs in the current directory. Takes about 2 minutes.

**Step 3 — Restart your tool and run your first briefing**

Restart Claude Code (or your chosen tool), then type:

```
/khanote.start-my-day
```

Your first daily briefing is saved as Markdown in your vault. Open it in Obsidian.

---

## Sample Output

```markdown
# Daily Briefing — 2026-03-26

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
cd ~/your-obsidian-vault
khanote init
    └─▶ asks: language → tool → role → interests → API keys
    └─▶ copies skills to .claude/commands/ (or .cursor/rules/, etc.)
    └─▶ writes config + preferences to .khanote/
    └─▶ everything lives in the current directory

Restart Claude Code, then:

/khanote.start-my-day
    └─▶ Claude reads your config and feeds
    └─▶ fetches results from configured researchers
    └─▶ synthesizes briefing per your preferences
    └─▶ saves Markdown to your vault
```

Your config lives in `.khanote/` inside the folder where you ran `khanote init`:
- `config.yaml` — feeds, researchers, vault path
- `preferences.yaml` — language, role, interests, depth, tone

---

## Init Wizard (5 Steps)

When you run `khanote init`, the wizard walks you through setup:

| Step | Question | Default | Notes |
|------|----------|---------|-------|
| 1 | Language | English | en / zh / ja / ko / fr — all following prompts switch to your language |
| 2 | Tool | claude-code | claude-code / cursor / codex / gemini-cli / opencode |
| 3 | Role | mixed | developer / pm / researcher / operations / mixed |
| 4 | Interests | (skip) | ai, product, market, tech, medical, finance, sports, climate, security, devops, web, saas |
| 5 | API Keys | (skip) | PERPLEXITY_API_KEY, NEWSAPI_KEY, PRODUCTHUNT_TOKEN, GOOGLE_API_KEY — each validated inline |

Every question has a default — you can press Enter through all 5 and get a working config.

Re-running `khanote init` in the same directory detects your existing config and pre-fills current values.

---

## All User Flows

### Flow 1: Daily Briefing

The primary workflow. Run it every morning or whenever you want a research update.

```
/khanote.start-my-day                  ← daily briefing from your feeds
/khanote.start-my-day AI agents        ← ad-hoc research on any topic
```

**What happens:**
1. Reads your config (feeds, researchers) and preferences (language, role, interests, depth)
2. Fetches all active feeds from their researchers
3. Deduplicates results across feeds
4. Selects: **Top Story** (highest relevance) → **Your Focus** (top 3-5 matching your interests) → **Discover** (1-2 adjacent-domain items for serendipity)
5. Saves a Markdown briefing to `khanote/briefings/{date}.md`

---

### Flow 2: Research Session

For deep-dive research on a specific topic. Creates an isolated session folder with sources, analysis, and synthesis.

**Option A — Full pipeline (one command):**

```
/khanote.research.pipeline
```

The AI asks for your topic and sources, then runs start → ingest → analyze → save automatically.

**Option B — Step by step (fine-grained control):**

```
/khanote.research.start              ← create session folder
/khanote.research.ingest             ← add URLs, PDFs, or text
/khanote.research.analyze            ← extract findings across sources
/khanote.research.save               ← synthesize and finalize
```

**Session folder structure:**
```
khanote/2026-03-26_AI-Agents-Overview/
    _session.md          ← metadata and source list
    sources/             ← raw inputs (URLs, PDFs, text)
    research/            ← structured analysis notes
    synthesis/           ← final synthesized output
    artifacts/           ← generated files
```

---

### Flow 3: Feed Management

Feeds are recurring research queries. Each feed has a researcher and a query — they run automatically during your daily briefing.

**Add a feed (guided conversation):**
```
/khanote.feed.add
```
The AI walks you through: choose a researcher → set a query → add keyword filters → name it → save.

**Manage feeds:**
```
/khanote.feed.list                   ← see all feeds with status
/khanote.feed.pause                  ← temporarily skip a feed
/khanote.feed.resume                 ← re-activate a paused feed
/khanote.feed.remove                 ← permanently delete a feed
```

Or use the terminal CLI:
```bash
khanote feed list
khanote feed add
khanote feed pause ai-papers
khanote feed resume ai-papers
khanote feed remove old-feed
```

---

### Flow 4: Connect a Custom Researcher

Already have an API you want khanote to use? Connect it with zero code:

```
/khanote.researcher.add
```

The AI walks you through: describe the API → set the endpoint and auth → test the connection → save. Works with any HTTP REST API.

---

### Flow 5: Tune Your Discover Recommendations

The Discover section in your daily briefing shows adjacent-domain items for serendipity. Give feedback to tune it:

```
/khanote.discover.feedback
```

Just tell the AI your reaction:
- "I loved that Rust article" → more like this
- "Not interested in cryptocurrency" → less like this
- "Block tabloid news" → never show from that domain

Or use the CLI: `khanote discover like "rust"` / `khanote discover dislike "crypto"`

---

### Flow 6: Check Setup & Troubleshoot

```bash
khanote status                       # overview: tool, feeds, preferences, API keys
khanote check                        # validate config, tools, researchers
```

`khanote status` shows:
- Initialized tool and vault path
- Feed count
- Language, role, interests, depth
- API key status (present ✓ / missing ✗, masked values)
- Warnings for missing config

---

### Flow 7: Update Skills

```
/khanote.update                      # inside your vibe coding tool
```
Or:
```bash
khanote update                       # from the terminal
```

Updates the SSOT skills in `.khanote/skills/` and re-distributes to all initialized tools.

---

## Terminal CLI Reference

The CLI is for setup and config — not for research. All research runs inside your vibe coding tool.

| Command | Purpose |
|---------|---------|
| `khanote init` | Initialize in the current directory (5-step wizard) |
| `khanote status` | Show config status, feeds, API keys |
| `khanote check` | Validate vault, tools, researchers |
| `khanote update` | Update skills to latest version |
| `khanote feed add` | Add a feed (guided) |
| `khanote feed list` | List all feeds |
| `khanote feed pause <name>` | Pause a feed |
| `khanote feed resume <name>` | Resume a feed |
| `khanote feed remove <name>` | Delete a feed |
| `khanote discover like <topic>` | Like a Discover topic |
| `khanote discover dislike <topic>` | Dislike a Discover topic |
| `khanote preferences show` | View preferences |

---

## Available Skills (14)

Run these inside your vibe coding tool (Claude Code, Cursor, etc.):

| Skill | What it does |
|-------|-------------|
| `/khanote.start-my-day` | Daily briefing from your feeds, or ad-hoc research on any topic |
| `/khanote.research.pipeline` | Full research pipeline: start → ingest → analyze → save |
| `/khanote.research.start` | Start a new research session (creates dated folder) |
| `/khanote.research.ingest` | Add sources (URLs, PDFs, text) to the active session |
| `/khanote.research.analyze` | Extract findings from ingested sources |
| `/khanote.research.save` | Finalize and synthesize the session |
| `/khanote.feed.add` | Add a recurring research feed (guided conversation) |
| `/khanote.feed.list` | List all feeds with status |
| `/khanote.feed.pause` | Pause a feed temporarily |
| `/khanote.feed.resume` | Resume a paused feed |
| `/khanote.feed.remove` | Delete a feed permanently |
| `/khanote.discover.feedback` | Like/dislike Discover items to tune recommendations |
| `/khanote.researcher.add` | Connect a new API as a researcher (zero code) |
| `/khanote.update` | Update skills to the latest version |

---

## Built-in Researchers (9)

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

Initialize once per tool in the same directory; all tools share the same config:

| Tool | Entry File | Skills Directory |
|------|-----------|-----------------|
| Claude Code | `CLAUDE.md` | `.claude/commands/` |
| Cursor | `.cursorrules` | `.cursor/rules/` |
| Codex | `AGENTS.md` | `.codex/` |
| Gemini CLI | `GEMINI.md` | `.gemini/` |
| OpenCode | `OPENCODE.md` | `.opencode/` |

```bash
cd ~/my-obsidian-vault
khanote init --tool claude-code
khanote init --tool cursor          # same directory, second tool
```

---

## Why Obsidian?

We strongly recommend **[Obsidian](https://obsidian.md)** as your vault:

- **Graph View** — see connections between your briefings, research sessions, and topics at a glance
- **Backlinks** — every source, every finding, every briefing links back to its origins
- **Search** — full-text search across all your research, instantly
- **Daily Notes** — pair with khanote's daily briefings for a research journal
- **Plugins** — extend with dataview, calendar, kanban, and hundreds more
- **Local-first** — your data stays on your machine, in plain Markdown
- **Free** for personal use

khanote writes standard Markdown with `[[wikilinks]]` and YAML frontmatter — designed for Obsidian's features. Any Markdown editor works, but Obsidian unlocks the full potential.

---

## Preferences

Personalize all output by running `khanote init` or editing `.khanote/preferences.yaml`:

```yaml
language: en-US               # BCP-47 tag (zh-CN, fr-FR, ja-JP, ko-KR)
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

## Config Files

```
your-vault/
    .khanote/
        config.yaml            ← feeds, researchers, initialized tools
        preferences.yaml       ← language, role, interests, depth, tone
        skills/                ← SSOT skill source files
        context.md             ← skill context template (editable)
    .claude/commands/          ← skills distributed to Claude Code
    CLAUDE.md                  ← entry file for Claude Code
    khanote/
        briefings/             ← daily briefings saved here
        sessions/              ← research sessions saved here
```

---

## Design Principles

1. **Requires a vibe coding tool** — khanote adds skills to Claude Code, Cursor, etc. It does not run standalone AI.
2. **CWD install model** — `cd` into your vault, run `khanote init`. Everything lives in the current directory.
3. **CLI = config, skills = intelligence** — terminal for setup; research runs inside your IDE.
4. **SOP as skills** — research workflows live in SKILL.md files, not in your head.
5. **Zero-code for everyone** — all operations via guided prompts; no CLI flags needed after setup.
6. **Session-driven** — each research run = an independent date-prefixed folder.
7. **Obsidian-native** — Markdown with wikilinks and frontmatter, optimized for Obsidian's graph and search.

---

## Name

**Khan** (from AlmostKhan) + **note** — Khan's notes / notes that conquer knowledge.

## Status

Active development. 14 skills, 9 built-in researchers, feed management, daily briefing, preference system, and serendipity Discover are all implemented.

## License

TBD
