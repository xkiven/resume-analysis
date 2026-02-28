import unittest
import io
from src.parser import clean_text, split_sections


class TestParser(unittest.TestCase):
    def test_clean_text(self):
        text = "  测试   文本  \n\n  多余空格  "
        result = clean_text(text)
        self.assertIn("测试", result)
        self.assertIn("文本", result)

    def test_split_sections(self):
        text = """张三
电话: 13800138000
邮箱: test@example.com

教育背景
北京大学

工作经历
某科技公司

技能
Python, JavaScript"""
        result = split_sections(text)
        self.assertIsInstance(result, dict)
        self.assertIn("header", result)


if __name__ == '__main__':
    unittest.main()
