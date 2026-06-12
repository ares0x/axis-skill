import unittest
import unittest.mock

import os
import shutil
import json
from scripts.injector import KnowledgeInjector
from scripts.evaluator import MajorEvaluator, SanageAxisEvaluator
from scripts.trait_evaluator import TraitEvaluator
from scripts.output_generator import OutputGenerator
from runner import AxisRunner

class TestSanageAxis(unittest.TestCase):
    def setUp(self):
        self.injector = KnowledgeInjector()
        self.evaluator = MajorEvaluator()
        self.trait_evaluator = TraitEvaluator()
        self.generator = OutputGenerator()

    def test_injector_loading(self):
        self.assertTrue(len(self.injector.cancelled_majors) > 0)
        self.assertTrue(len(self.injector.added_majors) > 0)
        self.assertIn("“十五五”", self.injector.five_year_plan)
        self.assertIn("张雪峰", self.injector.expert_rules)

    def test_injector_matching(self):
        # Test cancelled check
        cancelled_res = self.injector.check_major_cancelled("土木工程", "Ordinary")
        self.assertIsNotNone(cancelled_res)
        name_key = 'MajorName' if 'MajorName' in cancelled_res else 'major_name'
        self.assertEqual(cancelled_res[name_key], '土木工程')

        # Test added check
        added_res = self.injector.check_major_added("人工智能")
        self.assertIsNotNone(added_res)
        name_key_added = 'MajorName' if 'MajorName' in added_res else 'major_name'
        self.assertIn("人工智能", added_res[name_key_added])

    def test_trait_evaluator(self):
        # Test Q1='B' (Investigative), Q2='A' (Barriers)
        res = self.trait_evaluator.evaluate_traits('B', 'A')
        self.assertIn("I", res["holland_code_inferred"])
        self.assertEqual(res["core_driver"], "壁垒优先")
        self.assertIn("数理逻辑与符号分析", res["derived_strengths"])

        # Test Q1='A' (Realistic), Q2='B' (High Risk/Return)
        res2 = self.trait_evaluator.evaluate_traits('A', 'B')
        self.assertIn("R", res2["holland_code_inferred"])
        self.assertEqual(res2["core_driver"], "高风险高回报")

    def test_evaluator_scoring(self):
        student_facts = {
            "basic_info": {
                "uid": "test_score",
                "province": "河南",
                "track_type": "夏季高考",
                "subjects": "物理, 化学, 生物",
                "score_details": {
                    "culture_score": 600,
                    "art_province_ranking": 0
                }
            },
            "psychological_profile": {
                "holland_code_inferred": ["I", "R"],
                "core_driver": "壁垒优先",
                "derived_strengths": ["数理逻辑"],
                "blind_spots": []
            }
        }
        
        # Test physics+chemistry constraint approved
        res_ee = self.evaluator.evaluate_major("电气工程及其自动化", student_facts)
        self.assertFalse(res_ee['is_vetoed'])
        self.assertTrue(res_ee['survival_score'] > 70)
        self.assertEqual(res_ee['fit_score'], 100)

        # Test physics+chemistry constraint vetoed (missing chemistry)
        bad_student = {
            "basic_info": {
                "uid": "test_bad",
                "province": "河南",
                "track_type": "夏季高考",
                "subjects": "物理, 地理, 生物",
                "score_details": {
                    "culture_score": 600
                }
            }
        }
        res_ee_bad = self.evaluator.evaluate_major("电气工程及其自动化", bad_student)
        self.assertTrue(res_ee_bad['is_vetoed'])
        self.assertIn("未选【物理+化学】科目", "".join(res_ee_bad['veto_reasons']))

        # Test 2026 Cancelled major veto
        res_accounting = self.evaluator.evaluate_major("大数据与会计", student_facts)
        self.assertTrue(res_accounting['is_vetoed'])
        self.assertIn("大模型财务助手", "".join(res_accounting['veto_reasons']))

    def test_sanage_axis_evaluator(self):
        user_data = {
            "basic_info": {
                "province": "广东",
                "track_type": "广东春考",
                "subjects": "物理,化学,历史"
            },
            "psychological_profile": {
                "holland_code_inferred": ["R", "C"],
                "core_driver": "壁垒优先"
            }
        }
        compat_eval = SanageAxisEvaluator(user_data=user_data)
        recommendations = compat_eval.evaluate_major_compatibility()
        self.assertTrue(len(recommendations) > 0)
        self.assertEqual(recommendations[0]['major'], "智能控制技术")

    def test_output_generator(self):
        student_facts = {
            "basic_info": {
                "uid": "test_gen",
                "province": "浙江",
                "track_type": "夏季高考",
                "subjects": "物理, 化学, 技术",
                "score_details": {
                    "culture_score": 650
                }
            },
            "psychological_profile": {
                "holland_code_inferred": ["I", "R"],
                "core_driver": "高风险高回报",
                "derived_strengths": ["数理逻辑"]
            },
            "Target Majors": ["人工智能", "软件工程"]
        }
        report = self.generator.generate_report(student_facts)
        self.assertIn("test_gen", report)
        self.assertIn("人工智能", report)
        self.assertIn("1+X", report)

    def test_runner_state_transitions(self):
        runner = AxisRunner()
        uid = "test_run_student_v3"
        session_path = os.path.join(runner.sessions_dir, uid)
        
        # Clean up if exists
        if os.path.exists(session_path):
            shutil.rmtree(session_path)
            
        runner.handle_init(uid, interactive=False)
        self.assertTrue(os.path.exists(session_path))
        self.assertTrue(os.path.exists(os.path.join(session_path, 'facts.json')))
        
        # Test initial step is 0 (new session has empty/missing gate 1 facts)
        step = runner.get_profile_step(runner.current_facts)
        self.assertEqual(step, 0)
        
        # Set basic details to complete Gate 1 (Step 1)
        runner.handle_set("province 河南")
        runner.handle_set("track 夏季高考")
        runner.handle_set("score 630")
        runner.handle_set("subjects 物理,化学,生物")
        
        step = runner.get_profile_step(runner.current_facts)
        self.assertEqual(step, 1)
        
        # Set career/body info to complete Gate 2 (Step 2)
        runner.handle_set("core_driver 壁垒优先")
        runner.handle_set("body_restriction 无")
        runner.handle_set("willing_special 否")
        runner.handle_set("priority 学校优先")
        
        step = runner.get_profile_step(runner.current_facts)
        self.assertEqual(step, 2)
        
        # Mock psychological profile/Holland code to complete Gate 3 (Step 3)
        runner.current_facts["psychological_profile"]["holland_code_inferred"] = ["I", "R"]
        runner.save_facts(uid, runner.current_facts)
        
        step = runner.get_profile_step(runner.current_facts)
        self.assertEqual(step, 3)
        
        # Clean up session
        if os.path.exists(session_path):
            shutil.rmtree(session_path)

    def test_runner_snapshots(self):
        runner = AxisRunner()
        uid = "test_snapshot_student"
        session_path = os.path.join(runner.sessions_dir, uid)
        
        if os.path.exists(session_path):
            shutil.rmtree(session_path)
            
        runner.handle_init(uid, interactive=False)
        runner.handle_set("province 浙江")
        runner.handle_set("track 夏季高考")
        runner.handle_set("score 610")
        runner.handle_set("subjects 物理,化学,技术")
        runner.handle_add_major("计算机科学与技术")
        
        # Save snapshot 1
        runner.handle_save("Initial Computer Science Selection")
        
        # Verify snapshot 1 exists
        snapshots_dir = os.path.join(session_path, 'snapshots')
        self.assertTrue(os.path.exists(snapshots_dir))
        snapshot_files = sorted([f for f in os.listdir(snapshots_dir) if f.endswith('.md')])
        self.assertEqual(len(snapshot_files), 1)
        
        # Sleep for a bit to ensure a different timestamp prefix (second resolution)
        import time
        time.sleep(1.1)
        
        # Change state
        runner.handle_add_major("智能制造工程")
        runner.handle_save("Added Smart Manufacturing")
        
        snapshot_files = sorted([f for f in os.listdir(snapshots_dir) if f.endswith('.md')])
        self.assertEqual(len(snapshot_files), 2)
        
        # Test listing
        runner.handle_list()
        
        # Modify current memory state and restore
        runner.current_facts["basic_info"]["province"] = "北京"
        runner.save_facts(uid, runner.current_facts)
        
        # Restore to snapshot 1 (index 1)
        runner.handle_restore("1")
        
        # Verify state is restored to Zhejiang
        self.assertEqual(runner.current_facts["basic_info"]["province"], "浙江")
        self.assertIn("计算机科学与技术", runner.current_facts["Target Majors"])
        
        # Restore to latest
        runner.handle_restore("")
        self.assertIn("智能制造工程", runner.current_facts["Target Majors"])
        
        # Test cumulative report contains evolution stages
        runner.current_facts["psychological_profile"]["holland_code_inferred"] = ["I", "R"]
        runner.current_facts["psychological_profile"]["core_driver"] = "高风险高回报"
        runner.current_facts["basic_info"]["priority_choice"] = "学校优先"
        runner.save_facts(uid, runner.current_facts)
        
        runner.handle_report()
        report_path = os.path.join(session_path, 'survival_report.md')
        self.assertTrue(os.path.exists(report_path))
        with open(report_path, 'r', encoding='utf-8') as f:
            report_content = f.read()
        self.assertIn("志愿偏好与决策演进过程", report_content)
        self.assertIn("Initial Computer Science Selection", report_content)
        self.assertIn("Added Smart Manufacturing", report_content)
        
        # Clean up
        if os.path.exists(session_path):
            shutil.rmtree(session_path)

    def test_gaokao_mapper(self):
        from scripts.gaokao_mapper import normalize_province, normalize_stream
        # 1. Test province normalization
        self.assertEqual(normalize_province("魔都"), "上海")
        self.assertEqual(normalize_province("广州"), "广东")
        self.assertEqual(normalize_province("深圳"), "广东")
        self.assertEqual(normalize_province("粤"), "广东")
        # 2. Test stream normalization
        # Guangdong is 3+1+2 in 2024: "理科" -> "物理"
        self.assertEqual(normalize_stream("广东", 2024, "理科"), "物理")
        # Shanghai is 3+3 in 2024: anything -> "综合"
        self.assertEqual(normalize_stream("上海", 2024, "物理"), "综合")
        # Sichuan was traditional in 2024: "物理" -> "理科"
        self.assertEqual(normalize_stream("四川", 2024, "物理"), "理科")

    @unittest.mock.patch('urllib.request.urlopen')
    def test_sogou_api_and_binary_search(self, mock_urlopen):
        import urllib.request
        from scripts.sogou_api import fetch_province_control_lines, fetch_score_range
        
        # Mock responses
        mock_control_json = {
            "status": 0,
            "message": "success",
            "data": {
                "地区分数线": [
                    {"录取批次": "本科批", "考生类别": "物理", "分数": "442", "分数查询年份": "2024", "分数线所属地区": "广东"}
                ]
            }
        }
        mock_range_json = {
            "status": 0,
            "message": "success",
            "data": {
                "score_range_res": [
                    {
                        "选科类别": "物理",
                        "查询分数线年份": "2024",
                        "适用地区": "广东",
                        "查询数据": [
                            {"返回的查询分数": "700", "同分人数": "10", "排名位次": "50"},
                            {"返回的查询分数": "600", "同分人数": "50", "排名位次": "200"},
                            {"返回的查询分数": "500", "同分人数": "100", "排名位次": "1000"}
                        ]
                    }
                ]
            }
        }
        
        class MockResponse:
            def __init__(self, json_data):
                self.json_data = json_data
            def read(self):
                return json.dumps(self.json_data).encode('utf-8')
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
        # Set side_effect to return MockResponse based on calls
        mock_urlopen.side_effect = [MockResponse(mock_control_json), MockResponse(mock_range_json), MockResponse(mock_range_json)]
        
        # Test Sogou API client
        control_lines = fetch_province_control_lines("广东", "2024", "物理")
        self.assertEqual(len(control_lines), 1)
        self.assertEqual(control_lines[0]["录取批次"], "本科批")
        
        # Test binary search rank lookup
        rank = self.evaluator.get_rank_from_score("广东", 2024, "物理", 600)
        self.assertEqual(rank, 200)
        
        # Test binary search score lookup
        score = self.evaluator.get_score_from_rank("广东", 2024, "物理", 200)
        self.assertEqual(score, 600)

    def test_output_generator_compliance(self):
        student_facts = {
            "basic_info": {
                "uid": "test_compliance",
                "province": "浙江",
                "track_type": "夏季高考",
                "subjects": "物理, 化学, 技术",
                "score_details": {
                    "culture_score": 650
                }
            },
            "psychological_profile": {
                "holland_code_inferred": ["I", "R"],
                "core_driver": "高风险高回报",
                "derived_strengths": ["数理逻辑"]
            },
            "Target Majors": ["人工智能", "软件工程"]
        }
        original_evaluate_major = self.generator.evaluator.evaluate_major
        def mock_evaluate(*args, **kwargs):
            res = original_evaluate_major(*args, **kwargs)
            res['match_reasons'].append("我们保证录取此专业。")
            return res
        self.generator.evaluator.evaluate_major = mock_evaluate
        
        report = self.generator.generate_report(student_facts)
        self.generator.evaluator.evaluate_major = original_evaluate_major
        
        # Check standard disclaimers
        self.assertIn("🚨 **【AI 辅助说明与免责声明】**", report)
        # Check dynamic link to Zhejiang Authority
        self.assertIn("[浙江省教育考试院](https://www.zjzs.net/)", report)
        # Check dynamic sources section
        self.assertIn("## 📅 数据来源与时效声明", report)
        # Check that "保证录取" was sanitized to "录取概率较大"
        self.assertIn("我们录取概率较大此专业", report)
        self.assertNotIn("保证录取", report)

    def test_runner_cli_and_set_profile(self):
        runner = AxisRunner()
        uid = "test_cli_runner_student"
        session_path = os.path.join(runner.sessions_dir, uid)
        
        if os.path.exists(session_path):
            shutil.rmtree(session_path)
            
        # 1. Test single-shot CLI command execution for init (interactive=False)
        runner.execute_command(f"/init {uid}", interactive=False)
        self.assertTrue(os.path.exists(session_path))
        self.assertEqual(runner.current_uid, uid)
        
        # 2. Test setting province, score, and subjects
        runner.execute_command("/set province 广东")
        runner.execute_command("/set score 600")
        runner.execute_command("/set subjects 物理,化学,生物")
        self.assertEqual(runner.current_facts["basic_info"]["province"], "广东")
        self.assertEqual(runner.current_facts["basic_info"]["score_details"]["culture_score"], 600)
        self.assertEqual(runner.current_facts["basic_info"]["subjects"], "物理,化学,生物")
        
        # 3. Test setting holland_code, core_driver, restrictions, and special paths
        runner.execute_command("/set holland_code E,S,C")
        runner.execute_command("/set core_driver 环境优先")
        runner.execute_command("/set body_restriction 无")
        runner.execute_command("/set willing_special 否")
        runner.execute_command("/set priority 学校优先")
        runner.execute_command("/set dislikes 土木,生化环材")
        
        profile = runner.current_facts["psychological_profile"]
        self.assertEqual(profile["holland_code_inferred"], ["E", "S", "C"])
        self.assertEqual(profile["core_driver"], "环境优先")
        self.assertEqual(runner.current_facts["basic_info"]["body_restriction"], "无")
        self.assertEqual(runner.current_facts["basic_info"]["willing_special"], "否")
        self.assertEqual(runner.current_facts["basic_info"]["priority_choice"], "学校优先")
        self.assertEqual(runner.current_facts["basic_info"]["dislikes"], ["土木", "生化环材"])
        
        # 4. Check step completion is Step 3 (all Gates complete)
        step = runner.get_profile_step(runner.current_facts)
        self.assertEqual(step, 3)
        
        # Clean up
        if os.path.exists(session_path):
            shutil.rmtree(session_path)

    def test_veto_and_special_policies(self):
        """Test physical restrictions, quick-payback VETOs, RCA mapping and special policies."""
        from scripts.evaluator import MajorEvaluator, SanageAxisEvaluator
        evaluator = MajorEvaluator()
        
        # Case A: Low income, needs quick income, chooses Clinical Medicine (should VETO)
        student_facts = {
            "basic_info": {
                "uid": "test_med_veto",
                "province": "广东",
                "track_type": "夏季高考",
                "subjects": "物理,化学,生物",
                "score_details": {
                    "culture_score": 615,
                    "rank": 14000
                },
                "body_restriction": "无",
                "willing_special": "是"
            },
            "psychological_profile": {
                "holland_code_inferred": ["I", "R"],
                "core_driver": "尽快有稳定收入"
            }
        }
        res_med = evaluator.evaluate_major("临床医学", student_facts)
        self.assertTrue(res_med["is_vetoed"])
        self.assertTrue(any("独立行医周期长达8年" in r for r in res_med["veto_reasons"]))
        
        # Case B: Color weakness "色弱", chooses Electrical Engineering (should VETO)
        student_facts["basic_info"]["body_restriction"] = "色弱"
        res_elec = evaluator.evaluate_major("电气工程及其自动化", student_facts)
        self.assertTrue(res_elec["is_vetoed"])
        self.assertTrue(any("色盲/色弱考生禁止报考" in r for r in res_elec["veto_reasons"]))

        # Case C: Holland RCA, should recommend Industrial Design & Digital Media
        student_facts["psychological_profile"]["holland_code_inferred"] = ["R", "C", "A"]
        compat_eval = SanageAxisEvaluator(user_data=student_facts)
        recommendations = compat_eval.evaluate_major_compatibility()
        rec_majors = [r["major"] for r in recommendations]
        self.assertIn("工业设计", rec_majors)
        self.assertIn("数字媒体技术", rec_majors)
        
        # Case D: Willing special is True + Quick income driver -> should suggest Police Academy/Public-funded
        student_facts["basic_info"]["willing_special"] = "是"
        student_facts["basic_info"]["body_restriction"] = "无"
        compat_eval = SanageAxisEvaluator(user_data=student_facts)
        recommendations2 = compat_eval.evaluate_major_compatibility()
        rec_majors2 = [r["major"] for r in recommendations2]
        self.assertIn("提前批公安警校", rec_majors2)
        self.assertIn("公费定向师范生 (提前批)", rec_majors2)
        self.assertIn("农村卫生定向 (临床/中医)", rec_majors2)

        # Case E: Dislikes filtering (VETO for civil engineering / chemistry)
        student_facts["basic_info"]["dislikes"] = ["土木", "生化环材"]
        res_civil = evaluator.evaluate_major("土木工程", student_facts)
        res_chem = evaluator.evaluate_major("应用化学", student_facts)
        self.assertTrue(res_civil["is_vetoed"])
        self.assertTrue(res_chem["is_vetoed"])
        self.assertTrue(any("匹配了您意向规避/排斥的专业关键词【土木】" in r for r in res_civil["veto_reasons"]))
        self.assertTrue(any("匹配了您意向规避/排斥的专业关键词【生化环材】" in r for r in res_chem["veto_reasons"]))

        # Case F: Priority recommendation injection
        student_facts["basic_info"]["priority_choice"] = "学校优先"
        compat_eval3 = SanageAxisEvaluator(user_data=student_facts)
        recommendations3 = compat_eval3.evaluate_major_compatibility()
        rec_majors3 = [r["major"] for r in recommendations3]
        self.assertIn("大类招生 (如工科/理科试验班)", rec_majors3)

        # Case G: Rank-based "垫" (Anchor) recommendation
        rank_rec = evaluator.get_recommendations_by_rank("浙江", 41842)
        self.assertIn("垫", rank_rec)

    def test_evaluator_config_loading_and_fallback(self):
        """Test MajorEvaluator loading from config, schema verification, and fallbacks."""
        import tempfile
        import shutil
        import json
        from unittest.mock import patch

        # Prepare a temp directory structure
        temp_dir = tempfile.mkdtemp()
        data_dir = os.path.join(temp_dir, "data")
        os.makedirs(data_dir, exist_ok=True)

        try:
            # 1. Test loading valid JSON
            valid_rules = {
                "ai_replacement_rates": {
                    "translation": 0.95,
                    "翻译": 0.95
                },
                "employment_stability": {
                    "clinical medicine": 0.90,
                    "临床医学": 0.90
                }
            }
            config_file = os.path.join(data_dir, "major_rules.json")
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(valid_rules, f)

            # We need to make sure 15th_five_year_plan.md and alpha_expert_rules.md also exist in data_dir
            # otherwise KnowledgeInjector will warn/be empty, which is fine since we check config path loading
            with open(os.path.join(data_dir, "15th_five_year_plan.md"), "w", encoding="utf-8") as f:
                f.write("- **人工智能**\n- **智能制造**")
            with open(os.path.join(data_dir, "alpha_expert_rules.md"), "w", encoding="utf-8") as f:
                f.write("")

            evaluator = MajorEvaluator(data_dir=data_dir)
            # Verify it loaded the json config successfully
            self.assertEqual(evaluator.ai_replacement_rates.get("translation"), 0.95)
            self.assertEqual(evaluator.employment_stability.get("clinical medicine"), 0.90)

            # 2. Test invalid schema bounds (AI rate > 1.0) -> should trigger fallback
            invalid_rules_bounds = {
                "ai_replacement_rates": {
                    "translation": 1.5,
                },
                "employment_stability": {
                    "clinical medicine": 0.90,
                }
            }
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(invalid_rules_bounds, f)

            evaluator = MajorEvaluator(data_dir=data_dir)
            # Should fallback to default in-code config (e.g. accounting, etc. exist)
            self.assertIn("accounting", evaluator.ai_replacement_rates)
            self.assertEqual(evaluator.ai_replacement_rates.get("translation"), 0.95)

            # 3. Test invalid schema structure (not a dict) -> should trigger fallback
            invalid_rules_struct = {
                "ai_replacement_rates": [0.95],
                "employment_stability": {
                    "clinical medicine": 0.90,
                }
            }
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(invalid_rules_struct, f)

            evaluator = MajorEvaluator(data_dir=data_dir)
            self.assertIn("accounting", evaluator.ai_replacement_rates)

            # 4. Test missing config file -> should trigger fallback
            os.remove(config_file)
            evaluator = MajorEvaluator(data_dir=data_dir)
            self.assertIn("accounting", evaluator.ai_replacement_rates)

        finally:
            shutil.rmtree(temp_dir)

    def test_sogou_api_caching_behavior(self):
        """Test API caching manager and read/write flow under temp CACHE_DIR."""
        import tempfile
        import shutil
        import json
        from unittest.mock import patch
        import scripts.sogou_api as sogou_api

        # Create a temp cache directory
        temp_cache_dir = tempfile.mkdtemp()
        original_cache_dir = sogou_api.CACHE_DIR
        sogou_api.CACHE_DIR = temp_cache_dir

        try:
            # Prepare mock JSON responses
            mock_control_json = {
                "status": 0,
                "message": "success",
                "data": {
                    "地区分数线": [
                        {"录取批次": "本科批", "考生类别": "物理", "分数": "450", "分数查询年份": "2024", "分数线所属地区": "广东"}
                    ]
                }
            }

            class MockResponse:
                def __init__(self, json_data):
                    self.json_data = json_data
                def read(self):
                    return json.dumps(self.json_data).encode('utf-8')
                def __enter__(self):
                    return self
                def __exit__(self, exc_type, exc_val, exc_tb):
                    pass

            # Mock urlopen
            with patch("urllib.request.urlopen", return_value=MockResponse(mock_control_json)) as mock_urlopen:
                # 1. First call (cache miss) -> should call API and write cache
                res1 = sogou_api.fetch_province_control_lines("广东", "2024", "物理")
                self.assertEqual(len(res1), 1)
                self.assertEqual(res1[0]["分数"], "450")
                self.assertTrue(mock_urlopen.called)

                # Reset mock to verify it doesn't get called on cache hit
                mock_urlopen.reset_mock()

                # 2. Second call (cache hit) -> should return cached data without calling urlopen
                res2 = sogou_api.fetch_province_control_lines("广东", "2024", "物理")
                self.assertEqual(len(res2), 1)
                self.assertEqual(res2[0]["分数"], "450")
                self.assertFalse(mock_urlopen.called)

        finally:
            sogou_api.CACHE_DIR = original_cache_dir
            shutil.rmtree(temp_cache_dir)

if __name__ == '__main__':
    unittest.main()

