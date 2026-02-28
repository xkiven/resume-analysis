import re
import pdfplumber
from typing import Dict, List, Optional


def extract_text_from_pdf(pdf_file) -> str:
    """从PDF文件中提取文本内容"""
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        raise ValueError(f"PDF解析失败: {str(e)}")
    return text


def clean_text(text: str) -> str:
    """清洗和结构化处理文本"""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if line:
            cleaned_lines.append(line)
    return '\n'.join(cleaned_lines)


def split_sections(text: str) -> Dict[str, str]:
    """将简历文本按章节分割"""
    sections = {
        "header": "",
        "education": "",
        "experience": "",
        "skills": "",
        "other": ""
    }
    
    section_keywords = {
        "education": ["教育", "学历", "毕业", "学校", "大学", "学院"],
        "experience": ["工作", "经历", "经验", "任职", "职位", "公司"],
        "skills": ["技能", "专长", "能力", "熟悉", "掌握", "精通"]
    }
    
    lines = text.split('\n')
    current_section = "header"
    
    for line in lines:
        line_lower = line.lower()
        for section, keywords in section_keywords.items():
            if any(keyword in line_lower for keyword in keywords):
                current_section = section
                break
        sections[current_section] += line + "\n"
    
    for section in sections:
        sections[section] = sections[section].strip()
    
    return sections
