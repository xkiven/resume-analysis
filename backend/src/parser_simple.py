import io
import re
import pdfplumber

def extract_text_from_pdf(pdf_file):
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


def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if line:
            cleaned_lines.append(line)
    return '\n'.join(cleaned_lines)


def split_sections(text):
    sections = {"header": "", "education": "", "experience": "", "skills": "", "other": ""}
    section_keywords = {
        "education": ["教育", "学历", "毕业", "学校"],
        "experience": ["工作", "经历", "经验", "公司"],
        "skills": ["技能", "专长", "能力"]
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
