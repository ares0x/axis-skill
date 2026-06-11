import unittest
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

if __name__ == '__main__':
    unittest.main()
