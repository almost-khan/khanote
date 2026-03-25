# khanote

*Your research was almost Khan-worthy. Now it is. You're welcome.*

通用研究工作流工具包，为 vibe coding 工具打造。输出纯 Markdown——可配合 Obsidian、任何笔记软件、或直接用文件夹。

[English](README.md)

---

## khanote 是什么？

khanote 让你的 vibe coding 工具（Claude Code / Cursor / Codex / Gemini CLI / OpenCode）变成研究利器。它编排 researcher、管理 feed，输出结构化 Markdown 文件。SOP 以 skills 形式沉淀，用户只需修改配置。

**强烈推荐 Obsidian** 来构建个人知识库（双向链接、知识图谱、插件生态），但任何支持 Markdown 的工具或普通文件夹都可以。

## 安装

```bash
# pip
pip install khanote

# 或 Homebrew
brew tap almost-khan/tap
brew install khanote

# 或 pipx（隔离环境）
pipx install khanote
```

## 快速开始

```bash
khanote init --output ~/your-research-folder --tool claude-code --researcher perplexity

# 或者配合 Obsidian vault（推荐）
khanote init --output ~/your-obsidian-vault --tool claude-code --researcher perplexity
```

然后在你的 vibe coding 工具中运行：

```
/khanote.research.start AI agents
```

## 功能

### 研究工作流
- **Session 驱动**：每次研究 = 输出目录中一个日期前缀文件夹
- **流水线**：开始 → 导入来源 → 分析 → 保存为 Markdown
- **内置 researcher**：Perplexity、arXiv、PubMed、NotebookLM、GitHub、Hacker News、NewsAPI、RSS、Product Hunt
- **知识图谱**：通过共享主题自动关联 session（配合 Obsidian 效果更佳）

### 自定义 Researcher（零代码）
通过 `config.yaml` 把任何 HTTP REST API 接入为 researcher，不需要写 Python：

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

运行 `/khanote.researcher.add` 进入引导式配置——不需要命令行参数，不需要写代码。

### 每日简报（start-my-day）
获取个性化的每日研究简报，或运行临时研究：

```bash
# 每日简报——执行到期的 feed，去重，生成 Markdown
khanote start-my-day

# 临时研究——分解查询，路由到各 researcher，合成报告
khanote start-my-day "最新的 AI 智能体进展有哪些？"
```

或在 vibe coding 工具中运行：
```
/khanote.start-my-day
/khanote.start-my-day 最新的 AI 智能体进展有哪些？
```

简报保存至 `{vault}/khanote/briefings/{date}-{slug}.md`，报告保存至 `{vault}/khanote/sessions/{date}-{slug}/report.md`。

### 偏好设置系统
通过 `khanote init` 或直接编辑 `preferences.yaml` 个性化所有输出：

```yaml
language: zh-CN          # 任意 BCP 47 标签（en-US、fr-FR、de-DE 等）
role: developer          # developer | pm | researcher | mixed
interests: [ai, web]     # 驱动初始 feed 选择和关注点聚焦
depth: summary           # headlines | summary | detailed | deep_dive
expertise: intermediate  # beginner | intermediate | expert
tone: professional_briefing  # formal_report | professional_briefing | casual_notes
discover:
  enabled: true
  serendipity: 0.15      # 0.0 = 关闭，1.0 = 最大探索
```

查看当前偏好：`khanote preferences show`

### 随机发现 / Discover 功能
每次每日简报都包含 **Discover** 模块，推荐 1-2 条来自相邻领域的内容——打破信息茧房。可通过反馈调整推荐：

```bash
khanote discover like "rust programming"
khanote discover dislike "cryptocurrency"
```

或自然地说：`/khanote.discover.feedback`

### Feed 管理
设置定期研究 feed，自动获取并分析内容：

```yaml
feeds:
  llm-papers:
    researcher: arxiv
    query: "large language models"
    keywords: [llm, transformer, agent]
    frequency: daily
    active: true
```

