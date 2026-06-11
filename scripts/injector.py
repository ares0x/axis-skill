import os
import csv
from scripts.gaokao_mapper import normalize_province, normalize_stream
from scripts.sogou_api import fetch_province_control_lines

class KnowledgeInjector:
    def __init__(self, data_dir=None):
        if data_dir is None:
            # Default to the sibling data directory
            self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        else:
            self.data_dir = data_dir
        
        self.cancelled_majors = []
        self.added_majors = []
        self.province_control_lines = []
        self.five_year_plan = ""
        self.expert_rules = ""
        
        self.load_all()

    def load_all(self):
        self._load_cancelled()
        self._load_added()
        self._load_province_control_lines()
        self._load_five_year_plan()
        self._load_expert_rules()

    def _load_cancelled(self):
        path = os.path.join(self.data_dir, '2026_cancelled_majors.csv')
        if os.path.exists(path):
            with open(path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                self.cancelled_majors = [row for row in reader]

    def _load_added(self):
        path = os.path.join(self.data_dir, '2026_added_majors.csv')
        if os.path.exists(path):
            with open(path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                self.added_majors = [row for row in reader]

    def _load_province_control_lines(self):
        path = os.path.join(self.data_dir, 'province_control_lines.csv')
        if os.path.exists(path):
            with open(path, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                self.province_control_lines = [row for row in reader]

    def _load_five_year_plan(self):
        path = os.path.join(self.data_dir, '15th_five_year_plan.md')
        if os.path.exists(path):
            with open(path, mode='r', encoding='utf-8') as f:
                self.five_year_plan = f.read()

    def _load_expert_rules(self):
        path = os.path.join(self.data_dir, 'alpha_expert_rules.md')
        if os.path.exists(path):
            with open(path, mode='r', encoding='utf-8') as f:
                self.expert_rules = f.read()

    def check_major_cancelled(self, major_name, institution_level):
        """
        Check if a major is in the cancelled list.
        Supports fuzzy name matching.
        """
        major_name_lower = major_name.lower()
        for row in self.cancelled_majors:
            name_key = 'MajorName' if 'MajorName' in row else 'major_name'
            level_key = 'InstitutionLevel' if 'InstitutionLevel' in row else 'risk_level'
            
            full_name_lower = row.get(name_key, '').lower()
            # If the query is a substring of the major name, or vice versa
            if major_name_lower in full_name_lower or any(part in major_name_lower for part in full_name_lower.replace('(', ' ').replace(')', ' ').split() if len(part) > 1):
                level = row.get(level_key, 'All')
                if level.lower() in ['all', 'high', 'medium'] or level.lower() == institution_level.lower():
                    return row
        return None

    def check_major_added(self, major_name):
        """
        Check if a major is in the strategic new added majors.
        """
        major_name_lower = major_name.lower()
        for row in self.added_majors:
            name_key = 'MajorName' if 'MajorName' in row else 'major_name'
            full_name_lower = row.get(name_key, '').lower()
            if major_name_lower in full_name_lower or any(part in major_name_lower for part in full_name_lower.replace('(', ' ').replace(')', ' ').split() if len(part) > 1):
                return row
        return None

    def get_province_control_line(self, province, track_type, year=2024):
        """
        Lookup control score lines for a given province and track.
        """
        results = []
        year_str = str(year)
        
        # 1. Normalize province and track
        prov_clean = normalize_province(province)
        try:
            year_int = int(year)
        except (ValueError, TypeError):
            year_int = 2024
        track_clean = normalize_stream(prov_clean, year_int, track_type)
        
        # Determine normalized track inside CSV (e.g., 理科, 物理类)
        csv_tracks = []
        if "物理" in track_clean:
            csv_tracks = ["物理类", "理科", "不分科"]
        elif "历史" in track_clean or "文科" in track_clean:
            csv_tracks = ["历史类", "文科", "不分科"]
        elif "春考" in track_clean:
            csv_tracks = ["物理类", "历史类", "不分科"]
        else:
            csv_tracks = [track_clean, "理科", "物理类", "不分科"]

        # 2. Try querying local CSV first
        for row in self.province_control_lines:
            if row.get('province') == prov_clean and row.get('year') == year_str:
                if row.get('track_type') in csv_tracks:
                    results.append(row)
                    
        # 3. If local CSV doesn't have the lines, call Sogou Gaokao API as fallback
        if not results:
            api_lines = fetch_province_control_lines(prov_clean, year_str, track_clean)
            for item in api_lines:
                # Convert API keys to match CSV schema
                results.append({
                    'province': item.get('分数线所属地区', prov_clean),
                    'year': item.get('分数查询年份', year_str),
                    'track_type': item.get('考生类别', track_clean),
                    'batch_name': item.get('录取批次', ''),
                    'control_score': item.get('分数', '')
                })
        return results

    def get_policy_context_for_prompt(self):
        """
        Synthesize relevant context for feeding to the LLM agent.
        """
        context = "### Policy and Industry Context\n\n"
        context += "#### Canceled Majors (High Risk):\n"
        for row in self.cancelled_majors[:5]:
            name = row.get('MajorName') or row.get('major_name') or 'Unknown'
            code = row.get('MajorCode') or row.get('major_code') or 'N/A'
            level = row.get('InstitutionLevel') or row.get('risk_level') or 'High'
            reason = row.get('Reason') or row.get('reason') or ''
            context += f"- {name} ({code}) at {level} level. Reason: {reason}\n"
        
        context += "\n#### Newly Added Strategic Majors (Low Risk / Supported):\n"
        for row in self.added_majors[:5]:
            name = row.get('MajorName') or row.get('major_name') or 'Unknown'
            code = row.get('MajorCode') or row.get('major_code') or 'N/A'
            focus = row.get('FocusArea') or row.get('focus_area') or 'N/A'
            reason = row.get('Reason') or row.get('reason') or ''
            context += f"- {name} ({code}). Focus: {focus}. Reason: {reason}\n"
            
        return context

if __name__ == '__main__':
    # Simple testing print
    injector = KnowledgeInjector()
    print("Loaded cancelled majors count:", len(injector.cancelled_majors))
    print("Loaded added majors count:", len(injector.added_majors))
    print("Policy context sample:\n", injector.get_policy_context_for_prompt()[:400])
