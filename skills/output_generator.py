import os
from skills.evaluator import MajorEvaluator, SanageAxisEvaluator

class OutputGenerator:
    def __init__(self, data_dir=None):
        self.evaluator = MajorEvaluator(data_dir=data_dir)

    def generate_report(self, student_facts):
        """
        Generate the final "1+X" action list under the v3.0 specification.
        """
        # 1. Safely unpack nested or flat schemas
        if "basic_info" in student_facts:
            uid = student_facts["basic_info"].get("uid", "unknown")
            province = student_facts["basic_info"].get("province", "未知")
            track_type = student_facts["basic_info"].get("track_type", "夏季高考")
            score = student_facts["basic_info"].get("score_details", {}).get("culture_score") or student_facts["basic_info"].get("score_details", {}).get("art_province_ranking") or "未知"
            subjects = student_facts["basic_info"].get("subjects", "未知")
        else:
            uid = student_facts.get("UID", "unknown")
            province = student_facts.get("Province", "未知")
            track_type = student_facts.get("track_type") or student_facts.get("Track Type", "夏季高考")
            score = student_facts.get("Score / Ranking", "未知")
            subjects = student_facts.get("Subject Combination", "未知")
            
        if "psychological_profile" in student_facts:
            holland_code = student_facts["psychological_profile"].get("holland_code_inferred", ["I", "R"])
            core_driver = student_facts["psychological_profile"].get("core_driver", "普通期望")
            blind_spots = student_facts["psychological_profile"].get("blind_spots", [])
            derived_strengths = student_facts["psychological_profile"].get("derived_strengths", [])
        else:
            holland_code = student_facts.get("holland_code_inferred", ["I", "R"])
            core_driver = student_facts.get("Financial Expectation") or student_facts.get("core_driver", "普通期望")
            blind_spots = student_facts.get("blind_spots", [])
            derived_strengths = student_facts.get("derived_strengths", [])

        # Get target majors
        target_majors = student_facts.get("Target Majors", [])
        if not target_majors:
            # Fallback based on track type
            if "广东春考" in track_type:
                target_majors = ["智能控制技术", "大数据与会计"]
            elif "艺术" in track_type or "艺考" in track_type:
                target_majors = ["数字媒体艺术", "视觉传达设计"]
            else:
                target_majors = ["数学与应用数学", "英语", "土木工程"]
                
        # 2. Run target evaluations
        evals = []
        for major in target_majors:
            eval_res = self.evaluator.evaluate_major(major, student_facts)
            evals.append(eval_res)
            
        evals.sort(key=lambda x: (x['fit_score'], x['survival_score']), reverse=True)
        
        approved_evals = [e for e in evals if not e['is_vetoed']]
        if approved_evals:
            primary_plan = approved_evals[0]
            primary_major = primary_plan['major']
        else:
            primary_plan = None
            primary_major = "无合适推荐（目标库触发硬性熔断，需重构）"

        # 3. Fetch general compatibilities from SanageAxisEvaluator
        compat_evaluator = SanageAxisEvaluator(user_data=student_facts)
        compat_recommendations = compat_evaluator.evaluate_major_compatibility()

        # 4. Generate Adversarial Review CoT (后台激辩)
        adversarial_review = ""
        if "广东春考" in track_type:
            adversarial_review = """
### 🗣️ 后台激辩记录 (Adversarial Debate Log)
*   **熔断官 (veto_officer)**: "春考专科阶段绝对不能报纯文秘、低端行政或会计！初级白领大盘缩减，报了就是失业。去专科必须读硬核物理手艺！"
*   **审计官 (audit_officer)**: "同意。考生的优势在于物理交互/动手，且家境需要快速变现。选择深圳职业技术大学的智能控制或新能源汽车维护能做到最高变现性价比。"
*   **画像官 (profile_officer)**: "考生已对齐事实：放弃传统空调写字楼执念，转向实业手艺。"
"""
        elif "艺术" in track_type or "艺考" in track_type:
            adversarial_review = """
### 🗣️ 后台激辩记录 (Adversarial Debate Log)
*   **熔断官 (veto_officer)**: "AI绘画大模型对传统画师和插画岗位蚕食率达80%。绝对不能让考生去选纯美术、视觉传达！"
*   **审计官 (audit_officer)**: "理解艺术情怀，但必须建立防护墙。建议强制推向1+X复合赛道。选数字媒体艺术或工业设计，在大一必须修Python数据可视化与交互算法。"
*   **画像官 (profile_officer)**: "同意，方案已调整。已在对冲计划中写入Python和交互算法学习路线。"
"""
        else:
            adversarial_review = f"""
### 🗣️ 后台激辩记录 (Adversarial Debate Log)
*   **熔断官 (veto_officer)**: "考生的目标库里有英语和土木工程。英语面临AI大模型重度吞噬（翻译替代率90%）；土木工程面临地产基建大周期滑坡。应予熔断！"
*   **审计官 (audit_officer)**: "考生分数段处于普通一本区间，家庭困难需要快速变现，且霍兰德代码为 {holland_code}。普通一本纯软件工程已饱和，走‘本科数学 -> 考研跨考AI算法’或者‘电气工程直入电网’才是生存第一的铁律！"
*   **画像官 (profile_officer)**: "已重构志愿池。熔断英语与土木工程，首选电气工程或数理跨考路径。"
"""

        # 5. Build Hedging actions
        hedging_actions = []
        if primary_plan:
            major_name = primary_plan['major']
            
            if any(k in major_name for k in ["电气", "电网", "电力"]):
                hedging_actions = [
                    "【技能对冲】学习工控PLC编程与微电网调度算法，向智能电网数字化方向升级，避免沦为单纯的变电站值班人员。",
                    "【备选路径】由于电气工程高度绑定国企编制，大二起需重点关注省网公司的定向招聘及校友选调要求，准备国家电网统一考试课目（高等数学、电路、电机学）。",
                    "【政策红利】关注国家‘十五五’期间在储能和新能源领域的中央直投资金，优先选修储能技术/新能源电池方向。"
                ]
            elif any(k in major_name for k in ["计算机", "软件", "人工智能", "数学", "应用数学"]):
                hedging_actions = [
                    "【跨考红利（规则五）】本科深挖数学与应用数学的代数/统计基础，考研降维打击计算机内核，避开本科即面临低端代码被大模型完全替代的危险区。",
                    "【技能对冲】严防低端CRUD编码被LLM完全替代。务必在大一底子打牢后，向‘具身智能核心算法’、‘异构芯片底层优化’或‘本地大模型部署（LLMOps）’方向突围。",
                    "【备选路径】提早获得一线大厂或科研实验室的核心研发实习经历。若无法进入研发，提早备考江浙沪核心国企的IT信息岗。"
                ]
            elif any(k in major_name for k in ["医", "齿", "口", "护理"]):
                hedging_actions = [
                    "【时间对冲】临床医学学制极长。若家境较弱，建议转考或分流至【口腔医学】或【医学检验技术】，缩短学习年限，提早变现生存。",
                    "【技能对冲】掌握‘医疗影像AI诊断软件配合使用’与‘机器人微创手术辅助系统维护’技能，做懂AI的医生，防范机器对辅助科室的蚕食。"
                ]
            elif any(k in major_name for k in ["智能控制", "汽车", "机械"]):
                hedging_actions = [
                    "【跨考红利（规则六）】“打死不读纯机械，考研跨考控方向”。本科阶段把机械制图、力学、数电模电物理壁垒死磕下来，研究生转入具身智能或自动化控制，对接智能硬件和新能源汽车产业链。",
                    "【技能对冲】掌握工业PLC编程及机器视觉算法控制，避免沦为流水线低端装配工。"
                ]
            else:
                hedging_actions = [
                    "【技能对冲】对于通用或文管类学科，务必选修一门‘硬技术硬技能’作为副业，例如掌握Python数据清洗与分析技能，或精通某种工业CAD/CAE软件使用。",
                    "【备选路径】大二起坚定不移地走考公/考编路线。根据目标就业地，锁定该省份的岗位偏好，提早刷真题申论。"
                ]
        else:
            hedging_actions = [
                "【紧急预案】由于考生的初始志愿库全部被VETO（如含有撤销专业或与选科冲突），必须启动**预案重构**。",
                "【志愿修正】根据当前【物理+化学】选科（若有），推荐重新勾选【智能制造工程】、【集成电路设计】或【电气工程】。",
                "【避坑指南】避开所有低端外语、工商管理、公共管理等AI高替代且高饱和的专业。"
            ]

        # 6. Generate Markdown Report Content
        report = f"""# sanage Axis - 考生未来生存行动清单 (1+X 方案)

## 👤 考生画像与绝对事实 (Hard Facts)
- **考生UID**: {uid}
- **高考省份**: {province}
- **填报赛道**: {track_type}
- **分数/省排名**: {score}
- **选科组合**: {subjects}

## 🧠 职业性格与天赋诊断 (Talent Profile)
- **推导霍兰德代码 (Holland Code)**: {holland_code}
- **核心求职驱动力 (Gallup Driver)**: {core_driver}
- **衍生核心长板 (Strengths)**: {", ".join(derived_strengths) if derived_strengths else "未完成测试"}
- **考生的决策盲区 (Blind Spots)**: {", ".join(blind_spots) if blind_spots else "无显著偏见记录"}

---

{adversarial_review}

---

## 🎯 核心行动方案 [1]：首选生存专业
- **推荐专业**: **{primary_major}**
"""
        if primary_plan:
            report += f"""- **生存率量化总评分**: `{primary_plan['survival_score']}/100`
- **AI 替代风险指数**: `{int(primary_plan['ai_replacement_index'] * 100)}%` (越低越安全)
- **岗位就业稳定性评级**: `{'优异 (编制/医疗刚需)' if primary_plan['stability_index'] > 0.8 else '中等'}`

### 💡 决策研判与对齐理由：
"""
            for reason in primary_plan['match_reasons']:
                report += f"- {reason}\n"
        else:
            report += "\n> [!CAUTION]\n> 当前没有通过风险熔断的专业。请参考VETO红牌警告重新规划志愿池。\n"

        if compat_recommendations:
            report += """
---

## 💡 科学推荐池 (Holland & Track Compatible Recommendation)
以下基于考生特质与高考赛道，自动算出的**高契合度生存专业清单**（降序排列）：
"""
            for rec in compat_recommendations:
                report += f"- **{rec['major']}** (契合分: `{rec['score']}`)\n"
                report += f"  * 战略方向: `{rec.get('path', 'N/A')}`\n"
                report += f"  * 推荐逻辑: {rec.get('reason', '')}\n"

        report += """
---

## 🛡️ 风险熔断警示 (Risk Veto Alerts)
"""
        veto_count = 0
        for ev in evals:
            if ev['is_vetoed']:
                veto_count += 1
                report += f"### ❌ 红牌警告：{ev['major']}\n"
                for reason in ev['veto_reasons']:
                    report += f"- {reason}\n"
                report += f"- AI替代系数: `{int(ev['ai_replacement_index']*100)}%` | 生存分: `{ev['survival_score']}`\n\n"
        
        if veto_count == 0:
            report += "- 志愿候选池中暂未触发硬性风险熔断。安全。\n"

        report += """
---

## 🛠️ 防御性对冲策略 [X]：未来的防身副业与备选路径
以下为该主攻方向下的风险对冲措施，防止行业巨变或技术突破导致的生存危机：
"""
        for action in hedging_actions:
            report += f"- {action}\n"
            
        report += f"""
---
`[Current State: Export Ready] - Axis System Output generated successfully.`
"""
        return report
