"""
AIDocument 工具模块
提供百度文心一言图像理解功能

Bearer: 新一代 API Key 鉴权（bce-v3/ALTAK...）- 推荐使用，已内置项目 API Key
V1: 基于 requests 的实现（旧版 access_token 鉴权）
V2: 基于 OpenAI SDK 的实现（需要单独配置）
"""

# Bearer 鉴权（新一代 API Key）- 推荐，已内置配置
from .baidu_client_bearer import (
    BaiduImageClientBearer,
    get_baidu_client_bearer,
    reset_baidu_client_bearer
)

# V1 接口（手动 requests，旧版）
from .baidu_client import BaiduImageClient, get_baidu_client, reset_baidu_client

# V2 接口（OpenAI SDK）
from .baidu_client_v2 import BaiduImageClientV2, get_baidu_client_v2, reset_baidu_client_v2

__all__ = [
    # Bearer 鉴权 - 推荐使用，已内置 API Key
    "BaiduImageClientBearer",
    "get_baidu_client_bearer",
    "reset_baidu_client_bearer",
    # V1（旧版）
    "BaiduImageClient",
    "get_baidu_client",
    "reset_baidu_client",
    # V2（OpenAI SDK）
    "BaiduImageClientV2",
    "get_baidu_client_v2",
    "reset_baidu_client_v2"
]
