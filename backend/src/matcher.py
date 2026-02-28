import os
import json
import dashscope
from dashscope import Generation
from typing import Dict, List

dashscope.api_key = os.environ.get('DASHSCOPE_API_KEY', '')


def match_with_ai(resume_info: Dict, job_description: str) -> Dict:
    """使用AI模型进行简历与岗位的匹配分析"""
    
    skills = resume_info.get("skills", [])
    experience = resume_info.get("experience", "")
    education = resume_info.get("education", "")
    work_years = resume_info.get("work_years", "")
    
    job_keywords = []
    import re
    tech_pattern = r'[A-Za-z+#]+'
    job_keywords = re.findall(tech_pattern, job_description)
    job_keywords = [k for k in job_keywords if len(k) > 1]
    
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
    
    prompt = f"""你是一个招聘顾问。分析以下简历与岗位的匹配度。

简历技能: {json.dumps(skills, ensure_ascii=False)}
项目经历: {experience[:300] if experience else '无'}
岗位要求: {job_description[:300]}

已匹配的技能: {matched}
缺失的技能: {missing}

请根据以上信息给出评分。只返回JSON：
{{
    "match_score": 0-100,
    "skill_match_rate": 0.0-1.0,
    "experience_relevance": 0.0-1.0,
    "matched_skills": {json.dumps(matched)},
    "missing_skills": {json.dumps(missing)},
    "analysis": "简短分析"
}}"""

    try:
        response = Generation.call(
            model=Generation.Models.qwen_turbo,
            prompt=prompt,
            temperature=0.2
        )
        
        if response.status_code == 200:
            content = response.output.text
            result = parse_match_result(content)
            return result
        else:
            return create_default_match()
            
    except Exception as e:
        print(f"AI匹配错误: {e}")
        return create_default_match()


def parse_match_result(text: str) -> Dict:
    """解析AI返回的匹配结果"""
    import re
    try:
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        if matches:
            return json.loads(matches[0])
    except:
        pass
    return create_default_match()


def create_default_match() -> Dict:
    """创建默认匹配结果"""
    return {
        "match_score": 50,
        "skill_match_rate": 0.5,
        "experience_relevance": 0.5,
        "matched_skills": [],
        "missing_skills": [],
        "analysis": "无法进行AI分析"
    }


def calculate_skill_match(resume_skills: List[str], job_skills: List[str]) -> float:
    """计算技能匹配率"""
    if not resume_skills or not job_skills:
        return 0.0
    
    resume_skills_lower = [s.lower() for s in resume_skills]
    job_skills_lower = [s.lower() for s in job_skills]
    
    matched = sum(1 for skill in job_skills_lower if any(skill in rs or rs in skill for rs in resume_skills_lower))
    
    return matched / len(job_skills_lower)


def extract_job_keywords(job_description: str) -> List[str]:
    """从岗位描述中提取关键词"""
    import re
    
    common_skills = [
        "python", "java", "javascript", "c++", "c#", "go", "rust", "php", "ruby", "swift",
        "react", "vue", "angular", "nodejs", "django", "flask", "spring", "mybatis",
        "mysql", "redis", "mongodb", "postgresql", "elasticsearch", "kafka",
        "docker", "kubernetes", "jenkins", "git", "linux", "aws", "azure", "gcp",
        "ai", "machine learning", "deep learning", "tensorflow", "pytorch",
        "nlp", "computer vision", "sql", "nosql", "api", "rest", "graphql",
        "agile", "scrum", "devops", "cloud", "microservices"
    ]
    
    text_lower = job_description.lower()
    found_skills = []
    
    for skill in common_skills:
        if skill in text_lower:
            found_skills.append(skill)
    
    return found_skills
