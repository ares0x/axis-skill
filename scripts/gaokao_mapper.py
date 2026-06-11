#!/usr/bin/env python3
"""
Gaokao province and subject stream normalizer based on historical reform timelines.
"""

# Standard list of 31 mainland Chinese provinces/regions
STANDARD_PROVINCES = [
    "北京", "天津", "河北", "山西", "内蒙古", "辽宁", "吉林", "黑龙江",
    "上海", "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南",
    "湖北", "湖南", "广东", "广西", "海南", "重庆", "四川", "贵州",
    "云南", "西藏", "陕西", "甘肃", "青海", "宁夏", "新疆"
]

# Alias to standard province mappings
ALIAS_MAP = {
    "魔都": "上海", "首都": "北京", "闽南": "福建", "闽": "福建",
    "桂": "广西", "粤": "广东", "蜀": "四川", "川": "四川",
    "赣": "江西", "湘": "湖南", "鄂": "湖北", "冀": "河北",
    "晋": "山西", "鲁": "山东", "豫": "河南", "浙": "浙江",
    "苏": "江苏", "皖": "安徽", "辽": "辽宁", "吉": "吉林",
    "黑": "黑龙江", "蒙": "内蒙古", "陕": "陕西", "秦": "陕西",
    "甘": "甘肃", "陇": "甘肃", "青": "青海", "宁": "宁夏",
    "藏": "西藏", "新": "新疆", "琼": "海南", "津": "天津",
    "渝": "重庆", "贵": "贵州", "黔": "贵州", "滇": "云南",
    "云": "云南"
}

# Major cities to province mappings
CITY_TO_PROVINCE = {
    "广州": "广东", "深圳": "广东", "珠海": "广东", "汕头": "广东", "佛山": "广东",
    "东莞": "广东", "中山": "广东", "惠州": "广东", "福州": "福建", "厦门": "福建",
    "泉州": "福建", "杭州": "浙江", "宁波": "浙江", "温州": "浙江", "南京": "江苏",
    "苏州": "江苏", "无锡": "江苏", "成都": "四川", "武汉": "湖北", "长沙": "湖南",
    "郑州": "河南", "济南": "山东", "青岛": "山东", "西安": "陕西", "石家庄": "河北",
    "太原": "山西", "呼和浩特": "内蒙古", "沈阳": "辽宁", "大连": "辽宁", "长春": "吉林",
    "哈尔滨": "黑龙江", "合肥": "安徽", "南昌": "江西", "南宁": "广西", "海口": "海南",
    "贵阳": "贵州", "昆明": "云南", "拉萨": "西藏", "兰州": "甘肃", "西宁": "青海",
    "银川": "宁夏", "乌鲁木齐": "新疆"
}

# Gaokao Reform Years
# Key: Province, Value: Year the reform took effect
REFORM_3_3 = {
    "上海": 2017, "浙江": 2017,
    "北京": 2020, "天津": 2020, "山东": 2020, "海南": 2020
}

REFORM_3_1_2 = {
    "河北": 2021, "辽宁": 2021, "江苏": 2021, "福建": 2021,
    "湖北": 2021, "湖南": 2021, "广东": 2021, "重庆": 2021,
    "甘肃": 2024, "吉林": 2024, "黑龙江": 2024, "安徽": 2024,
    "江西": 2024, "贵州": 2024, "广西": 2024,
    "山西": 2025, "内蒙古": 2025, "河南": 2025, "四川": 2025,
    "云南": 2025, "陕西": 2025, "青海": 2025, "宁夏": 2025
}

def normalize_province(province_str: str) -> str:
    """
    Clean and resolve a province name from string input.
    """
    if not province_str:
        return ""
    
    clean_str = province_str.strip()
    
    # 1. Direct match in standard list
    for p in STANDARD_PROVINCES:
        if p in clean_str or clean_str in p:
            return p
            
    # 2. Check alias map
    for alias, std in ALIAS_MAP.items():
        if alias in clean_str:
            return std
            
    # 3. Check city mapping
    for city, std in CITY_TO_PROVINCE.items():
        if city in clean_str:
            return std
            
    return clean_str

def get_gaokao_model(province: str, year: int) -> str:
    """
    Determine the Gaokao model for a given province and year.
    Returns: '3+3', '3+1+2', or 'traditional'
    """
    std_province = normalize_province(province)
    
    # Check 3+3
    if std_province in REFORM_3_3:
        if year >= REFORM_3_3[std_province]:
            return "3+3"
            
    # Check 3+1+2
    if std_province in REFORM_3_1_2:
        if year >= REFORM_3_1_2[std_province]:
            return "3+1+2"
            
    return "traditional"

def normalize_stream(province: str, year: int, stream_str: str) -> str:
    """
    Normalize student category/stream based on province, year, and policy.
    Returns: '物理', '历史', '理科', '文科', '综合', or original string
    """
    if not stream_str:
        return ""
    
    std_province = normalize_province(province)
    clean_stream = stream_str.strip()
    
    model = get_gaokao_model(std_province, year)
    
    if model == "3+3":
        # 3+3 has no division of science/arts, it is all "综合" (comprehensive)
        return "综合"
        
    elif model == "3+1+2":
        # 3+1+2 standard categories are "物理" (Physics) or "历史" (History)
        if any(x in clean_stream for x in ["理", "物理", "理工"]):
            return "物理"
        if any(x in clean_stream for x in ["文", "历史", "文史"]):
            return "历史"
        return clean_stream
        
    else:
        # Traditional Gaokao is divided into "理科" (Science) or "文科" (Arts)
        if any(x in clean_stream for x in ["物理", "理", "理工"]):
            return "理科"
        if any(x in clean_stream for x in ["历史", "文", "文史"]):
            return "文科"
        return clean_stream
