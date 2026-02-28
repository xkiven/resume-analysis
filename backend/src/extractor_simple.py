import os
import json
import requests
from typing import Dict

DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY', '')


def call_qwen(prompt: str) -> str:
    """直接调用通义千问API"""
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "qwen-turbo",
        "input": {"prompt": prompt},
        "parameters": {"temperature": 0.1}
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        return result.get('output', {}).get('text', '')
    return ''


def extract_info_with_ai(text: str) -> Dict:
    prompt = f"""你是一个简历信息提取助手。从以下简历中提取所有信息。
返回JSON格式：
{{
    "name": "姓名",
    "phone": "电话",
    "email": "邮箱",
    "address": "地址",
    "job_intent": "求职意向",
    "work_years": "工作年限",
    "education": "学历背景",
    "skills": ["技能1", "技能2"],
    "experience": "项目经历"
}}
简历文本：{text[:3500]}"""

    try:
        content = call_qwen(prompt)
        json_str = extract_json_from_response(content)
        if json_str:
            result = json.loads(json_str)
            return result
    except Exception as e:
        print(f"提取错误: {e}")
    return create_default_info()


def extract_json_from_response(text: str) -> str:
    import re
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        return match.group()
    return ''


def create_default_info() -> Dict:
    return {
        "name": "",
        "phone": "",
        "email": "",
        "address": "",
        "job_intent": "",
        "work_years": "",
        "education": "",
        "skills": [],
        "experience": ""
    }
