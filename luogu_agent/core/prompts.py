import json

def get_system_prompt(fields):
    system_prompt = f"""
你是一个算法竞赛金牌教练。
请你严格按照以下 JSON Schema 格式返回你的分析报告：
{fields}
"""
    return system_prompt

def get_user_prompt(problem_data, solutions_data):
    user_prompt = f"""
请综合分析以下题目信息和多份爬取来的原始题解，生成一份全新的、高质量的分析报告。

[题目完整信息]:
{json.dumps(problem_data, indent=2, ensure_ascii=False)}

[爬取的多份原始题解参考]:
{json.dumps(solutions_data, indent=2, ensure_ascii=False)}

请只返回 JSON，不要任何多余文本。
"""
    return user_prompt