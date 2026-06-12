import os
import json
from datetime import datetime
from scripts.evaluator import MajorEvaluator, SanageAxisEvaluator
from scripts.gaokao_mapper import normalize_province

PROVINCE_EXAM_AUTHORITIES = {
    "北京": ("北京教育考试院", "https://www.bjeea.cn/"),
    "天津": ("天津市教育招生考试院", "http://www.zhaokao.net/"),
    "上海": ("上海市教育考试院", "https://www.shmeea.edu.cn/"),
    "重庆": ("重庆市教育考试院", "https://www.cqksy.cn/"),
    "河北": ("河北省教育考试院", "http://www.hebeea.edu.cn/"),
    "山西": ("山西招生考试网", "http://www.sxkszx.cn/"),
    "辽宁": ("辽宁省招生考试之窗", "https://www.lnzsks.com/"),
    "吉林": ("吉林省教育考试院", "http://www.jleea.com.cn/"),
    "黑龙江": ("黑龙江省招生考试信息港", "https://www.lzk.hl.cn/"),
    "江苏": ("江苏省教育考试院", "https://www.jseea.cn/"),
    "浙江": ("浙江省教育考试院", "https://www.zjzs.net/"),
    "安徽": ("安徽省教育招生考试院", "https://www.ahzsks.cn/"),
    "福建": ("福建省教育考试院", "https://www.eeafj.cn/"),
    "江西": ("江西省教育考试院", "http://www.jxeea.cn/"),
    "山东": ("山东省教育招生考试院", "https://www.sdzk.cn/"),
    "河南": ("河南省教育考试院", "http://www.haeea.cn/"),
    "湖北": ("湖北省教育考试院", "http://www.hbea.edu.cn/"),
    "湖南": ("湖南省教育考试院", "https://www.hneao.edu.cn/"),
    "广东": ("广东省教育考试院", "https://eea.gd.gov.cn/"),
    "广西": ("广西招生考试院", "https://www.gxeea.cn/"),
    "海南": ("海南省考试局", "http://ea.hainan.gov.cn/"),
    "四川": ("四川省教育考试院", "https://www.sceea.cn/"),
    "贵州": ("贵州省招生考试院", "http://zsksy.guizhou.gov.cn/"),
    "云南": ("云南省招生考试院", "https://www.ynzs.cn/"),
    "陕西": ("陕西省教育考试院", "http://www.sneac.com/"),
    "甘肃": ("甘肃省教育考试院", "https://www.ganseea.cn/"),
    "青海": ("青海省教育考试网", "http://www.qhjyks.com/"),
    "宁夏": ("宁夏教育考试院", "https://www.nxjyks.cn/"),
    "新疆": ("新疆招生网", "http://www.xjzk.gov.cn/"),
    "内蒙古": ("内蒙古自治区教育招生考试中心", "https://www.nm.zsks.cn/"),
    "西藏": ("西藏自治区教育考试院", "http://zsks.edu.xizang.gov.cn/")
}

def parse_markdown_with_frontmatter(content):
    frontmatter = {}
    body = ""
    lines = content.splitlines()
    if len(lines) > 0 and lines[0].strip() == "---":
        yaml_lines = []
        body_lines = []
        in_yaml = True
        for line in lines[1:]:
            if in_yaml:
                if line.strip() == "---":
                    in_yaml = False
                else:
                    yaml_lines.append(line)
            else:
                body_lines.append(line)
        body = "\n".join(body_lines)

        # Simple key-value parser
        for line in yaml_lines:
            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip()
                if (val.startswith("[") and val.endswith("]")) or (val.startswith("['") and val.endswith("']")) or (val.startswith('["') and val.endswith('"]')):
                    import ast
                    try:
                        val = ast.literal_eval(val)
                    except:
                        val = [item.strip().strip("'\"") for item in val[1:-1].split(",") if item.strip()]
                elif val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
                elif val.startswith("'") and val.endswith("'"):
                    val = val[1:-1]
                elif val.isdigit():
                    val = int(val)
                frontmatter[key] = val
    else:
        body = content
    return frontmatter, body

