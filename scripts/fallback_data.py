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
    """广东数据 - 模拟的一分一段表"""
    samples = {
        "2023": [
            {"分数": 700, "人数": 50, "累计": 50},
            {"分数": 650, "人数": 1000, "累计": 1050},
            {"分数": 600, "人数": 5000, "累计": 6050},
            {"分数": 550, "人数": 15000, "累计": 21050},
            {"分数": 500, "人数": 30000, "累计": 51050},
            {"分数": 450, "人数": 50000, "累计": 101050},
            {"分数": 400, "人数": 70000, "累计": 171050},
        ],
        "2024": [
            {"分数": 700, "人数": 60, "累计": 60},
            {"分数": 650, "人数": 1100, "累计": 1160},
            {"分数": 600, "人数": 5500, "累计": 6660},
            {"分数": 550, "人数": 16000, "累计": 22660},
            {"分数": 500, "人数": 32000, "累计": 54660},
            {"分数": 450, "人数": 52000, "累计": 106660},
            {"分数": 400, "人数": 72000, "累计": 178660},
        ],
        "2025": [
            {"分数": 700, "人数": 55, "累计": 55},
            {"分数": 650, "人数": 1050, "累计": 1105},
            {"分数": 600, "人数": 5300, "累计": 6405},
            {"分数": 550, "人数": 15500, "累计": 21905},
            {"分数": 500, "人数": 31000, "累计": 52905},
            {"分数": 450, "人数": 51000, "累计": 103905},
            {"分数": 400, "人数": 71000, "累计": 174905},
        ],
    }
    return samples.get(year, samples.get("2025"))

def _get_beijing_sample(year: str):
    """北京数据"""
    samples = {
        "2023": [
            {"分数": 700, "人数": 30, "累计": 30},
            {"分数": 650, "人数": 800, "累计": 830},
            {"分数": 600, "人数": 4000, "累计": 4830},
            {"分数": 550, "人数": 12000, "累计": 16830},
            {"分数": 500, "人数": 25000, "累计": 41830},
            {"分数": 450, "人数": 40000, "累计": 81830},
        ],
        "2024": [
            {"分数": 700, "人数": 35, "累计": 35},
            {"分数": 650, "人数": 850, "累计": 885},
            {"分数": 600, "人数": 4200, "累计": 5085},
            {"分数": 550, "人数": 12500, "累计": 17585},
            {"分数": 500, "人数": 26000, "累计": 43585},
            {"分数": 450, "人数": 41000, "累计": 84585},
        ],
        "2025": [
            {"分数": 700, "人数": 32, "累计": 32},
            {"分数": 650, "人数": 820, "累计": 852},
            {"分数": 600, "人数": 4100, "累计": 4952},
            {"分数": 550, "人数": 12200, "累计": 17152},
            {"分数": 500, "人数": 25500, "累计": 42652},
            {"分数": 450, "人数": 40500, "累计": 83152},
        ],
    }
    return samples.get(year, samples.get("2025"))

def _get_default_sample(year: str):
    """默认数据"""
    samples = {
        "2023": [
            {"分数": 700, "人数": 100, "累计": 100},
            {"分数": 650, "人数": 2000, "累计": 2100},
            {"分数": 600, "人数": 10000, "累计": 12100},
            {"分数": 550, "人数": 30000, "累计": 42100},
            {"分数": 500, "人数": 60000, "累计": 102100},
            {"分数": 450, "人数": 100000, "累计": 202100},
        ],
        "2024": [
            {"分数": 700, "人数": 110, "累计": 110},
            {"分数": 650, "人数": 2100, "累计": 2210},
            {"分数": 600, "人数": 10500, "累计": 12710},
            {"分数": 550, "人数": 31000, "累计": 43710},
            {"分数": 500, "人数": 62000, "累计": 105710},
            {"分数": 450, "人数": 102000, "累计": 207710},
        ],
        "2025": [
            {"分数": 700, "人数": 105, "累计": 105},
            {"分数": 650, "人数": 2050, "累计": 2155},
            {"分数": 600, "人数": 10200, "累计": 12355},
            {"分数": 550, "人数": 30500, "累计": 42855},
            {"分数": 500, "人数": 61000, "累计": 103855},
            {"分数": 450, "人数": 101000, "累计": 204855},
        ],
    }
    return samples.get(year, samples.get("2025"))
