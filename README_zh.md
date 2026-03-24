# khanote

*Your research was almost Khan-worthy. Now it is. You're welcome.*

通用研究工作流工具包，连接 vibe coding 工具与 Obsidian。

[English](README.md)

---

## khanote 是什么？

khanote 将你的 vibe coding 工具（Claude Code / Cursor / Codex / Gemini CLI / OpenCode）与 Obsidian 连接起来，中间研究层可插拔。SOP 以 skills 形式沉淀，用户只需修改配置。

## 快速开始

```bash
pip install khanote
khanote init --vault ~/your-obsidian-vault --tool claude-code --researcher perplexity
```

然后在你的 vibe coding 工具中运行：

```
/khanote.research.start AI agents
```

## 功能

### 研究工作流
- **Session 驱动**：每次研究 = vault 中一个日期前缀文件夹
- **流水线**：开始 → 导入来源 → 分析 → 保存到 Obsidian
- **内置 researcher**：Perplexity、arXiv、NotebookLM
- **知识图谱**：通过共享主题自动关联 session

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
- **analyze**：PRISMA 风格的主题综合分析 + 思维链
- **ingest**：从来源中提取元数据
- **search**：相关性排序和过滤
- **generate**：结构化研究报告生成

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

1. **两端固定，中间可换** — vibe coding 工具 ↔ [researcher + feed] ↔ Obsidian
2. **SOP 即 skills** — 工作流沉淀在 SKILL.md 中，不在人脑里
3. **零代码使用** — 所有操作通过引导式对话完成，无需 CLI 参数
4. **Session 驱动** — 每次研究 = 一个独立的日期前缀文件夹
5. **渐进式暴露** — 默认简单，需要时深入

## 可用 Skills

| Skill | 说明 |
|-------|------|
| `/khanote.research.start` | 开始新的研究 session |
| `/khanote.research.ingest` | 向 session 添加来源 |
| `/khanote.research.analyze` | 对已导入的来源进行分析 |
| `/khanote.research.save` | 保存结果到 Obsidian |
| `/khanote.research.pipeline` | 一键完整流水线 |
| `/khanote.researcher.add` | 添加自定义 HTTP researcher |
| `/khanote.feed.add` | 创建定期 feed |
| `/khanote.feed.list` | 列出所有 feed |
| `/khanote.update` | 更新 skills 到最新版本 |

## 名字由来

**Khan**（来自 AlmostKhan）+ **note** — Khan 的笔记 / 征服知识领地的笔记。

## 状态

积极开发中。核心研究工作流与自定义 researcher/feed 管理已实现，222 个测试通过。

## 许可证

待定
