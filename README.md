# sanage Axis — 高考志愿 AI 顾问 Skill

> 帮助高考生在 AI 替代浪潮中做出真正能保护未来生存能力的报考决策。
> 融合张雪峰流派七条决策规则 × 十五五产业规划 × Holland 职业测评。

本 Skill 已完全重构为符合 **gstack** 规范的 Agentic Skill 架构。现在，AI 智能体（如 Claude Code 或 claude.ai）可以直接读取 `SKILL.md` 的指令，通过对话驱动来调度底层子 Skill 与评估工具。

---

## 🛠️ Repository Directory

- `SKILL.md` — Agent 总入口与触发约束。
- `skills/` — 子 Skill 配置：
  - `profile/SKILL.md` — 信息采集（分数、选科、春考/夏考分流、8题Holland性格测试）。
  - `analyze/SKILL.md` — 推理分析（三官激辩后台对抗 review、张雪峰跨考降维规则比对）。
  - `report/SKILL.md` — 输出格式规范（生成包含志愿演进的 1+X 报告）。
  - `save/SKILL.md` — [NEW] 状态存档子 Skill。
  - `restore/SKILL.md` — [NEW] 状态接续子 Skill。
  - `list/SKILL.md` — [NEW] 历史快照与学生会话列表子 Skill。
- `scripts/` — 底层工具包（`evaluator.py`, `injector.py`, `trait_evaluator.py`, `output_generator.py`）。
- `data/` — 专家决策规则与投档线库。

---

## 🔧 安装方法 (Installation Methods)

由于本项目已包含 `.claude-plugin/marketplace.json` 元数据配置并对子技能目录进行了 `skills/` 重构，支持以下一键安装方式：

### 1. Claude Code 插件式安装
在支持 `claude` 终端命令的客户端下，直接运行以下命令：
```bash
# 从 GitHub 仓库直接作为插件添加（请将 ares0x/axis-skill 替换为你的实际仓库路径）
claude plugin marketplace add ares0x/axis-skill

# 或直接安装特定注册的技能名
claude plugin install axis@axis-skills
```

### 2. 通用全局安装（适用于 Codex / Claude Code 等）
通过 `skills` 技能管理器进行全局添加：
```bash
npx -y skills add ares0x/axis-skill -g --all
```

### 3. 本地集成（推荐开发者使用）
直接克隆本项目到你的开发工作区：
```bash
git clone https://github.com/ares0x/axis-skill.git
```
克隆后在此目录下启动 `claude` 命令行，Claude Code 会通过根目录的 `CLAUDE.md` 与 `SKILL.md` 自动无缝识别并挂载本 Skill 决策引擎。

---

## 🚀 使用方法与命令行菜单 (Command Menu)

本 Skill 配套了确定性的 Python 计算引擎。你可以直接在终端中交互式运行 `python3 runner.py` 或让 AI 智能体（如 Claude Code 或 claude.ai）通过调用子 Skill 运行以下指令：

| 命令 | 说明 | 示例 |
|---|---|---|
| `/init [uid]` | 初始化或载入考生 facts 档案 | `/init student_jace` |
| `/set [key] [val]` | 设置画像数据（province, track, score, art_rank, subjects） | `/set province 广东` |
| `/explore` | 启动 Holland 霍兰德职业性格与 Gallup 优势测评 | `/explore` |
| `/add_major [major]` | 向考生目标专业候选池添加意向专业 | `/add_major 智能控制技术` |
| `/status` | 检查当前考生的画像完整度与省控线对比状态 | `/status` |
| `/veto` | 运行风险熔断官（查杀 AI 替代率及教育部撤销名单） | `/veto` |
| `/audit` | 运行生存审计官（分析变现周期、家庭经济条件、城市优先权） | `/audit` |
| `/save [title]` | [NEW] 保存当前考生状态为快照存档 | `/save 初始偏好排查` |
| `/restore [arg]` | [NEW] 从特定快照中恢复考生 facts 与专业池（可传序号或标题） | `/restore 1` |
| `/list` | [NEW] 列出当前考生的历史存档快照，以及其他可切换的考生会话 | `/list` |
| `/report` | [NEW] 整合多次快照的志愿演进轨迹，编译输出最终 1+X 生存报告 | `/report` |
| `/help` | 查看命令帮助菜单 | `/help` |
| `/exit` | 退出交互式控制台 | `/exit` |

### 智能体运行链路

AI 智能体检测到报考、高考、选专业等关键词时会自动激活该 Skill，或由用户直接输入命令运行。智能体将通过以下调用链进行计算与输出：
`/axis` (入口) $\rightarrow$ `/profile` (信息采集) $\rightarrow$ `/analyze` (激辩与推理) $\rightarrow$ `/save` (存档备忘) $\rightarrow$ `/report` (编译输出包含决策演进的 1+X 报告)

---

---

## 🔌 智能体集成指南 (AI Agent Integrations)

为了在各种主流 AI 助手产品中最大化发挥本 Skill 的效能，请按照以下指南进行配置加载：

### 1. Claude Code
- **自动加载**：由于根目录存在 [CLAUDE.md](file:///Users/jace/workspace/Code/Node/Personal/jacejia/axis-skill/CLAUDE.md)，在当前工作空间启动 `claude` 终端命令时，Claude Code 将自动检索并注入项目铁律、知识目录及 Skill 规范。
- **命令行工具绑定**：如果您希望 Claude 直接执行本地计算以保证零幻觉，可以提示 Claude 使用 `python3 runner.py` 作为执行代理。

### 2. Cursor / Codex
- **.cursorrules 全局规则**：
  您可以直接在项目根目录下创建一个 `.cursorrules` 文件，或在 Cursor Settings -> Rules for AI 中将根目录 [CLAUDE.md](file:///Users/jace/workspace/Code/Node/Personal/jacejia/axis-skill/CLAUDE.md) 和 [SKILL.md](file:///Users/jace/workspace/Code/Node/Personal/jacejia/axis-skill/SKILL.md) 的核心提示词内容进行绑定。
- **Agent 模式提示词**：
  使用 Cursor 的 Composer 模式（Agent 模式）时，引导其：
  > “读取 `SKILL.md`，使用 `python3 runner.py` 进行硬性数据校验，为当前会话状态进行排查。”

### 3. Model Context Protocol (MCP) 集成
为了让本决策引擎的 Python 校验工具变成标准的 AI 工具（Tools），我们可以利用 MCP 进行绑定：
- 在 Claude Desktop 配置文件 `claude_desktop_config.json` 中添加以下配置项以加载本地 Python 运行工具：
```json
{
  "mcpServers": {
    "sanage-axis-analyzer": {
      "command": "python3",
      "args": ["/absolute/path/to/runner.py", "--test-mode"]
    }
  }
}
```
*注：可基于 MCP SDK 封装 `runner.py` 提供的接口，使其支持更丰富的实时动态交互。*

---

## 📊 数据源基础

- 教育部 2026 年最新全国高校撤销/新增本科专业点名单。
- 国家“十五五”战略规划高频受扶持产业关键词。
- 广东省教育考试院春考（依学考/高职单招）与艺考（美术设计）综合分换算及投档规则。
- 专家功利主义决策逻辑（张雪峰考研跨考与降维套利法则）。
- 历年高校投档最低分数线与位次数据库。

