import os
import json
from skills.injector import KnowledgeInjector

class MajorEvaluator:
    def __init__(self, data_dir=None):
        self.injector = KnowledgeInjector(data_dir=data_dir)

        # Hardcoded dictionary for AI replacement rates (0.0 means immune, 1.0 means fully replaceable)
        self.ai_replacement_rates = {
            "translation": 0.95,
            "翻译": 0.95,
            "english": 0.90,
            "英语": 0.90,
            "accounting": 0.85,
            "会计": 0.85,
            "business administration": 0.80,
            "工商管理": 0.80,
            "public administration": 0.85,
            "公共事业管理": 0.85,
            "social work": 0.65,
            "社会工作": 0.65,
            "journalism": 0.85,
            "新闻学": 0.85,
            "finance": 0.70,
            "金融": 0.70,
            "law": 0.60,
            "法律": 0.60,
            "法学": 0.60,
            "graphic design": 0.75,
            "平面设计": 0.75,
            "civil engineering": 0.40,
            "土木": 0.40,
            "computer science": 0.55,
            "计算机": 0.55,
            "software engineering": 0.50,
            "软件工程": 0.50,
            "artificial intelligence": 0.20,
            "人工智能": 0.20,
            "integrated circuit": 0.15,
            "集成电路": 0.15,
            "semiconductor": 0.15,
            "半导体": 0.15,
            "electrical engineering": 0.15,
            "电气": 0.15,
            "smart grid": 0.15,
            "电网": 0.15,
            "smart manufacturing": 0.25,
            "智能制造": 0.25,
            "clinical medicine": 0.08,
            "临床医学": 0.08,
            "dentist": 0.05,
            "dentistry": 0.05,
            "口腔": 0.05,
            "nursing": 0.10,
            "护理": 0.10,
            "special education": 0.15,
            "特殊教育": 0.15,
            "数字媒体艺术": 0.80,
            "工业设计": 0.45,
            "智能控制技术": 0.25,
            "新能源汽车检测与维修": 0.15
        }

        # Hardcoded stability rating (0.0 to 1.0)
        self.employment_stability = {
            "electrical engineering": 0.95,
            "电气": 0.95,
            "smart grid": 0.95,
            "电网": 0.95,
            "clinical medicine": 0.90,
            "临床医学": 0.90,
            "dentist": 0.95,
            "dentistry": 0.95,
            "口腔": 0.95,
            "nursing": 0.85,
            "护理": 0.85,
            "special education": 0.80,
            "特殊教育": 0.80,
            "integrated circuit": 0.85,
            "集成电路": 0.85,
            "semiconductor": 0.85,
            "半导体": 0.85,
            "artificial intelligence": 0.75,
            "人工智能": 0.75,
            "software engineering": 0.70,
            "软件工程": 0.70,
            "computer science": 0.65,
            "计算机": 0.65,
            "smart manufacturing": 0.80,
            "智能制造": 0.80,
            "civil engineering": 0.30,
            "土木": 0.30,
            "business administration": 0.20,
            "工商管理": 0.20,
            "english": 0.20,
            "英语": 0.20,
            "translation": 0.15,
            "翻译": 0.15,
            "public administration": 0.20,
            "公共事业管理": 0.20,
            "social work": 0.30,
            "社会工作": 0.30,
            "journalism": 0.20,
            "新闻学": 0.20,
            "finance": 0.40,
            "金融": 0.40,
            "law": 0.50,
            "法律": 0.50,
            "法学": 0.50,
            "数字媒体艺术": 0.65,
            "工业设计": 0.75,
            "智能控制技术": 0.85,
            "新能源汽车检测与维修": 0.90
        }

    def get_ai_replacement_rate(self, major_name):
        major_lower = major_name.lower()
        for key, rate in self.ai_replacement_rates.items():
            if key in major_lower or major_lower in key:
                return rate
        return 0.50  # Default moderate risk

    def get_employment_stability(self, major_name):
        major_lower = major_name.lower()
        for key, rate in self.employment_stability.items():
            if key in major_lower or major_lower in key:
                return rate
        return 0.50  # Default moderate stability

    def evaluate_major(self, major_name, student_facts, institution_level="Ordinary"):
        """
        Evaluate major survival metrics and fit with student facts.
        Supports both nested v3.0 facts and flat facts structure.
        """
        major_lower = major_name.lower()

        # 1. AI Replacement Index
        ai_replace_rate = self.get_ai_replacement_rate(major_name)

        # 2. Check if cancelled or newly added in national policies
        is_cancelled = self.injector.check_major_cancelled(major_name, institution_level) is not None
        is_added = self.injector.check_major_added(major_name) is not None

        # 3. Policy Alignment (0.0 - 1.0)
        policy_alignment = 0.5
        if is_added:
            policy_alignment = 0.9
        elif is_cancelled:
            policy_alignment = 0.1

        # Check 15th Five Year Plan markdown file
        five_year_keywords = ["集成电路", "半导体", "人工智能", "新一代计算", "新能源", "储能", "智能制造", "生物医学", "微电子"]
        for kw in five_year_keywords:
            if kw in major_name:
                policy_alignment = max(policy_alignment, 0.95)

        # 4. Employment Stability
        stability = self.get_employment_stability(major_name)

        # 5. Calculate Survival Score (0.0 - 100)
        survival_score = int(((1.0 - ai_replace_rate) * 0.4 + policy_alignment * 0.3 + stability * 0.3) * 100)

        # 6. Fit / Match Score with Student Constraints
        match_reasons = []
        veto_reasons = []
        is_vetoed = False

        # Extract facts safely from nested or flat schema
        if "basic_info" in student_facts:
            province = student_facts["basic_info"].get("province", "")
            track_type = student_facts["basic_info"].get("track_type", "")
            subjects = student_facts["basic_info"].get("subjects", "") or student_facts.get("Subject Combination", "")
        else:
            province = student_facts.get("Province", "")
            track_type = student_facts.get("track_type", "夏季高考")
            subjects = student_facts.get("Subject Combination", "")

        if "psychological_profile" in student_facts:
            family_support = student_facts.get("Family Background Support", "") or student_facts["psychological_profile"].get("core_driver", "")
            financial_expectation = student_facts.get("Financial Expectation", "") or student_facts["psychological_profile"].get("core_driver", "")
        else:
            family_support = student_facts.get("Family Background Support", "")
            financial_expectation = student_facts.get("Financial Expectation", "")

        subjects_str = "".join([s.strip() for s in subjects.replace("，", ",").split(",")])

        # A. Check Subject Combinations (物化强约束)
        is_science = any(kw in major_lower for kw in ["computer", "software", "artificial intelligence", "integrated circuit", "semiconductor", "electrical", "grid", "engineering", "manufacturing", "medicine", "dentist", "dentistry", "clinical", "nursing", "储能", "新能源", "芯片", "医学", "工程", "智能", "智能控制", "汽车"])

        if is_science and ("广东春考" not in track_type):
            has_physics = "物理" in subjects_str or "physics" in major_lower or "physics" in subjects_str.lower()
            has_chemistry = "化学" in subjects_str or "chemistry" in major_lower or "chemistry" in subjects_str.lower()
            if not (has_physics and has_chemistry):
                is_vetoed = True
                veto_reasons.append("未选【物理+化学】科目，该理工医学类专业不符合夏季高考报考资格。")

        # B. Check Family Resource fit
        is_low_income = "低" in family_support or "困难" in family_support or "即就业" in family_support or "立即就业" in family_support or "壁垒优先" in family_support or "壁垒优先" in financial_expectation

        # Clinical medicine needs long duration
        if "clinical medicine" in major_lower or "临床医学" in major_name:
            if is_low_income:
                match_reasons.append("临床医学学制长（通常需要5年本科+3年规培/硕士），对于需要毕业即就业的家庭经济压力极大，请谨慎。")
            else:
                match_reasons.append("家庭资源支持长周期，临床医学是高壁垒抗AI的黄金学科。")

        # Public system targets (Electrical Grid / Police / Military)
        if any(x in major_lower or x in major_name for x in ["电气", "电网", "electrical", "grid"]):
            if is_low_income or "编制" in financial_expectation or "壁垒" in financial_expectation:
                match_reasons.append("电气工程适配进入国家电网，属于极佳的高薪稳定编制方向。")

        # Cancelled or high replacement risks
        if is_cancelled:
            is_vetoed = True
            cancelled_info = self.injector.check_major_cancelled(major_name, institution_level)
            reason_str = ""
            if cancelled_info:
                reason_str = cancelled_info.get('reason') or cancelled_info.get('Reason') or ""
            veto_reasons.append(f"该专业（{major_name}）在教育部2026年撤销专业布点名单中。原因: {reason_str}")

        if ai_replace_rate >= 0.80:
            match_reasons.append(f"警告：该专业受生成式AI技术冲击巨大，替代率高达{int(ai_replace_rate*100)}%。")
            if "编制" not in financial_expectation and is_low_income:
                is_vetoed = True
                veto_reasons.append("家庭需要毕业即挣钱，但该专业面临严峻AI替代和市场萎缩风险，予以否决。")

        # C. Regional Specials rules
        if "广东春考" in track_type:
            # If they choose generic office work in Spring gaokao
            if any(x in major_lower for x in ["会计", "市场营销", "工商管理", "英语", "文秘", "行政"]):
                is_vetoed = True
                veto_reasons.append("广东春考专科严禁报纯白领流水线岗位（如会计/市场营销），AI替代率高且招聘大盘趋近归零。")

        if "艺术" in track_type or "艺考" in track_type:
            if any(x in major_lower for x in ["视觉传达", "原画", "插画", "国画", "油画", "美术"]):
                match_reasons.append("警告：传统画师/设计受AI生成绘画冲击严重，建议转向【数字媒体艺术】等1+X复合赛道。")

        # Calculate fit rating
        fit_score = 100
        if is_vetoed:
            fit_score = 0
        else:
            deductions = len(veto_reasons) * 30 + (1 if is_low_income and ai_replace_rate > 0.5 else 0) * 20
            fit_score = max(20, 100 - deductions)

        return {
            "major": major_name,
            "ai_replacement_index": ai_replace_rate,
            "policy_alignment": policy_alignment,
            "stability_index": stability,
            "survival_score": survival_score,
            "fit_score": fit_score,
            "is_vetoed": is_vetoed,
            "veto_reasons": veto_reasons,
            "match_reasons": match_reasons
        }


