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
        
        # Test initial step is 1 (new session sets defaults but has 0 scores)
        step = runner.get_profile_step(runner.current_facts)
        self.assertEqual(step, 1)
        
        # Set basic details to complete Step 1 & 2
        runner.handle_set("province 河南")
        runner.handle_set("track 夏季高考")
        runner.handle_set("score 630")
        runner.handle_set("subjects 物理,化学,生物")
        
        step = runner.get_profile_step(runner.current_facts)
        self.assertEqual(step, 2)
        
        # Mock psychological profile to complete Step 3 & 4
        runner.current_facts["psychological_profile"]["holland_code_inferred"] = ["I", "R"]
        runner.current_facts["psychological_profile"]["core_driver"] = "壁垒优先"
        runner.save_facts(uid, runner.current_facts)
        
        step = runner.get_profile_step(runner.current_facts)
        self.assertEqual(step, 4)
        
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
        
        # 3. Test setting holland_code and core_driver
        runner.execute_command("/set holland_code E,S,C")
        runner.execute_command("/set core_driver 环境优先")
        
        profile = runner.current_facts["psychological_profile"]
        self.assertEqual(profile["holland_code_inferred"], ["E", "S", "C"])
        self.assertEqual(profile["core_driver"], "环境优先")
        
        # 4. Check step completion is Step 4
        step = runner.get_profile_step(runner.current_facts)
        self.assertEqual(step, 4)
        
        # Clean up
        if os.path.exists(session_path):
            shutil.rmtree(session_path)

if __name__ == '__main__':
    unittest.main()
