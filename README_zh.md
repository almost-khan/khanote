# khanote

*你的研究差点达到汗级水准。现在真的到了。不客气。*

专为 vibe coding 工具设计的研究工作流套件——包含每日简报、订阅管理和结构化笔记的 SOP 技能。输出纯 Markdown，可配合 Obsidian、任何笔记软件或直接使用文件夹。

> **需要 vibe coding 工具**：Claude Code、Cursor、Codex、Gemini CLI 或 OpenCode。khanote 为你已使用的工具增添智能——它本身没有独立的 AI 能力。

[English Documentation](README.md)

---

## khanote 是什么？

khanote 将一套**技能**（SOP 指令）安装到你的 vibe coding 工具中。当你在 Claude Code 中输入 `/khanote.start-my-day`，AI 会按照技能中的指令拉取你的订阅内容、合成简报，并将结构化 Markdown 保存到你的输出文件夹。你无需离开你的编程工具。

```
┌─────────────────────────────────────────────────────────────┐
│  你输入：/khanote.start-my-day                              │
│                                                             │
│  Claude Code 读取 khanote 技能 → 拉取订阅内容              │
│  → 合成研究发现 → 保存 Markdown 简报                       │
└─────────────────────────────────────────────────────────────┘
```

**终端 CLI（`khanote`）仅用于初始化和配置管理。** 所有研究智能均在你的 vibe coding 工具内部运行。

---

## 快速开始

**第一步 — 安装**

```bash
pip install khanote
# 或：brew install khanote  |  pipx install khanote
```

**第二步 — 初始化（在你的 vault / 项目目录下）**

```bash
cd ~/your-obsidian-vault   # 或任何文件夹
khanote init
```

初始化向导会依次询问你的语言、工具、角色和兴趣方向。所有文件安装在当前目录——和 speckit 一样。大约需要 2 分钟。

**第三步 — 重启工具，运行第一份简报**

重启 Claude Code（或你选择的工具），然后输入：

```
/khanote.start-my-day
```

完成。你的第一份每日简报已保存到你的输出目录。

---

## 输出示例

```markdown
# 每日简报 — 2026-03-25

## 头条
[Gemini 2.0 Flash 在编程基准测试中超越 GPT-4o](https://...) — Google 最新模型
在 HumanEval 上比上一代提升 23%。

## 你的焦点
1. [混合专家模型扩展规律更新](https://arxiv.org/...) — 新论文修订了 1000 亿+
   参数模型的 MoE 效率估算。
2. [Cursor 完成 9 亿美元 C 轮融资](https://...) — vibe coding 工具市值持续攀升。

## 你的订阅
### ai-papers (arxiv)
- [无注意力机制 Transformer 重访](https://arxiv.org/...) — RWKV-v6 基准测试

## 发现
- [DeepMind AlphaFold 3 用于药物研发](https://...) — 与你的 AI 兴趣相关：
  蛋白质结构预测正在推动制药管线革新。

## 来源
[所有引用链接]
```

---

## 工作原理

```
cd ~/your-vault
khanote init
    └─▶ 将技能复制到 .claude/commands/（或 .cursor/rules/ 等）
    └─▶ 将配置和偏好写入 .khanote/
    └─▶ 所有内容都在当前目录下

/khanote.start-my-day（在 Claude Code 中运行）
    └─▶ Claude 读取你的配置和订阅
    └─▶ 从已配置的研究者获取内容
    └─▶ 根据你的偏好合成简报
    └─▶ 将 Markdown 保存到同一目录
```

你的配置存储在运行 `khanote init` 的目录下的 `.khanote/`：
- `config.yaml` — 订阅、研究者、vault 路径
- `preferences.yaml` — 语言、角色、兴趣、详细程度、语气

---

## 可用技能

在你的 vibe coding 工具中运行这些技能（Claude Code、Cursor 等）：

