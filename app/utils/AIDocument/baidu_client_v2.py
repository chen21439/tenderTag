"""
百度文心一言图像理解客户端 V2
基于 OpenAI SDK 的兼容接口（推荐使用）

优势：
1. 使用熟悉的 OpenAI SDK
2. 代码更简洁
3. 百度官方支持的新接口

安装依赖：
pip install openai
"""
from openai import OpenAI
import base64
import json
from typing import Optional, Dict, Any, List


class BaiduImageClientV2:
    """百度图像理解客户端 V2（基于 OpenAI SDK）"""

    def __init__(
        self,
        api_key: str,
        model: str = "qianfan-vl-8b"
    ):
        """
        初始化百度客户端 V2

        Args:
            api_key: 百度 API Key（从控制台获取）
            model: 模型名称，默认 qianfan-vl-8b（支持视觉理解）
                  其他可用模型参考：https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Fm2vrveyu
        """
        self.api_key = api_key
        self.model = model

        # 初始化 OpenAI 客户端（指向百度的 base_url）
        self.client = OpenAI(
            base_url='https://qianfan.baidubce.com/v2',
            api_key=api_key
        )

        print(f"[BaiduImageClientV2] 初始化完成，模型: {model}")

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
            return f"data:image/jpeg;base64,{b64_str}"

    def send_request(
        self,
        prompt: str,
        image_path: str,
        temperature: float = 0.000001,
        top_p: float = 1.0,
        repetition_penalty: float = 1.05,
        verbose: bool = True
    ) -> str:
        """
        发送图像理解请求

        Args:
            prompt: 用户提示词
            image_path: 图片文件路径
            temperature: 温度参数（0.000001-1.0，越小越确定）
            top_p: top_p参数（0-1.0）
            repetition_penalty: 重复惩罚（1.0为无惩罚，>1.0减少重复）
            verbose: 是否打印详细信息

        Returns:
            AI响应文本
        """
        # 编码图片
        if verbose:
            print(f"[BaiduImageClientV2] 读取图片: {image_path}")
        image_base64 = self.encode_image_to_base64(image_path)

        # 构建 messages（OpenAI 格式）
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

        if verbose:
            print(f"\n{'=' * 80}")
            print(f"[BaiduImageClientV2] 发送请求")
            print(f"{'=' * 80}")
            print(f"Model: {self.model}")
            print(f"Prompt (前200字): {prompt[:200]}...")
            print(f"Temperature: {temperature}, Top_p: {top_p}")
            print(f"{'=' * 80}\n")

        # 调用 OpenAI SDK（指向百度的 V2 接口）
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                top_p=top_p,
                extra_body={
                    "repetition_penalty": repetition_penalty,
                    "frequency_penalty": 0,
                    "presence_penalty": 0,
                    "stop": [],
                    "enable_thinking": False
                }
            )

            # 提取响应内容
            answer = response.choices[0].message.content

            if verbose:
                print(f"\n{'=' * 80}")
                print(f"[BaiduImageClientV2] 收到响应")
                print(f"{'=' * 80}")
                print(answer[:500] + ("..." if len(answer) > 500 else ""))
                print(f"{'=' * 80}\n")

            return answer

        except Exception as e:
            raise Exception(f"请求失败: {e}")

    def send_request_with_json(
        self,
        prompt_template: str,
        image_path: str,
        json_data: Dict[str, Any],
        temperature: float = 0.000001,
        top_p: float = 1.0,
        repetition_penalty: float = 1.05,
        verbose: bool = True
    ) -> str:
        """
        发送图像理解请求（包含JSON上下文）

        Args:
            prompt_template: 提示词模板（可以使用 {json_data} 占位符）
            image_path: 图片文件路径
            json_data: JSON数据（会被序列化后插入到prompt中）
            temperature: 温度参数
            top_p: top_p参数
            repetition_penalty: 重复惩罚
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
            repetition_penalty=repetition_penalty,
            verbose=verbose
        )


# 全局单例
_global_baidu_client_v2: Optional[BaiduImageClientV2] = None


def get_baidu_client_v2(api_key: str, model: str = "qianfan-vl-8b") -> BaiduImageClientV2:
    """获取全局百度客户端 V2（单例模式）"""
    global _global_baidu_client_v2
    if _global_baidu_client_v2 is None:
        _global_baidu_client_v2 = BaiduImageClientV2(api_key=api_key, model=model)
    return _global_baidu_client_v2


def reset_baidu_client_v2():
    """重置全局客户端 V2"""
    global _global_baidu_client_v2
    _global_baidu_client_v2 = None


if __name__ == "__main__":
    print("""
BaiduImageClientV2 模块已加载（基于 OpenAI SDK）

使用示例:

from app.utils.AIDocument import BaiduImageClientV2

# 初始化客户端
client = BaiduImageClientV2(
    api_key="你的API Key",
    model="qianfan-vl-8b"
)

# 发送请求
response = client.send_request(
    prompt="请描述这张图片",
    image_path="path/to/image.jpg"
)

print(response)
    """)
