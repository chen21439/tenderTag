"""
章节标注服务 - 从JSON提取字段并使用模型打标签
"""
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from openai import OpenAI
from datetime import datetime

# 添加项目根目录到 Python 路径
_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from app.utils.file_reader import FileReader, DEFAULT_FILE_DIR


class SectionTagger:
    """处理招标文件JSON数据,提取关键字段并使用模型进行标注"""

    def __init__(
        self,
        model_name: str = "qwen3-32b",
        base_url: str = "http://112.111.20.89:8888/v1",
        api_key: str = "not-needed",
        file_directory: Optional[str] = None
    ):
        """
        初始化 SectionTagger

        Args:
            model_name: 模型名称,默认为 "qwen3-32b"
            base_url: API 地址,默认为 "http://112.111.20.89:8888/v1"
            api_key: API密钥,默认为 "not-needed"
            file_directory: JSON文件目录,默认使用 FileReader.DEFAULT_FILE_DIR
        """
        self.model_name = model_name
        self.base_url = base_url

        # 初始化 OpenAI 客户端
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

        # 使用共享的文件读取器
        self.file_directory = file_directory or DEFAULT_FILE_DIR
        self.file_reader = FileReader(self.file_directory)

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

    def extract_section_fields(self, section: Dict[str, Any]) -> Dict[str, Any]:
        """
        从section节点提取关键字段

        Args:
            section: 章节节点数据

        Returns:
            提取的关键字段字典
        """
        extracted = {
            "type": section.get("type"),
            "level": section.get("level"),
            "text": section.get("text"),
            "normalized": section.get("normalized"),
            "heading_source": section.get("heading_source"),
            "id": section.get("id"),
        }

        # 提取 blocks (内容块) - 直接从section的blocks字段获取
        if "blocks" in section and section["blocks"]:
            extracted["blocks"] = self._extract_blocks(section["blocks"])

        return extracted

    def _extract_blocks(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        从blocks中提取关键信息

        Args:
            blocks: 内容块列表

        Returns:
            提取的内容块列表
        """
        extracted_blocks = []
        for block in blocks:
            if block.get("type") == "table":
                extracted_block = {
                    "type": "table",
                    "id": block.get("id"),
                    "header_row": block.get("header_row"),
                    "caption": block.get("caption"),
                    "detected_kind": block.get("detected_kind"),
                    "body_row_count": block.get("body_row_count"),
                }
                extracted_blocks.append(extracted_block)
            elif block.get("type") == "paragraph":
                # 只保留有文本的段落
                text = block.get("text", "").strip()
                if text:
                    extracted_block = {
                        "type": "paragraph",
                        "id": block.get("id"),
                        "text": text,
                    }
                    extracted_blocks.append(extracted_block)
            elif block.get("type") == "list":
                extracted_block = {
                    "type": "list",
                    "id": block.get("id"),
                    "text": block.get("text"),
                }
                extracted_blocks.append(extracted_block)

        return extracted_blocks

    def call_model(
        self,
        content: str,
        system_prompt: str,
        temperature: float = 0.4,
        max_tokens: int = 8192,
        top_p: float = 0.7,
        repetition_penalty: float = 1.05
    ) -> str:
        """
        调用模型进行标注

        Args:
            content: 要分析的内容
            system_prompt: 系统提示词
            temperature: 温度参数 (0-1)
            max_tokens: 最大token数
            top_p: top_p 参数
            repetition_penalty: 重复惩罚参数

        Returns:
            模型返回的标注结果
        """
        print(f"DEBUG: call_model开始执行", flush=True)

        try:
            print(f"DEBUG: 开始调用 OpenAI API", flush=True)
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
            print(f"DEBUG: 收到响应", flush=True)

            result = response.choices[0].message.content
            print(f"DEBUG: 解析完成", flush=True)
            return result or ""

        except Exception as e:
            print(f"DEBUG: 请求异常: {e}", flush=True)
            return f"错误: API请求失败 - {str(e)}"

    def tag_section(
        self,
        section: Dict[str, Any],
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        对单个章节进行标注

        Args:
            section: 章节数据
            system_prompt: 自定义系统提示词

        Returns:
            包含原始数据和标注结果的字典
        """
        print(f"DEBUG: tag_section开始执行", flush=True)
        # 提取关键字段
        extracted = self.extract_section_fields(section)
        print(f"DEBUG: extract_section_fields完成", flush=True)

        # 构建发送给模型的内容
        content = json.dumps(extracted, ensure_ascii=False, indent=2)
        print(f"DEBUG: JSON序列化完成, 长度: {len(content)}", flush=True)

        # 默认系统提示词
        if system_prompt is None:
            system_prompt = """你是一个专业的招标文件分析助手。
请分析以下章节数据,并识别:
1. 章节类型和层级
2. 内容块的类型(表格/段落/列表)
3. 如果是表格,判断是否为"评标表"、"偏离表"或"清单"类型
4. 提取关键信息和证据

请以JSON格式返回标注结果。"""

        # 调用模型
        section_text = extracted.get('text', 'N/A')[:30]
        print(f"    → 调用模型标注: {section_text}... (内容长度: {len(content)} 字符)", flush=True)

        print(f"DEBUG: 准备调用call_model", flush=True)
        tag_result = self.call_model(content, system_prompt)
        print(f"DEBUG: call_model返回", flush=True)

        print(f"    ← 模型返回结果长度: {len(tag_result)} 字符", flush=True)

        return {
            "original_section": section,
            "extracted_fields": extracted,
            "tag_result": tag_result
        }

    def tag_latest_json(
        self,
        task_id: str = "1978018096320905217",
        system_prompt: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        自动获取最新的分析JSON文件并进行标注

        Args:
            task_id: 任务ID
            system_prompt: 自定义系统提示词

        Returns:
            所有章节的标注结果列表
        """
        # 获取最新的JSON文件
        latest_json = self.file_reader.get_latest_analysis_json(task_id)
        if not latest_json:
            raise FileNotFoundError(f"未找到任务 {task_id} 的分析JSON文件")

        print(f"使用文件: {latest_json.name}")
        return self.tag_json_file(latest_json, system_prompt)

    def tag_json_file(
        self,
        json_path: Path,
        system_prompt: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        读取JSON文件并对所有章节进行标注

        Args:
            json_path: JSON文件路径
            system_prompt: 自定义系统提示词

        Returns:
            所有章节的标注结果列表
        """
        print(f"\n[1/5] 读取JSON文件: {json_path.name}", flush=True)
        # 使用 FileReader 读取文件
        content = self.file_reader.read_file(str(json_path))
        data = json.loads(content)
        print(f"[2/5] JSON解析成功", flush=True)

        results = []

        # 处理 tree 节点
        tree = data.get("tree", [])
        print(f"[3/5] 找到 {len(tree)} 个tree节点", flush=True)

        # 统计section数量
        section_count = 0
        for node in tree:
            if isinstance(node, dict) and node.get("type") == "section":
                section_count += 1
        print(f"[4/5] 预计需要标注 {section_count} 个section", flush=True)

        # 递归处理所有section节点
        processed_count = 0
        def process_node(node, depth=0):
            nonlocal processed_count
            print(f"DEBUG: process_node被调用, node类型: {type(node)}, depth: {depth}", flush=True)
            if isinstance(node, dict) and node.get("type") == "section":
                print(f"DEBUG: 进入section处理分支", flush=True)
                processed_count += 1
                print(f"DEBUG: processed_count已增加到 {processed_count}", flush=True)
                section_text = node.get("text", "N/A")
                print(f"DEBUG: section_text = {repr(section_text[:50] if section_text else 'None')}", flush=True)
                print(f"  [{processed_count}/{section_count}] 处理section (depth={depth}): {section_text[:50] if section_text else 'N/A'}", flush=True)

                # 标注当前section
                result = self.tag_section(node, system_prompt)
                results.append(result)

                print(f"  [{processed_count}/{section_count}] ✓ 完成: {section_text[:50]}")

                # 递归处理children (子章节)
                if "children" in node and node["children"]:
                    print(f"    └─ 处理 {len(node['children'])} 个子节点...")
                    for child in node["children"]:
                        process_node(child, depth + 1)
            elif isinstance(node, list):
                for item in node:
                    process_node(item, depth)

        # 处理tree中的所有节点
        print(f"[5/5] 开始递归处理...\n", flush=True)
        print(f"DEBUG: tree类型: {type(tree)}, 长度: {len(tree) if isinstance(tree, list) else 'N/A'}", flush=True)
        if isinstance(tree, list) and len(tree) > 0:
            print(f"DEBUG: 第一个元素类型: {type(tree[0])}, 是否为dict: {isinstance(tree[0], dict)}", flush=True)
            if isinstance(tree[0], dict):
                print(f"DEBUG: 第一个元素的type字段: {tree[0].get('type')}", flush=True)
        process_node(tree)

        print(f"\n✓ 共标注了 {len(results)} 个章节", flush=True)
        return results

    def save_results(self, results: List[Dict[str, Any]], output_path: Path):
        """
        保存标注结果到文件

        Args:
            results: 标注结果列表
            output_path: 输出文件路径
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"标注结果已保存到: {output_path}")


def main():
    """测试函数"""
    import sys
    import io
    from pathlib import Path as P

    # 添加项目根目录到 Python 路径
    project_root = P(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # 设置控制台输出编码为UTF-8
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # 初始化标注器
    try:
        tagger = SectionTagger()  # 使用默认配置
    except Exception as e:
        print(f"初始化失败: {e}")
        return

    # 支持两种用法:
    # 1. 不传参数: 自动使用最新的分析JSON文件
    # 2. 传入文件路径: 使用指定的JSON文件
    if len(sys.argv) < 2:
        print(f"使用默认目录: {DEFAULT_FILE_DIR}")
        print("自动获取最新的分析JSON文件...")
        try:
            results = tagger.tag_latest_json()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path(DEFAULT_FILE_DIR) / f"latest_tagged_{timestamp}.json"
        except FileNotFoundError as e:
            print(f"错误: {e}")
            return
    else:
        json_path = Path(sys.argv[1])
        if not json_path.exists():
            print(f"文件不存在: {json_path}")
            return

        # 执行标注
        results = tagger.tag_json_file(json_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = json_path.parent / f"{json_path.stem}_tagged_{timestamp}.json"

    # 保存结果
    tagger.save_results(results, output_path)


if __name__ == '__main__':
    main()
