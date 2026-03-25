# khanote

*Your research was almost Khan-worthy. Now it is. You're welcome.*

A universal research workflow kit for vibe coding tools. Output is plain Markdown — use with Obsidian, any note app, or just a folder.

[中文文档](README_zh.md)

---

## What is khanote?

khanote turns your vibe coding tools (Claude Code / Cursor / Codex / Gemini CLI / OpenCode) into a research powerhouse. It orchestrates researchers, manages feeds, and outputs structured Markdown files. SOPs are codified as skills — you only touch config.

**Obsidian is strongly recommended** for building a personal knowledge base (backlinks, graph view, plugins), but any Markdown-compatible tool or folder works.

## Install

```bash
# pip
pip install khanote

# or Homebrew
brew tap almost-khan/tap
brew install khanote

# or pipx (isolated)
pipx install khanote
```

## Quick Start

```bash
khanote init --output ~/your-research-folder --tool claude-code --researcher perplexity

# or with an Obsidian vault (recommended)
khanote init --output ~/your-obsidian-vault --tool claude-code --researcher perplexity
```

Then inside your vibe coding tool, run:

```
/khanote.research.start AI agents
```

## Features

### Research Workflow
- **Session-driven**: each research run = a date-prefixed folder in your output directory
- **Pipeline**: start → ingest sources → analyze → save as Markdown
- **Built-in researchers**: Perplexity, arXiv, PubMed, NotebookLM, GitHub, Hacker News, NewsAPI, RSS, Product Hunt
- **Knowledge graph**: automatic linking between sessions via shared topics (enhanced with Obsidian)

### Custom Researchers (Zero Code)
Add any HTTP REST API as a researcher through `config.yaml` — no Python required:

```yaml
researchers:
  exa:
    type: http
    api_key: ${EXA_API_KEY}
    capabilities: [search]
    endpoints:
      search:
        url: "https://api.exa.ai/search"
        method: POST
        headers:
          Authorization: "Bearer {api_key}"
        body_template: '{"query": "{query}", "numResults": 10}'
        response_mapping:
          results: "$.results"
          title: "$.title"
          excerpt: "$.text"
```

Run `/khanote.researcher.add` for a guided setup — no flags, no code.

### Daily Briefing (`start-my-day`)
Get a personalized daily research briefing or run ad-hoc research:

```bash
# Daily briefing — executes due feeds, deduplicates, generates Markdown
khanote start-my-day

# Ad-hoc research — decompose query, route to researchers, synthesize report
khanote start-my-day "What are the latest advances in AI agents?"
```

Or inside your vibe coding tool:
```
/khanote.start-my-day
/khanote.start-my-day What are the latest advances in AI agents?
```

Briefings saved to `{vault}/khanote/briefings/{date}-{slug}.md`. Reports to `{vault}/khanote/sessions/{date}-{slug}/report.md`.

### Preference System
Personalize all output via `khanote init` or by editing `preferences.yaml`:

```yaml
language: en-US          # Any BCP 47 tag (zh-CN, fr-FR, de-DE, ...)
role: developer          # developer | pm | researcher | mixed
interests: [ai, web]     # Drives starter feeds and focus selection
depth: summary           # headlines | summary | detailed | deep_dive
expertise: intermediate  # beginner | intermediate | expert
tone: professional_briefing  # formal_report | professional_briefing | casual_notes
discover:
  enabled: true
  serendipity: 0.15      # 0.0 = off, 1.0 = max exploration
```

View current preferences: `khanote preferences show`

### Serendipity / Discover
Every daily briefing includes a **Discover** section with 1-2 items from adjacent domains — breaking the filter bubble. Give feedback to tune recommendations:

```bash
khanote discover like "rust programming"
khanote discover dislike "cryptocurrency"
```

Or naturally: `/khanote.discover.feedback`

### Feed Management
Set up recurring research feeds that automatically fetch and analyze content:

