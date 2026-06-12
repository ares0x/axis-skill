# sanage Axis — 高考志愿 AI 顾问 Skill

> 帮助高考生在 AI 替代浪潮中做出真正能保护未来生存能力的报考决策。
> 融合志愿填报专家四大核心原则 × 张雪峰跨考套利法则 × 十五五产业规划 × 3级严密质量闸门。

本 Skill 已完全重构为符合 **gstack** 规范的 Agentic Skill 架构。AI 智能体（如 Claude Code 或 claude.ai）可以直接读取 `SKILL.md` 的指令，通过对话驱动来调度底层子 Skill、评估工具及腾讯搜狗高考 API。

---

## 🛠️ Repository Directory

- `skills/axis/SKILL.md` — Agent 总入口与触发约束。
- `skills/` — 子 Skill 配置：
  - `profile/SKILL.md` — 信息采集（分数、选科、春考/夏考分流、体检受限、专项意向、志愿优先级、规避专业、8题Holland性格测试）。
  - `analyze/SKILL.md` — 推理分析（三官后台激辩、长培养周期医学 veto、规避专业 veto、体检色盲色弱 veto、张雪峰跨考降维规则比对）。
  - `report/SKILL.md` — 输出格式规范（生成包含平行志愿“服从调剂”预警、取舍优先级与规避专业、以及决策演进的 1+X 报告）。
  - `save/SKILL.md` — 状态快照存档子 Skill。
  - `restore/SKILL.md` — 从特定快照中恢复状态。
  - `list/SKILL.md` — 历史快照与学生会话列表。
- `scripts/` — 底层计算引擎：
  - `sogou_api.py` — 腾讯搜狗高考 API 客户端（拉取省控线及一分一段表）。
  - `gaokao_mapper.py` — 省份归一化与新高考流派科目映射器。
  - `evaluator.py` — 志愿评估引擎（支持 4 梯度“冲稳保垫”推荐、大类分流、体检及周期 veto）。
  - `trait_evaluator.py` — Holland RIASEC 测评转换。
  - `output_generator.py` — 1+X 报告生成器。
- `data/` — 静态专家决策规则及撤销本科专业点数据库。

---

## 🔧 安装方法 (Installation)

由于本项目已包含 `.claude-plugin/marketplace.json` 元数据配置并对子技能目录进行了 `skills/` 重构，支持以下一键安装方式：

### 1. Claude Code 插件式安装

在支持 `claude` 终端命令的客户端下，直接运行以下命令：

```bash
# 从 GitHub 仓库直接作为插件添加（请将 ares0x/axis-skill 替换为你的实际仓库路径）
claude plugin marketplace add ares0x/axis-skill

# 或直接安装特定注册的技能名
claude plugin install axis@axis-skills
```

### 2. 本地集成（推荐开发者使用）

直接克隆本项目到你的开发工作区：

```bash
git clone https://github.com/ares0x/axis-skill.git
```

克隆后在此目录下启动 `claude` 命令行，Claude Code 会通过根目录的 `CLAUDE.md` 与 `SKILL.md` 自动无缝识别并挂载本 Skill 决策引擎。

---

## 🚀 使用方法与命令行菜单 (Command Menu)

你可以直接在终端中交互式运行 `python3 runner.py` 或让 AI 智能体（如 Claude Code 或 claude.ai）通过调用子 Skill 运行以下指令：

| 命令                 | 说明                                                                                                                   | 示例                      |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------- | ------------------------- |
| `/init [uid]`        | 初始化或载入考生 facts 档案                                                                                            | `/init student_jace`      |
| `/set [key] [val]`   | 设置画像数据（含 province, track, score, rank, subjects, body_restriction, willing_special, priority, dislikes, mbti） | `/set province 广东`      |
| `/explore`           | 启动 Holland 霍兰德职业性格与 Gallup 优势测评                                                                          | `/explore`                |
| `/add_major [major]` | 向考生目标专业候选池添加意向专业                                                                                       | `/add_major 智能制造工程` |
| `/status`            | 检查当前考生的画像完整度与省控线对比状态                                                                               | `/status`                 |
| `/veto`              | 运行风险熔断官（查杀身体受限、周期冲突、AI替代及撤销专业）                                                             | `/veto`                   |
| `/audit`             | 运行生存审计官（分析变现周期、家庭经济条件、城市优先权）                                                               | `/audit`                  |
| `/save [title]`      | 保存当前考生状态为快照存档                                                                                             | `/save 初始偏好排查`      |
| `/restore [arg]`     | 从特定快照中恢复考生 facts 与专业池（可传序号或标题）                                                                  | `/restore 1`              |
| `/list`              | 列出当前考生的历史存档快照，以及其他可切换的考生会话                                                                   | `/list`                   |
| `/report`            | 整合多次快照的志愿演进轨迹，编译输出最终 1+X 生存报告                                                                  | `/report`                 |
| `/help`              | 查看命令帮助菜单                                                                                                       | `/help`                   |
| `/exit`              | 退出交互式控制台                                                                                                       | `/exit`                   |

### 💡 `/set` 常用配置项说明

