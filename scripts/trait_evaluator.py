import json

class TraitEvaluator:
    def __init__(self):
        pass

    def evaluate_8q(self, q1, q2, q3, q4, q5, q6, q7, q8_open="", driver_choice=None):
        """
        Score the full 8-question Holland quiz from profile/SKILL.md Gate 3.

        Question → dimension pair mapping:
          Q1: R vs I   Q2: A vs S   Q3: E vs C   Q4: R vs A
          Q5: I vs E   Q6: S vs C   Q7: R vs I   Q8: open-ended keyword scoring
        """
        scores = {"R": 0, "I": 0, "A": 0, "S": 0, "E": 0, "C": 0}
        derived_strengths = []

        # Q1 (R vs I)
        if q1.upper().strip() == 'A':
            scores['R'] += 3;  derived_strengths.append("物理交互与动手组装")
        elif q1.upper().strip() == 'B':
            scores['I'] += 3;  derived_strengths.append("数理逻辑与符号分析")

        # Q2 (A vs S)
        if q2.upper().strip() == 'A':
            scores['A'] += 3;  derived_strengths.append("视觉创意与艺术表达")
        elif q2.upper().strip() == 'B':
            scores['S'] += 3;  derived_strengths.append("人际沟通与资源协调")

        # Q3 (E vs C)
        if q3.upper().strip() == 'A':
            scores['E'] += 3;  derived_strengths.append("公众表达与说服领导")
        elif q3.upper().strip() == 'B':
            scores['C'] += 3;  derived_strengths.append("数据精确与流程规范")

        # Q4 (R vs A)
        if q4.upper().strip() == 'A':
            scores['R'] += 3
        elif q4.upper().strip() == 'B':
            scores['A'] += 3;  derived_strengths.append("视觉创意与艺术表达")

        # Q5 (I vs E)
        if q5.upper().strip() == 'A':
            scores['I'] += 3
        elif q5.upper().strip() == 'B':
            scores['E'] += 3;  derived_strengths.append("人际沟通与资源协调")

        # Q6 (S vs C)
        if q6.upper().strip() == 'A':
            scores['S'] += 3
        elif q6.upper().strip() == 'B':
            scores['C'] += 3;  derived_strengths.append("数据精确与流程规范")

        # Q7 (R vs I)
        if q7.upper().strip() == 'A':
            scores['R'] += 3
        elif q7.upper().strip() == 'B':
            scores['I'] += 3

        # Q8: keyword scoring on open-ended interest text
        if q8_open:
            q8_lower = q8_open.lower()
            if any(k in q8_lower for k in ["画", "艺术", "设计", "平面", "美", "art", "design", "音乐", "写作"]):
                scores['A'] += 2;  derived_strengths.append("视觉创意与艺术表达")
            if any(k in q8_lower for k in ["数", "逻辑", "代码", "编程", "math", "code", "算法"]):
                scores['I'] += 2;  derived_strengths.append("数理逻辑与符号分析")
            if any(k in q8_lower for k in ["拆", "修", "动手", "机械", "运动", "球"]):
                scores['R'] += 2;  derived_strengths.append("物理交互与动手组装")
            if any(k in q8_lower for k in ["聊天", "交朋友", "帮人", "教", "social"]):
                scores['S'] += 2;  derived_strengths.append("人际沟通与资源协调")
            if any(k in q8_lower for k in ["组织", "领导", "策划", "管理", "leader"]):
                scores['E'] += 2
            if any(k in q8_lower for k in ["整理", "计划", "规划", "记账", "秩序"]):
                scores['C'] += 2

        sorted_traits = sorted(scores, key=scores.get, reverse=True)
        if scores[sorted_traits[0]] == 0:
            holland_code = ["I", "R"]
        else:
            holland_code = sorted_traits[:2]

        core_driver = "普通期望"
        if driver_choice == "A":
            core_driver = "壁垒优先";  derived_strengths.append("风险规避与体系嵌入")
        elif driver_choice == "B":
            core_driver = "高风险高回报";  derived_strengths.append("核心技能溢价与拼搏倾向")
        elif driver_choice == "C":
            core_driver = "环境优先";  derived_strengths.append("和谐同理与生活平衡")

        return {
            "holland_code_inferred": holland_code,
            "core_driver": core_driver,
            "derived_strengths": list(set(derived_strengths))
        }

    def evaluate_traits(self, q1_choice, q2_choice, general_interests=""):
        """
        Evaluate user responses and return Holland Codes and Gallup core drivers.
        
        q1_choice: 'A' (Hardware), 'B' (Algorithms), 'C' (Resource/Business)
        q2_choice: 'A' (Barriers/Stability), 'B' (High risk/return), 'C' (Environment/Social)
        """
        scores = {"R": 0, "I": 0, "A": 0, "S": 0, "E": 0, "C": 0}
        derived_strengths = []
        
        # 1. Holland Code inference based on Q1
        q1_choice = q1_choice.upper().strip()
        if q1_choice == 'A':
            scores['R'] += 5  # Realistic: hardware/hands-on
            scores['C'] += 2  # Conventional: structured maintenance
            derived_strengths.append("物理交互与动手组装")
        elif q1_choice == 'B':
            scores['I'] += 5  # Investigative: math/logical analysis
            scores['A'] += 1  # Artistic: creative problem solving
            derived_strengths.append("数理逻辑与符号分析")
        elif q1_choice == 'C':
            scores['E'] += 4  # Enterprising: leadership/negotiation
            scores['S'] += 4  # Social: interpersonal connections
            derived_strengths.append("人际沟通与资源协调")
            
        # Parse general interests if any key phrases exist
        interests_lower = general_interests.lower()
        if any(x in interests_lower for x in ["画", "艺术", "设计", "平面", "美", "art", "design"]):
            scores['A'] += 3
            derived_strengths.append("视觉创意与艺术表达")
        if any(x in interests_lower for x in ["数", "逻辑", "代码", "编程", "math", "code"]):
            scores['I'] += 2
            derived_strengths.append("抽象符号思维")
        if any(x in interests_lower for x in ["拆", "修", "动手", "机械"]):
            scores['R'] += 2
            
        # Select top two traits as the Holland Code
        sorted_traits = sorted(scores, key=scores.get, reverse=True)
        # Handle cases where all scores are 0 by defaulting to I and R
        if scores[sorted_traits[0]] == 0:
            holland_code = ["I", "R"]
        else:
            holland_code = sorted_traits[:2]
            
        # 2. Core Driver inference based on Q2
        q2_choice = q2_choice.upper().strip()
        core_driver = "普通期望"
        if q2_choice == 'A':
            core_driver = "壁垒优先"
            derived_strengths.append("风险规避与体系嵌入")
        elif q2_choice == 'B':
            core_driver = "高风险高回报"
            derived_strengths.append("核心技能溢价与拼搏倾向")
        elif q2_choice == 'C':
            core_driver = "环境优先"
            derived_strengths.append("和谐同理与生活平衡")
            
        return {
            "holland_code_inferred": holland_code,
            "core_driver": core_driver,
            "derived_strengths": list(set(derived_strengths))
        }

if __name__ == '__main__':
    evaluator = TraitEvaluator()
    print("Test traits:", evaluator.evaluate_traits('B', 'A'))
