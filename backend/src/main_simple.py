import os
import sys
import json
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import io

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY', '')

resume_storage = {}


def extract_text_from_pdf_simple(file_data):
    return "简历文本提取功能需要pdfplumber，请在本地环境使用"


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"service": "resume-analysis", "status": "ok"})


@app.route('/api/resume/upload', methods=['POST'])
def resume_upload():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "请上传文件"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "未选择文件"}), 400
    
    if not file.filename.endswith('.pdf'):
        return jsonify({"success": False, "error": "只支持PDF格式文件"}), 400
    
    try:
        file_content = file.read()
        text = extract_text_from_pdf_simple(file_content)
        
        resume_id = str(uuid.uuid4())
        resume_storage[resume_id] = {"text": text, "file_content": base64.b64encode(file_content).decode()}
        
        return jsonify({
            "success": True,
            "data": {
                "resume_id": resume_id,
                "text": text[:500] if text else "PDF解析需要本地环境支持",
                "text_length": len(text) if text else 0,
                "status": "success"
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/resume/extract', methods=['POST'])
def resume_extract():
    data = request.get_json()
    resume_id = data.get('resume_id')
    
    if not resume_id:
        return jsonify({"success": False, "error": "缺少resume_id"}), 400
    
    resume_data = resume_storage.get(resume_id)
    if not resume_data:
        return jsonify({"success": False, "error": "简历不存在"}), 404
    
    try:
        from src.extractor_simple import extract_info_with_ai
        info = extract_info_with_ai(resume_data.get('text', ''))
        info["resume_id"] = resume_id
        resume_storage[resume_id]["info"] = info
        
        return jsonify({
            "success": True,
            "data": info
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/resume/match', methods=['POST'])
def resume_match():
    data = request.get_json()
    resume_id = data.get('resume_id')
    job_description = data.get('job_description', '')
    
    if not resume_id or not job_description:
        return jsonify({"success": False, "error": "缺少必要参数"}), 400
    
    resume_data = resume_storage.get(resume_id)
    if not resume_data:
        return jsonify({"success": False, "error": "简历不存在"}), 404
    
    try:
        from src.matcher_simple import match_with_ai
        info = resume_data.get('info', {})
        if not info:
            from src.extractor_simple import extract_info_with_ai
            info = extract_info_with_ai(resume_data.get('text', ''))
        
        result = match_with_ai(info, job_description)
        result["resume_id"] = resume_id
        
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def handler(environ, start_response):
    return app(environ, start_response)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
