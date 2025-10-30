"""
跨页单元格智能分类器
使用 AI 模型判断两个跨页单元格是否是同一个单元格被截断

基于 Qwen3-32B 模型进行智能判断
"""
from typing import Dict, Any, List, Tuple, Optional
from openai import OpenAI
import json


class CrossPageCellClassifier:
    """使用 AI 模型判断跨页单元格是否应该合并"""

    def __init__(
        self,
        model_name: str = "qwen3-32b",
        base_url: str = "http://112.111.20.89:8888/v1",
        api_key: str = "not-needed",
        temperature: float = 0.1,  # 低温度，输出更确定
        max_tokens: int = 100,  # 只需要简单的判断结果
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
        self.truncate_length = truncate_length

        # 初始化 OpenAI 客户端
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

        # 系统提示词（单元格级别）
        self.system_prompt = """你是一个专业的PDF表格分析专家，擅长判断跨页表格中的单元格是否被分页符截断。

你的任务：
1. 分析两个单元格的内容（上页最后一行的单元格 + 下页第一行的单元格）
2. 判断它们是否是同一个单元格被分页符截断

判断依据：
- **应该合并（截断）的情况**：
  - 上页内容以"、，；：-"等结尾，下页是后续内容
  - 上页内容是不完整的句子，下页是补全部分
  - 上页内容以"（"、"【"等开始符号结尾，下页以"）"、"】"等结束符号开始
  - 上页内容突然中断，下页内容明显是延续
  - 两个内容合并后语义完整，分开则语义不通

- **不应合并（独立）的情况**：
  - 上页内容是完整的句子或词组
  - 下页内容是全新的独立内容
  - 两者之间没有语义连续性
  - 两者是不同的数据项或配置项

输出格式：
只需输出一个 JSON 对象：
{
    "should_merge": true/false,  # 是否应该合并
    "confidence": 0.95,          # 置信度 (0-1)
    "reason": "原因说明"         # 简短说明
}

**重要**：只输出 JSON，不要输出其他内容。
"""

        # 系统提示词（行级别）
        self.row_system_prompt = """你是一个专业的PDF表格分析专家，擅长判断跨页表格中的数据行是否被分页符截断。

你的任务：
判断两行数据是否是"同一行被分页截断"

输入数据格式：
- 上页最后一行：多个单元格的内容（key-value格式）
- 下页第一行：多个单元格的内容（key-value格式）

判断依据：
- **应该合并（同一行被截断）**：
  1. 某个单元格内容明显被截断（上页以"、，；：-"等结尾，下页是后续内容）
  2. 上页某列是不完整的句子，下页是补全部分
  3. 下页某些列为空，但上页对应列有内容且被截断
  4. 整体看，下页第一行像是上页最后一行的"延续"
  5. 上页某列以"（"、"【"等开始符号结尾，下页以"）"、"】"等结束符号开始

- **不应合并（两行独立）**：
  1. 两行都有完整的独立内容
  2. 下页第一行是新的数据项
  3. 没有明显的内容截断痕迹
  4. 两行的数据结构不同（如上页是表头，下页是数据）
  5. 所有列的内容都是完整的

输出格式（JSON）：
{
    "should_merge": true/false,
    "confidence": 0.95,
    "reason": "第0列内容明显被截断，应该合并"
}

**重要**：只输出 JSON，不要输出其他内容。
"""

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

    def classify_cell_pair(
        self,
        prev_cell_content: str,
        next_cell_content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        判断两个跨页单元格是否应该合并

        Args:
            prev_cell_content: 上页单元格的内容
            next_cell_content: 下页单元格的内容
            context: 可选的上下文信息（如列名、相邻单元格内容等）

        Returns:
            判断结果字典：
            {
                "should_merge": bool,      # 是否应该合并
                "confidence": float,       # 置信度 (0-1)
                "reason": str,             # 原因说明
                "error": str (optional)    # 如果出错，返回错误信息
            }
        """
        # 构建用户输入
        user_content = f"""请分析以下跨页单元格是否应该合并：

**上页单元格内容**：
```
{prev_cell_content}
```

**下页单元格内容**：
```
{next_cell_content}
```
"""

        # 如果有上下文信息，添加到输入中
        if context:
            user_content += f"\n**上下文信息**：\n```json\n{json.dumps(context, ensure_ascii=False, indent=2)}\n```\n"

        user_content += "\n请输出 JSON 格式的判断结果。"

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=0.9,
                extra_body={
                    "repetition_penalty": 1.05
                },
                timeout=30.0  # 30秒超时
            )

            result_text = response.choices[0].message.content.strip()

            # 尝试解析 JSON
            # 移除可能的 markdown 代码块标记
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()

            result = json.loads(result_text)

            # 验证结果格式
            if "should_merge" not in result:
                return {
                    "should_merge": False,
                    "confidence": 0.0,
                    "reason": "模型输出格式错误",
                    "error": "Missing 'should_merge' field"
                }

            return result

        except json.JSONDecodeError as e:
            return {
                "should_merge": False,
                "confidence": 0.0,
                "reason": f"JSON 解析失败: {str(e)}",
                "error": f"JSON decode error: {str(e)}",
                "raw_response": result_text if 'result_text' in locals() else None
            }

        except Exception as e:
            return {
                "should_merge": False,
                "confidence": 0.0,
                "reason": f"API 请求失败: {str(e)}",
                "error": str(e)
            }

    def classify_cell_pairs_batch(
        self,
        cell_pairs: List[Tuple[str, str]],
        contexts: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        批量判断多个单元格对是否应该合并

        Args:
            cell_pairs: 单元格对列表，每个元素是 (prev_content, next_content)
            contexts: 可选的上下文信息列表

        Returns:
            判断结果列表
        """
        results = []

        if contexts is None:
            contexts = [None] * len(cell_pairs)

        for i, (prev_content, next_content) in enumerate(cell_pairs):
            context = contexts[i] if i < len(contexts) else None
            result = self.classify_cell_pair(prev_content, next_content, context)
            results.append(result)

        return results

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
        row_pairs: List[Dict[str, Any]]
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

        Returns:
            判断结果列表
        """
        if not row_pairs:
            return []

        print(f"[CellClassifier] 批量判断 {len(row_pairs)} 个跨页行对...")

        # 构建批量请求
        user_content = self._build_batch_row_prompt(row_pairs)

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.row_system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens * len(row_pairs),  # 批量需要更多 tokens
                top_p=0.9,
                extra_body={
                    "repetition_penalty": 1.05
                },
                timeout=60.0  # 60秒超时
            )

            result_text = response.choices[0].message.content.strip()

            # 解析批量结果
            results = self._parse_batch_result(result_text, len(row_pairs))
            return results

        except Exception as e:
            print(f"[CellClassifier] 批量判断失败: {e}")
            # 返回默认结果（全部不合并）
            return [
                {
                    "should_merge": False,
                    "confidence": 0.0,
                    "reason": f"API 请求失败: {str(e)}",
                    "error": str(e)
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

    def analyze_raw_json_with_hints(
        self,
        raw_json_data: Dict[str, Any],
        hints_by_page: Dict[int, Dict]
    ) -> Dict[str, Any]:
        """
        分析 raw.json 数据，使用 AI 判断有 hint 的单元格是否应该合并

        Args:
            raw_json_data: raw.json 的数据（包含所有表格）
            hints_by_page: 续页 hint 信息

        Returns:
            分析结果，包含每个单元格对的判断
        """
        results = {
            "total_cell_pairs": 0,
            "classified_pairs": [],
            "summary": {
                "should_merge": 0,
                "should_not_merge": 0,
                "errors": 0
            }
        }

        tables = raw_json_data.get('tables', [])
        if not tables:
            return results

        # 按页码分组表格
        tables_by_page = {}
        for table in tables:
            page = table.get('page', 1)
            if page not in tables_by_page:
                tables_by_page[page] = []
            tables_by_page[page].append(table)

        # 遍历有 hint 的页面
        for next_page, hint in hints_by_page.items():
            if next_page not in tables_by_page:
                continue

            prev_page = next_page - 1
            if prev_page not in tables_by_page:
                continue

            prev_tables = tables_by_page[prev_page]
            next_tables = tables_by_page[next_page]

            # 获取上页最后一张表和下一页第一张表
            if not prev_tables or not next_tables:
                continue

            prev_table = prev_tables[-1]  # 最后一张
            next_table = next_tables[0]   # 第一张

            # 获取上页最后一行和下页第一行
            prev_rows = prev_table.get('rows', [])
            next_rows = next_table.get('rows', [])

            if not prev_rows or not next_rows:
                continue

            prev_last_row = prev_rows[-1]
            next_first_row = next_rows[0]

            prev_cells = prev_last_row.get('cells', [])
            next_cells = next_first_row.get('cells', [])

            # 遍历所有列，判断每个单元格对
            min_cols = min(len(prev_cells), len(next_cells))
            for col_idx in range(min_cols):
                prev_cell = prev_cells[col_idx]
                next_cell = next_cells[col_idx]

                prev_content = prev_cell.get('content', '').strip()
                next_content = next_cell.get('content', '').strip()

                # 跳过两边都是空的情况
                if not prev_content and not next_content:
                    continue

                # 准备上下文信息
                context = {
                    "prev_table_id": prev_table.get('id'),
                    "next_table_id": next_table.get('id'),
                    "prev_page": prev_page,
                    "next_page": next_page,
                    "col_index": col_idx,
                    "hint_score": hint.get('score', 0),
                    "column_name": prev_table.get('columns', [{}])[col_idx].get('name', '') if col_idx < len(prev_table.get('columns', [])) else ''
                }

                # 调用 AI 模型判断
                print(f"[CellClassifier] 分析单元格对: 页{prev_page}→{next_page}, 列{col_idx}")
                classification = self.classify_cell_pair(prev_content, next_content, context)

                # 记录结果
                cell_pair_result = {
                    "prev_page": prev_page,
                    "next_page": next_page,
                    "col_index": col_idx,
                    "prev_content": prev_content,
                    "next_content": next_content,
                    "context": context,
                    "classification": classification
                }

                results["classified_pairs"].append(cell_pair_result)
                results["total_cell_pairs"] += 1

                # 更新统计
                if classification.get("error"):
                    results["summary"]["errors"] += 1
                elif classification.get("should_merge"):
                    results["summary"]["should_merge"] += 1
                else:
                    results["summary"]["should_not_merge"] += 1

        return results


def main():
    """测试函数"""
    print("=" * 60)
    print("跨页单元格智能分类器 - 测试")
    print("=" * 60)

    # 初始化分类器
    try:
        classifier = CrossPageCellClassifier()
    except Exception as e:
        print(f"初始化失败: {e}")
        return

    # 测试用例1：应该合并的情况（句子被截断）
    test_cases = [
        {
            "name": "测试1: 句子被截断",
            "prev": "根据投标人提供的项目技术方案，包括总体架构设计、业务架构设计、数据架构设计、技术架构设",
            "next": "计、网络架构设计、与现有国土空间规划\"一张图\"实施监测系统及相关系统对接方案等方面进行综合评审。",
            "expected": True
        },
        {
            "name": "测试2: 完整句子，不应合并",
            "prev": "技术方案设计科学、合理、实际可实施、操作性强",
            "next": "整体技术方案设计合理可行但内容通用",
            "expected": False
        },
        {
            "name": "测试3: 逗号结尾被截断",
            "prev": "针对本期项目综合服务要求响应完善，与现有国土空间规划\"一张图\"实施监测系统及相关系统进行充分对接，",
            "next": "对项目整体技术需求范围覆盖程度高，完全满足招标相关需求",
            "expected": True
        },
        {
            "name": "测试4: 括号被截断",
            "prev": "整体技术方案设计科学、合理、实际可实施、操作性强，针对本期项目综合服务要求响应完善（",
            "next": "包括但不限于以下内容）",
            "expected": True
        }
    ]

    # 执行测试
    for test_case in test_cases:
        print(f"\n{test_case['name']}")
        print(f"上页内容: {test_case['prev'][:50]}...")
        print(f"下页内容: {test_case['next'][:50]}...")
        print(f"预期结果: {'应该合并' if test_case['expected'] else '不应合并'}")

        result = classifier.classify_cell_pair(test_case['prev'], test_case['next'])

        print(f"\n判断结果:")
        print(f"  should_merge: {result.get('should_merge')}")
        print(f"  confidence: {result.get('confidence', 0):.2f}")
        print(f"  reason: {result.get('reason', 'N/A')}")

        # 判断是否符合预期
        is_correct = result.get('should_merge') == test_case['expected']
        print(f"  ✅ 正确" if is_correct else f"  ❌ 错误")
        print("-" * 60)


if __name__ == '__main__':
    main()