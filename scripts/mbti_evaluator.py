#!/usr/bin/env python3
"""
MBTI (Myers-Briggs Type Indicator) 评估器
用于评估用户的性格类型、思维方式、决策模式
配合霍兰德测试使用，提供更全面的用户画像
"""

import json

class MBTIEvaluator:
    """MBTI 性格评估器"""
    
    # MBTI 四个维度的含义
    DIMENSIONS = {
        "EI": {
            "name": "能量来源",
            "E": "外向 (Extraversion): 从外界获取能量，喜欢社交",
            "I": "内向 (Introversion): 从内心获取能量，喜欢独处"
        },
        "SN": {
            "name": "感知方式",
            "S": "感觉 (Sensing): 关注事实和细节，务实",
            "N": "直觉 (Intuition): 关注模式和可能性，创新"
        },
        "TF": {
            "name": "决策方式",
            "T": "思考 (Thinking): 基于逻辑和分析做决策",
            "F": "情感 (Feeling): 基于价值观和人情做决策"
        },
        "JP": {
            "name": "生活方式",
            "J": "判断 (Judging): 有条理，喜欢计划",
            "P": "感知 (Perceiving): 灵活，喜欢随机应变"
        }
    }
    
    # MBTI 类型对应的描述
    TYPE_DESCRIPTIONS = {
        "INTJ": {"name": "建筑师", "traits": ["有远见", "独立思考", "创新", "完美主义"]},
        "INTP": {"name": "逻辑学家", "traits": ["好奇", "逻辑", "灵活", "创新"]},
        "ENTJ": {"name": "指挥官", "traits": ["领导力", "决断", "高效", "直接"]},
        "ENTP": {"name": "辩论家", "traits": ["机智", "创新", "适应", "好奇"]},
        "INFJ": {"name": "提倡者", "traits": ["理想主义", "创造力", "洞察力", "有原则"]},
        "INFP": {"name": "调停者", "traits": ["理想主义", "价值观", "创造性", "灵活"]},
        "ENFJ": {"name": "教育家", "traits": ["有魅力", "关怀", "利他", "善于沟通"]},
        "ENFP": {"name": "竞选者", "traits": ["热情", "创造性", "灵活", "社交"]},
        "ISTJ": {"name": "检查员", "traits": ["实际", "务实", "有条理", "可靠"]},
        "ISFJ": {"name": "后卫", "traits": ["关怀", "温暖", "尽职", "可靠"]},
        "ESTJ": {"name": "总经理", "traits": ["实际", "现实", "有条理", "直接"]},
        "ESFJ": {"name": "领事", "traits": ["社交", "关怀", "合作", "务实"]},
        "ISTP": {"name": "鉴赏家", "traits": ["实际", "灵活", "务实", "冷静"]},
        "ISFP": {"name": "探险家", "traits": ["审美", "敏感", "灵活", "温和"]},
        "ESTP": {"name": "企业家", "traits": ["灵活", "务实", "直接", "精力充沛"]},
        "ESFP": {"name": "表演者", "traits": ["热情", "乐观", "社交", "务实"]}
    }
    
    def __init__(self):
        self.scores = {"E": 0, "I": 0, "S": 0, "N": 0, "T": 0, "F": 0, "J": 0, "P": 0}
        self.responses = []
        
    def evaluate_dimension(self, ei_score=0, sn_score=0, tf_score=0, jp_score=0):
        """
        基于简洁问题评估 MBTI 维度
        
        Args:
            ei_score: E/I 分数 (正数偏E, 负数偏I)
            sn_score: S/N 分数 (正数偏S, 负数偏N)
            tf_score: T/F 分数 (正数偏T, 负数偏F)
            jp_score: J/P 分数 (正数偏J, 负数偏P)
        """
        # E/I 维度
        if ei_score > 0:
            self.scores["E"] += ei_score
        else:
            self.scores["I"] += abs(ei_score)
            
        # S/N 维度
        if sn_score > 0:
            self.scores["S"] += sn_score
        else:
            self.scores["N"] += abs(sn_score)
            
        # T/F 维度
        if tf_score > 0:
            self.scores["T"] += tf_score
        else:
            self.scores["F"] += abs(tf_score)
            
        # J/P 维度
        if jp_score > 0:
            self.scores["J"] += jp_score
        else:
            self.scores["P"] += abs(jp_score)
            
    def get_type(self):
        """获取 MBTI 类型"""
        mbti_type = ""
        
        # E/I
        mbti_type += "E" if self.scores["E"] > self.scores["I"] else "I"
        # S/N
        mbti_type += "S" if self.scores["S"] > self.scores["N"] else "N"
        # T/F
        mbti_type += "T" if self.scores["T"] > self.scores["F"] else "F"
        # J/P
        mbti_type += "J" if self.scores["J"] > self.scores["P"] else "P"
        
        return mbti_type
    
    def evaluate_from_simple_questions(self, answers):
        """
        从简洁问题（4-8个）评估 MBTI
        
        Args:
            answers: 问题答案 dict {q1: 'A', q2: 'B', ...}
        """
        # 重置分数
        self.scores = {"E": 0, "I": 0, "S": 0, "N": 0, "T": 0, "F": 0, "J": 0, "P": 0}
        
        # 问题 1: 能量来源 (E/I)
        # A: 聚会获得能量 | B: 独处获得能量
        if answers.get("q1") == "A":
            self.scores["E"] += 3
        elif answers.get("q1") == "B":
            self.scores["I"] += 3
            
        # 问题 2: 获取信息 (S/N)
        # A: 关注事实和细节 | B: 关注模式和可能性
        if answers.get("q2") == "A":
            self.scores["S"] += 3
        elif answers.get("q2") == "B":
            self.scores["N"] += 3
            
        # 问题 3: 决策方式 (T/F)
        # A: 基于逻辑分析 | B: 考虑人情和价值观
        if answers.get("q3") == "A":
            self.scores["T"] += 3
        elif answers.get("q3") == "B":
            self.scores["F"] += 3
            
        # 问题 4: 生活方式 (J/P)
        # A: 喜欢计划和条理 | B: 喜欢灵活和随机
        if answers.get("q4") == "A":
            self.scores["J"] += 3
        elif answers.get("q4") == "B":
            self.scores["P"] += 3
            
        return self.get_type()
    
    def get_type_description(self, mbti_type=None):
        """获取 MBTI 类型的详细描述"""
        if mbti_type is None:
            mbti_type = self.get_type()
            
        return self.TYPE_DESCRIPTIONS.get(mbti_type, {
            "name": mbti_type,
            "traits": ["平衡型", "适应性强"]
        })
    
    def get_dimension_summary(self):
        """获取四个维度的偏好总结"""
        summary = {}
        
        # E/I
        if self.scores["E"] > self.scores["I"]:
            summary["energy"] = {"type": "E", "name": "外向", "strength": self.scores["E"] - self.scores["I"]}
        else:
            summary["energy"] = {"type": "I", "name": "内向", "strength": self.scores["I"] - self.scores["E"]}
            
        # S/N
        if self.scores["S"] > self.scores["N"]:
            summary["perception"] = {"type": "S", "name": "感觉", "strength": self.scores["S"] - self.scores["N"]}
        else:
            summary["perception"] = {"type": "N", "name": "直觉", "strength": self.scores["N"] - self.scores["S"]}
            
        # T/F
        if self.scores["T"] > self.scores["F"]:
            summary["decision"] = {"type": "T", "name": "思考", "strength": self.scores["T"] - self.scores["F"]}
        else:
            summary["decision"] = {"type": "F", "name": "情感", "strength": self.scores["F"] - self.scores["T"]}
            
        # J/P
        if self.scores["J"] > self.scores["P"]:
            summary["lifestyle"] = {"type": "J", "name": "判断", "strength": self.scores["J"] - self.scores["P"]}
        else:
            summary["lifestyle"] = {"type": "P", "name": "感知", "strength": self.scores["P"] - self.scores["J"]}
            
        return summary

    def combine_with_holland(self, mbti_type, holland_code, core_driver):
        """
        结合 MBTI 和霍兰德测试结果，生成综合画像
        
        Args:
            mbti_type: MBTI 类型 (如 "INTJ")
            holland_code: 霍兰德代码 (如 ["I", "R"])
            core_driver: 核心驱动力 (如 "壁垒优先")
        
        Returns:
            综合画像 dict
        """
        mbti_info = self.get_type_description(mbti_type)
        
        # 结合 MBTI 和霍兰德，推荐适合的专业方向
        recommended_focus = []
        
        # 基于 MBTI 的推荐
        if mbti_type in ["INTJ", "INTP", "ENTJ", "ENTP"]:
            recommended_focus.append("科技创新与研发")
        if mbti_type in ["INFJ", "INFP", "ENFJ", "ENFP"]:
            recommended_focus.append("人文社科与创意")
        if mbti_type in ["ISTJ", "ISFJ", "ESTJ", "ESFJ"]:
            recommended_focus.append("稳定职业与管理")
        if mbti_type in ["ISTP", "ISFP", "ESTP", "ESFP"]:
            recommended_focus.append("实操技能与应用")
            
        # 基于霍兰德的推荐
        if "I" in holland_code:
            recommended_focus.append("研究与分析")
        if "R" in holland_code:
            recommended_focus.append("技术与实操")
        if "A" in holland_code:
            recommended_focus.append("艺术与创意")
        if "S" in holland_code:
            recommended_focus.append("服务与人交往")
        if "E" in holland_code:
            recommended_focus.append("管理与创业")
        if "C" in holland_code:
            recommended_focus.append("事务与数据处理")
        
        # 去重
        recommended_focus = list(set(recommended_focus))
        
        return {
            "mbti_type": mbti_type,
            "mbti_name": mbti_info["name"],
            "mbti_traits": mbti_info["traits"],
            "holland_code": holland_code,
            "core_driver": core_driver,
            "recommended_focus": recommended_focus,
            "dimension_summary": self.get_dimension_summary()
        }

if __name__ == '__main__':
    # 测试 MBTI 评估器
    evaluator = MBTIEvaluator()
    
    # 测试：典型的 INTJ 答案
    test_answers = {
        "q1": "B",  # 独处获得能量 (I)
        "q2": "B",  # 关注模式可能性 (N)
        "q3": "A",  # 基于逻辑分析 (T)
        "q4": "A"   # 喜欢计划条理 (J)
    }
    
    mbti_type = evaluator.evaluate_from_simple_questions(test_answers)
    print(f"MBTI 类型: {mbti_type}")
    print(f"类型名称: {evaluator.get_type_description()['name']}")
    print(f"性格特质: {evaluator.get_type_description()['traits']}")
    
    # 测试结合霍兰德
    holland_code = ["I", "R"]
    core_driver = "壁垒优先"
    combined = evaluator.combine_with_holland(mbti_type, holland_code, core_driver)
    print(f"\n综合画像:")
    print(f"推荐专业方向: {combined['recommended_focus']}")
