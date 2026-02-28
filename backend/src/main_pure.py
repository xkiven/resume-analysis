import os
import json
import uuid
import base64
import re
from urllib import request, parse
from urllib.request import urlopen, Request
from urllib.error import URLError

DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY', '')

resume_storage = {}


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
    
    try:
        req = Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
        with urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get('output', {}).get('text', '')
    except Exception as e:
        print(f"API调用错误: {e}")
        return ''


def extract_info_with_ai(text: str) -> dict:
    prompt = f"""你是一个简历信息提取助手。从以下简历中提取信息。
返回JSON格式：{{"name":"姓名","phone":"电话","email":"邮箱","address":"地址","job_intent":"求职意向","work_years":"工作年限","education":"学历","skills":["技能1"],"experience":"经历"}}
简历：{text[:2000]}"""
    
    try:
        content = call_qwen(prompt)
        match = re.search(r'\{[\s\S]*\}', content)
        if match:
            return json.loads(match.group())
    except Exception as e:
        print(f"提取错误: {e}")
    
    return {"name": "", "phone": "", "email": "", "address": "", "job_intent": "", "work_years": "", "education": "", "skills": [], "experience": ""}


def extract_job_keywords(job_description: str) -> list:
    tech_pattern = r'[A-Za-z+#]+'
    keywords = re.findall(tech_pattern, job_description)
    return [k for k in keywords if len(k) > 1]


def calculate_skill_match(skills: list, job_keywords: list) -> dict:
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
    return {"matched": matched, "missing": missing, "skill_rate": skill_rate}


def match_with_ai(resume_info: dict, job_description: str) -> dict:
    skills = resume_info.get("skills", [])
    experience = resume_info.get("experience", "")
    
    job_keywords = extract_job_keywords(job_description)
    match_result = calculate_skill_match(skills, job_keywords)
    
    prompt = f"""分析匹配度。技能:{skills},经历:{experience[:200]},岗位:{job_description[:200]},已匹配:{match_result['matched']},缺失:{match_result['missing']}
返回JSON：{{"match_score":0-100,"skill_match_rate":0.0,"experience_relevance":0.0,"matched_skills":[],"missing_skills":[],"analysis":"分析"}}"""
    
    try:
        content = call_qwen(prompt)
        match = re.search(r'\{[\s\S]*\}', content)
        if match:
            result = json.loads(match.group())
            result['matched_skills'] = match_result['matched']
            result['missing_skills'] = match_result['missing']
            result['skill_match_rate'] = match_result['skill_rate']
            return result
    except Exception as e:
        print(f"匹配错误: {e}")
    
    return {"match_score": 0, "skill_match_rate": 0.0, "experience_relevance": 0.0, "matched_skills": [], "missing_skills": [], "analysis": "匹配失败"}


def handler(environ, start_response):
    path = environ.get('PATH_INFO', '')
    method = environ.get('REQUEST_METHOD', 'GET')
    
    if path == '/api/health' and method == 'GET':
        response = json.dumps({"service": "resume-analysis", "status": "ok"})
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [response.encode('utf-8')]
    
    if path == '/api/resume/upload' and method == 'POST':
        try:
            request_body_size = int(environ.get('CONTENT_LENGTH', 0))
            request_body = environ['wsgi.input'].read(request_body_size)
            
            content_type = environ.get('CONTENT_TYPE', '')
            if 'multipart/form-data' in content_type:
                boundary = content_type.split('boundary=')[-1]
                parts = request_body.split(('--' + boundary).encode())
                
                for part in parts:
                    if b'filename=' in part and b'.pdf' in part:
                        file_content = part.split(b'\r\n\r\n')[-1].split(b'\r\n--')[0]
                        
                        resume_id = str(uuid.uuid4())
                        resume_storage[resume_id] = {"text": "PDF解析需要本地环境", "file_content": base64.b64encode(file_content).decode()}
                        
                        response = json.dumps({
                            "success": True,
                            "data": {
                                "resume_id": resume_id,
                                "text": "PDF解析功能需要本地环境支持",
                                "text_length": 0,
                                "status": "success"
                            }
                        })
                        start_response('200 OK', [('Content-Type', 'application/json')])
                        return [response.encode('utf-8')]
        except Exception as e:
            response = json.dumps({"success": False, "error": str(e)})
            start_response('500 OK', [('Content-Type', 'application/json')])
            return [response.encode('utf-8')]
    
    if path == '/api/resume/extract' and method == 'POST':
        try:
            request_body_size = int(environ.get('CONTENT_LENGTH', 0))
            request_body = environ['wsgi.input'].read(request_body_size)
            data = json.loads(request_body.decode('utf-8'))
            resume_id = data.get('resume_id')
            
            if not resume_id or resume_id not in resume_storage:
                response = json.dumps({"success": False, "error": "简历不存在"})
                start_response('404 OK', [('Content-Type', 'application/json')])
                return [response.encode('utf-8')]
            
            resume_data = resume_storage[resume_id]
            info = extract_info_with_ai(resume_data.get('text', ''))
            info["resume_id"] = resume_id
            resume_storage[resume_id]["info"] = info
            
            response = json.dumps({"success": True, "data": info})
            start_response('200 OK', [('Content-Type', 'application/json')])
            return [response.encode('utf-8')]
        except Exception as e:
            response = json.dumps({"success": False, "error": str(e)})
            start_response('500 OK', [('Content-Type', 'application/json')])
            return [response.encode('utf-8')]
    
    if path == '/api/resume/match' and method == 'POST':
        try:
            request_body_size = int(environ.get('CONTENT_LENGTH', 0))
            request_body = environ['wsgi.input'].read(request_body_size)
            data = json.loads(request_body.decode('utf-8'))
            resume_id = data.get('resume_id')
            job_description = data.get('job_description', '')
            
            if not resume_id or resume_id not in resume_storage:
                response = json.dumps({"success": False, "error": "简历不存在"})
                start_response('404 OK', [('Content-Type', 'application/json')])
                return [response.encode('utf-8')]
            
            resume_data = resume_storage[resume_id]
            info = resume_data.get('info', {})
            if not info:
                info = extract_info_with_ai(resume_data.get('text', ''))
            
            result = match_with_ai(info, job_description)
            result["resume_id"] = resume_id
            
            response = json.dumps({"success": True, "data": result})
            start_response('200 OK', [('Content-Type', 'application/json')])
            return [response.encode('utf-8')]
        except Exception as e:
            response = json.dumps({"success": False, "error": str(e)})
            start_response('500 OK', [('Content-Type', 'application/json')])
            return [response.encode('utf-8')]
    
    response = json.dumps({"error": "Not Found"})
    start_response('404 OK', [('Content-Type', 'application/json')])
    return [response.encode('utf-8')]


if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    port = int(os.environ.get('PORT', 5000))
    server = make_server('0.0.0.0', port, handler)
    print(f'Starting server on port {port}...')
    server.serve_forever()
