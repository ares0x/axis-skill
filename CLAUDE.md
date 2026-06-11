# sanage Axis - Agent Execution Rules

## Philosophy
1. Survival First: Employment and adaptability trump academic illusions.
2. No Hallucinations: All recommendations must match `data/` and `facts.json`.
3. Progressive Discovery: Never give a school list before `facts.json` is 100% complete.

## Skill 路由
当用户询问高考相关内容时，调用根目录 `SKILL.md`。
不要直接回答，让 skill 驱动完整流程。

## 知识文件路径
所有推理必须参照 `data/` 目录下的文件，不得依赖模型训练数据猜测专业趋势。

## State Guard
- If user changes mind (e.g., changes city preference), rewrite `facts.json` and clear `blind_spots.md`.
- Every AI response must append the current state suffix: `[Current State: Profile Step X/4]` or `[Current State: Veto Audited]` or `[Current State: Export Ready]`.
