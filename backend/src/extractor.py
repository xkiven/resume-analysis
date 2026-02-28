import os
import json
import dashscope
from typing import Dict, Optional

dashscope.api_key = os.environ.get('DASHSCOPE_API_KEY', '')


def extract_info_with_ai(text: str) -> Dict:
    """使用通义千问AI模型从简历文本中提取关键信息"""
    
    prompt = f"""你是一个专业的简历信息提取助手。请从以下简历文本中提取关键信息，并以JSON格式返回。

必须提取的信息：
- name: 姓名
- phone: 电话号码
- email: 电子邮箱
- address: 地址

可选提取的信息：
- job_intent: 求职意向
- work_years: 工作年限
- education: 学历背景
- skills: 技能列表（数组形式）
- experience: 工作经历摘要

请严格按照以下JSON格式返回，不要添加任何解释性文字：
{{
    "name": "姓名",
    "phone": "电话号码",
    "email": "电子邮箱",
    "address": "地址",
    "job_intent": "求职意向",
    "work_years": "工作年限",
    "education": "学历背景",
    "skills": ["技能1", "技能2"],
    "experience": "工作经历摘要"
}}

简历文本：
{text[:3000]}"""

    try:
        response = dashscope.Generation.call(
            model=dashscope.Generation.Models.QWEN_TURBO,
            prompt=prompt,
            format='message',
            messages=[{
                'role': 'user',
                'content': prompt
            }],
            temperature=0.1
        )
        
        if response.status_code == 200:
            content = response.output.choices[0].message.content
            json_str = extract_json_from_response(content)
            if json_str:
                return json.loads(json_str)
            else:
                return create_default_info()
        else:
            return create_default_info()
            
    except Exception as e:
        return create_default_info()


def extract_json_from_response(text: str) -> Optional[str]:
    """从AI响应中提取JSON字符串"""
    import re
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(json_pattern, text, re.DOTALL)
    if matches:
        return matches[0]
    return None


def create_default_info() -> Dict:
    """创建默认信息结构"""
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


def extract_info_fallback(text: str) -> Dict:
    """使用正则表达式作为备选方案提取信息"""
    import re
    
    info = create_default_info()
    
    phone_pattern = r'1[3-9]\d{9}'
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    
    phone_match = re.search(phone_pattern, text)
    if phone_match:
        info["phone"] = phone_match.group()
    
    email_match = re.search(email_pattern, text)
    if email_match:
        info["email"] = email_match.group()
    
    return info
