import os
import json
import bisect
from scripts.injector import KnowledgeInjector
from scripts.gaokao_mapper import normalize_province, normalize_stream
from scripts.sogou_api import fetch_score_range

class MajorEvaluator:
    def __init__(self, data_dir=None):
        self.data_dir = data_dir
        self.injector = KnowledgeInjector(data_dir=data_dir)
        self._build_five_year_keywords()

    def _build_five_year_keywords(self):
        """从 15th_five_year_plan.md 动态提取高频产业关键词"""
        text = self.injector.five_year_plan
        import re
        keywords = re.findall(r'[-*]\s+\*\*(.+?)\*\*', text)
        keywords += re.findall(r'[-*]\s+(.{2,12})[（(「\n]', text)
        self.five_year_keywords = list(set(k.strip() for k in keywords if len(k) > 1))

        # Initialize dictionaries
        self.ai_replacement_rates = {}
        self.employment_stability = {}
        self.major_aliases = {}

        # 1. Fallback default configurations
        fallback_ai = {
            "translation": 0.95, "翻译": 0.95, "english": 0.90, "英语": 0.90,
            "accounting": 0.85, "会计": 0.85, "business administration": 0.80, "工商管理": 0.80,
            "public administration": 0.85, "公共事业管理": 0.85, "social work": 0.65, "社会工作": 0.65,
            "journalism": 0.85, "新闻学": 0.85, "finance": 0.70, "金融": 0.70,
            "law": 0.60, "法律": 0.60, "法学": 0.60, "graphic design": 0.75, "平面设计": 0.75,
            "civil engineering": 0.40, "土木": 0.40, "computer science": 0.55, "计算机": 0.55,
            "software engineering": 0.50, "软件工程": 0.50, "artificial intelligence": 0.20, "人工智能": 0.20,
            "integrated circuit": 0.15, "集成电路": 0.15, "semiconductor": 0.15, "半导体": 0.15,
            "electrical engineering": 0.15, "电气": 0.15, "smart grid": 0.15, "电网": 0.15,
            "smart manufacturing": 0.25, "智能制造": 0.25, "clinical medicine": 0.08, "临床医学": 0.08,
            "dentist": 0.05, "dentistry": 0.05, "口腔": 0.05, "nursing": 0.10, "护理": 0.10,
            "special education": 0.15, "特殊教育": 0.15, "数字媒体艺术": 0.80, "工业设计": 0.45,
            "智能控制技术": 0.25, "新能源汽车检测与维修": 0.15
        }
        fallback_stability = {
            "electrical engineering": 0.95, "电气": 0.95, "smart grid": 0.95, "电网": 0.95,
            "clinical medicine": 0.90, "临床医学": 0.90, "dentist": 0.95, "dentistry": 0.95,
            "口腔": 0.95, "nursing": 0.85, "护理": 0.85, "special education": 0.80, "特殊教育": 0.80,
            "integrated circuit": 0.85, "集成电路": 0.85, "semiconductor": 0.85, "半导体": 0.85,
            "artificial intelligence": 0.75, "人工智能": 0.75, "software engineering": 0.70, "软件工程": 0.70,
            "computer science": 0.65, "计算机": 0.65, "smart manufacturing": 0.80, "智能制造": 0.80,
            "civil engineering": 0.30, "土木": 0.30, "business administration": 0.20, "工商管理": 0.20,
            "english": 0.20, "英语": 0.20, "translation": 0.15, "翻译": 0.15,
            "public administration": 0.20, "公共事业管理": 0.20, "social work": 0.30, "社会工作": 0.30,
            "journalism": 0.20, "新闻学": 0.20, "finance": 0.40, "金融": 0.40,
            "law": 0.50, "法律": 0.50, "法学": 0.50, "数字媒体艺术": 0.65, "工业设计": 0.75,
            "智能控制技术": 0.85, "新能源汽车检测与维修": 0.90
        }

        # 1.1 Fallback major aliases
        fallback_aliases = {
            "计科": "计算机科学与技术",
            "计算机科学": "计算机科学与技术",
            "cs": "计算机科学与技术",
            "软工": "软件工程",
            "se": "软件工程",
            "ai": "人工智能",
            "人工智能技术": "人工智能",
            "智能科学与技术": "人工智能"
        }
        
        # 2. Attempt loading from configuration file
        if self.data_dir:
            config_path = os.path.join(self.data_dir, "major_rules.json")
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_path, "data", "major_rules.json")
        loaded_successfully = False
        
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    
                ai_rates = config.get("ai_replacement_rates")
                stability = config.get("employment_stability")
                aliases = config.get("major_aliases")
                
                if isinstance(ai_rates, dict) and isinstance(stability, dict):
                    valid_ai = all(isinstance(v, (int, float)) and 0 <= v <= 1 for v in ai_rates.values())
                    valid_stab = all(isinstance(v, (int, float)) and 0 <= v <= 1 for v in stability.values())
                    valid_aliases = isinstance(aliases, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in aliases.items())
                    
                    if valid_ai and valid_stab:
                        self.ai_replacement_rates = ai_rates
                        self.employment_stability = stability
                        if valid_aliases:
                            self.major_aliases = aliases
                        else:
                            self.major_aliases = fallback_aliases
                        loaded_successfully = True
            except Exception:
                pass
                
        if not loaded_successfully:
            self.ai_replacement_rates = fallback_ai
            self.employment_stability = fallback_stability
            self.major_aliases = fallback_aliases

    def normalize_major(self, major_name):
        """标准化专业名称：将别名转换为标准名称"""
        if not major_name:
            return major_name
        
        # 检查是否有精确匹配的别名
        major_name_clean = major_name.strip()
        if major_name_clean in self.major_aliases:
            return self.major_aliases[major_name_clean]
        
        # 检查是否有包含关系的别名（不区分大小写）
        major_lower = major_name_clean.lower()
        for alias, standard in self.major_aliases.items():
            if alias.lower() in major_lower or major_lower in alias.lower():
                return standard
        
        return major_name

    def _fuzzy_match_rate(self, name_lower, lookup_dict):
        """Exact-first match, then length-ratio-guarded substring.
        Prevents short generic keys like "自动化"(3 chars) from matching
        compound names like "电气工程及其自动化"(9 chars)."""
        # 1. Exact match (highest priority)
        if name_lower in lookup_dict:
            return lookup_dict[name_lower]
        # 2. Substring with length-ratio guard (≥60%)
        best_rate, best_len = 0.50, 0
        for key, rate in lookup_dict.items():
            if key in name_lower or name_lower in key:
                shorter = min(len(key), len(name_lower))
                longer = max(len(key), len(name_lower))
                if shorter >= 2 and shorter / longer >= 0.6:
                    if len(key) > best_len:
                        best_rate, best_len = rate, len(key)
        return best_rate

    def get_ai_replacement_rate(self, major_name):
        return self._fuzzy_match_rate(major_name.lower(), self.ai_replacement_rates)

    def get_employment_stability(self, major_name):
        return self._fuzzy_match_rate(major_name.lower(), self.employment_stability)

    def get_rank_from_score(self, province, year, stream, score):
        """
        Get exact cumulative rank for a given score in a province, year, and stream.
        """
        prov_clean = normalize_province(province)
        try:
            year_int = int(year)
        except (ValueError, TypeError):
            year_int = 2024
        stream_clean = normalize_stream(prov_clean, year_int, stream)
        
        records = fetch_score_range(prov_clean, str(year), stream_clean)
        if not records or not isinstance(records, list):
            return None
            
        detail = []
        for r in records:
            if r.get("查询数据"):
                detail = r["查询数据"]
                break
        if not detail:
            return None
            
        valid = []
        for item in detail:
            try:
                score_str = item.get("返回的查询分数", "")
                if "-" in score_str:
                    s_val = int(score_str.split("-")[0])
                else:
                    s_val = int(score_str)
                valid.append((item, s_val, int(item.get("排名位次", 0))))
            except (KeyError, ValueError, TypeError):
                continue
                
        if not valid:
            return None
            
        valid_rev = list(reversed(valid))
        scores = [v[1] for v in valid_rev]
        
        try:
            target_score = int(score)
        except (ValueError, TypeError):
            return None
            
        idx = bisect.bisect_right(scores, target_score) - 1
        if idx < 0:
            idx = 0
            
        item = valid_rev[idx][0]
        item_score = valid_rev[idx][1]
        
        if target_score < item_score:
            return int(item.get("排名位次", 999999))
            
        return int(item.get("排名位次", 0))

    def get_score_from_rank(self, province, year, stream, rank):
        """
        Get score corresponding to a given cumulative rank in a province, year, and stream.
        """
        prov_clean = normalize_province(province)
        try:
            year_int = int(year)
        except (ValueError, TypeError):
            year_int = 2024
        stream_clean = normalize_stream(prov_clean, year_int, stream)
        
        records = fetch_score_range(prov_clean, str(year), stream_clean)
        if not records or not isinstance(records, list):
            return None
            
        detail = []
        for r in records:
            if r.get("查询数据"):
                detail = r["查询数据"]
                break
        if not detail:
            return None
            
        total_nums = []
        valid_items = []
        for item in detail:
            try:
                rank_val = int(item.get("排名位次", 0))
                total_nums.append(rank_val)
                valid_items.append(item)
            except (KeyError, ValueError, TypeError):
                total_nums.append(999999)
                valid_items.append(item)
                
        if not total_nums:
            return None
            
        try:
            target_rank = int(rank)
        except (ValueError, TypeError):
            return None
            
        idx = bisect.bisect_left(total_nums, target_rank)
        if idx >= len(valid_items):
            idx = len(valid_items) - 1
            
        item = valid_items[idx]
        score_str = item.get("返回的查询分数", "")
        if "-" in score_str:
            try:
                return int(score_str.split("-")[0])
            except ValueError:
                return score_str
        try:
            return int(score_str)
        except ValueError:
            return score_str

    def get_batch_lines_status(self, student_facts, year=2024):
        """
        Evaluate student score against provincial control batch lines.
        """
        if "basic_info" in student_facts:
            info = student_facts["basic_info"]
            province = info.get("province", "")
            track_type = info.get("track_type", "")
            score = info.get("score_details", {}).get("culture_score")
        else:
            province = student_facts.get("Province", "")
            track_type = student_facts.get("track_type") or student_facts.get("Track Type", "")
            score = student_facts.get("Score / Ranking")
            
        try:
            score = int(score)
        except (ValueError, TypeError):
            return "无法解析分数，不作对比。"

        if not province or not track_type:
            return "省份或科类缺失，无法对比。"

        # Search for lines
        lines = self.injector.get_province_control_line(province, track_type, year=year)
        if not lines:
            # Try 2025 as fallback
            lines = self.injector.get_province_control_line(province, track_type, year=2025)
            if not lines:
                return "暂未收录该省份的批次线。"

        status_messages = []
        for line in lines:
            try:
                line_score = int(line.get('control_score'))
                batch_name = line.get('batch_name')
                diff = score - line_score
                diff_str = f"+{diff}" if diff >= 0 else f"{diff}"
                status_messages.append(f"{batch_name}: {line_score}分(差值:{diff_str})")
            except (ValueError, TypeError):
                continue
        return " | ".join(status_messages)

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
        for kw in self.five_year_keywords:
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

        if is_science and track_type in ["夏季高考"]:
            has_physics = "物理" in subjects_str or "physics" in major_lower or "physics" in subjects_str.lower()
            has_chemistry = "化学" in subjects_str or "chemistry" in major_lower or "chemistry" in subjects_str.lower()
            if not (has_physics and has_chemistry):
                is_vetoed = True
                veto_reasons.append("未选【物理+化学】科目，该理工医学类专业不符合夏季高考报考资格。")

        # B. Check Family Resource fit
        is_low_income = (
            "低" in family_support or "困难" in family_support or 
            "即就业" in family_support or "立即就业" in family_support or 
            "变现" in family_support or "变现" in financial_expectation or
            "变现" in str(student_facts) or "尽快有稳定收入" in str(student_facts) or
            "壁垒优先" in family_support or "壁垒优先" in financial_expectation
        )

        # Medicine needs long duration check (VETO under low income / quick变现)
        if any(x in major_lower or x in major_name for x in ["clinical medicine", "临床医学", "口腔", "dentist", "dentistry"]):
            if is_low_income:
                is_vetoed = True
                veto_reasons.append(f"该医学专业（{major_name}）学制长（通常为5年本科+3年规培），独立行医周期长达8年，严重违背您毕业后尽快有稳定收入的核心诉求。")
            else:
                match_reasons.append("家庭资源支持长周期，该医学专业是高壁垒抗AI的黄金学科。")

        # Pure science check (VETO under low income / quick变现)
        is_pure_science = any(kw in major_name for kw in ["数学与应用数学", "物理学", "化学", "生物科学", "生物技术", "地理科学", "基础理学", "基础科学"]) and not any(kw in major_name for kw in ["工业设计", "数字媒体"])
        if is_pure_science and is_low_income:
            is_vetoed = True
            veto_reasons.append(f"该纯基础理科专业（{major_name}）变现转化链路极长，试错成本高，不符合快速稳定就业的期望。")

        # Physical constraints check (Color blindness / weakness)
        restriction = student_facts.get("basic_info", {}).get("body_restriction", "无") if "basic_info" in student_facts else student_facts.get("body_restriction", "无")
        if any(r in restriction for r in ["色盲", "色弱"]):
            color_sensitive_majors = ["电气", "电网", "电力", "化学", "化工", "医学", "临床", "口腔", "护理", "药学", "生物", "农学", "电子信息"]
            if any(m in major_name for m in color_sensitive_majors):
                is_vetoed = True
                veto_reasons.append(f"考生体检情况为【{restriction}】，受高校招生体检规定限制，色盲/色弱考生禁止报考【{major_name}】相关专业。")

        # D. Check Dislikes (排斥/规避专业)
        dislikes = []
        if "basic_info" in student_facts:
            dislikes = student_facts["basic_info"].get("dislikes", [])
        else:
            dislikes = student_facts.get("dislikes", [])

        if dislikes:
            for item in dislikes:
                mapped_keywords = [item]
                if item == "生化环材":
                    mapped_keywords = ["生物", "化学", "环境", "材料"]
                
                for kw in mapped_keywords:
                    if kw in major_name:
                        is_vetoed = True
                        veto_reasons.append(f"该专业（{major_name}）匹配了您意向规避/排斥的专业关键词【{item}】。")
                        break

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

    def get_recommendations_by_rank(self, province, student_rank, subjects_str=""):
        """
        Group benchmark schools from database into 冲, 稳, 保 based on student rank.
        """
        stretch = []
        target = []
        safe = []
        anchor = []
        
        try:
            r_val = int(student_rank)
        except (ValueError, TypeError):
            return {"冲": [], "稳": [], "保": [], "垫": []}
            
        for row in self.injector.score_lines:
            if row.get("province") == province:
                try:
                    min_r = int(row.get("min_rank", 0))
                except (ValueError, TypeError):
                    continue
                if min_r <= 0:
                    continue
                    
                school = row.get("school_name", "")
                major = row.get("major", "")
                item_str = f"{school}（{major}，2024最低排位约{min_r}）"
                
                if int(r_val * 0.5) <= min_r < int(r_val * 0.95):
                    stretch.append(item_str)
                elif int(r_val * 0.95) <= min_r < int(r_val * 1.25):
                    target.append(item_str)
                elif int(r_val * 1.25) <= min_r < int(r_val * 1.45):
                    safe.append(item_str)
                elif min_r >= int(r_val * 1.45):
                    anchor.append(item_str)
                    
        return {
            "冲": list(set(stretch))[:3],
            "稳": list(set(target))[:3],
            "保": list(set(safe))[:3],
            "垫": list(set(anchor))[:3]
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
        elif "艺术类" in track_type or "艺术" in track_type or "艺考" in track_type:
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

            # Map RCA (or A alongside R/C) to Industrial Design & Digital Media Technology
            if "A" in traits and ("R" in traits or "C" in traits):
                recommendation_pool.append({
                    "major": "工业设计",
                    "score": 93,
                    "path": "工科背景 + 产品美学与创意设计",
                    "strategy_tag": "COMPOSITE_X",
                    "reason": "完美结合 R/C 的工科物理世界壁垒与 A 的创意美学，AI难以完全替代这种复合型设计。"
                })
                recommendation_pool.append({
                    "major": "数字媒体技术",
                    "score": 90,
                    "path": "计算机技术 + 艺术交互开发",
                    "strategy_tag": "COMPOSITE_X",
                    "reason": "代码开发底座（R/C）与交互美学设计（A）的结合，避开纯程序员的低端替代，对接新质生产力数字创意岗位。"
                })

        # Check special paths willingness and quick stable income driver
        willing_special = False
        if "basic_info" in self.user_data:
            willing_special = self.user_data["basic_info"].get("willing_special") in ["是", "y", "yes", "true", True, "willing"]
        else:
            willing_special = self.user_data.get("willing_special") in ["是", "y", "yes", "true", True, "willing"]

        is_quick_income = (
            "变现" in driver or "即就业" in driver or "尽快" in driver or "壁垒" in driver or
            "尽快有稳定收入" in str(self.user_data) or "尽快变现" in str(self.user_data)
        )

        if willing_special and is_quick_income:
            recommendation_pool.append({
                "major": "公费定向师范生 (提前批)",
                "score": 98,
                "path": "本科免学费 -> 毕业直通生源地中小学教师编制",
                "strategy_tag": "SPECIAL_PATH",
                "reason": "四年学费全免，毕业直接解决地方事业编制，满足快速稳定变现的终极诉求。"
            })
            recommendation_pool.append({
                "major": "提前批公安警校",
                "score": 97,
                "path": "本科警校 -> 参加公安联考直通入警带编",
                "strategy_tag": "SPECIAL_PATH",
                "reason": "毕业参加公安联考入警率超90%，4年毕业直接入警带公务员编制，铁饭碗保障。"
            })
            recommendation_pool.append({
                "major": "农村卫生定向 (临床/中医)",
                "score": 96,
                "path": "免费医学教育 -> 毕业直通基层卫生院带编岗位",
                "strategy_tag": "SPECIAL_PATH",
                "reason": "避开普通医学长达8年的变现泥潭，免费学医，毕业即有地方卫生院事业编工作。"
            })

        # Check priority preferences (三维平衡取舍)
        priority_choice = "未定"
        if "basic_info" in self.user_data:
            priority_choice = self.user_data["basic_info"].get("priority_choice", "未定")
        else:
            priority_choice = self.user_data.get("priority_choice", "未定")

        if priority_choice == "学校优先":
            recommendation_pool.append({
                "major": "大类招生 (如工科/理科试验班)",
                "score": 92,
                "path": "大一通用培养 -> 大二再分流确定专业",
                "strategy_tag": "SCHOOL_FIRST",
                "reason": "【学校优先】策略下的最佳通道：优先提升学校名气与层级，用大一的一年时间作为‘专业体验卡’，大二再分流分科。"
            })
            recommendation_pool.append({
                "major": "数学与应用数学 (宽口径)",
                "score": 89,
                "path": "名校基础理科 -> 硕士高保研或跨考金牌专业",
                "strategy_tag": "SCHOOL_FIRST",
                "reason": "【学校优先】策略的备选路径：利用基础学科的高保研率 and 名校光环，在硕士阶段轻松跨考实现专业二次定位。"
            })
        elif priority_choice == "城市优先":
            recommendation_pool.append({
                "major": "计算机类/电子信息类 (城市产业对齐)",
                "score": 92,
                "path": "发达城市双非高校 -> 深度融入本地高新技术产业链",
                "strategy_tag": "CITY_FIRST",
                "reason": "【城市优先】策略的打法：虽然学校层级适当让步，但留在核心城市能获得更好的本地实习、社会资源与高频校招机会。"
            })
        elif priority_choice == "专业优先":
            recommendation_pool.append({
                "major": "电气工程及其自动化 (强壁垒应用)",
                "score": 92,
                "path": "专业强校 -> 稳步直通电网/工业巨头",
                "strategy_tag": "MAJOR_FIRST",
                "reason": "【专业优先】策略的铁律：放弃部分名校层级，下沉到行业特色大学（如双非强电高校），确保守住国家电网等高垄断就业窄门。"
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
