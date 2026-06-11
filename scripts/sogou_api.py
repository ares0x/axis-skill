#!/usr/bin/env python3
import json
import sys
import urllib.request
import urllib.parse
import urllib.error

BASE_URL = "https://gaokao.search.qq.com/skills_data"
SOURCE = "open_tB0fU5wP"

def fetch_province_control_lines(place: str, year: str, student: str, retry_times: int = 2) -> list:
    """
    Fetch province control lines (录取控制分数线) from the Sogou Gaokao API.
    API endpoint: type=province_score_line
    """
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
                # In different contexts, the key might be "地区分数线" or similar
                return data.get("地区分数线", [])
        except urllib.error.URLError as e:
            print(f"[SogouAPI] Network error (attempt {attempt+1}): {e}", file=sys.stderr)
        except json.JSONDecodeError as e:
            print(f"[SogouAPI] JSON parsing error (attempt {attempt+1}): {e}", file=sys.stderr)
        except Exception as e:
            print(f"[SogouAPI] Unexpected error (attempt {attempt+1}): {e}", file=sys.stderr)

    return []

def fetch_score_range(place: str, year: str, classify: str, retry_times: int = 2) -> list:
    """
    Fetch score range (一分一段表) from the Sogou Gaokao API.
    API endpoint: type=score_range
    """
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
                return data.get("score_range_res", [])
        except urllib.error.URLError as e:
            print(f"[SogouAPI] Network error (attempt {attempt+1}): {e}", file=sys.stderr)
        except json.JSONDecodeError as e:
            print(f"[SogouAPI] JSON parsing error (attempt {attempt+1}): {e}", file=sys.stderr)
        except Exception as e:
            print(f"[SogouAPI] Unexpected error (attempt {attempt+1}): {e}", file=sys.stderr)

    return []
