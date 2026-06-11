import os
import json
import sys
from datetime import datetime
from scripts.injector import KnowledgeInjector
from scripts.evaluator import MajorEvaluator, SanageAxisEvaluator
from scripts.trait_evaluator import TraitEvaluator
from scripts.output_generator import OutputGenerator, parse_markdown_with_frontmatter

class AxisRunner:
    def __init__(self):
        self.workspace_dir = os.path.join(os.path.dirname(__file__), 'workspace')
        self.sessions_dir = os.path.join(self.workspace_dir, 'sessions')
        self.template_dir = os.path.join(self.workspace_dir, 'template')
        
        # Ensure directories exist
        os.makedirs(self.sessions_dir, exist_ok=True)
        
        self.current_uid = None
        self.current_facts = {}
        
        self.injector = KnowledgeInjector()
        self.evaluator = MajorEvaluator()
        self.trait_evaluator = TraitEvaluator()
        self.generator = OutputGenerator()

    def log_timeline(self, uid, message):
        """Append log to timeline.log for the session."""
        log_path = os.path.join(self.sessions_dir, uid, 'timeline.log')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")

    def save_facts(self, uid, facts):
        """Save facts.json for the session."""
        facts_path = os.path.join(self.sessions_dir, uid, 'facts.json')
        with open(facts_path, 'w', encoding='utf-8') as f:
            json.dump(facts, f, indent=2, ensure_ascii=False)

    def load_facts(self, uid):
        """Load facts.json for the session."""
        facts_path = os.path.join(self.sessions_dir, uid, 'facts.json')
        if os.path.exists(facts_path):
            with open(facts_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def update_blind_spots(self, uid, content):
        """Write or update blind_spots.md."""
        bs_path = os.path.join(self.sessions_dir, uid, 'blind_spots.md')
        with open(bs_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def get_profile_step(self, facts):
        """Calculate current profile step (1 to 4) under v3.0 schema."""
        if not facts:
            return 1
            
        info = facts.get("basic_info", {})
        profile = facts.get("psychological_profile", {})
        
        # Step 1: uid, province, track_type, score
        step1 = bool(info.get("uid") and info.get("province") and info.get("track_type") and 
                     (info.get("score_details", {}).get("culture_score") or info.get("score_details", {}).get("art_province_ranking")))
                     
        # Step 2: subjects
        step2 = step1 and bool(info.get("subjects"))
        
        # Step 3: Holland codes
        step3 = step2 and bool(profile.get("holland_code_inferred"))
        
        # Step 4: Core driver / expectations
        step4 = step3 and bool(profile.get("core_driver"))
        
        if step4: return 4
        if step3: return 3
        if step2: return 2
        return 1

    def handle_init(self, uid, interactive=True):
        """Initialize session for the student under v3.0 nested structure."""
        session_path = os.path.join(self.sessions_dir, uid)
        is_new = not os.path.exists(session_path)
        os.makedirs(session_path, exist_ok=True)
        
        self.current_uid = uid
        
        if is_new:
            self.current_facts = {
                "basic_info": {
                    "uid": uid,
                    "province": "",
                    "track_type": "夏季高考",
                    "subjects": "",
                    "score_details": {
                        "culture_score": 0,
                        "art_province_ranking": 0
                    }
                },
                "psychological_profile": {
                    "holland_code_inferred": [],
                    "core_driver": "",
                    "derived_strengths": [],
                    "blind_spots": []
                },
                "Target Majors": []
            }
            self.save_facts(uid, self.current_facts)
            self.update_blind_spots(uid, "# sanage Axis - Target Universities & Majors Paradoxes\n\n- No paradoxes recorded yet.\n")
            
            # Create empty timeline.log
            timeline_path = os.path.join(session_path, 'timeline.log')
            with open(timeline_path, 'w', encoding='utf-8') as f:
                f.write(f"=== Session Initialized for {uid} ===\n")
            
            self.log_timeline(uid, "Session initialized from template state v3.0.")
            print(f"🎉 Created new session for student '{uid}'.")
            
            # Interactive Holland explore prompt
            if interactive:
                print("\n💡 Detected new student profile. Do you want to run the Talent Exploration Test now? (yes/no)")
                choice = input("axis-skill> ").strip().lower()
                if choice == 'yes' or choice == 'y':
                    self.handle_explore()
        else:
            self.current_facts = self.load_facts(uid)
            # Ensure nested structure exists for old flat schema compatibility
            if "basic_info" not in self.current_facts:
                print("🔄 Converting old session schema to v3.0 nested schema...")
                old_facts = self.current_facts
                self.current_facts = {
                    "basic_info": {
                        "uid": old_facts.get("UID", uid),
                        "province": old_facts.get("Province", ""),
                        "track_type": old_facts.get("track_type", "夏季高考"),
                        "subjects": old_facts.get("Subject Combination", ""),
                        "score_details": {
                            "culture_score": int(old_facts.get("Score / Ranking", "0").replace("分", "").split("/")[0].strip()) if old_facts.get("Score / Ranking", "").replace("分", "").strip().isdigit() else 500,
                            "art_province_ranking": 0
                        }
                    },
                    "psychological_profile": {
                        "holland_code_inferred": old_facts.get("holland_code_inferred", []),
                        "core_driver": old_facts.get("Financial Expectation", ""),
                        "derived_strengths": old_facts.get("derived_strengths", []),
                        "blind_spots": old_facts.get("blind_spots", [])
                    },
                    "Target Majors": old_facts.get("Target Majors", [])
                }
                self.save_facts(uid, self.current_facts)
                
            print(f"📂 Loaded existing session for student '{uid}'.")
            
        self.print_status()

    def handle_explore(self):
        """Guided scenario quiz for Holland personality and Gallup driver."""
        if not self.current_uid:
            print("❌ Please initialize a student session first with `/init [uid]`.")
            return
            
        print("\n================ SCIENTIFIC TALENT ASSESSMENT ================")
        print("🎯 Q1: 测算霍兰德职业人格 (R/I/E 型冲突)")
        print("如果学校要举办一个新质生产力科技节，现在有三个志愿岗位，你直觉想去哪一个？")
        print("   A. 硬件整备组：拆解、维修无人机和智能硬件（R现实型：物理动手）")
        print("   B. 算法破解组：推演关卡逻辑、找代码漏洞（I研究型：数理逻辑）")
        print("   C. 资源招商组：谈判拉赞助、组织现场同学（E企业型 / S社会型：人际组织）")
        
        q1_ans = ""
        while q1_ans not in ['A', 'B', 'C']:
            q1_ans = input("Choose (A/B/C): ").strip().upper()
            
        print("\n🎯 Q2: 测算盖洛普优势与抗风险内驱力")
        print("假设 4 年后毕业时就业形势剧烈震荡，选择工作时你绝对不能妥协的底线是？")
        print("   A. 确定性的窄门（壁垒优先，如电网/特种行业，追求绝对安全感）")
        print("   B. 个人长板变现（高风险高回报，创意/代码/运营，拼搏拿高薪）")
        print("   C. 稳定的社会关系（环境优先，简单不内耗，追求生活平衡）")
        
        q2_ans = ""
        while q2_ans not in ['A', 'B', 'C']:
            q2_ans = input("Choose (A/B/C): ").strip().upper()
            
        # Run evaluator
        results = self.trait_evaluator.evaluate_traits(q1_ans, q2_ans)
        
        # Save to facts
        profile = self.current_facts["psychological_profile"]
        profile["holland_code_inferred"] = results["holland_code_inferred"]
        profile["core_driver"] = results["core_driver"]
        profile["derived_strengths"] = results["derived_strengths"]
        
        self.save_facts(self.current_uid, self.current_facts)
        self.log_timeline(self.current_uid, f"Completed talent assessment. Holland: {results['holland_code_inferred']}, Driver: {results['core_driver']}")
        
        print("\n✅ Assessment completed and saved!")
        print(f"   Holland Codes: {results['holland_code_inferred']}")
        print(f"   Core Driver: {results['core_driver']}")
        print(f"   Derived Strengths: {results['derived_strengths']}")
        print("==============================================================\n")
        
        step = self.get_profile_step(self.current_facts)
        print(f"[Current State: Profile Step {step}/4]")

    def print_status(self):
        """Print current profile status and fields under v3.0 nested structure."""
        if not self.current_uid:
            print("❌ No active student session. Run `/init [uid]` first.")
            return
            
        info = self.current_facts.get("basic_info", {})
        profile = self.current_facts.get("psychological_profile", {})
        
        print("\n================ STUDENT PROFILE STATUS (v3.0) ================")
        print(f"UID: {info.get('uid')}")
        print(f"Province (省份): {info.get('province') or '[Missing]'}")
        print(f"Track Type (填报赛道): {info.get('track_type') or '[Missing]'}")
        print(f"Culture Score (文化分): {info.get('score_details', {}).get('culture_score') or '[Missing]'}")
        print(f"Art Rank (艺术省排名): {info.get('score_details', {}).get('art_province_ranking') or '[Missing]'}")
        print(f"Subjects (选科): {info.get('subjects') or '[Missing]'}")
        if info.get("province") and info.get("track_type") and info.get("score_details", {}).get("culture_score"):
            status = self.evaluator.get_batch_lines_status(self.current_facts)
            print(f"Province Control Lines (省控线对比): {status}")
        print(f"Holland Code (霍兰德人格): {profile.get('holland_code_inferred') or '[Missing]'}")
        print(f"Core Driver (核心求职驱力): {profile.get('core_driver') or '[Missing]'}")
        print(f"Strengths (长板优势): {profile.get('derived_strengths') or '[]'}")
        print(f"Target Majors (目标专业): {self.current_facts.get('Target Majors', [])}")
        
        step = self.get_profile_step(self.current_facts)
        print(f"Profile Completion: Step {step}/4")
        print("================================================================\n")
        
        print(f"[Current State: Profile Step {step}/4]")

    def handle_set(self, args_str):
        """Set specific profile fields in v3.0 nested facts.json."""
        if not self.current_uid:
            print("❌ Please initialize a student session first with `/init [uid]`.")
            return
            
        parts = args_str.split(' ', 1)
        if len(parts) < 2:
            print("❌ Invalid set command. Format: `/set [key] [value]`")
            print("Valid keys: `province`, `track`, `score`, `art_rank`, `subjects`, `holland_code`, `core_driver`")
            return
            
        key, value = parts[0].strip().lower(), parts[1].strip()
        info = self.current_facts["basic_info"]
        
        old_val = ""
        is_critical = False
        
        if key == "province":
            old_val = info.get("province", "")
            info["province"] = value
            is_critical = True
            # Guangdong spring gaokao routing alert
            if value == "广东" or value.lower() == "guangdong":
                print("💡 [Guangdong detected] Triggering Spring Gaokao / 夏季 Gaokao routing alert.")
        elif key == "track":
            old_val = info.get("track_type", "")
            info["track_type"] = value
            is_critical = True
        elif key == "score":
            old_val = str(info["score_details"].get("culture_score", ""))
            info["score_details"]["culture_score"] = int(value) if value.isdigit() else 0
        elif key == "art_rank":
            old_val = str(info["score_details"].get("art_province_ranking", ""))
            info["score_details"]["art_province_ranking"] = int(value) if value.isdigit() else 0
            is_critical = True
        elif key == "subjects":
            old_val = info.get("subjects", "")
            info["subjects"] = value
            is_critical = True
        elif key in ["holland_code", "holland"]:
            profile = self.current_facts["psychological_profile"]
            old_val = ",".join(profile.get("holland_code_inferred", []))
            profile["holland_code_inferred"] = [x.strip().upper() for x in value.split(",") if x.strip()]
        elif key in ["core_driver", "driver"]:
            profile = self.current_facts["psychological_profile"]
            old_val = profile.get("core_driver", "")
            profile["core_driver"] = value
        else:
            print(f"❌ Unknown key '{key}'. Valid keys: `province`, `track`, `score`, `art_rank`, `subjects`, `holland_code`, `core_driver`")
            return
            
        if old_val != value:
            self.log_timeline(self.current_uid, f"Field '{key}' updated from '{old_val}' to '{value}'")
            
            # State Guard rule: If changing critical facts, reset targets and log
            if is_critical:
                self.current_facts["Target Majors"] = []
                self.update_blind_spots(self.current_uid, f"# sanage Axis - Targets Paradoxes\n\nState Reset: Critical fact '{key}' was updated. Targets cleared to prevent hallucinations.\n")
                self.log_timeline(self.current_uid, f"Critical state change. Target major pool cleared.")
                print(f"⚠️ Critical field changed. Target Majors list cleared to prevent mismatch.")
                
            self.save_facts(self.current_uid, self.current_facts)
            
        step = self.get_profile_step(self.current_facts)
        print(f"✅ Set '{key}' to '{value}'.")
        print(f"[Current State: Profile Step {step}/4]")

    def handle_add_major(self, major_name):
        """Add a major to candidate's list."""
        if not self.current_uid:
            print("❌ Please initialize a student session first with `/init [uid]`.")
            return
            
        major_name = major_name.strip()
        if not major_name:
            print("❌ Please specify a major name.")
            return
            
        if major_name not in self.current_facts["Target Majors"]:
            self.current_facts["Target Majors"].append(major_name)
            self.save_facts(self.current_uid, self.current_facts)
            self.log_timeline(self.current_uid, f"Added major target: '{major_name}'")
            print(f"✅ Added '{major_name}' to candidate target majors.")
        else:
            print(f"ℹ️ '{major_name}' is already in target majors.")
            
        step = self.get_profile_step(self.current_facts)
        print(f"[Current State: Profile Step {step}/4]")

    def handle_veto(self):
        """Run veto officer check with Adversarial Review."""
        if not self.current_uid:
            print("❌ Please initialize a student session first with `/init [uid]`.")
            return
            
        step = self.get_profile_step(self.current_facts)
        if step < 4:
            print(f"⚠️ Profile is not complete (Step {step}/4). Please fill all fields or run `/explore` first.")
            return
            
        print("\n🛡️ [Veto Officer] Running Adversarial Review v3.0 checks...")
        
        target_majors = self.current_facts.get("Target Majors", [])
        if not target_majors:
            print("❌ Target majors list is empty. Add majors using `/add_major [major]`.")
            return
            
        # Adversarial Monologue Simulation
        print("\n[Thought (Internal Monologue - CoT)]:")
        print("  1. 反思梦想: 审查专业在2026年是属于考生的文人情怀还是生存理智。")
        print("  2. 查杀风险: 比对撤销专业及AI替代率。")
        print("  3. 折中对冲: 拒绝低水平跟风，推演1+X对冲路径。")
        
        has_vetoes = False
        veto_content = "# Veto Officer Risk Log (Adversarial Review)\n\n"
        
        info = self.current_facts["basic_info"]
        track = info.get("track_type", "夏季高考")
        
        # Trigger specific debate dialogs on console
        if "广东春考" in track:
            print("\n🗣️ [Adversarial Debate dialog]:")
            print("   * Veto Officer: \"春考专科阶段绝对不能报纯白领流水线岗位（如会计/市场营销/英语），AI替代率高且招聘大盘趋近归零！\"")
            print("   * Audit Officer: \"同意。去专科必须读物理世界无法被AI闭环的硬手艺。全面转向大湾区实体产业专科。\"")
        elif "艺术" in track or "艺考" in track:
            print("\n🗣️ [Adversarial Debate dialog]:")
            print("   * Veto Officer: \"AI绘画与大模型对设计插画等岗位的蚕食率已达80%。绝不能报纯美术和普通视觉传达！\"")
            print("   * Audit Officer: \"赞同。必须强制推向1+X复合赛道（如数字媒体艺术/工业设计），并强制选修交互算法和数据可视化。\"")
            
        for major in target_majors:
            res = self.evaluator.evaluate_major(major, self.current_facts)
            if res['is_vetoed']:
                has_vetoes = True
                print(f"\n🚨 **VETO WARNING: {major}**")
                for reason in res['veto_reasons']:
                    print(f"   - {reason}")
                veto_content += f"## ❌ Vetoed: {major}\n"
                for reason in res['veto_reasons']:
                    veto_content += f"- {reason}\n"
            else:
                print(f"\n✅ Approved: {major}")
                print(f"   - AI Replacement Risk: {int(res['ai_replacement_index']*100)}%")
                
        self.log_timeline(self.current_uid, f"Executed Risk Veto Officer checks. Has vetoes: {has_vetoes}")
        
        # Write to blind spots if vetoes occurred
        if has_vetoes:
            self.update_blind_spots(self.current_uid, f"# sanage Axis - Veto Officer Flagged Mismatches\n\n{veto_content}")
            
        print("\n[Current State: Veto Audited]")

    def handle_audit(self):
        """Run audit officer check (payback period and city preference rules)."""
        if not self.current_uid:
            print("❌ Please initialize a student session first with `/init [uid]`.")
            return
            
        step = self.get_profile_step(self.current_facts)
        if step < 4:
            print(f"⚠️ Profile is not complete (Step {step}/4). Please fill all fields or run `/explore` first.")
            return
            
        print("\n⚖️ [Survival Audit Officer] Auditing payback period and city priority rules...")
        
        target_majors = self.current_facts.get("Target Majors", [])
        if not target_majors:
            print("❌ Target majors list is empty. Add majors using `/add_major [major]`.")
            return
            
        audit_log = "# Survival Audit Officer Report (v3.0)\n\n"
        
        for major in target_majors:
            res = self.evaluator.evaluate_major(major, self.current_facts)
            print(f"\n📊 **Major: {major}**")
            print(f"   - Survival Score: {res['survival_score']}/100")
            print(f"   - Suitability Match Score: {res['fit_score']}/100")
            
            audit_log += f"## Major: {major} | Survival Score: {res['survival_score']}/100\n"
            
            if res['match_reasons']:
                print("   - Audit Insights:")
                for reason in res['match_reasons']:
                    print(f"     * {reason}")
                    audit_log += f"- {reason}\n"
            else:
                print("   - No special constraints or warnings triggered.")
                audit_log += "- No special warnings.\n"
                
        self.log_timeline(self.current_uid, "Executed Survival Audit Officer checks v3.0.")
        print("\n[Current State: Survival Audited]")

    def handle_export(self):
        """Export the final survival action list under v3.0 template."""
        if not self.current_uid:
            print("❌ Please initialize a student session first with `/init [uid]`.")
            return
            
        step = self.get_profile_step(self.current_facts)
        if step < 4:
            print(f"⚠️ Profile is not complete (Step {step}/4). Cannot export final recommendations.")
            return
            
        print("\n📦 Generating '1+X' future survival report...")
        snapshots_dir = os.path.join(self.sessions_dir, self.current_uid, 'snapshots')
        report = self.generator.generate_report(self.current_facts, snapshots_dir=snapshots_dir)
        
        # Save to file
        report_path = os.path.join(self.sessions_dir, self.current_uid, 'survival_report.md')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
            
        self.log_timeline(self.current_uid, "Generated and exported final 1+X Survival Report v3.0.")
        
        print(f"✅ Report saved to: {report_path}")
        print("\n" + "="*60)
        print(report)
        print("="*60 + "\n")
        print("[Current State: Export Ready]")

    def handle_save(self, title):
        """Save candidate facts and state to a snapshot."""
        if not self.current_uid:
            print("❌ Please initialize a student session first with `/init [uid]`.")
            return
            
        import re
        title_clean = title.strip()
        title_slug = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5]+', '-', title_clean).strip('-')
        if not title_slug:
            title_slug = "untitled"
            
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        filename = f"{timestamp}-{title_slug}.md"
        
        snapshots_dir = os.path.join(self.sessions_dir, self.current_uid, 'snapshots')
        os.makedirs(snapshots_dir, exist_ok=True)
        
        filepath = os.path.join(snapshots_dir, filename)
        
        info = self.current_facts.get("basic_info", {})
        profile = self.current_facts.get("psychological_profile", {})
        target_majors = self.current_facts.get("Target Majors", [])
        
        iso_timestamp = datetime.now().astimezone().isoformat(timespec='seconds')
        step = self.get_profile_step(self.current_facts)
        stage = f"Profile Step {step}/4"
        if step == 4:
            stage = "Profile Complete"
            
        # Serialize YAML frontmatter
        yaml_lines = [
            "---",
            f"uid: {self.current_uid}",
            f"timestamp: '{iso_timestamp}'",
            f"title: '{title_clean}'",
            f"province: '{info.get('province', '')}'",
            f"track: '{info.get('track_type', '')}'",
            f"score: {info.get('score_details', {}).get('culture_score', 0)}",
            f"art_rank: {info.get('score_details', {}).get('art_province_ranking', 0)}",
            f"subjects: '{info.get('subjects', '')}'",
            f"holland_code: {json.dumps(profile.get('holland_code_inferred', []), ensure_ascii=False)}",
            f"core_driver: '{profile.get('core_driver', '')}'",
            f"stage: '{stage}'",
            "---"
        ]
        
        # Body sections
        body_lines = [
            f"# Snapshot: {title_clean}",
            "",
            "## 目标专业候选池",
            ""
        ]
        for major in target_majors:
            body_lines.append(f"- {major}")
        if not target_majors:
            body_lines.append("- （暂无）")
            
        body_lines.extend([
            "",
            "## 备注",
            "",
            f"This snapshot was automatically saved on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
        ])
        
        content = "\n".join(yaml_lines) + "\n\n" + "\n".join(body_lines)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
        self.log_timeline(self.current_uid, f"Saved snapshot: '{filename}' with title '{title_clean}'")
        
        # Count snapshots
        snapshot_files = [f for f in os.listdir(snapshots_dir) if f.endswith('.md')]
        print(f"已存档：workspace/sessions/{self.current_uid}/snapshots/{filename}")
        print(f"当前项目下共 {len(snapshot_files)} 份存档。")

    def handle_restore(self, arg=""):
        """Restore candidate details and target majors from a snapshot."""
        if not self.current_uid:
            print("❌ Please initialize a student session first with `/init [uid]`.")
            return
            
        snapshots_dir = os.path.join(self.sessions_dir, self.current_uid, 'snapshots')
        if not os.path.exists(snapshots_dir):
            print(f"❌ '{self.current_uid}' has no saved snapshots. Save one using `/save [title]`.")
            return
            
        snapshot_files = sorted([f for f in os.listdir(snapshots_dir) if f.endswith('.md')])
        if not snapshot_files:
            print(f"❌ '{self.current_uid}' has no saved snapshots. Save one using `/save [title]`.")
            return
            
        target_file = None
        if not arg:
            # Load latest
            target_file = snapshot_files[-1]
        else:
            arg_str = arg.strip()
            if arg_str.isdigit():
                idx = int(arg_str) - 1
                if 0 <= idx < len(snapshot_files):
                    target_file = snapshot_files[idx]
                else:
                    print(f"❌ Invalid snapshot index. '{self.current_uid}' has {len(snapshot_files)} snapshots.")
                    return
            else:
                # Match by title or file name
                for f in snapshot_files:
                    if arg_str in f:
                        target_file = f
                        break
                if not target_file:
                    print(f"❌ Could not find snapshot matching '{arg_str}'.")
                    return
                    
        filepath = os.path.join(snapshots_dir, target_file)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        frontmatter, body = parse_markdown_with_frontmatter(content)
        
        # Restore basic info
        info = self.current_facts["basic_info"]
        info["province"] = frontmatter.get("province", "")
        info["track_type"] = frontmatter.get("track", "")
        info["subjects"] = frontmatter.get("subjects", "")
        if "score" in frontmatter:
            info["score_details"]["culture_score"] = int(frontmatter["score"])
        if "art_rank" in frontmatter:
            info["score_details"]["art_province_ranking"] = int(frontmatter["art_rank"])
            
        # Restore psychological profile
        profile = self.current_facts["psychological_profile"]
        profile["holland_code_inferred"] = frontmatter.get("holland_code", [])
        profile["core_driver"] = frontmatter.get("core_driver", "")
        
        # Parse target majors from body
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
                        
        self.current_facts["Target Majors"] = target_majors
        self.save_facts(self.current_uid, self.current_facts)
        
        self.log_timeline(self.current_uid, f"Restored state from snapshot: '{target_file}'")
        print(f"✅ Restored state from snapshot: {target_file}")
        self.print_status()

    def handle_list(self):
        """List active snapshots and candidate folders."""
        print("\n================ AVAILABLE SESSIONS & SNAPSHOTS ================")
        if self.current_uid:
            print(f"Active Candidate: {self.current_uid}")
            snapshots_dir = os.path.join(self.sessions_dir, self.current_uid, 'snapshots')
            if os.path.exists(snapshots_dir):
                snapshot_files = sorted([f for f in os.listdir(snapshots_dir) if f.endswith('.md')])
                if snapshot_files:
                    print("Snapshots:")
                    for idx, filename in enumerate(snapshot_files, 1):
                        filepath = os.path.join(snapshots_dir, filename)
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        fm, _ = parse_markdown_with_frontmatter(content)
                        title = fm.get("title", filename)
                        timestamp = filename[:15]
                        if len(timestamp) == 15 and timestamp[8] == '-':
                            formatted_ts = f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]} {timestamp[9:11]}:{timestamp[11:13]}"
                        else:
                            formatted_ts = timestamp
                        stage = fm.get("stage", "Unknown")
                        print(f"  {idx}. {formatted_ts} · {title} · {stage}")
                else:
                    print("Snapshots: (No snapshots found. Save with `/save [title]`)")
            else:
                print("Snapshots: (No snapshots folder found)")
        else:
            print("Active Candidate: [None] (Run `/init [uid]` to select/create a candidate)")
            
        if os.path.exists(self.sessions_dir):
            candidates = sorted([d for d in os.listdir(self.sessions_dir) if os.path.isdir(os.path.join(self.sessions_dir, d))])
            other_candidates = [c for c in candidates if c != self.current_uid]
            if other_candidates:
                print("\nOther Candidates:")
                for c in other_candidates:
                    print(f"  - {c}")
            else:
                if not self.current_uid:
                    print("\nNo candidate sessions found.")
        print("================================================================\n")

    def handle_report(self):
        """Compile reports from active candidate snapshots."""
        self.handle_export()

    def print_help(self):
        print("""
🌟 sanage Axis v3.0 - Command Menu 🌟
--------------------------------------
/init [uid]        - Start or load session for a candidate
/set [key] [val]   - Set profile value. Keys:
                      * province (省份, e.g. 广东)
                      * track (赛道, e.g. 广东春考, 夏季高考, 艺术类)
                      * score (文化分, e.g. 520)
                      * art_rank (艺术省排, e.g. 1200)
                      * subjects (选科, e.g. 物理,化学,生物)
/explore           - Run the Holland & Gallup Talent Exploration Test
/add_major [major] - Add major to candidate's target selection list
/status            - Check current profile completeness and state
/veto              - Run Risk Veto check (checks Adversarial Review v3.0)
/audit             - Run Survival Audit (checks payback period & city priorities)
/save [title]      - Save current profile state to a snapshot
/restore [arg]     - Restore profile state from snapshot (by index or title)
/list              - List all snapshots and candidate sessions
/report            - Compile snapshots and generate final cumulative report
/export            - Compile and export the final '1+X' action plan
/help              - Show this help menu
/exit              - Exit the application
""")

    def execute_command(self, cmd_line, interactive=True):
        """Execute a single command line string."""
        cmd_line = cmd_line.strip()
        if not cmd_line:
            return
            
        if cmd_line.startswith("/init"):
            parts = cmd_line.split(' ', 1)
            if len(parts) < 2:
                print("❌ Usage: /init [uid]")
                return
            self.handle_init(parts[1].strip(), interactive=interactive)
        elif cmd_line.startswith("/set"):
            parts = cmd_line.split(' ', 1)
            if len(parts) < 2:
                print("❌ Usage: /set [key] [value]")
                return
            self.handle_set(parts[1].strip())
        elif cmd_line.startswith("/add_major"):
            parts = cmd_line.split(' ', 1)
            if len(parts) < 2:
                print("❌ Usage: /add_major [major_name]")
                return
            self.handle_add_major(parts[1].strip())
        elif cmd_line == "/explore":
            if not interactive:
                print("❌ Cannot run talent assessment quiz non-interactively.")
                return
            self.handle_explore()
        elif cmd_line == "/status":
            self.print_status()
        elif cmd_line == "/veto":
            self.handle_veto()
        elif cmd_line == "/audit":
            self.handle_audit()
        elif cmd_line.startswith("/save"):
            parts = cmd_line.split(' ', 1)
            title = parts[1].strip() if len(parts) >= 2 else "counseling milestone"
            self.handle_save(title)
        elif cmd_line.startswith("/restore"):
            parts = cmd_line.split(' ', 1)
            arg = parts[1].strip() if len(parts) >= 2 else ""
            self.handle_restore(arg)
        elif cmd_line == "/list":
            self.handle_list()
        elif cmd_line == "/report":
            self.handle_report()
        elif cmd_line == "/export":
            self.handle_export()
        elif cmd_line == "/help":
            self.print_help()
        else:
            print(f"❌ Unknown command: {cmd_line}. Type `/help` for options.")

    def start_loop(self):
        print("⚡ Welcome to sanage Axis v3.0 - Agent-Driven Major Selector ⚡")
        self.print_help()
        
        while True:
            try:
                cmd_line = input("axis-skill> ").strip()
                if not cmd_line:
                    continue
                
                if cmd_line == "/exit":
                    print("Goodbye!")
                    break
                self.execute_command(cmd_line, interactive=True)
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"⚠️ Error: {e}")

