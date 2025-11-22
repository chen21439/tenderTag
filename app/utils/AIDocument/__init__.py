"""
AIDocument 工具模块
提供百度文心一言图像理解功能（V2 API）
"""

# V2 Bearer 鉴权（推荐使用，已内置项目 API Key）
from .baidu_client_bearer import (
    BaiduImageClientBearer,
    get_baidu_client_bearer,
    reset_baidu_client_bearer
)

__all__ = [
    "BaiduImageClientBearer",
    "get_baidu_client_bearer",
    "reset_baidu_client_bearer",
]
