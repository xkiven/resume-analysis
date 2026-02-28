import os
import json
import hashlib
import redis
from typing import Optional, Dict
import time

redis_host = os.environ.get('REDIS_HOST', 'localhost')
redis_port = int(os.environ.get('REDIS_PORT', 6379))
redis_password = os.environ.get('REDIS_PASSWORD', None)

try:
    redis_client.ping()
    REDIS_AVAILABLE = False # 强制禁用Redis
except Exception:
    redis_client = None
    REDIS_AVAILABLE = False


CACHE_TTL = 3600


def cache_resume_text(resume_id: str, text: str) -> bool:
    """缓存简历原始文本"""
    if not REDIS_AVAILABLE:
        return False
    try:
        key = f"resume:text:{resume_id}"
        redis_client.setex(key, CACHE_TTL, text)
        return True
    except Exception:
        return False


def get_cached_resume_text(resume_id: str) -> Optional[str]:
    """获取缓存的简历文本"""
    if not REDIS_AVAILABLE:
        return None
    try:
        key = f"resume:text:{resume_id}"
        return redis_client.get(key)
    except Exception:
        return None


def cache_resume_info(resume_id: str, info: Dict) -> bool:
    """缓存解析后的简历信息"""
    if not REDIS_AVAILABLE:
        return False
    try:
        key = f"resume:info:{resume_id}"
        redis_client.setex(key, CACHE_TTL, json.dumps(info, ensure_ascii=False))
        return True
    except Exception:
        return False


def get_cached_resume_info(resume_id: str) -> Optional[Dict]:
    """获取缓存的简历信息"""
    if not REDIS_AVAILABLE:
        return None
    try:
        key = f"resume:info:{resume_id}"
        data = redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception:
        return None


def cache_match_result(resume_id: str, job_desc: str, result: Dict) -> bool:
    """缓存匹配结果"""
    if not REDIS_AVAILABLE:
        return False
    try:
        cache_key = hashlib.md5(f"{resume_id}:{job_desc}".encode()).hexdigest()
        key = f"match:result:{cache_key}"
        redis_client.setex(key, CACHE_TTL, json.dumps(result, ensure_ascii=False))
        return True
    except Exception:
        return False


def get_cached_match_result(resume_id: str, job_desc: str) -> Optional[Dict]:
    """获取缓存的匹配结果"""
    if not REDIS_AVAILABLE:
        return None
    try:
        import hashlib
        cache_key = hashlib.md5(f"{resume_id}:{job_desc}".encode()).hexdigest()
        key = f"match:result:{cache_key}"
        data = redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception:
        return None


def clear_cache():
    """清空所有缓存"""
    if not REDIS_AVAILABLE:
        return False
    try:
        redis_client.flushdb()
        return True
    except Exception:
        return False
