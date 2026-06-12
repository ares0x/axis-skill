#!/usr/bin/env python3
"""
本地 fallback 数据模块，当 API 不可用时使用本地数据
"""

import csv
import os
import sys
from collections import defaultdict

def get_fallback_dir():
    fallback_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    return os.path.abspath(fallback_dir)

def estimate_rank_from_score(score: int, max_score: int = 750) -> int:
    """
    根据分数估算位次（简化版 fallback）
    使用正态分布估算位次
    """
    if score >= max_score:
        return 1
    elif score <= 0:
        return 1000000

    normal_curve = {
        750: 1,
        700: 100,
        650: 1000,
        600: 5000,
        550: 20000,
        500: 50000,
        450: 100000,
        400: 200000,
        350: 350000,
        300: 500000,
    }
    
    sorted_scores = sorted(normal_curve.keys(), reverse=True)
    for i, s_score in enumerate(sorted_scores):
        if score >= s_score:
            if i == 0:
                return normal_curve[s_score]
            prev_score = sorted_scores[i-1]
            prev_rank = normal_curve[prev_score]
            curr_rank = normal_curve[s_score]
            ratio = (score - s_score) / (prev_score - s_score)
            return int(curr_rank + ratio * (prev_rank - curr_rank))
    
    return normal_curve[sorted_scores[-1]]

def get_fallback_province_control_lines(place: str, year: str, student: str = None):
    """
    本地 fallback 的省控线数据
    """
    fallback_dir = get_fallback_dir()
    csv_path = os.path.join(fallback_dir, "province_control_lines.csv")
    
    if not os.path.exists(csv_path):
        return []

    results = []
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["province"] == place and (year is None or str(row["year"]) == str(year)):
                    results.append({
                        "省份": row["province"],
                        "年份": row["year"],
                        "科类": row["track_type"],
                        "批次": row["batch_name"],
                        "分数线": row["control_score"]
                    })
    except Exception as e:
        print(f"[Fallback] 加载省控线数据失败: {e}", file=sys.stderr)
    
    return results

def get_fallback_score_range(place: str, year: str, classify: str = None):
    """
    本地 fallback 的分数位次数据
    当 API 不可用时使用简化估算
    """
    if place in ["广东", "广东省"]:
        return _get_guangdong_sample(year)
    elif place in ["北京", "北京市"]:
        return _get_beijing_sample(year)
    else:
        return _get_default_sample(year)

def _get_guangdong_sample(year: str):
    """广东数据 - 模拟的一分一段表 (键名匹配API格式)"""
    score_list = {
        "2023": [
            {"返回的查询分数": 700, "人数": 50, "排名位次": 50},
            {"返回的查询分数": 650, "人数": 1000, "排名位次": 1050},
            {"返回的查询分数": 600, "人数": 5000, "排名位次": 6050},
            {"返回的查询分数": 550, "人数": 15000, "排名位次": 21050},
            {"返回的查询分数": 500, "人数": 30000, "排名位次": 51050},
            {"返回的查询分数": 450, "人数": 50000, "排名位次": 101050},
            {"返回的查询分数": 400, "人数": 70000, "排名位次": 171050},
        ],
        "2024": [
            {"返回的查询分数": 700, "人数": 60, "排名位次": 60},
            {"返回的查询分数": 650, "人数": 1100, "排名位次": 1160},
            {"返回的查询分数": 600, "人数": 5500, "排名位次": 6660},
            {"返回的查询分数": 550, "人数": 16000, "排名位次": 22660},
            {"返回的查询分数": 500, "人数": 32000, "排名位次": 54660},
            {"返回的查询分数": 450, "人数": 52000, "排名位次": 106660},
            {"返回的查询分数": 400, "人数": 72000, "排名位次": 178660},
        ],
        "2025": [
            {"返回的查询分数": 700, "人数": 55, "排名位次": 55},
            {"返回的查询分数": 650, "人数": 1050, "排名位次": 1105},
            {"返回的查询分数": 600, "人数": 5300, "排名位次": 6405},
            {"返回的查询分数": 550, "人数": 15500, "排名位次": 21905},
            {"返回的查询分数": 500, "人数": 31000, "排名位次": 52905},
            {"返回的查询分数": 450, "人数": 51000, "排名位次": 103905},
            {"返回的查询分数": 400, "人数": 71000, "排名位次": 174905},
        ],
    }
    # 包装成API期望的格式：{"查询数据": [...]}
    return [{"查询数据": score_list.get(year, score_list.get("2025"))}]