class SanageAxisEvaluator:
    def __init__(self, session_id=None, user_data=None):
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        if user_data is not None:
            self.user_data = user_data
        elif session_id is not None:
            self.session_path = os.path.join(self.base_path, f"workspace/sessions/{session_id}/facts.json")
            self.user_data = self._load_user_data()
        else:
            self.user_data = {}

    def _load_user_data(self):
        if hasattr(self, 'session_path') and os.path.exists(self.session_path):
            with open(self.session_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def evaluate_major_compatibility(self):
        """
        核心匹配度计算引擎：结合分数段、赛道、霍兰德代码与生存策略
        """
        if not self.user_data:
            return []

        # Parse nested or flat keys
        if "basic_info" in self.user_data:
            track_type = self.user_data["basic_info"].get("track_type", "夏季高考")
        else:
            track_type = self.user_data.get("track_type") or self.user_data.get("Track Type", "夏季高考")

        if "psychological_profile" in self.user_data:
            traits = self.user_data["psychological_profile"].get("holland_code_inferred", ["I", "R"])
            driver = self.user_data["psychological_profile"].get("core_driver", "普通期望")
        else:
            traits = self.user_data.get("holland_code_inferred", ["I", "R"])
            driver = self.user_data.get("Financial Expectation") or self.user_data.get("core_driver", "普通期望")

        recommendation_pool = []

        # 1. 赛道分流逻辑
        if "广东春考" in track_type:
            # 春考严禁推荐纯白领流水线，强推手艺壁垒型专科
            recommendation_pool.extend([
                {
                    "major": "智能控制技术",
                    "score": 95,
                    "path": "专科直通高端制造",
                    "strategy_tag": "SURVIVAL_FIRST",
                    "reason": "物理世界难以被AI闭环，大湾区头部公办专科（深职大/番职院）王牌专业"
                },
                {
                    "major": "新能源汽车检测与维修",
                    "score": 90,
                    "path": "技术出海与新能源产业链",
                    "strategy_tag": "SURVIVAL_FIRST",
                    "reason": "迎合大湾区智能新能源实体产业红利，偏重物理落地技能"
                }
            ])
        elif "艺术类" in track_type or "艺考" in track_type:
            # 艺考走 1+X 复合或考公洗白路径
            recommendation_pool.extend([
                {
                    "major": "数字媒体艺术",
                    "score": 85,
                    "path": "1+X复合：艺术+游戏交互/UI",
                    "strategy_tag": "COMPOSITE_X",
                    "reason": "对接数字内容开发，通过学习交互与编码对抗纯画师被AI完全替代的风险"
                },
                {
                    "major": "工业设计",
                    "score": 80,
                    "path": "艺术+具身智能硬件视觉",
                    "strategy_tag": "COMPOSITE_X",
                    "reason": "偏物理实体造型与硬件界面设计，具备极强物理交互壁垒"
                }
            ])
        else:
            # 夏季高考统招：启动张雪峰流派“跨考红利”与“霍兰德代码”交叉匹配
            if "I" in traits and "R" in traits: # 研究型 + 现实型
                recommendation_pool.append({
                    "major": "数学与应用数学",
                    "score": 95,
                    "path": "本科数学 -> 硕士跨考计算机/数据科学",
                    "strategy_tag": "CROSS_POSTGRAD",
                    "reason": "考研降维打击计算机内核，避开本科直接学软件工程面临代码大模型降级的高危期"
                })
                recommendation_pool.append({
                    "major": "机械设计制造及其自动化",
                    "score": 88,
                    "path": "本科机械 -> 硕士跨考具身智能/机器人控制",
                    "strategy_tag": "CROSS_POSTGRAD",
                    "reason": "本科扎实机械与物理力学底子，考研转控向，进可攻新质生产力，退可守制造业稳定编制"
                })

            if "E" in traits or "S" in traits: # 企业型 / 社会型
                recommendation_pool.append({
                    "major": "法学",
                    "score": 85,
                    "path": "本科法学 -> 硕士考公/考编或垂直行业合规",
                    "strategy_tag": "SURVIVAL_FIRST",
                    "reason": "考公大户，自带行业窄门与行政壁垒，AI无法闭环复杂的法庭辩论与人际博弈"
                })

        # 2. 功利主义权重修正 (根据家庭资源审计)
        if driver == "壁垒优先":
            for rec in recommendation_pool:
                if "CROSS_POSTGRAD" in rec.get("strategy_tag", "") or "SURVIVAL_FIRST" in rec.get("strategy_tag", ""):
                    rec["score"] += 5  # 增加稳健/复合路径的权重
        elif driver == "高风险高回报":
            for rec in recommendation_pool:
                if "新能源" in rec["major"] or "智能" in rec["major"] or "COMPOSITE_X" in rec.get("strategy_tag", ""):
                    rec["score"] += 5

        # 按得分降序排序
        recommendation_pool = sorted(recommendation_pool, key=lambda x: x["score"], reverse=True)
        return recommendation_pool

if __name__ == "__main__":
    evaluator = SanageAxisEvaluator(user_data={
        "basic_info": {
            "track_type": "夏季高考"
        },
        "psychological_profile": {
            "holland_code_inferred": ["I", "R"],
            "core_driver": "壁垒优先"
        }
    })
    print(evaluator.evaluate_major_compatibility())
