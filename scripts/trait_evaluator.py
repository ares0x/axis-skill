import json

class TraitEvaluator:
    def __init__(self):
        pass

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