```yaml
feeds:
  llm-papers:
    researcher: arxiv
    query: "large language models"
    keywords: [llm, transformer, agent]
    frequency: daily
    active: true
```

Manage feeds with guided commands:
- `/khanote.feed.add` — create a new feed or clone from existing
- `/khanote.feed.list` — see all feeds with status
- `/khanote.feed.pause` / `resume` / `remove`

### SOP Prompt Templates
Capabilities without a direct API endpoint use SOP prompt templates — structured prompts that your vibe coding tool processes:
- **analyze**: Source quality assessment, synthesis matrix (STRONG/MODERATE/WEAK/EMERGING), contradiction detection, two-step gap analysis
- **ingest**: Source type classification, 3-depth summaries (headline/summary/detailed), "use null never fabricate"
- **search**: 4-dimensional scoring (topical 40%, quality 25%, density 20%, freshness 15%), dedup step
- **generate-briefing**: Inverted pyramid — Top Story, Your Focus, Your Feeds, Discover, Watch List
- **generate-report**: McKinsey pyramid — Executive Summary (recommendation-first), Key Findings with confidence levels, Dissenting Views
- **decompose**: Query decomposition → JSON routing to multiple researchers
- **discover**: Serendipity generation — adjacent domain exploration with connection/surprise/follow-up

### Multi-Tool Support
Initialize once per tool, share the same config:

| Tool | Entry File | Skills Directory |
|------|-----------|-----------------|
| Claude Code | `CLAUDE.md` | `.claude/commands/` |
| Cursor | `.cursorrules` | `.cursor/rules/` |
| Codex | `AGENTS.md` | `.codex/` |
| Gemini CLI | `GEMINI.md` | `.gemini/` |
| OpenCode | `OPENCODE.md` | `.opencode/` |

## Design Principles

1. **Two ends fixed, middle swappable** — vibe coding tool ↔ [researcher + feed] ↔ Markdown output
2. **SOP as skills** — workflows live in SKILL.md, not in your head
3. **Zero-code for everyone** — all operations via guided prompts, no CLI flags
4. **Session-driven** — each research run = an independent date-prefixed folder
5. **Progressive disclosure** — simple by default, powerful when you need it

## Available Skills

| Skill | Description |
|-------|-------------|
| `/khanote.start-my-day` | Daily briefing or ad-hoc research |
| `/khanote.discover.feedback` | Like/dislike Discover items |
| `/khanote.research.start` | Start a new research session |
| `/khanote.research.ingest` | Add sources to a session |
| `/khanote.research.analyze` | Run analysis on ingested sources |
| `/khanote.research.save` | Save results to Obsidian |
| `/khanote.research.pipeline` | Full pipeline in one command |
| `/khanote.researcher.add` | Add a custom HTTP researcher |
| `/khanote.feed.add` | Create a recurring feed |
| `/khanote.feed.list` | List all feeds |
| `/khanote.update` | Update skills to latest version |

## Built-in Researchers (9)

| Researcher | Domains | Key Required |
|-----------|---------|-------------|
| `perplexity` | General, news, Q&A | Yes (`PERPLEXITY_API_KEY`) |
| `arxiv` | Academic: CS, AI, math, physics | No |
| `pubmed` | Medical, biomedical literature | No |
| `github` | Open-source repositories | No (optional `GITHUB_TOKEN`) |
| `hackernews` | Tech community, startups | No |
| `newsapi` | News from 70k+ sources | Yes (`NEWSAPI_KEY`) |
| `rss` | Any RSS/Atom feed URL | No |
| `producthunt` | New products and launches | Yes (`PRODUCTHUNT_TOKEN`) |
| `notebooklm` | Document ingestion, synthesis | Yes (`GOOGLE_API_KEY`) |

## Name

**Khan** (from AlmostKhan) + **note** — Khan's notes / notes that conquer knowledge.

## Status

Active development. Core research workflow, feed management, daily briefing (`start-my-day`), preference system, 9 built-in researchers, and serendipity Discover section are all implemented. 398 tests passing.

## License

TBD
