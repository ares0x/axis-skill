---
name: report
description: 高考志愿最终生存报告输出。生成结构化 1+X 方案报告，支持用户追问。
---

# Report — 输出报告协议

当 `/analyze` 推理分析阶段完成，调用此 subskill 生成最终的 Markdown 报告。

## 报告结构规范

### 1. 👤 考生画像与绝对事实 (Hard Facts)
- **考生UID**: `{uid}`
- **高考省份**: `{province}`
- **填报赛道**: `{track_type}`
- **分数/省排名**: `{score}` (若有位次，同时列出)
- **选科组合**: `{subjects}`

### 2. 🧠 职业性格与天赋诊断 (Talent Profile)
- **推导霍兰德代码 (Holland Code)**: `[A, B]` (列出前两位)
- **核心求职驱动力 (Gallup Driver)**: `壁垒优先 / 高风险高回报 / 环境优先`
- **衍生核心长板 (Strengths)**: `[长板列表]`
- **考生的决策盲区 (Blind Spots)**: `[盲区描述]`

### 3. 🗣️ 后台激辩记录 (Adversarial Debate Log)
展示在推理分析中，熔断官与审计官就考生意向专业产生的交锋细节。

### 4. 📈 志愿偏好与决策演进过程 (Counseling Preference Evolution)
根据多次评估存档快照（由 `/save` 产生），追溯展示考生从最初填报偏好到最终免疫避坑志愿的动态心路历程与决策变化。

### 5. 🎯 核心行动方案 [1]：首选生存专业
- **推荐专业**: **`{major_name}`**
- **生存率量化总评分**: `{survival_score}/100` (由 scripts/evaluator.py 计算)
- **AI 替代风险指数**: `{ai_replacement_index}%`
- **岗位就业稳定性评级**: `优异 (编制/医疗刚需) / 中等 / 较低`
- **对齐理由与决策研判**: 列出对齐的专家规则逻辑。

### 6. 💡 科学推荐池 (Holland & Track Compatible Recommendation)
列出 2-3 个其他符合 Holland 人格和赛道的备选专业，按契合分降序排列，包含其战略跨考路线和推荐逻辑。

### 7. 🛡️ 风险熔断警示 (Risk Veto Alerts)
列出被 VETO 否决的所有意向专业，并明确指明否决理由（如教育部撤销、高AI替代率、选科不符）。

### 8. 🛠️ 防御性对冲策略 [X]：未来的防身副业与备选路径
为考生制定具体的对冲动作：
- 必修的软硬件/工具包（如：PLC、Python、交互软件等）
- 备选的出路和考公/考编考证时间线
- 十五五政策红利补贴如何利用

---
`[Current State: Export Ready] - Axis System Output generated successfully.`
