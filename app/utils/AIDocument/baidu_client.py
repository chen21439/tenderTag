"""
百度文心一言图像理解客户端
简化版本，access_token 由外部直接提供

核心三步：
1. 拼 URL：https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chatv/[API名称]?access_token=xxx
2. 组 messages：[{"role":"user", "content":[{"type":"text","text":"..."}, {"type":"image_url","image_url":{"url":"data:image/jpeg;base64,xxx"}}]}]
3. 用 requests 发 POST 拿结果
"""
import requests
import base64
import json
from typing import Optional, Dict, Any, List


class BaiduImageClient:
    """百度图像理解客户端（简化版）"""

    def __init__(
        self,
        access_token: str,
        api_name: str = "ernie-4.0-turbo-128k-preview"
    ):
        """
        初始化百度客户端

        Args:
            access_token: 百度API的access_token（外部提供）
            api_name: API服务名称，默认 ernie-4.0-turbo-128k-preview
        """
        self.access_token = access_token
        self.api_name = api_name

    def encode_image_to_base64(self, image_path: str) -> str:
        """
        将图片编码为 base64（带 data URI 前缀）

        Args:
            image_path: 图片文件路径

        Returns:
            data:image/jpeg;base64,xxx 格式
        """
        with open(image_path, 'rb') as f:
            image_data = f.read()
            b64_str = base64.b64encode(image_data).decode('utf-8')
            # 百度要求：data:image/jpeg;base64,xxx
            return f"data:image/jpeg;base64,{b64_str}"

    def send_request(
        self,
        prompt: str,
        image_path: str,
        temperature: float = 0.01,
        top_p: float = 0.8,
        verbose: bool = True
    ) -> str:
        """
        发送图像理解请求（简化版：单图 + 单文本）

        Args:
            prompt: 用户提示词
            image_path: 图片文件路径
            temperature: 温度参数（0.01-1.0）
            top_p: top_p参数（0-1.0）
            verbose: 是否打印详细信息

        Returns:
            AI响应文本
        """
        # 步骤1: 读取并编码图片
        if verbose:
            print(f"[BaiduImageClient] 读取图片: {image_path}")
        image_base64 = self.encode_image_to_base64(image_path)

        # 步骤2: 拼 URL
        url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chatv/{self.api_name}?access_token={self.access_token}"

        # 步骤3: 组 messages（重点！按照百度文档格式）
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_base64
                        }
                    }
                ]
            }
        ]

        # 完整请求体
        payload = {
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "stream": False
        }

        headers = {
            'Content-Type': 'application/json'
        }

        if verbose:
            print(f"\n{'=' * 80}")
            print(f"[BaiduImageClient] 发送请求")
            print(f"{'=' * 80}")
            print(f"API: {self.api_name}")
            print(f"Prompt (前200字): {prompt[:200]}...")
            print(f"{'=' * 80}\n")

        # 步骤4: 发 POST 拿结果
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()

            result = response.json()

            # 检查错误
            if "error_code" in result:
                error_msg = f"API错误: {result.get('error_code')} - {result.get('error_msg')}"
                raise Exception(error_msg)

            # 提取 result 字段
            answer = result.get("result", "")

            if verbose:
                print(f"\n{'=' * 80}")
                print(f"[BaiduImageClient] 收到响应")
                print(f"{'=' * 80}")
                print(answer[:500] + ("..." if len(answer) > 500 else ""))
                print(f"{'=' * 80}\n")

            return answer

        except requests.exceptions.RequestException as e:
            raise Exception(f"请求失败: {e}")
        except Exception as e:
            raise Exception(f"处理响应失败: {e}")

    def send_request_with_json(
        self,
        prompt_template: str,
        image_path: str,
        json_data: Dict[str, Any],
        temperature: float = 0.01,
        top_p: float = 0.8,
        verbose: bool = True
    ) -> str:
        """
        发送图像理解请求（包含JSON上下文）

        适用场景：需要将 JSON 数据（如 lines 列表）拼接到提示词中

        Args:
            prompt_template: 提示词模板（可以使用 {json_data} 占位符）
            image_path: 图片文件路径
            json_data: JSON数据（会被序列化后插入到prompt中）
            temperature: 温度参数
            top_p: top_p参数
            verbose: 是否打印详细信息

        Returns:
            AI响应文本
        """
        # 将JSON数据格式化为字符串
        json_str = json.dumps(json_data, ensure_ascii=False, indent=2)

        # 替换prompt中的占位符
        full_prompt = prompt_template.replace("{json_data}", json_str)

        return self.send_request(
            prompt=full_prompt,
            image_path=image_path,
            temperature=temperature,
            top_p=top_p,
            verbose=verbose
        )


# 全局单例
_global_baidu_client: Optional[BaiduImageClient] = None


def get_baidu_client(access_token: str) -> BaiduImageClient:
    """获取全局百度客户端（单例模式）"""
    global _global_baidu_client
    if _global_baidu_client is None:
        _global_baidu_client = BaiduImageClient(access_token)
    return _global_baidu_client


def reset_baidu_client():
    """重置全局客户端"""
    global _global_baidu_client
    _global_baidu_client = None


if __name__ == "__main__":
    # 测试示例
    print("BaiduImageClient 模块已加载")
    print("使用示例:")
    print("""
    from app.utils.AIDocument import BaiduImageClient

    client = BaiduImageClient(access_token="your_token_here")

    response = client.send_request(
        prompt="请描述这张图片的内容",
        image_path="path/to/image.jpg"
    )

    print(response)
    """)