class OutputGenerator:
    def __init__(self, data_dir=None):
        self.evaluator = MajorEvaluator(data_dir=data_dir)

    def generate_report(self, student_facts, snapshots_dir=None):
        """
        Generate the final "1+X" action list under the v3.0 specification,
        incorporating cumulative history if snapshots exist.
        """
        # 1. Parse evolution section from snapshots
        evolution_section = ""
        if snapshots_dir and os.path.exists(snapshots_dir):
            snapshot_files = sorted([f for f in os.listdir(snapshots_dir) if f.endswith('.md')])
            if len(snapshot_files) >= 1:
                evolution_section = "\n## 📈 志愿偏好与决策演进过程 (Counseling Preference Evolution)\n\n"
                evolution_section += "在咨询评估过程中，考生的报考志愿经历以下调整：\n\n"

                for idx, filename in enumerate(snapshot_files, 1):
                    filepath = os.path.join(snapshots_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as sf:
                        content = sf.read()
                    fm, body = parse_markdown_with_frontmatter(content)
                    title = fm.get("title", filename)
                    timestamp = filename[:15]
                    if len(timestamp) == 15 and timestamp[8] == '-':
                        formatted_ts = f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]} {timestamp[9:11]}:{timestamp[11:13]}"
                    else:
                        formatted_ts = timestamp

                    # Parse target majors
                    target_majors = []
                    in_targets = False
                    for line in body.splitlines():
                        line_strip = line.strip()
                        if line_strip.startswith("## 目标专业候选池"):
                            in_targets = True
                            continue
                        elif line_strip.startswith("##"):
                            in_targets = False
                        if in_targets:
                            if line_strip.startswith("-"):
                                major = line_strip[1:].strip()
                                if major and major != "（暂无）":
                                    target_majors.append(major)

                    majors_str = "、".join(target_majors) if target_majors else "无"
                    evolution_section += f"- **阶段 {idx} ({formatted_ts})** · *{title}*  \n"
                    evolution_section += f"  - 目标专业候选池: `{majors_str}`  \n"
                    evolution_section += f"  - 状态阶段: `{fm.get('stage', '未标记')}`\n"

                evolution_section += "\n---\n"

        # 2. Safely unpack nested or flat schemas
        if "basic_info" in student_facts:
            uid = student_facts["basic_info"].get("uid", "unknown")
            province = student_facts["basic_info"].get("province", "未知")
            track_type = student_facts["basic_info"].get("track_type", "夏季高考")
            score = student_facts["basic_info"].get("score_details", {}).get("culture_score") or "未知"
            rank = student_facts["basic_info"].get("score_details", {}).get("rank") or "未知"
            art_province_ranking = student_facts["basic_info"].get("score_details", {}).get("art_province_ranking") or "未知"
            subjects = student_facts["basic_info"].get("subjects", "未知")
            body_restriction = student_facts["basic_info"].get("body_restriction", "无")
            willing_special = student_facts["basic_info"].get("willing_special", "否")
            priority_choice = student_facts["basic_info"].get("priority_choice", "未定")
            dislikes = student_facts["basic_info"].get("dislikes", [])
        else:
            uid = student_facts.get("UID", "unknown")
            province = student_facts.get("Province", "未知")
            track_type = student_facts.get("track_type") or student_facts.get("Track Type", "夏季高考")
            score = student_facts.get("Score / Ranking", "未知")
            rank = student_facts.get("rank") or "未知"
            art_province_ranking = student_facts.get("art_province_ranking") or "未知"
            subjects = student_facts.get("Subject Combination", "未知")
            body_restriction = student_facts.get("body_restriction", "无")
            willing_special = student_facts.get("willing_special", "否")
            priority_choice = student_facts.get("priority_choice", "未定")
            dislikes = student_facts.get("dislikes", [])

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

        # Get batch lines status
        batch_line_status = self.evaluator.get_batch_lines_status(student_facts)

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
        adversarial_review = self._build_adversarial_review(track_type, target_majors, evals, holland_code)

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

        # 6. Lookup Province Exam Authority
        norm_prov = normalize_province(province)
        authority_name, authority_url = PROVINCE_EXAM_AUTHORITIES.get(
            norm_prov, ("阳光高考", "https://gaokao.chsi.com.cn/")
        )

        # 7. Generate Disclaimer Block
        disclaimer_block = f"""> 🚨 **【AI 辅助说明与免责声明】**
> 本报告内容均由 AI 辅助生成，仅供参考，不构成任何填报、录取或决策的承诺与建议。最终决定请你和家人结合官方信息综合判断。
> 录取位次、招生计划等核心数据具有时效性与大小年波动风险，具体填报事项请前往 **[{authority_name}]({authority_url})** 查看和操作。
>
> ⚠️ **【平行志愿投档重要安全预警】**
> **志愿填报必须勾选“服从专业调剂”**！平行志愿实行一次投档，若考生的档案投进某高校后，因分数不够所报专业且不服从调剂，高校将直接做退档处理。一旦退档，在本批次平行志愿中将不再有二次投档机会，直接滑档至征集志愿或下一批次。
"""

        # Fetch 冲稳保 suggestions dynamically
        rank_rec = self.evaluator.get_recommendations_by_rank(province, rank)

        # Build 冲稳保垫 block
        rank_rec_block = ""
        if rank_rec.get("冲") or rank_rec.get("稳") or rank_rec.get("保") or rank_rec.get("垫"):
            rank_rec_block += "\n---\n\n## 🎯 动态位次志愿推荐 (冲稳保垫建议 - Heuristics Based on Live Rank)\n"
            rank_rec_block += "根据您当前的高考位次，从 benchmark 数据库中筛选的推荐组合如下：\n\n"

            if rank_rec.get("冲"):
                rank_rec_block += "### 🚀 冲刺学校 (Stretch Goals - 录取概率较小，适合冲击名校)\n"
                for item in rank_rec["冲"]:
                    rank_rec_block += f"- {item}\n"
            if rank_rec.get("稳"):
                rank_rec_block += "### ⚖️ 稳健学校 (Target Goals - 录取概率较大，建议重点关注)\n"
                for item in rank_rec["稳"]:
                    rank_rec_block += f"- {item}\n"
            if rank_rec.get("保"):
                rank_rec_block += "### 🛡️ 保底学校 (Safe Goals - 录取概率极高，防止滑档)\n"
                for item in rank_rec["保"]:
                    rank_rec_block += f"- {item}\n"
            if rank_rec.get("垫"):
                rank_rec_block += "### ⚓ 垫底学校 (Anchor Goals - 绝对安全志愿，用于极端兜底)\n"
                for item in rank_rec["垫"]:
                    rank_rec_block += f"- {item}\n"
        else:
            rank_rec_block += "\n---\n\n## 🎯 动态位次志愿推荐 (冲稳保垫建议)\n"
            rank_rec_block += "⚠️ 警告：当前本地数据库中未收录该省份足够的录取最低位次数据。\n"
            rank_rec_block += f"请您务必手动对照官方《高考志愿填报指南》中各高校往年的录取最低位次，与您的当前位次（{rank}）进行比对：\n"
            rank_rec_block += f"- **冲**：往年录取最低位次在您位次的 80%~95% 区间（即您位次前 5%-20% 的学校）\n"
            rank_rec_block += f"- **稳**：往年录取最低位次在您位次的 95%~120% 区间（即您位次左右的学校）\n"
            rank_rec_block += f"- **保**：往年录取最低位次在您位次的 120%~145% 区间\n"
            rank_rec_block += f"- **垫**：往年录取最低位次大于您位次的 145%（兜底保障线）\n"

        # Build special paths suggestions
        special_paths_block = ""
        is_quick_income = (
            "变现" in core_driver or "即就业" in core_driver or "尽快" in core_driver or "壁垒" in core_driver or
            "尽快有稳定收入" in str(student_facts) or "尽快变现" in str(student_facts)
        )
        if willing_special in ["是", "y", "yes", "true", True] and is_quick_income:
            special_paths_block += "\n---\n\n## 💡 特殊政策与提前批绿色通道 (Special Policy Channels)\n"
            special_paths_block += "由于您有快速稳定变现的诉求，且愿意接受定向/专项计划，特为您匹配以下招生通道：\n\n"
            special_paths_block += "1. **提前批公安警校**：建议重点关注省属警校（如广东警官学院等）的提前批公安类专业。毕业参加公安联考入警率超90%，4年本科毕业直接入警带编制。\n"
            special_paths_block += "2. **公费定向师范生**：毕业直接回生源地带编任教，大学四年免学费且发生活补助，毕业即解决编制，最快4年变现。\n"
            special_paths_block += "3. **农村卫生专项计划**：免费学医，5年毕业后定向基层医院带编安置，省去考公和长期规培读博的时间消耗。\n"
            special_paths_block += "4. **电网/铁路订单班**：若匹配相关专科或工科，关注学校与南方电网、国家电网或铁路局的合作培养项目，毕业直通校招渠道。\n"

        # 8. Generate Markdown Report Content
        report = f"""# sanage Axis - 考生未来生存行动清单 (1+X 方案)

{disclaimer_block}

## 👤 考生画像与绝对事实 (Hard Facts)
- **考生UID**: {uid}
- **高考省份**: {province}
- **填报赛道**: {track_type}
- **分数/位次**: 文化分: {score} | 预估位次: {rank} | 艺术省排名: {art_province_ranking}
- **选科组合**: {subjects}
- **体检受限**: {body_restriction}
- **接受定向/专项计划**: {willing_special}
- **志愿取舍偏好**: {priority_choice}
- **意向规避/排斥专业**: {", ".join(dislikes) if dislikes else "无"}
- **省控批次线对比**: {batch_line_status}

## 🧠 职业性格与天赋诊断 (Talent Profile)
- **推导霍兰德代码 (Holland Code)**: {holland_code}
- **核心求职驱动力 (Gallup Driver)**: {core_driver}
- **衍生核心长板 (Strengths)**: {", ".join(derived_strengths) if derived_strengths else "未完成测试"}
- **考生的决策盲区 (Blind Spots)**: {", ".join(blind_spots) if blind_spots else "无显著偏见记录"}

---

{adversarial_review}

---
"""
        if evolution_section:
            report += evolution_section

        report += f"""
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

        if rank_rec_block:
            report += rank_rec_block

        if special_paths_block:
            report += special_paths_block

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

        # 9. Append Dynamic Data Sources Table
        report += f"""
