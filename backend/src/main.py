import os
import sys
import json
import uuid
import base64

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import io

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

from src.parser import extract_text_from_pdf, clean_text, split_sections
from src.extractor import extract_info_with_ai, extract_info_fallback
from src.matcher import match_with_ai, extract_job_keywords, calculate_skill_match
from src.cache import (
    cache_resume_text, get_cached_resume_text,
    cache_resume_info, get_cached_resume_info,
    cache_match_result, get_cached_match_result
)


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        "status": "ok",
        "service": "resume-analysis",
        "version": "1.0.0"
    })


@app.route('/api/resume/upload', methods=['POST'])
def resume_upload():
    """简历上传与解析接口"""
    try:
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "error": "未找到上传文件"
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                "success": False,
                "error": "文件名为空"
            }), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({
                "success": False,
                "error": "仅支持PDF格式文件"
            }), 400
        
        resume_id = str(uuid.uuid4())
        
        pdf_bytes = file.read()
        pdf_file = io.BytesIO(pdf_bytes)
        
        text = extract_text_from_pdf(pdf_file)
        text = clean_text(text)
        
        cache_resume_text(resume_id, text)
        
        return jsonify({
            "success": True,
            "data": {
                "resume_id": resume_id,
                "text": text[:500] + "..." if len(text) > 500 else text,
                "text_length": len(text),
                "status": "success"
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"处理失败: {str(e)}"
        }), 500


@app.route('/api/resume/extract', methods=['POST'])
def resume_extract():
    """简历信息提取接口"""
    try:
        data = request.get_json()
        if not data or 'resume_id' not in data:
            return jsonify({
                "success": False,
                "error": "缺少resume_id参数"
            }), 400
        
        resume_id = data['resume_id']
        
        cached_info = get_cached_resume_info(resume_id)
        if cached_info:
            return jsonify({
                "success": True,
                "data": cached_info,
                "cached": True
            })
        
        cached_text = get_cached_resume_text(resume_id)
        if not cached_text:
            return jsonify({
                "success": False,
                "error": "简历不存在或已过期，请重新上传"
            }), 404
        
        try:
            info = extract_info_with_ai(cached_text)
        except Exception:
            info = extract_info_fallback(cached_text)
        
        info["resume_id"] = resume_id
        
        cache_resume_info(resume_id, info)
        
        return jsonify({
            "success": True,
            "data": info,
            "cached": False
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"处理失败: {str(e)}"
        }), 500


@app.route('/api/resume/match', methods=['POST'])
def resume_match():
    """简历岗位匹配接口"""
    try:
        data = request.get_json()
        if not data or 'resume_id' not in data or 'job_description' not in data:
            return jsonify({
                "success": False,
                "error": "缺少必要参数"
            }), 400
        
        resume_id = data['resume_id']
        job_description = data['job_description']
        
        cached_result = get_cached_match_result(resume_id, job_description)
        if cached_result:
            return jsonify({
                "success": True,
                "data": cached_result,
                "cached": True
            })
        
        cached_info = get_cached_resume_info(resume_id)
        if not cached_info:
            return jsonify({
                "success": False,
                "error": "简历信息未提取，请先调用提取接口"
            }), 404
        
        try:
            result = match_with_ai(cached_info, job_description)
        except Exception as e:
            job_skills = extract_job_keywords(job_description)
            resume_skills = cached_info.get("skills", [])
            skill_rate = calculate_skill_match(resume_skills, job_skills)
            
            result = {
                "match_score": int(skill_rate * 100),
                "skill_match_rate": skill_rate,
                "experience_relevance": 0.5,
                "matched_skills": [s for s in job_skills if s.lower() in [rs.lower() for rs in resume_skills]],
                "missing_skills": [s for s in job_skills if s.lower() not in [rs.lower() for rs in resume_skills]],
                "analysis": "使用规则引擎进行匹配"
            }
        
        result["resume_id"] = resume_id
        result["job_description"] = job_description[:200]
        
        cache_match_result(resume_id, job_description, result)
        
        return jsonify({
            "success": True,
            "data": result,
            "cached": False
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"处理失败: {str(e)}"
        }), 500


def handler(environ, start_response):
    """阿里云FC入口函数"""
    return app(environ, start_response)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
