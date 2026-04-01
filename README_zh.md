# khanote

*Your research was almost Khan-worthy. Now it is. You're welcome.*

专为 vibe coding 工具设计的研究工作流套件——包含每日简报、订阅管理和结构化研究会话的 SOP 技能。输出纯 Markdown，强烈推荐配合 **[Obsidian](https://obsidian.md)** 使用。

> **需要 vibe coding 工具**：Claude Code、Cursor、Codex、Gemini CLI 或 OpenCode。khanote 为你已使用的工具增添智能——它本身没有独立的 AI 能力。

> **强烈推荐：[Obsidian](https://obsidian.md)** 作为你的知识库。khanote 生成相互链接的 Markdown 文件——Obsidian 的图谱视图、反向链接和搜索功能让你的研究知识库真正活起来。其他笔记应用或纯文件夹也能用，但 Obsidian 是最佳体验。

[English Documentation](README.md)

---

## khanote 是什么？

khanote 将一套**技能**（SOP 指令）安装到你的 vibe coding 工具中。当你在 Claude Code 中输入 `/khanote.start-my-day`，AI 会按照技能中的指令拉取你的订阅内容、合成简报，并将结构化 Markdown 保存到你的 Obsidian vault。你无需离开你的编程工具。

```
┌─────────────────────────────────────────────────────────────┐
│  你输入：/khanote.start-my-day                              │
│                                                             │
│  Claude Code 读取 khanote 技能 → 拉取订阅内容              │
│  → 合成研究发现 → 保存 Markdown 到你的 vault               │
└─────────────────────────────────────────────────────────────┘
```

**终端 CLI（`khanote`）仅用于初始化和配置管理。** 所有研究智能均在你的 vibe coding 工具内部运行。

---

## 快速开始

**第一步 — 安装**

```bash
brew install almost-khan/tap/khanote
# 或：pip install khanote  |  pipx install khanote
```

**第二步 — 初始化（在你的 Obsidian vault 目录下）**

```bash
cd ~/your-obsidian-vault
khanote init
```

交互式向导会展示渐变色 ASCII 艺术 Logo，然后用箭头键导航和圆点进度条（`● ● ○ ○ ○`）引导你完成 5 步设置。所有文件安装在当前目录。

**第三步 — 重启工具，运行第一份简报**

重启 Claude Code（或你选择的工具），然后输入：

```
/khanote.start-my-day
```

你的第一份每日简报已保存为 Markdown。在 Obsidian 中打开它。

---

## 输出示例

```markdown
# 每日简报 — 2026-03-26

## Gemini 2.0 Flash 以编程基准 23% 领先提升企业采用门槛
[Gemini 2.0 Flash](https://...) 在 HumanEval 上超越 GPT-4o。
**这意味着**：评估编程助手的企业团队现在有了 OpenAI 旗舰产品的有力替代品。
[[Google AI Blog]](https://...)

## 你的焦点
- **MoE 扩展规律在千亿参数以上被向下修正** — 新论文表明超过千亿参数后收益递减。
  [[arXiv]](https://arxiv.org/...)
- **Cursor 9 亿美元 C 轮标志 Vibe Coding 市场整合** — 开发者工具市场正收窄至
  3-4 个主要玩家。[[TechCrunch]](https://...)

## 你的订阅
### ai-papers (arxiv)
- RWKV-v6 在不使用注意力机制的情况下匹配 Transformer 质量 [[arXiv]](https://...)

## 发现
- **AlphaFold 3 蛋白质折叠突破与 LLM 注意力机制存在平行关系** — 结构生物学与
  ML 架构的交叉融合正在加速。[[Nature]](https://...)

## 来源
[所有引用链接]
```

> 每个标题都是**行动标题**（陈述洞察而非描述话题）。每条内容回答"这意味着什么？"并附上来源引用。这是 khanote SOP 模板强制执行的[金字塔原则](https://en.wikipedia.org/wiki/Minto_Pyramid_Principle)写作质量。

---

## 工作原理

```
cd ~/your-obsidian-vault
khanote init
    └─▶ 询问：语言 → 工具 → 角色 → 兴趣 → API keys
    └─▶ 将技能复制到 .claude/commands/（或 .cursor/rules/ 等）
    └─▶ 将配置和偏好写入 .khanote/
    └─▶ 所有内容都在当前目录下

重启 Claude Code，然后：

/khanote.start-my-day
    └─▶ Claude 读取你的配置和订阅
    └─▶ 从已配置的研究者获取内容
    └─▶ 根据你的偏好合成简报
    └─▶ 将 Markdown 保存到你的 vault
```

你的配置存储在运行 `khanote init` 的目录下的 `.khanote/`：
- `config.yaml` — 订阅、研究者、vault 路径
- `preferences.yaml` — 语言、角色、兴趣、详细程度、语气

---

## 初始化向导（5 步）

运行 `khanote init` 时，首先展示渐变色 ASCII 艺术 Logo：

```
  ██╗  ██╗██╗  ██╗ █████╗ ███╗   ██╗ ██████╗ ████████╗███████╗
  ██║ ██╔╝██║  ██║██╔══██╗████╗  ██║██╔═══██╗╚══██╔══╝██╔════╝
  █████╔╝ ███████║███████║██╔██╗ ██║██║   ██║   ██║   █████╗
  ██╔═██╗ ██╔══██║██╔══██║██║╚██╗██║██║   ██║   ██║   ██╔══╝
  ██║  ██╗██║  ██║██║  ██║██║ ╚████║╚██████╔╝   ██║   ███████╗
  ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝    ╚═╝   ╚══════╝
```

然后 5 步箭头键导航 + 圆点进度：

| 步骤 | 问题 | 交互方式 | 默认值 |
|------|------|---------|--------|
| 1 | 语言 | 箭头键选择 | English |
| 2 | 工具 | 箭头键选择 | Claude Code |
| 3 | 角色 | 箭头键选择 | Mixed |
| 4 | 兴趣 | 空格键复选框（多选）+ "Other (custom)" | （跳过） |
| 5 | API Keys | 文本输入，Enter 跳过 | （跳过） |

```
● ● ● ○ ○  Step 3 of 5
  What is your role?
```

每个问题都有默认值——你可以一路按 Enter 直接完成。非 TTY 环境（CI、管道输入）自动回退到文本输入。

在同一目录再次运行 `khanote init` 会检测到已有配置，并预填当前值。

---

## 全部用户流程

### 流程 1：每日简报

主要工作流。每天早上运行，或任何时候想要研究更新。

```
/khanote.start-my-day                  ← 从订阅生成每日简报
/khanote.start-my-day AI agents        ← 对任意主题即时研究
```

**执行过程：**
1. 读取配置（订阅、研究者）和偏好（语言、角色、兴趣、详细程度）
2. 从各研究者获取所有活跃订阅内容
3. 跨订阅去重
4. 选出：**头条**（最高相关性）→ **你的焦点**（匹配兴趣的 3-5 项）→ **发现**（1-2 个跨领域推荐）
5. 保存 Markdown 简报到 `khanote/briefings/{date}.md`

---

### 流程 2：研究会话

对特定主题进行深度研究。创建一个隔离的会话文件夹，包含来源、分析和合成。

**方式 A — 一键全流程：**

```
/khanote.research.pipeline
```

AI 会询问你的主题和来源，然后自动执行：开始 → 摄入 → 分析 → 保存。

**方式 B — 分步执行（精细控制）：**

```
/khanote.research.start              ← 创建会话文件夹
/khanote.research.ingest             ← 添加 URL、PDF 或文本
/khanote.research.analyze            ← 从来源中提取发现
/khanote.research.save               ← 合成并最终保存
```

**会话文件夹结构：**
```
khanote/2026-03-26_AI-Agents-Overview/
    _session.md          ← 元数据和来源列表
    sources/             ← 原始输入（URL、PDF、文本）
    research/            ← 结构化分析笔记
    synthesis/           ← 最终合成输出
    artifacts/           ← 生成的文件
```

---

### 流程 3：订阅管理

订阅是循环的研究查询。每个订阅有一个研究者和一个查询——在每日简报时自动运行。

**添加订阅（对话引导）：**
```
/khanote.feed.add
```
AI 引导你：选择研究者 → 设置查询 → 添加关键词过滤 → 命名 → 保存。

**管理订阅：**
```
/khanote.feed.list                   ← 查看所有订阅及状态
/khanote.feed.pause                  ← 临时暂停一个订阅
/khanote.feed.resume                 ← 恢复已暂停的订阅
/khanote.feed.remove                 ← 永久删除一个订阅
```

或使用终端 CLI：
```bash
khanote feed list
khanote feed add
khanote feed pause ai-papers
khanote feed resume ai-papers
khanote feed remove old-feed
```

---

### 流程 4：连接自定义研究者

已经有想让 khanote 使用的 API？零代码连接：

```
/khanote.researcher.add
```

AI 引导你：描述 API → 设置端点和认证 → 测试连接 → 保存。支持任何 HTTP REST API。

---

### 流程 5：调优发现推荐

每日简报的「发现」栏目展示跨领域内容。通过反馈来调优：

```
/khanote.discover.feedback
```

直接告诉 AI 你的反应：
- "我喜欢那篇 Rust 文章" → 推荐更多类似内容
- "对加密货币不感兴趣" → 减少此类推荐
- "屏蔽八卦新闻" → 永远不显示该领域

或使用 CLI：`khanote discover like "rust"` / `khanote discover dislike "crypto"`

---

### 流程 6：检查配置与排错

```bash
khanote status                       # 概览：工具、订阅、偏好、API key
khanote check                        # 验证配置、工具、研究者
```

`khanote status` 显示：
- 已初始化工具和 vault 路径
- 订阅数量
- 语言、角色、兴趣、详细程度
- API key 状态（已设置 ✓ / 未设置 ✗，脱敏显示）
- 缺失配置的警告

---

### 流程 7：更新技能

```
/khanote.update                      # 在 vibe coding 工具内
```
或：
```bash
khanote update                       # 从终端
```

更新 `.khanote/skills/` 中的源技能文件，并重新分发到所有已初始化的工具。

---

## 终端 CLI 参考

CLI 用于配置管理——研究流程在你的 vibe coding 工具中运行。

| 命令 | 用途 |
|------|------|
| `khanote init` | 在当前目录初始化（5 步向导） |
| `khanote status` | 查看配置状态、订阅、API key |
| `khanote check` | 验证 vault、工具、研究者 |
| `khanote update` | 更新技能到最新版 |
| `khanote feed add` | 添加订阅（引导式） |
| `khanote feed list` | 查看所有订阅 |
| `khanote feed pause <name>` | 暂停订阅 |
| `khanote feed resume <name>` | 恢复订阅 |
| `khanote feed remove <name>` | 删除订阅 |
| `khanote discover like <topic>` | 点赞发现主题 |
| `khanote discover dislike <topic>` | 踩发现主题 |
| `khanote preferences show` | 查看偏好 |

---

## 可用技能（14 个）

在你的 vibe coding 工具中运行（Claude Code、Cursor 等）：

| 技能 | 功能 |
|------|------|
| `/khanote.start-my-day` | 从订阅生成每日简报，或对任意主题即时研究 |
| `/khanote.research.pipeline` | 完整研究流程：开始 → 摄入 → 分析 → 保存 |
| `/khanote.research.start` | 开始新的研究会话（创建日期前缀文件夹） |
| `/khanote.research.ingest` | 向当前会话添加来源（URL、PDF、文本） |
| `/khanote.research.analyze` | 从摄入的来源中提取研究发现 |
| `/khanote.research.save` | 完成并合成研究会话 |
| `/khanote.feed.add` | 添加循环研究订阅（对话引导） |
| `/khanote.feed.list` | 查看所有订阅及状态 |
| `/khanote.feed.pause` | 暂停订阅 |
| `/khanote.feed.resume` | 恢复已暂停的订阅 |
| `/khanote.feed.remove` | 永久删除订阅 |
| `/khanote.discover.feedback` | 对发现栏目内容点赞/踩，调整推荐 |
| `/khanote.researcher.add` | 将新 API 添加为研究者（零代码） |
| `/khanote.update` | 将技能更新到最新版本 |

---

## 内置研究者（10 个）

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
| `local` | 你自己的 vault 文件（.md、.txt、.pdf） | 否 |

`local` 研究者从文件系统读取文件——将它指向一个 vault 目录，即可在每日简报中包含你自己的笔记。在 `config.yaml` 中绑定订阅：

```yaml
feeds:
  my-notes:
    researcher: local
    query: "AI agents"
    source: "./notes/research"
```

通过 `/khanote.researcher.add` 将任意 HTTP REST API 添加为自定义研究者——零代码，全程对话引导。

---

## 多工具支持

在同一目录下为不同工具各初始化一次，所有工具共享同一配置：

| 工具 | 入口文件 | 技能目录 |
|------|---------|---------|
| Claude Code | `CLAUDE.md` | `.claude/commands/` |
| Cursor | `.cursorrules` | `.cursor/rules/` |
| Codex | `AGENTS.md` | `.codex/` |
| Gemini CLI | `GEMINI.md` | `.gemini/` |
| OpenCode | `OPENCODE.md` | `.opencode/` |

```bash
cd ~/my-obsidian-vault
khanote init --tool claude-code
khanote init --tool cursor          # 同一目录，第二个工具
```

---

## 为什么推荐 Obsidian？

我们强烈推荐 **[Obsidian](https://obsidian.md)** 作为你的 vault：

- **图谱视图** — 一眼看到简报、研究会话和主题之间的关联
- **反向链接** — 每个来源、每个发现、每份简报都能回溯到源头
- **全文搜索** — 瞬间搜索所有研究内容
- **每日笔记** — 配合 khanote 的每日简报，打造研究日志
- **插件生态** — dataview、calendar、kanban 等数百个插件
- **本地优先** — 数据在你的电脑上，纯 Markdown 格式
- **个人使用免费**

khanote 生成标准 Markdown，包含 `[[wikilinks]]` 和 YAML frontmatter——专为 Obsidian 的特性设计。任何 Markdown 编辑器都能用，但 Obsidian 能释放全部潜力。

---

## 偏好设置

通过 `khanote init` 或直接编辑 `.khanote/preferences.yaml` 个性化所有输出：

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

## 配置文件

```
your-vault/
    .khanote/
        config.yaml            ← 订阅、研究者、已初始化工具
        preferences.yaml       ← 语言、角色、兴趣、详细程度、语气
        skills/                ← 技能源文件（SSOT）
        context.md             ← 技能上下文模板（可编辑）
    .claude/commands/          ← 分发到 Claude Code 的技能
    CLAUDE.md                  ← Claude Code 入口文件
    khanote/
        briefings/             ← 每日简报保存在此
        sessions/              ← 研究会话保存在此
```

---

## 设计原则

1. **需要 vibe coding 工具** — khanote 为 Claude Code、Cursor 等添加技能，不独立运行 AI
2. **CWD 安装模型** — `cd` 到你的 vault，运行 `khanote init`，一切在当前目录
3. **CLI = 配置，技能 = 智能** — 终端做配置管理，研究在 IDE 内运行
4. **SOP 即技能** — 研究工作流存储在 SKILL.md 文件中，而非存在于记忆里
5. **零代码门槛** — 所有操作通过对话引导完成，初始化后无需 CLI 参数
6. **会话驱动** — 每次研究 = 一个独立的日期前缀文件夹
7. **Obsidian 原生** — Markdown + wikilinks + frontmatter，为 Obsidian 的图谱和搜索优化

---

## 名称由来

**Khan**（来自 AlmostKhan）+ **note** — 汗的笔记 / 征服知识的笔记。

## 状态

积极开发中。14 个技能、10 个内置研究者（含本地文件读取）、订阅管理、金字塔原则输出质量的每日简报、交互式初始化向导、偏好系统和发现栏目均已实现。

## 许可证

TBD