引导式命令管理 feed：
- `/khanote.feed.add` — 新建 feed 或从已有 feed 复制
- `/khanote.feed.list` — 查看所有 feed 及状态
- `/khanote.feed.pause` / `resume` / `remove`

### SOP 提示模板
没有直接 API 端点的能力使用 SOP 提示模板——由 vibe coding 工具处理的结构化 prompt：
- **analyze**：来源质量评估、综合矩阵（STRONG/MODERATE/WEAK/EMERGING）、矛盾检测、两步差距分析
- **ingest**：来源类型分类、三深度摘要（标题/摘要/详情）、"使用 null，绝不捏造"
- **search**：四维评分（主题相关性 40%、来源质量 25%、信息密度 20%、新鲜度 15%）、去重步骤
- **generate-briefing**：倒金字塔——头条故事、你的关注点、你的 Feed、随机发现、Watch List
- **generate-report**：麦肯锡金字塔——执行摘要（建议优先）、关键发现（含置信度）、异见观点
- **decompose**：查询分解 → JSON 路由到多个 researcher
- **discover**：随机发现生成——相邻领域探索，含关联/惊喜/后续跟进

### 多工具支持
每个工具初始化一次，共享同一份配置：

| 工具 | 入口文件 | Skills 目录 |
|------|---------|------------|
| Claude Code | `CLAUDE.md` | `.claude/commands/` |
| Cursor | `.cursorrules` | `.cursor/rules/` |
| Codex | `AGENTS.md` | `.codex/` |
| Gemini CLI | `GEMINI.md` | `.gemini/` |
| OpenCode | `OPENCODE.md` | `.opencode/` |

## 设计原则

1. **两端固定，中间可换** — vibe coding 工具 ↔ [researcher + feed] ↔ Markdown 输出
2. **SOP 即 skills** — 工作流沉淀在 SKILL.md 中，不在人脑里
3. **零代码使用** — 所有操作通过引导式对话完成，无需 CLI 参数
4. **Session 驱动** — 每次研究 = 一个独立的日期前缀文件夹
5. **渐进式暴露** — 默认简单，需要时深入

## 可用 Skills

| Skill | 说明 |
|-------|------|
| `/khanote.start-my-day` | 每日简报或临时研究 |
| `/khanote.discover.feedback` | 对 Discover 内容点赞/踩 |
| `/khanote.research.start` | 开始新的研究 session |
| `/khanote.research.ingest` | 向 session 添加来源 |
| `/khanote.research.analyze` | 对已导入的来源进行分析 |
| `/khanote.research.save` | 保存结果到 Obsidian |
| `/khanote.research.pipeline` | 一键完整流水线 |
| `/khanote.researcher.add` | 添加自定义 HTTP researcher |
| `/khanote.feed.add` | 创建定期 feed |
| `/khanote.feed.list` | 列出所有 feed |
| `/khanote.update` | 更新 skills 到最新版本 |

## 内置 Researcher（9 个）

| Researcher | 适用领域 | 需要 API Key |
|-----------|---------|-------------|
| `perplexity` | 通用、新闻、问答 | 是（`PERPLEXITY_API_KEY`）|
| `arxiv` | 学术：CS、AI、数学、物理 | 否 |
| `pubmed` | 医学、生物医学文献 | 否 |
| `github` | 开源仓库 | 否（可选 `GITHUB_TOKEN`）|
| `hackernews` | 技术社区、创业 | 否 |
| `newsapi` | 70,000+ 来源的新闻 | 是（`NEWSAPI_KEY`）|
| `rss` | 任意 RSS/Atom Feed URL | 否 |
| `producthunt` | 新产品与发布 | 是（`PRODUCTHUNT_TOKEN`）|
| `notebooklm` | 文档摄入、综合 | 是（`GOOGLE_API_KEY`）|

## 名字由来

**Khan**（来自 AlmostKhan）+ **note** — Khan 的笔记 / 征服知识领地的笔记。

## 状态

积极开发中。核心研究工作流、feed 管理、每日简报（`start-my-day`）、偏好设置系统、9 个内置 researcher 以及随机发现 Discover 模块均已实现。398 个测试通过。

## 许可证

待定
