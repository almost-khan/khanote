# khanote

*Your research was almost Khan-worthy. Now it is. You're welcome.*

A universal research workflow kit bridging vibe coding tools and Obsidian.

[中文文档](README_zh.md)

---

## What is khanote?

khanote connects your vibe coding tools (Claude Code / Cursor / Codex / Gemini CLI / OpenCode) with Obsidian, using a pluggable research layer in between. SOPs are codified as skills — you only touch config.

## Quick Start

```bash
pip install khanote
khanote init --vault ~/your-obsidian-vault --tool claude-code --researcher perplexity
```

Then inside your vibe coding tool, run:

```
/khanote.research.start AI agents
```

## Features

### Research Workflow
- **Session-driven**: each research run = a date-prefixed folder in your vault
- **Pipeline**: start → ingest sources → analyze → save to Obsidian
- **Built-in researchers**: Perplexity, arXiv, NotebookLM
- **Knowledge graph**: automatic linking between sessions via shared topics

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
- **analyze**: PRISMA-style thematic synthesis with chain-of-thought
- **ingest**: metadata extraction from sources
- **search**: relevance ranking and filtering
- **generate**: structured research report generation

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

1. **Two ends fixed, middle swappable** — vibe coding tool ↔ [researcher + feed] ↔ Obsidian
2. **SOP as skills** — workflows live in SKILL.md, not in your head
3. **Zero-code for everyone** — all operations via guided prompts, no CLI flags
4. **Session-driven** — each research run = an independent date-prefixed folder
5. **Progressive disclosure** — simple by default, powerful when you need it

## Available Skills

| Skill | Description |
|-------|-------------|
| `/khanote.research.start` | Start a new research session |
| `/khanote.research.ingest` | Add sources to a session |
| `/khanote.research.analyze` | Run analysis on ingested sources |
| `/khanote.research.save` | Save results to Obsidian |
| `/khanote.research.pipeline` | Full pipeline in one command |
| `/khanote.researcher.add` | Add a custom HTTP researcher |
| `/khanote.feed.add` | Create a recurring feed |
| `/khanote.feed.list` | List all feeds |
| `/khanote.update` | Update skills to latest version |

## Name

**Khan** (from AlmostKhan) + **note** — Khan's notes / notes that conquer knowledge.

## Status

Active development. Core research workflow and custom researcher/feed management are implemented. 222 tests passing.

## License

TBD
