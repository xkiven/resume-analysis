import os
import json
import requests
from typing import Dict, List

DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY', '')


def call_qwen(prompt: str) -> str:
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "qwen-turbo",
        "input": {"prompt": prompt},
        "parameters": {"temperature": 0.2}
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        return result.get('output', {}).get('text', '')
    return ''


def extract_job_keywords(job_description: str) -> List[str]:
    import re
    tech_pattern = r'[A-Za-z+#]+'
    keywords = re.findall(tech_pattern, job_description)
    return [k for k in keywords if len(k) > 1]


def calculate_skill_match(skills: List[str], job_keywords: List[str]) -> Dict:
    matched = []
    missing = []
    for kw in job_keywords:
        kw_lower = kw.lower()
        found = any(kw_lower in s.lower() or kw in s for s in skills)
        if found:
            matched.append(kw)
        else:
            missing.append(kw)
    skill_rate = len(matched) / len(job_keywords) if job_keywords else 0
    return {
        "matched": matched,
        "missing": missing,
        "skill_rate": skill_rate
    }


def match_with_ai(resume_info: Dict, job_description: str) -> Dict:
    skills = resume_info.get("skills", [])
    experience = resume_info.get("experience", "")
    education = resume_info.get("education", "")
    work_years = resume_info.get("work_years", "")
    
    job_keywords = extract_job_keywords(job_description)
    match_result = calculate_skill_match(skills, job_keywords)
    
    prompt = f"""分析简历与岗位的匹配度。
简历技能: {json.dumps(skills, ensure_ascii=False)}
项目经历: {experience[:300] if experience else '无'}
岗位要求: {job_description[:300]}
已匹配: {match_result['matched']}
缺失: {match_result['missing']}
返回JSON：{{"match_score":0-100,"skill_match_rate":0.0-1_relevance":.0,"experience0.0-1.0,"matched_skills":[],"missing_skills":[],"analysis":"分析"}}"""

    try:
        content = call_qwen(prompt)
        json_str = extract_json_from_response(content)
        if json_str:
            result = json.loads(json_str)
            result['matched_skills'] = match_result['matched']
            result['missing_skills'] = match_result['missing']
            result['skill_match_rate'] = match_result['skill_rate']
            return result
    except Exception as e:
        print(f"匹配错误: {e}")
    
    return create_default_match()


def extract_json_from_response(text: str) -> str:
    import re
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        return match.group()
    return ''


def create_default_match() -> Dict:
    return {
        "match_score": 0,
        "skill_match_rate": 0.0,
        "experience_relevance": 0.0,
        "matched_skills": [],
        "missing_skills": [],
        "analysis": "匹配分析失败"
    }
