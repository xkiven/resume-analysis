import os
import json
import dashscope
from dashscope import Generation
from typing import Dict, Optional

dashscope.api_key = os.environ.get('DASHSCOPE_API_KEY', '')


def extract_info_with_ai(text: str) -> Dict:
    """使用通义千问AI模型从简历文本中提取关键信息"""
    
    prompt = f"""你是一个简历信息提取助手。从以下简历中提取所有信息。

【关键】只提取简历中实际存在的内容，不要猜测。

返回格式（只返回JSON，包含所有字段）：
{{
    "name": "姓名",
    "phone": "电话",
    "email": "邮箱",
    "address": "地址",
    "job_intent": "求职意向",
    "work_years": "工作年限",
    "education": "学历背景",
    "skills": ["Go", "Python", "MySQL"],
    "experience": "项目经历描述，包含项目名称、职责、技术栈等"
}}

简历文本：
{text[:3500]}"""

    try:
        response = Generation.call(
            model=Generation.Models.qwen_turbo,
            prompt=prompt,
            temperature=0.1
        )
        
        if response.status_code == 200:
            content = response.output.text
            json_str = extract_json_from_response(content)
            if json_str:
                result = json.loads(json_str)
                if "experience" not in result or not result.get("experience"):
                    if "experiences" in result:
                        result["experience"] = "\n".join([
                            f"{exp.get('title', '')} - {exp.get('role', '')}: {exp.get('description', '')}" 
                            for exp in result.get("experiences", [])
                        ])
                return result
            else:
                return create_default_info()
        else:
            return create_default_info()
            
    except Exception as e:
        print(f"AI提取错误: {e}")
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