| 技能 | 功能 |
|------|------|
| `/khanote.start-my-day` | 从订阅生成每日简报，或对任意主题进行即时研究 |
| `/khanote.research.start` | 开始新的研究会话（创建日期前缀文件夹） |
| `/khanote.research.ingest` | 向当前会话添加来源（URL、PDF、文本） |
| `/khanote.research.analyze` | 从摄入的来源中提取研究发现 |
| `/khanote.research.save` | 完成并合成研究会话 |
| `/khanote.research.pipeline` | 完整流程：开始 → 摄入 → 分析 → 保存 |
| `/khanote.feed.add` | 添加一个循环研究订阅 |
| `/khanote.feed.list` | 查看所有订阅及其状态 |
| `/khanote.feed.pause` | 暂停订阅 |
| `/khanote.feed.resume` | 恢复已暂停的订阅 |
| `/khanote.feed.remove` | 永久删除订阅 |
| `/khanote.discover.feedback` | 对发现栏目内容点赞/踩，调整推荐 |
| `/khanote.researcher.add` | 将新 API 添加为研究者（无需代码） |
| `/khanote.update` | 将技能更新到最新版本 |

---

## 内置研究者

| 研究者 | 最适合 | 是否需要密钥 |
|--------|--------|-------------|
| `arxiv` | 学术论文（CS、AI、数学、物理） | 否 |
| `perplexity` | 通用查询、时事、问答 | 是（`PERPLEXITY_API_KEY`） |
| `newsapi` | 7 万+ 来源的新闻 | 是（`NEWSAPI_KEY`） |
| `hackernews` | 技术讨论、初创公司 | 否 |
| `pubmed` | 医学和生物医学文献 | 否 |
| `github` | 开源仓库 | 否（可选 `GITHUB_TOKEN`） |
| `rss` | 任何 RSS/Atom 订阅源 | 否 |
| `producthunt` | 新产品和发布 | 是（`PRODUCTHUNT_TOKEN`） |
| `notebooklm` | 文档合成 | 是（`GOOGLE_API_KEY`） |

通过 `/khanote.researcher.add` 将任意 HTTP REST API 添加为自定义研究者——无需代码，全程对话引导。

---

## 多工具支持

每个工具初始化一次，所有工具共享同一配置：

| 工具 | 入口文件 | 技能目录 |
|------|---------|---------|
| Claude Code | `CLAUDE.md` | `.claude/commands/` |
| Cursor | `.cursorrules` | `.cursor/rules/` |
| Codex | `AGENTS.md` | `.codex/` |
| Gemini CLI | `GEMINI.md` | `.gemini/` |
| OpenCode | `OPENCODE.md` | `.opencode/` |

---

## 偏好设置

通过 `khanote init` 或直接编辑 `preferences.yaml` 个性化所有输出：

```yaml
language: zh-CN               # BCP-47 标签（en-US、fr-FR、ja-JP 等）
role: pm                      # developer | pm | researcher | operations | mixed
interests: [ai, product]      # 驱动初始订阅和焦点选择
depth: summary                # headlines | summary | detailed | deep_dive
expertise: intermediate       # beginner | intermediate | expert
tone: professional_briefing   # formal_report | professional_briefing | casual_notes
discover:
  enabled: true
  serendipity: 0.15           # 0.0 = 关闭，1.0 = 最大探索
```

---

## 设计原则

1. **需要 vibe coding 工具** — khanote 为 Claude Code、Cursor 等添加技能，不独立运行 AI。
2. **SOP 即技能** — 研究工作流存储在 SKILL.md 文件中，而不是存在于你的记忆里。
3. **零代码门槛** — 所有操作通过对话引导完成，初始化后无需 CLI 参数。
4. **会话驱动** — 每次研究 = 一个独立的日期前缀文件夹。
5. **渐进式复杂度** — 默认简单，需要时功能强大。

---

## 名称由来

**Khan**（来自 AlmostKhan）+ **note** — 汗的笔记 / 征服知识的笔记。

## 状态

积极开发中。14 个技能、9 个内置研究者、订阅管理、每日简报、偏好系统和发现栏目均已实现。

## 许可证

TBD
