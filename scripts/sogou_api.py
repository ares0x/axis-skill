#!/usr/bin/env python3
import json
import sys
import urllib.request
import urllib.parse
import urllib.error
import os
import hashlib

BASE_URL = "https://gaokao.search.qq.com/skills_data"
SOURCE = "open_tB0fU5wP"
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".cache")

# 导入 fallback 模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fallback_data import get_fallback_province_control_lines, get_fallback_score_range

def read_cache(prefix, **kwargs):
    """Read cached JSON file if it exists."""
    if not os.path.exists(CACHE_DIR):
        return None
    sorted_params = sorted(kwargs.items())
    param_str = urllib.parse.urlencode(sorted_params)
    param_hash = hashlib.md5(param_str.encode('utf-8')).hexdigest()
    cache_file = os.path.join(CACHE_DIR, f"{prefix}_{param_hash}.json")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return None

def write_cache(prefix, data, **kwargs):
    """Write data to local JSON cache file."""
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        sorted_params = sorted(kwargs.items())
        param_str = urllib.parse.urlencode(sorted_params)
        param_hash = hashlib.md5(param_str.encode('utf-8')).hexdigest()
        cache_file = os.path.join(CACHE_DIR, f"{prefix}_{param_hash}.json")
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def fetch_province_control_lines(place: str, year: str, student: str = None, retry_times: int = 2, use_fallback: bool = True) -> list:
    """
    Fetch province control lines (录取控制分数线) from the Sogou Gaokao API.
    API endpoint: type=province_score_line
    If API fails, uses local fallback data.
    """
    # Check cache first
    cached_val = read_cache("control_lines", place=place, year=year, student=student)
    if cached_val is not None:
        print(f"[SogouAPI] 使用缓存的省控线数据", file=sys.stderr)
        return cached_val

    url = f"{BASE_URL}?type=province_score_line&from={SOURCE}"
    if place:
        url += f"&place={urllib.parse.quote(place)}"
    if year:
        url += f"&year={urllib.parse.quote(year)}"
    if student:
        url += f"&student={urllib.parse.quote(student)}"

    print(f"[SogouAPI] Accessing control lines: {url}", file=sys.stderr)

    for attempt in range(retry_times):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = resp.read().decode("utf-8")
                result = json.loads(raw)
                if result.get("status") != 0:
                    print(f"[SogouAPI] Status error: {result.get('message')}", file=sys.stderr)
                    continue
                data = result.get("data", {})
                if not data:
                    continue
                res_list = data.get("地区分数线", [])
                if res_list:
                    write_cache("control_lines", res_list, place=place, year=year, student=student)
                return res_list
        except urllib.error.URLError as e:
            print(f"[SogouAPI] Network error (attempt {attempt+1}): {e}", file=sys.stderr)
        except json.JSONDecodeError as e:
            print(f"[SogouAPI] JSON parsing error (attempt {attempt+1}): {e}", file=sys.stderr)
        except Exception as e:
            print(f"[SogouAPI] Unexpected error (attempt {attempt+1}): {e}", file=sys.stderr)

    # API 失败，使用 fallback
    if use_fallback:
        print(f"[SogouAPI] API 不可用，使用本地 fallback 省控线数据", file=sys.stderr)
        fallback_data = get_fallback_province_control_lines(place, year, student)
        if fallback_data:
            write_cache("control_lines", fallback_data, place=place, year=year, student=student)
            return fallback_data
    
    return []

def fetch_score_range(place: str, year: str, classify: str = None, retry_times: int = 2, use_fallback: bool = True) -> list:
    """
    Fetch score range (一分一段表) from the Sogou Gaokao API.
    API endpoint: type=score_range
    If API fails, uses local fallback data.
    """
    # Check cache first
    cached_val = read_cache("score_range", place=place, year=year, classify=classify)
    if cached_val is not None:
        print(f"[SogouAPI] 使用缓存的分数位次数据", file=sys.stderr)
        return cached_val

    url = f"{BASE_URL}?type=score_range&from={SOURCE}&title={urllib.parse.quote('高考;一分一段表')}"
    if place:
        url += f"&place={urllib.parse.quote(place)}"
    if year:
        url += f"&year={urllib.parse.quote(year)}"
    if classify:
        url += f"&classify={urllib.parse.quote(classify)}"

    print(f"[SogouAPI] Accessing score range: {url}", file=sys.stderr)

    for attempt in range(retry_times):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = resp.read().decode("utf-8")
                result = json.loads(raw)
                if result.get("status") != 0:
                    print(f"[SogouAPI] Status error: {result.get('message')}", file=sys.stderr)
                    continue
                data = result.get("data", {})
                if not data:
                    continue
                res_list = data.get("score_range_res", [])
                if res_list:
                    write_cache("score_range", res_list, place=place, year=year, classify=classify)
                return res_list
        except urllib.error.URLError as e:
            print(f"[SogouAPI] Network error (attempt {attempt+1}): {e}", file=sys.stderr)
        except json.JSONDecodeError as e:
            print(f"[SogouAPI] JSON parsing error (attempt {attempt+1}): {e}", file=sys.stderr)
        except Exception as e:
            print(f"[SogouAPI] Unexpected error (attempt {attempt+1}): {e}", file=sys.stderr)

    # API 失败，使用 fallback
    if use_fallback:
        print(f"[SogouAPI] API 不可用，使用本地 fallback 分数位次数据", file=sys.stderr)
        fallback_data = get_fallback_score_range(place, year, classify)
        if fallback_data:
            write_cache("score_range", fallback_data, place=place, year=year, classify=classify)
            return fallback_data
    
    return []