def _get_beijing_sample(year: str):
    """北京数据 (键名匹配API格式)"""
    score_list = {
        "2023": [
            {"返回的查询分数": 700, "人数": 30, "排名位次": 30},
            {"返回的查询分数": 650, "人数": 800, "排名位次": 830},
            {"返回的查询分数": 600, "人数": 4000, "排名位次": 4830},
            {"返回的查询分数": 550, "人数": 12000, "排名位次": 16830},
            {"返回的查询分数": 500, "人数": 25000, "排名位次": 41830},
            {"返回的查询分数": 450, "人数": 40000, "排名位次": 81830},
        ],
        "2024": [
            {"返回的查询分数": 700, "人数": 35, "排名位次": 35},
            {"返回的查询分数": 650, "人数": 850, "排名位次": 885},
            {"返回的查询分数": 600, "人数": 4200, "排名位次": 5085},
            {"返回的查询分数": 550, "人数": 12500, "排名位次": 17585},
            {"返回的查询分数": 500, "人数": 26000, "排名位次": 43585},
            {"返回的查询分数": 450, "人数": 41000, "排名位次": 84585},
        ],
        "2025": [
            {"返回的查询分数": 700, "人数": 32, "排名位次": 32},
            {"返回的查询分数": 650, "人数": 820, "排名位次": 852},
            {"返回的查询分数": 600, "人数": 4100, "排名位次": 4952},
            {"返回的查询分数": 550, "人数": 12200, "排名位次": 17152},
            {"返回的查询分数": 500, "人数": 25500, "排名位次": 42652},
            {"返回的查询分数": 450, "人数": 40500, "排名位次": 83152},
        ],
    }
    return [{"查询数据": score_list.get(year, score_list.get("2025"))}]

def _get_default_sample(year: str):
    """默认数据 (键名匹配API格式)"""
    score_list = {
        "2023": [
            {"返回的查询分数": 700, "人数": 100, "排名位次": 100},
            {"返回的查询分数": 650, "人数": 2000, "排名位次": 2100},
            {"返回的查询分数": 600, "人数": 10000, "排名位次": 12100},
            {"返回的查询分数": 550, "人数": 30000, "排名位次": 42100},
            {"返回的查询分数": 500, "人数": 60000, "排名位次": 102100},
            {"返回的查询分数": 450, "人数": 100000, "排名位次": 202100},
        ],
        "2024": [
            {"返回的查询分数": 700, "人数": 110, "排名位次": 110},
            {"返回的查询分数": 650, "人数": 2100, "排名位次": 2210},
            {"返回的查询分数": 600, "人数": 10500, "排名位次": 12710},
            {"返回的查询分数": 550, "人数": 31000, "排名位次": 43710},
            {"返回的查询分数": 500, "人数": 62000, "排名位次": 105710},
            {"返回的查询分数": 450, "人数": 102000, "排名位次": 207710},
        ],
        "2025": [
            {"返回的查询分数": 700, "人数": 105, "排名位次": 105},
            {"返回的查询分数": 650, "人数": 2050, "排名位次": 2155},
            {"返回的查询分数": 600, "人数": 10200, "排名位次": 12355},
            {"返回的查询分数": 550, "人数": 30500, "排名位次": 42855},
            {"返回的查询分数": 500, "人数": 61000, "排名位次": 103855},
            {"返回的查询分数": 450, "人数": 101000, "排名位次": 204855},
        ],
    }
    return [{"查询数据": score_list.get(year, score_list.get("2025"))}]
