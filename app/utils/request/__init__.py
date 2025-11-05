"""
请求工具模块
提供统一的 AI 请求接口
"""

from .ai_client import AIClient, get_global_client, reset_global_client

__all__ = [
    "AIClient",
    "get_global_client",
    "reset_global_client"
]