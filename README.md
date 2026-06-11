# sanage Axis — 高考志愿 AI 顾问 Skill

> 帮助高考生在 AI 替代浪潮中做出真正能保护未来生存能力的报考决策。
> 融合张雪峰流派七条决策规则 × 十五五产业规划 × Holland 职业测评。

本 Skill 已完全重构为符合 **gstack** 规范的 Agentic Skill 架构。现在，AI 智能体（如 Claude Code 或 claude.ai）可以直接读取 `SKILL.md` 的指令，通过对话驱动来调度底层子 Skill 与评估工具。

---

## 🛠️ Repository Directory

- `SKILL.md` — Agent 总入口与触发约束。
- `.agents/skills/` — 子 Skill 配置：
  - `profile/SKILL.md` — 信息采集（分数、选科、春考/夏考分流、8题Holland性格测试）。
  - `analyze/SKILL.md` — 推理分析（三官激辩后台对抗 review、张雪峰跨考降维规则比对）。
  - `report/SKILL.md` — 输出格式规范（生成 1+X 报告）。
- `scripts/` — 底层工具包（`evaluator.py`, `injector.py`, `trait_evaluator.py`, `output_generator.py`）。
- `data/` — 专家决策规则与投档线库（新增 `score_lines_2024_2025.csv`）。

---

## 🚀 使用方法（Claude Code / claude.ai）

AI 智能体检测到报考、高考、选专业等关键词时会自动激活该 Skill，或由用户直接输入命令运行：

```bash
# 激活本顾问
/axis
```

然后，直接发送您的请求开始：
> 「我今年高考 560 分，广东，物化生，帮我分析一下专业选择」

智能体将通过以下调用链进行计算与输出：
`/axis` (入口) $\rightarrow$ `/profile` (信息采集) $\rightarrow$ `/analyze` (激辩与推理) $\rightarrow$ `/report` (输出 1+X 方案报告)

---

## 📊 数据源基础

- 教育部 2026 年最新全国高校撤销/新增本科专业点名单。
- 国家“十五五”战略规划高频受扶持产业关键词。
- 广东省教育考试院春考（依学考/高职单招）与艺考（美术设计）综合分换算及投档规则。
- 专家功利主义决策逻辑（张雪峰考研跨考与降维套利法则）。
- 历年高校投档最低分数线与位次数据库。
