"""
PDF内容提取主协调器
协调表格提取器和段落提取器，统一编号和保存
"""
import json
from pathlib import Path
from typing import Dict, Any
import fitz  # PyMuPDF

try:
    from .table_extractor import TableExtractor
    from .paragraph_extractor import ParagraphExtractor
except ImportError:
    from table_extractor import TableExtractor
    from paragraph_extractor import ParagraphExtractor


class PDFContentExtractor:
    """PDF内容提取主协调器"""

    def __init__(self, pdf_path: str):
        """
        初始化PDF内容提取器

        Args:
            pdf_path: PDF文件路径
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

        # 初始化各个提取器
        self.table_extractor = TableExtractor(pdf_path)
        self.paragraph_extractor = ParagraphExtractor(pdf_path)

        # 全局块计数器（用于docN编号）
        self.block_counter = 0

    def extract_tables(self):
        """
        仅提取表格

        Returns:
            表格列表
        """
        return self.table_extractor.extract_tables()

    def extract_paragraphs(self, table_bboxes_per_page: Dict[int, list] = None):
        """
        仅提取段落

        Args:
            table_bboxes_per_page: 每页的表格bbox列表（如不提供，自动检测）

        Returns:
            段落列表
        """
        return self.paragraph_extractor.extract_paragraphs(table_bboxes_per_page)

    def extract_all_content(self) -> Dict[str, Any]:
        """
        提取所有内容（表格+段落），按页面和Y坐标排序，统一编号

        Returns:
            包含所有内容的字典
        """
        # 1. 提取表格
        tables_raw = self.table_extractor.extract_tables()

        # 2. 获取表格bbox（供段落提取使用）
        table_bboxes_per_page = self._build_table_bboxes_map(tables_raw)

        # 3. 提取段落
        paragraphs_raw = self.paragraph_extractor.extract_paragraphs(table_bboxes_per_page)

        # 4. 合并所有内容块，添加排序键
        all_blocks = []

        # 添加表格
        for table in tables_raw:
            # 计算表格的y0（用于排序）
            table_y0 = table.get("bbox", [0, 0, 0, 0])[1] if table.get("bbox") else 0
            all_blocks.append({
                "type": "table",
                "page": table["page"],
                "y0": table_y0,
                "data": table
            })

        # 添加段落
        for para in paragraphs_raw:
            all_blocks.append({
                "type": "paragraph",
                "page": para["page"],
                "y0": para["y0"],
                "data": para
            })

        # 5. 按页面顺序和y坐标排序
        all_blocks.sort(key=lambda x: (x["page"], x["y0"]))

        # 6. 重新分配docN编号
        structured_blocks = []
        self.block_counter = 0

        for block in all_blocks:
            self.block_counter += 1
            doc_id = f"doc{self.block_counter:03d}"

            if block["type"] == "table":
                # 更新表格的id
                table_data = block["data"]
                table_data["id"] = doc_id

                # 更新所有cell的id
                for row in table_data.get("rows", []):
                    row_id = row["id"]
                    for cell in row.get("cells", []):
                        col_id = cell["col_id"]
                        cell["id"] = f"{doc_id}-{row_id}-{col_id}"

                # 更新嵌套表格的parent_table_id
                for row in table_data.get("rows", []):
                    for cell in row.get("cells", []):
                        if "nested_tables" in cell:
                            for nested_table in cell["nested_tables"]:
                                nested_table["parent_table_id"] = doc_id

                structured_blocks.append(table_data)

            elif block["type"] == "paragraph":
                # 构建结构化段落
                para_data = block["data"]
                structured_blocks.append({
                    "type": "paragraph",
                    "id": doc_id,
                    "page": para_data["page"],
                    "bbox": para_data["bbox"],
                    "content": para_data["content"]
                })

        # 7. 获取页面元数据
        metadata = self._get_page_metadata()

        return {
            "pdf_file": str(self.pdf_path),
            "total_blocks": len(structured_blocks),
            "total_tables": sum(1 for b in structured_blocks if b.get("type") == "table"),
            "total_paragraphs": sum(1 for b in structured_blocks if b.get("type") == "paragraph"),
            "blocks": structured_blocks,
            "page_metadata": metadata
        }

    def extract_all_tables(self) -> Dict[str, Any]:
        """
        仅提取表格（带元数据）

        Returns:
            包含表格数据和元数据的字典
        """
        tables = self.table_extractor.extract_tables()

        # 添加docN编号
        self.block_counter = 0
        for table in tables:
            self.block_counter += 1
            doc_id = f"doc{self.block_counter:03d}"
            table["id"] = doc_id

            # 更新cell id
            for row in table.get("rows", []):
                row_id = row["id"]
                for cell in row.get("cells", []):
                    col_id = cell["col_id"]
                    cell["id"] = f"{doc_id}-{row_id}-{col_id}"

            # 更新嵌套表格的parent_table_id
            for row in table.get("rows", []):
                for cell in row.get("cells", []):
                    if "nested_tables" in cell:
                        for nested_table in cell["nested_tables"]:
                            nested_table["parent_table_id"] = doc_id

        metadata = self._get_page_metadata()

        return {
            "pdf_file": str(self.pdf_path),
            "total_tables": len(tables),
            "tables": tables,
            "page_metadata": metadata
        }

    def extract_all_paragraphs(self) -> Dict[str, Any]:
        """
        仅提取段落（带元数据和编号）

        Returns:
            包含段落数据和元数据的字典
        """
        # 获取表格bbox
        table_bboxes_per_page = self.table_extractor.get_table_bboxes_per_page()

        # 提取段落
        paragraphs_raw = self.paragraph_extractor.extract_paragraphs(table_bboxes_per_page)

        # 按页面和y坐标排序
        paragraphs_raw.sort(key=lambda x: (x["page"], x["y0"]))

        # 分配docN编号
        structured_paragraphs = []
        self.block_counter = 0

        for para in paragraphs_raw:
            self.block_counter += 1
            doc_id = f"doc{self.block_counter:03d}"

            structured_paragraphs.append({
                "type": "paragraph",
                "id": doc_id,
                "page": para["page"],
                "bbox": para["bbox"],
                "content": para["content"]
            })

        metadata = self._get_page_metadata()

        return {
            "pdf_file": str(self.pdf_path),
            "total_paragraphs": len(structured_paragraphs),
            "paragraphs": structured_paragraphs,
            "page_metadata": metadata
        }

    def save_to_json(self, output_dir: str = None, include_paragraphs: bool = True,
                     task_id: str = None) -> Dict[str, str]:
        """
        提取内容并保存到JSON文件

        Args:
            output_dir: 输出目录路径，如果为None则保存到PDF同目录
            include_paragraphs: 是否提取并保存段落
            task_id: 任务ID，用于生成文件名（如：taskId_table.json）

        Returns:
            保存的文件路径字典
        """
        # 确定输出目录
        if output_dir is None:
            output_dir = self.pdf_path.parent
        else:
            output_dir = Path(output_dir)

        # 确保输出目录存在
        output_dir.mkdir(parents=True, exist_ok=True)

        # 确定文件名前缀
        if task_id:
            table_filename = f"{task_id}_table.json"
            paragraph_filename = f"{task_id}_paragraph.json"
        else:
            table_filename = "table.json"
            paragraph_filename = "paragraph.json"

        result_paths = {}

        # 提取并保存表格
        tables_result = self.extract_all_tables()
        table_path = output_dir / table_filename
        with open(table_path, 'w', encoding='utf-8') as f:
            json.dump(tables_result, f, ensure_ascii=False, indent=2)
        result_paths["tables"] = str(table_path)

        # 提取并保存段落（如果需要）
        if include_paragraphs:
            paragraphs_result = self.extract_all_paragraphs()
            paragraph_path = output_dir / paragraph_filename
            with open(paragraph_path, 'w', encoding='utf-8') as f:
                json.dump(paragraphs_result, f, ensure_ascii=False, indent=2)
            result_paths["paragraphs"] = str(paragraph_path)

        return result_paths

    def _build_table_bboxes_map(self, tables):
        """
        从表格列表构建每页的bbox映射

        Args:
            tables: 表格列表

        Returns:
            {page_num: [bbox1, bbox2, ...]}
        """
        table_bboxes = {}
        for table in tables:
            page = table.get("page", 1)
            bbox = table.get("bbox")
            if bbox:
                if page not in table_bboxes:
                    table_bboxes[page] = []
                table_bboxes[page].append(tuple(bbox))
        return table_bboxes

    def _get_page_metadata(self):
        """
        获取PDF页面元数据

        Returns:
            页面元数据列表
        """
        metadata = []
        doc = fitz.open(self.pdf_path)

        for page_num in range(len(doc)):
            page = doc[page_num]
            text_blocks = page.get_text("dict")

            metadata.append({
                "page": page_num + 1,
                "method": "pymupdf",
                "width": page.rect.width,
                "height": page.rect.height,
                "blocks_count": len(text_blocks.get("blocks", []))
            })

        doc.close()
        return metadata


# 便捷函数
def extract_pdf_content(pdf_path: str, output_path: str = None, include_paragraphs: bool = True) -> Dict[str, str]:
    """
    提取PDF内容并保存到JSON

    Args:
        pdf_path: PDF文件路径
        output_path: 输出目录路径
        include_paragraphs: 是否包含段落

    Returns:
        保存的文件路径字典
    """
    extractor = PDFContentExtractor(pdf_path)
    return extractor.save_to_json(output_path, include_paragraphs=include_paragraphs)


def extract_pdf_tables(pdf_path: str, output_path: str = None) -> Dict[str, str]:
    """
    仅提取PDF表格并保存到JSON

    Args:
        pdf_path: PDF文件路径
        output_path: 输出目录路径

    Returns:
        保存的文件路径字典
    """
    extractor = PDFContentExtractor(pdf_path)
    return extractor.save_to_json(output_path, include_paragraphs=False)


# 主测试函数
def main():
    """
    主测试方法
    """
    # 从taskId构建路径
    task_id = "国土空间规划实施监测网络建设项目"
    base_dir = Path(r"E:\programFile\AIProgram\docxServer\pdf\task\国土空间规划实施监测网络建设项目")
    pdf_path = base_dir / f"{task_id}.pdf"

    print(f"开始测试PDF内容提取...")
    print(f"Task ID: {task_id}")
    print(f"PDF文件: {pdf_path}")

    try:
        extractor = PDFContentExtractor(str(pdf_path))

        # 保存结果，使用task_id作为文件名前缀
        output_paths = extractor.save_to_json(include_paragraphs=True, task_id=task_id)

        print(f"\n提取成功!")
        print(f"输出文件:")

        # 显示表格摘要
        if "tables" in output_paths:
            print(f"  - 表格文件: {output_paths['tables']}")
            with open(output_paths['tables'], 'r', encoding='utf-8') as f:
                tables_result = json.load(f)
            print(f"    共提取 {tables_result['total_tables']} 个表格")
            for table in tables_result['tables']:
                rows_count = len(table.get('rows', []))
                cols_count = len(table.get('columns', []))
                print(f"      {table['id']}: 页码 {table['page']}, {rows_count}行 × {cols_count}列")

                # 显示嵌套表格信息
                for row in table.get('rows', []):
                    for cell in row.get('cells', []):
                        if 'nested_tables' in cell:
                            for nested in cell['nested_tables']:
                                nested_rows = len(nested.get('rows', []))
                                nested_cols = len(nested.get('columns', []))
                                print(f"        └─ 嵌套表格: {nested_rows}行 × {nested_cols}列")

        # 显示段落摘要
        if "paragraphs" in output_paths:
            print(f"\n  - 段落文件: {output_paths['paragraphs']}")
            with open(output_paths['paragraphs'], 'r', encoding='utf-8') as f:
                paragraphs_result = json.load(f)
            print(f"    共提取 {paragraphs_result['total_paragraphs']} 个段落")
            for para in paragraphs_result['paragraphs'][:5]:
                content_preview = para.get('content', '')[:50]
                print(f"      {para['id']}: 页码 {para['page']}, 内容: {content_preview}...")
            if paragraphs_result['total_paragraphs'] > 5:
                print(f"      ... 还有 {paragraphs_result['total_paragraphs'] - 5} 个段落")

    except FileNotFoundError as e:
        print(f"\n错误: 文件未找到: {e}")
    except Exception as e:
        print(f"\n错误: 提取失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()