- `score`: 高考文化总分。若已设置 `province`，系统将自动调用搜狗 API 转换为预估位次 `rank`。
- `body_restriction`: 体检受限情况（如 `色弱`、`色盲` 或 `无`）。色盲色弱将硬性 veto 电力网、化工材料、医学等专业。
- `willing_special`: 是否接受定向/专项特殊招生通道（`是` 或 `否`），用于提前批警校/公费师范直通编制匹配。
- `priority`: 志愿三维平衡取舍偏好（`学校优先`、`专业优先` 或 `城市优先`）。
  - `学校优先`：强推**大类招生 (试验班)**与宽口径专业。
  - `专业优先`：强推高壁垒垄断性专业（如电气工程、软件工程），妥协学校与城市层级。
  - `城市优先`：优先契合核心城市群（第一梯队：长三角/珠三角/成渝；第二梯队：京津冀/华中）本地产业链，适当让步学校名气。
- `dislikes`: 考生痛恨/排除的专业词（如 `土木,生化环材`），匹配到的意向专业将一律触发熔断拦截。
- `mbti`: 用户可选择性提供MBTI类型（如 `INTJ`、`ENFP`），用于个性化推荐增强（非必填）。

---

## 🔌 智能体集成指南 (AI Agent Integrations)

### 1. Claude Code

- **自动加载**：由于根目录存在 `CLAUDE.md`，在当前工作空间启动 `claude` 终端命令时，Claude Code 将自动检索并注入项目铁律、知识目录及 Skill 规范。
- **命令行工具绑定**：如果您希望 Claude 直接执行本地计算以保证零幻觉，可以提示 Claude 使用 `python3 runner.py` 作为执行代理。

### 2. Model Context Protocol (MCP) 集成

为了让本决策引擎的 Python 校验工具变成标准的 AI 工具（Tools），配置 `claude_desktop_config.json` 如下：

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

---

## ⚙️ 核心技术特性：本地缓存与配置解耦 (Core Features)

为了解决单点 API 故障及系统可定制性，本项目引入了以下两项架构升级：

### 1. 本地 API 缓存机制 (Local API Caching)

- 搜狗高考 API（如省控线与一分一段位次表）在本地具有缓存保护机制，数据将被存储在隐藏目录 `.cache/` 下。
- 所有 API 查询结果会按照参数升序 URL 编码后进行 MD5 加密，生成确定性的缓存文件名（例如 `control_lines_[md5_hash].json`）。
- **缓存命中**时直接从本地读取 JSON 文件，大幅提升响应速度并避免接口调用超限；**缓存未命中**时则访问网络拉取并刷新本地缓存。
- 缓存写入和读取过程采取静默异常设计，若缓存目录由于权限或只读限制写入失败，系统将平滑穿透继续工作。

### 2. 配置解耦与数据校验 (Decoupled Config & Bounds Verification)

- 专业 AI 替代率及就业稳定性（AI replacement rates & employment stability）已从代码中解耦，统一配置在独立文件 [data/major_rules.json](file:///Users/jace/workspace/Code/Node/Personal/jacejia/axis-skill/data/major_rules.json) 中。
- 在 `MajorEvaluator` 初始化时，系统动态载入此 JSON。如果配置文件缺失、解析异常、或包含非法范围的值（非数字或不在 `[0.0, 1.0]` 范围内），系统将自动采用安全的代码内置备选配置（Fallback）进行覆盖，提高生产环境鲁棒性。

---

## 📊 数据源基础

- 腾讯搜狗高考 API 实时接口（拉取一分一段表及省控制线）。
- 教育部 2026 年最新全国高校撤销/新增本科专业点名单。
- 国家“十五五”战略规划高频受扶持产业关键词。
- 专家功利主义决策逻辑（张雪峰核心7条规则 + 3条分段/赛道补充规则 + 规则优先级机制 + 例外处理机制）。
- 历年高校各专业投档最低分数线与位次数据库。

---

## 🎯 2025.06.12 核心规则优化升级

基于系统分析，本次对专家决策逻辑进行了全面优化升级：

### 📋 规则体系扩展（7条→10条）

| 新增规则                   | 适用场景                 | 核心价值                           |
| -------------------------- | ------------------------ | ---------------------------------- |
| **规则八**：顶尖高校规划流 | 630分+，顶尖985/顶级211  | 学术导向优先，注重保研率和基础学科 |
| **规则九**：生存保底流     | 530分以下，专科/民办本科 | 就业实用性是唯一考量，专升本路径   |
| **规则十**：特殊赛道策略流 | 艺考、体育生、广东春考   | 针对特殊赛道的专项报考策略         |

### 🔄 新增机制

1. **规则优先级机制** - 多规则冲突时明确决策标准
2. **例外处理机制** - 特殊情况（强烈个人意愿、家庭资源、天赋异禀）的弹性处理
3. **地域均衡覆盖** - 从3个集群扩展到3个梯队（第一梯队：长三角/珠三角/成渝；第二梯队：京津冀/华中）

### ✨ 性别友好度优化

- 优化规则七表述，去除性别刻板印象
- 强调个人选择优先于性别假设