---

## 📅 数据来源与时效声明 (Data Sources & Validity)

- **高考批次省控制线**: [{authority_name}]({authority_url}) / 在线公开高考数据库 · 采集年份：2024-2025 · 采集于 {datetime.now().strftime('%Y-%m-%d')}
- **一分一段位次表**: [{authority_name}]({authority_url}) / 在线公开一分一段数据库 · 采集年份：2024-2025 · 采集于 {datetime.now().strftime('%Y-%m-%d')}
- **战略新增专业与撤销专业名单**: 中华人民共和国教育部官方公开数据 · 采集年份：2026 · 采集于 {datetime.now().strftime('%Y-%m')}

---

*💡 本报告由 **[sanage Axis](https://github.com/ares0x/axis-skill)** 高考志愿 AI 顾问（开发者：**Jace**）辅助生成。*
*如有疑问或需获取最新志愿填报规则，欢迎关注：**Sanage Lab** (抖音/小红书)。*

`[Current State: Export Ready] - Axis System Output generated successfully.`
"""
        # Sanitize report content for promise words
        prohibited_replacements = {
            "保证录取": "录取概率较大",
            "一定能录": "录取概率较大",
            "100%录取": "录取概率极高",
            "法律效力": "效力参考"
        }
        for bad, good in prohibited_replacements.items():
            report = report.replace(bad, good)

        return report

    def _build_adversarial_review(self, track_type, target_majors, evals, holland_code):
        """
        根据考生实际情况生成三官激辩，不再是固定字符串。
        """
        vetoed = [e for e in evals if e['is_vetoed']]
        high_risk = [e for e in evals if e['ai_replacement_index'] >= 0.7 and not e['is_vetoed']]

        veto_list = "、".join([e['major'] for e in vetoed]) or "无"
        risk_list = "`、`".join([e['major'] for e in high_risk]) or "无"
        all_majors = "、".join(target_majors)

        # Build dynamic dialogue based on track type
        if "广东春考" in track_type:
            return f"""
### 🗣️ 后台激辩记录 (Adversarial Debate Log)
- **熔断官 (veto_officer)**：「针对广东春考赛道专科，意向专业为【{all_majors}】。
  其中【{veto_list}】触发硬性熔断——春考专科阶段绝对不能报纯白领流水线岗位，AI替代率高且招聘大盘趋近归零！」
- **生存审计官 (audit_officer)**：「同意熔断官意见。考生需要快速变现，且霍兰德代码为 {holland_code}，应全面转向大湾区实体手艺产业专科，如智能控制或新能源汽车维护。」
- **用户画像官 (profile_officer)**：「已重构志愿。熔断高危专科，转向实业手艺专业。」
"""
        elif "艺术" in track_type or "艺考" in track_type:
            return f"""
### 🗣️ 后台激辩记录 (Adversarial Debate Log)
- **熔断官 (veto_officer)**：「设计类艺考意向专业为【{all_majors}】。
  AI绘画对传统原画/插画的蚕食率已达80%，普通视觉传达和美术专业存在高AI替代风险。」
- **生存审计官 (audit_officer)**：「理解艺术偏好，但必须增加防线。对于【{risk_list}】建议推向1+X复合赛道（如数字媒体艺术或工业设计），大学第一年必须选修交互算法和可视化工具。」
- **用户画像官 (profile_officer)**：「同意，X对冲策略已在报告后部列出，已注入Python和交互课程对冲路线。」
"""
        else:
            reason_str = vetoed[0]['veto_reasons'][0] if vetoed else '暂无强制熔断项'
            return f"""
### 🗣️ 后台激辩记录 (Adversarial Debate Log)
- **熔断官 (veto_officer)**：「高考统招考生，意向专业为【{all_majors}】。
  其中【{veto_list}】触发硬性熔断——
  {reason_str}」
- **生存审计官 (audit_officer)**：「熔断之外，【{risk_list}】虽未熔断但AI替代率偏高。
  结合考生 Holland 代码 {holland_code}，
  {'建议走数理降维跨考路径（规则五）' if 'I' in holland_code else '建议强化物理世界实业壁垒（规则六）'}」
- **用户画像官 (profile_officer)**：「综合两方意见，本案优先方向已调整，剩余方案见下方推荐清单。」
"""
