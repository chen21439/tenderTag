"""
招标文件标注服务 - 使用 Qwen3-32B 模型
"""
from pathlib import Path
from typing import Optional, Dict, Any
import json
from openai import OpenAI


class TenderTagger:
    """使用 Qwen3-32B 模型对招标文件进行标注分析"""

    def __init__(
        self,
        model_name: str = "qwen3-32b",
        base_url: str = "http://112.111.20.89:8888/v1",
        api_key: str = "not-needed"
    ):
        """
        初始化 TenderTagger

        Args:
            model_name: 模型名称，默认为 "qwen3-32b"
            base_url: API 地址，默认为 "http://112.111.20.89:8888/v1"
            api_key: API密钥，默认为 "not-needed"
        """
        self.model_name = model_name
        self.base_url = base_url

        # 初始化 OpenAI 客户端
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

        # 验证 API 是否可用
        self._check_api()

    def _check_api(self):
        """检查 API 服务是否可用"""
        try:
            # 尝试获取模型列表
            models = self.client.models.list()
            print(f"API 已连接,使用模型: {self.model_name}")
        except Exception as e:
            print(f"警告: API 连接测试失败: {e}")
            print(f"将在实际调用时验证连接")

    def analyze_content(
        self,
        content: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.4,
        max_tokens: int = 8192,
        top_p: float = 0.7,
        repetition_penalty: float = 1.05
    ) -> str:
        """
        使用模型分析文本内容

        Args:
            content: 要分析的文本内容
            system_prompt: 系统提示词，定义模型的任务
            temperature: 温度参数，控制生成的随机性 (0-1)
            max_tokens: 生成文本的最大 token 数
            top_p: top_p 参数
            repetition_penalty: 重复惩罚参数

        Returns:
            模型生成的分析结果
        """
        if system_prompt is None:
            system_prompt = "你是一个专业的招标文件分析助手，请仔细分析以下内容并提取关键信息。"

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                extra_body={
                    "repetition_penalty": repetition_penalty
                },
                timeout=120.0
            )

            result = response.choices[0].message.content
            return result or ""

        except Exception as e:
            return f"错误: API 请求失败 - {str(e)}"

    def analyze_json_file(
        self,
        json_path: Path,
        system_prompt: Optional[str] = None,
        extract_key: Optional[str] = None,
        max_content_length: int = 8000
    ) -> Dict[str, Any]:
        """
        分析 JSON 文件内容

        Args:
            json_path: JSON 文件路径
            system_prompt: 系统提示词
            extract_key: 如果指定，只提取 JSON 中特定 key 的内容进行分析
            max_content_length: 最大内容长度，避免 token 超限

        Returns:
            包含原始数据和分析结果的字典
        """
        # 读取 JSON 文件
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 提取要分析的内容
        if extract_key:
            content = json.dumps(data.get(extract_key, data), ensure_ascii=False, indent=2)
        else:
            content = json.dumps(data, ensure_ascii=False, indent=2)

        # 截断过长的内容
        if len(content) > max_content_length:
            print(f"警告: 内容过长 ({len(content)} 字符)，截断到 {max_content_length} 字符")
            content = content[:max_content_length] + "\n... (内容已截断)"

        # 分析内容
        print(f"正在分析文件: {json_path.name}")
        analysis_result = self.analyze_content(content, system_prompt)

        return {
            "original_data": data,
            "analysis_result": analysis_result,
            "source_file": str(json_path)
        }


def main():
    """测试函数 - 简单问答测试"""
    # 初始化 TenderTagger
    try:
        tagger = TenderTagger()  # 使用默认配置
    except Exception as e:
        print(f"初始化失败: {e}")
        return

    # 简单的测试问题
    test_question = "你好，请用一句话介绍一下你自己，并告诉我 1+1 等于几？"

    print(f"\n问题: {test_question}")
    print("=" * 60)
    print("正在请求模型...")

    # 调用模型
    answer = tagger.analyze_content(
        content=test_question,
        system_prompt="你是一个友好的AI助手。",
        temperature=0.7,
        max_tokens=500
    )

    print("\n模型回答:")
    print("-" * 60)
    print(answer)
    print("-" * 60)


if __name__ == '__main__':
    main()