if __name__ == '__main__':
    runner = AxisRunner()
    if len(sys.argv) > 1:
        if sys.argv[1] == '--test-mode':
            # Simulated run for Guangdong Spring Exam
            print("\n--- Running Simulation 1: Guangdong Spring Exam ---")
            runner.handle_init('test_spring_student', interactive=False)
            runner.handle_set('province 广东')
            runner.handle_set('track 广东春考')
            runner.handle_set('score 380')
            runner.handle_set('subjects 物理,化学,生物')
            # Simulate Q1='A' (Hardware), Q2='A' (Stability/Barriers)
            results = runner.trait_evaluator.evaluate_traits('A', 'A')
            profile = runner.current_facts["psychological_profile"]
            profile["holland_code_inferred"] = results["holland_code_inferred"]
            profile["core_driver"] = results["core_driver"]
            profile["derived_strengths"] = results["derived_strengths"]
            runner.save_facts(runner.current_uid, runner.current_facts)
            
            runner.handle_add_major('智能控制技术')
            runner.handle_add_major('大数据与会计')
            runner.handle_veto()
            runner.handle_audit()
            runner.handle_export()

            # Simulated run for Art Exam
            print("\n--- Running Simulation 2: Art/Design Exam ---")
            runner.handle_init('test_art_student', interactive=False)
            runner.handle_set('province 广东')
            runner.handle_set('track 艺术类')
            runner.handle_set('score 450')
            runner.handle_set('art_rank 800')
            runner.handle_set('subjects 历史,地理,生物')
            # Simulate Q1='C' (Interpersonal/Creative), Q2='B' (High risk/return)
            results2 = runner.trait_evaluator.evaluate_traits('C', 'B', '我喜欢画画、动漫与界面设计')
            profile2 = runner.current_facts["psychological_profile"]
            profile2["holland_code_inferred"] = results2["holland_code_inferred"]
            profile2["core_driver"] = results2["core_driver"]
            profile2["derived_strengths"] = results2["derived_strengths"]
            runner.save_facts(runner.current_uid, runner.current_facts)
            
            runner.handle_add_major('数字媒体艺术')
            runner.handle_add_major('视觉传达设计')
            runner.handle_veto()
            runner.handle_audit()
            runner.handle_export()
        elif sys.argv[1].startswith('/'):
            # Single-shot command execution
            cmd_line = ' '.join(sys.argv[1:])
            runner.execute_command(cmd_line, interactive=False)
        else:
            print("❌ Invalid argument. Usage:")
            print("  python3 runner.py            (runs interactive shell)")
            print("  python3 runner.py /init [id] (runs a single command)")
    else:
        runner.start_loop()
