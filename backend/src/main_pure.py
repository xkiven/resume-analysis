import os
import json
import uuid
import base64
import re
import io
from urllib import request, parse
from urllib.request import urlopen, Request
from urllib.error import URLError

from src.cache import cache_resume_text, get_cached_resume_text, cache_resume_info, get_cached_resume_info, cache_match_result, get_cached_match_result
from src.extractor_simple import extract_info_with_ai
from src.matcher_simple import match_with_ai

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
    
    try:
        req = Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
        with urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get('output', {}).get('text', '')
    except Exception as e:
        print(f"API调用错误: {e}")
        return ''


def extract_info_with_ai_wrapper(text: str) -> dict:
    return extract_info_with_ai(text)


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


def match_with_ai_wrapper(resume_info: dict, job_description: str) -> dict:
    return match_with_ai(resume_info, job_description)


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
                        
                        extracted_text = "PDF解析功能不可用，请配置本地环境或Layer"
                        
                        resume_id = str(uuid.uuid4())
                        cache_resume_text(resume_id, extracted_text) # 使用缓存
                        
                        response = json.dumps({
                            "success": True,
                            "data": {
                                "resume_id": resume_id,
                                "text": extracted_text,
                                "text_length": len(extracted_text),
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
            
            if not resume_id:
                response = json.dumps({"success": False, "error": "缺少resume_id"})
                start_response('400 OK', [('Content-Type', 'application/json')])
                return [response.encode('utf-8')]
            
            cached_info = get_cached_resume_info(resume_id)
            if cached_info:
                response = json.dumps({"success": True, "data": cached_info, "cached": True})
                start_response('200 OK', [('Content-Type', 'application/json')])
                return [response.encode('utf-8')]

            cached_text = get_cached_resume_text(resume_id)
            if not cached_text:
                response = json.dumps({"success": False, "error": "简历不存在或已过期"})
                start_response('404 OK', [('Content-Type', 'application/json')])
                return [response.encode('utf-8')]
            
            info = extract_info_with_ai_wrapper(cached_text)
            info["resume_id"] = resume_id
            cache_resume_info(resume_id, info) # 使用缓存
            
            response = json.dumps({"success": True, "data": info, "cached": False})
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
            
            if not resume_id or not job_description:
                response = json.dumps({"success": False, "error": "缺少必要参数"})
                start_response('400 OK', [('Content-Type', 'application/json')])
                return [response.encode('utf-8')]
            
            cached_result = get_cached_match_result(resume_id, job_description)
            if cached_result:
                response = json.dumps({"success": True, "data": cached_result, "cached": True})
                start_response('200 OK', [('Content-Type', 'application/json')])
                return [response.encode('utf-8')]

            cached_info = get_cached_resume_info(resume_id)
            if not cached_info:
                response = json.dumps({"success": False, "error": "简历信息未提取或已过期"})
                start_response('404 OK', [('Content-Type', 'application/json')])
                return [response.encode('utf-8')]
            
            result = match_with_ai_wrapper(cached_info, job_description)
            result["resume_id"] = resume_id
            cache_match_result(resume_id, job_description, result) # 使用缓存
            
            response = json.dumps({"success": True, "data": result, "cached": False})
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
