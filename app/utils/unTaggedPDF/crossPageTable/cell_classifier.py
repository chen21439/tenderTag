"""
跨页单元格智能分类器
使用 AI 模型判断两个跨页单元格是否是同一个单元格被截断

基于 Qwen3-32B 模型进行智能判断
"""
from typing import Dict, Any, List, Tuple, Optional
from openai import OpenAI
import json


class PromptTemplates:
    """提示词模板类"""

    # 行级别提示词
    ROW_SYSTEM_PROMPT = """你是一个专业的PDF表格分析专家，擅长判断跨页行内容是否被分页符截断。

你的任务：
判断两行数据是否是"表格中同一行被分页截断"，只关注行内容本身的连续性。

输入数据格式：
- 上页最后一行：多个单元格的内容（key-value格式）
- 下页第一行：多个单元格的内容（key-value格式）

输出格式（JSON）：
{
    "should_merge": true/false,
    "confidence": 0.95,
    "reason": "第0列内容明显被截断，应该合并"
}

**重要**：只输出 JSON，不要输出其他内容。
"""


class CrossPageCellClassifier:
    """使用 AI 模型判断跨页单元格是否应该合并"""

    def __init__(
        self,
        model_name: str = "qwen3-14b",
        base_url: str = "http://112.111.54.86:10011/v1",
        api_key: str = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1aWQiOiIxOTE3MTIzNDc4NDI5ODg4NTEzIiwiZGVwdE5hbWUiOiIiLCJhcmVhQ29kZSI6IiIsInJvbGUiOiJjdXN0b20iLCJhcmVhTmFtZSI6IiIsImNyZWF0ZVRpbWUiOjE3NTg1OTY0ODQsImFwcElkIjoiMTAwMDAwMDAwMDAwMDAwMDAiLCJ0ZWxlcGhvbmUiOiIxODc1MDc5OTAxOSIsInVzZXJUeXBlIjoiaW5zaWRlIiwidXNlcm5hbWUiOiJjaGVueGlhb21pbiJ9.EtvuTHzkSfozetNefVBz4jMjhbHkGi3V-JtWp6_WebU",
        temperature: float = 0.4,  # 根据API示例调整
        max_tokens: int = 8192,  # 根据API示例调整
        top_p: float = 0.7,  # 新增参数
        repetition_penalty: float = 1.05,  # 新增参数
        truncate_length: int = 50  # 字符截取长度（取最后/最前n个字符）
    ):
        """
        初始化跨页单元格分类器

        Args:
            model_name: 模型名称，默认为 "qwen3-32b"
            base_url: API 地址
            api_key: API密钥
            temperature: 温度参数（0-1），越低越确定
            max_tokens: 生成文本的最大 token 数
            truncate_length: 字符截取长度，用于行级别判断
        """
        self.model_name = model_name
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.repetition_penalty = repetition_penalty
        self.truncate_length = truncate_length

        # 初始化 OpenAI 客户端
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

        # 从提示词模板类加载
        self.row_system_prompt = PromptTemplates.ROW_SYSTEM_PROMPT

        # 验证 API 是否可用
        self._check_api()

    def _check_api(self):
        """检查 API 服务是否可用"""
        try:
            models = self.client.models.list()
            print(f"[CellClassifier] API 已连接，使用模型: {self.model_name}")
        except Exception as e:
            print(f"[CellClassifier] 警告: API 连接测试失败: {e}")
            print(f"[CellClassifier] 将在实际调用时验证连接")

    def _truncate_text(self, text: str, from_end: bool = True) -> str:
        """
        截取文本（取最后/最前 n 个字符）

        Args:
            text: 要截取的文本
            from_end: True=取最后n个字符，False=取最前n个字符

        Returns:
            截取后的文本
        """
        if not text:
            return text

        if len(text) <= self.truncate_length:
            return text

        if from_end:
            # 取最后 n 个字符
            return "..." + text[-self.truncate_length:]
        else:
            # 取最前 n 个字符
            return text[:self.truncate_length] + "..."

    def classify_row_pairs_batch(
        self,
        row_pairs: List[Dict[str, Any]],
        max_retries: int = 3,
        retry_delay: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        批量判断多个行对是否应该合并（行级别）

        Args:
            row_pairs: 行对列表，每个元素格式：
                {
                    "prev_row": {"第0列": "内容...", "第1列": "5分", ...},
                    "next_row": {"第0列": "内容...", "第1列": "", ...},
                    "context": {
                        "prev_table_id": "t1_p1",
                        "next_table_id": "t1_p2",
                        "prev_page": 1,
                        "next_page": 2,
                        "hint_score": 0.95
                    }
                }
            max_retries: 最大重试次数（默认3次）
            retry_delay: 重试延迟（秒，默认2秒）

        Returns:
            判断结果列表
        """
        if not row_pairs:
            return []

        print(f"[CellClassifier] 批量判断 {len(row_pairs)} 个跨页行对...")

        # 构建批量请求
        user_content = self._build_batch_row_prompt(row_pairs)

        # 打印发送的数据
        print("\n" + "="*80)
        print("[CellClassifier] 📤 发送给AI的数据:")
        print("="*80)
        print(f"System Prompt:\n{self.row_system_prompt}\n")
        print(f"User Content:\n{user_content}")
        print("="*80 + "\n")

        # 重试逻辑
        import time
        last_error = None

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    print(f"[CellClassifier] 重试 {attempt}/{max_retries-1}...")
                    time.sleep(retry_delay)

                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self.row_system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens * len(row_pairs),  # 批量需要更多 tokens
                    top_p=self.top_p,
                    extra_body={
                        "repetition_penalty": self.repetition_penalty
                    },
                    timeout=60.0  # 60秒超时
                )

                result_text = response.choices[0].message.content.strip()

                # 打印AI返回的数据
                print("\n" + "="*80)
                print("[CellClassifier] 📥 AI返回的数据:")
                print("="*80)
                print(result_text)
                print("="*80 + "\n")

                # 解析批量结果
                results = self._parse_batch_result(result_text, len(row_pairs))

                # 打印解析后的结果
                print("\n" + "="*80)
                print("[CellClassifier] 📊 解析后的结果:")
                print("="*80)
                for i, result in enumerate(results):
                    should_merge = result.get('should_merge', False)
                    confidence = result.get('confidence', 0)
                    reason = result.get('reason', 'N/A')
                    status = "✅ 合并" if should_merge else "❌ 不合并"
                    print(f"行对 {i+1}: {status} (置信度: {confidence:.2f}) - {reason}")
                print("="*80 + "\n")

                print(f"[CellClassifier] ✅ 判断成功")
                return results

            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    print(f"[CellClassifier] ⚠️  请求失败: {e}，将在 {retry_delay} 秒后重试...")
                else:
                    print(f"[CellClassifier] ❌ 批量判断失败（已重试 {max_retries} 次）: {e}")

        # 所有重试都失败，返回默认结果
        return [
            {
                "should_merge": False,
                "confidence": 0.0,
                "reason": f"API 请求失败: {str(last_error)}",
                "error": str(last_error)
            }
            for _ in range(len(row_pairs))
        ]

    def _build_batch_row_prompt(self, row_pairs: List[Dict]) -> str:
        """构建批量行对判断的提示词"""
        prompt = "请分析以下跨页表格的行对，判断每一对是否应该合并：\n\n"

        for i, pair in enumerate(row_pairs):
            prompt += f"## 行对 {i+1}\n\n"

            # 上页最后一行（截取字符）
            prompt += f"**上页最后一行**：\n"
            prev_row = pair.get('prev_row', {})
            for col, content in prev_row.items():
                truncated = self._truncate_text(content, from_end=True)  # 取最后n个字符
                prompt += f"  - {col}: {truncated}\n"

            # 下页第一行（截取字符）
            prompt += f"\n**下页第一行**：\n"
            next_row = pair.get('next_row', {})
            for col, content in next_row.items():
                truncated = self._truncate_text(content, from_end=False)  # 取最前n个字符
                prompt += f"  - {col}: {truncated}\n"

            # 上下文信息
            if 'context' in pair:
                ctx = pair['context']
                prompt += f"\n**上下文信息**：\n"
                prompt += f"  - 页码：{ctx.get('prev_page')} → {ctx.get('next_page')}\n"
                prompt += f"  - Hint得分：{ctx.get('hint_score', 0):.2f}\n"

            prompt += "\n" + "-" * 60 + "\n\n"

        prompt += """
请对每一对行输出 JSON 格式的判断结果，返回一个 JSON 数组：
[
    {"should_merge": true/false, "confidence": 0.95, "reason": "..."},
    {"should_merge": true/false, "confidence": 0.90, "reason": "..."},
    ...
]

**重要**：只输出 JSON 数组，不要输出其他内容。
"""
        return prompt

    def _parse_batch_result(self, result_text: str, expected_count: int) -> List[Dict[str, Any]]:
        """解析批量结果"""
        try:
            # 移除可能的 markdown 代码块标记
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()

            results = json.loads(result_text)

            # 验证结果格式
            if not isinstance(results, list):
                raise ValueError("结果不是数组")

            if len(results) != expected_count:
                print(f"[CellClassifier] 警告: 期望 {expected_count} 个结果，实际收到 {len(results)} 个")

            # 补全缺失的结果
            while len(results) < expected_count:
                results.append({
                    "should_merge": False,
                    "confidence": 0.0,
                    "reason": "结果缺失"
                })

            # 验证每个结果
            for i, result in enumerate(results):
                if "should_merge" not in result:
                    results[i] = {
                        "should_merge": False,
                        "confidence": 0.0,
                        "reason": "结果格式错误",
                        "error": "Missing 'should_merge' field"
                    }

            return results[:expected_count]

        except (json.JSONDecodeError, ValueError) as e:
            print(f"[CellClassifier] JSON 解析失败: {e}")
            print(f"[CellClassifier] 原始响应: {result_text[:200]}...")
            # 返回默认结果
            return [
                {
                    "should_merge": False,
                    "confidence": 0.0,
                    "reason": f"JSON 解析失败: {str(e)}",
                    "error": "Parse error"
                }
                for _ in range(expected_count)
            ]


if __name__ == '__main__':
    # 简单测试（如需测试，使用 test_row_classifier.py）
    print("跨页行级别分类器 - 使用 test_row_classifier.py 进行测试")