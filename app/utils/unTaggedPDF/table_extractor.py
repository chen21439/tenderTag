"""
PDF表格提取器
结合pdfplumber和PyMuPDF来提取PDF中的表格内容
"""

import json
from pathlib import Path
from typing import List, Dict, Any
import pdfplumber
import fitz  # PyMuPDF


class PDFTableExtractor:
    """PDF表格提取器"""

    def __init__(self, pdf_path: str):
        """
        初始化PDF表格提取器

        Args:
            pdf_path: PDF文件路径
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

        # 全局块计数器（用于docN编号）
        # TODO: 需要识别段落和表格的顺序来生成正确的docN
        # PDF按页提取，难以获取全局文档结构的顺序
        # 可能需要：1.先扫描全文档 2.按位置排序所有块 3.统一编号
        self.block_counter = 0

    def _is_bbox_overlap(self, bbox1: tuple, bbox2: tuple, threshold: float = 0.5) -> bool:
        """
        判断两个bbox是否重叠

        Args:
            bbox1: 第一个边界框 (x0, y0, x1, y1)
            bbox2: 第二个边界框 (x0, y0, x1, y1)
            threshold: 重叠面积阈值（相对于bbox1的面积）

        Returns:
            如果重叠面积超过阈值返回True
        """
        x0_1, y0_1, x1_1, y1_1 = bbox1
        x0_2, y0_2, x1_2, y1_2 = bbox2

        # 计算重叠区域
        x_overlap = max(0, min(x1_1, x1_2) - max(x0_1, x0_2))
        y_overlap = max(0, min(y1_1, y1_2) - max(y0_1, y0_2))
        overlap_area = x_overlap * y_overlap

        # 计算bbox1的面积
        bbox1_area = (x1_1 - x0_1) * (y1_1 - y0_1)

        if bbox1_area <= 0:
            return False

        return (overlap_area / bbox1_area) > threshold

    def extract_cell_text_with_pymupdf(self, page, bbox, debug=False) -> str:
        """
        使用PyMuPDF从指定边界框提取文本

        Args:
            page: PyMuPDF的page对象
            bbox: 边界框 (x0, y0, x1, y1)
            debug: 是否输出调试信息

        Returns:
            提取的文本内容（已移除换行符）
        """
        rect = fitz.Rect(bbox)
        text = page.get_text("text", clip=rect)

        if debug:
            print(f"\n[DEBUG] PyMuPDF提取:")
            print(f"  Bbox: {bbox}")
            print(f"  原始文本长度: {len(text)}")
            print(f"  包含\\n数量: {text.count(chr(10))}")
            print(f"  文本预览: {repr(text[:100])}")

        # 移除所有换行符
        text = text.replace('\n', '').replace('\r', '')

        return text.strip()

    def extract_tables_hybrid(self) -> List[Dict[str, Any]]:
        """
        混合使用pdfplumber和PyMuPDF提取表格
        - pdfplumber: 识别表格结构和单元格位置
        - PyMuPDF: 从单元格坐标提取文本内容（避免字符重复）

        Returns:
            提取的表格列表，每个表格包含页码和表格数据
        """
        tables_data = []

        # 打开PyMuPDF文档
        doc_pymupdf = fitz.open(self.pdf_path)

        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                # 获取PyMuPDF的对应页面
                pymupdf_page = doc_pymupdf[page_num - 1]

                # 使用pdfplumber找到表格
                tables = page.find_tables()

                for table_idx, table in enumerate(tables):
                    # 先用pdfplumber提取表格结构（用于获取行列结构）
                    pdfplumber_data = table.extract()

                    if not pdfplumber_data:
                        continue

                    # 获取单元格边界框
                    cells = table.cells  # cells是(x0, y0, x1, y1)的列表

                    # 构建单元格坐标到行列索引的映射
                    # 首先收集所有唯一的行和列边界
                    y_coords = sorted(set([cell[1] for cell in cells] + [cell[3] for cell in cells]))
                    x_coords = sorted(set([cell[0] for cell in cells] + [cell[2] for cell in cells]))

                    # 构建表格数据 - 使用PyMuPDF提取文本
                    table_data = []
                    bbox_data = []  # 存储每个单元格的bbox

                    for row_idx, row in enumerate(pdfplumber_data):
                        new_row = []
                        bbox_row = []
                        for col_idx in range(len(row)):
                            # pdfplumber提取的文本
                            pdfplumber_text = row[col_idx] if row[col_idx] else ""

                            # 找到对应的单元格边界
                            # 通过遍历cells找到匹配的单元格
                            cell_text = ""
                            cell_bbox_found = None
                            for cell_bbox in cells:
                                x0, y0, x1, y1 = cell_bbox
                                # 简化匹配：通过y坐标范围判断行，x坐标范围判断列
                                # 计算cell对应的行列索引
                                cell_row = self._find_index(y0, y_coords)
                                cell_col = self._find_index(x0, x_coords)

                                if cell_row == row_idx and cell_col == col_idx:
                                    # 使用PyMuPDF从这个bbox提取文本
                                    cell_text = self.extract_cell_text_with_pymupdf(
                                        pymupdf_page, cell_bbox
                                    )
                                    cell_bbox_found = cell_bbox
                                    break

                            new_row.append(cell_text if cell_text else "")
                            bbox_row.append(cell_bbox_found)
                        table_data.append(new_row)
                        bbox_data.append(bbox_row)

                    if table_data:  # 确保表格不为空
                        # 生成表格ID（使用block_counter作为docN）
                        self.block_counter += 1
                        table_id = f"doc{self.block_counter:03d}"

                        # 构建结构化表格数据
                        structured_table = self._build_structured_table(
                            table_id=table_id,
                            table_data=table_data,
                            bbox_data=bbox_data,
                            page_num=page_num,
                            cells_bbox=cells
                        )

                        tables_data.append(structured_table)

        doc_pymupdf.close()
        return tables_data

    def extract_paragraphs(self) -> List[Dict[str, Any]]:
        """
        提取PDF中表格外的段落文本
        使用PyMuPDF提取文本块，过滤掉与表格重叠的部分

        Returns:
            提取的段落列表
        """
        paragraphs_data = []

        # 打开PyMuPDF文档
        doc_pymupdf = fitz.open(self.pdf_path)

        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                # 获取PyMuPDF的对应页面
                pymupdf_page = doc_pymupdf[page_num - 1]

                # 使用pdfplumber找到当前页的所有表格
                tables = page.find_tables()
                table_bboxes = [table.bbox for table in tables]  # 表格的bbox列表

                # 使用PyMuPDF提取文本块
                # get_text("blocks") 返回: (x0, y0, x1, y1, "text", block_no, block_type)
                text_blocks = pymupdf_page.get_text("blocks")

                for block in text_blocks:
                    if len(block) < 7:
                        continue

                    x0, y0, x1, y1, text, block_no, block_type = block
                    block_bbox = (x0, y0, x1, y1)

                    # 过滤掉图像块（block_type=1是图像，0是文本）
                    if block_type != 0:
                        continue

                    # 检查是否与表格重叠
                    is_in_table = False
                    for table_bbox in table_bboxes:
                        if self._is_bbox_overlap(block_bbox, table_bbox, threshold=0.5):
                            is_in_table = True
                            break

                    # 如果不在表格内，则认为是段落
                    if not is_in_table:
                        # 移除换行符
                        text_clean = text.replace('\n', '').replace('\r', '').strip()

                        if text_clean:  # 只保存非空段落
                            paragraphs_data.append({
                                "page": page_num,
                                "bbox": list(block_bbox),
                                "content": text_clean,
                                "y0": y0  # 用于排序
                            })

        doc_pymupdf.close()
        return paragraphs_data

    def _build_structured_table(
        self,
        table_id: str,
        table_data: List[List[str]],
        bbox_data: List[List[tuple]],
        page_num: int,
        cells_bbox: list
    ) -> Dict[str, Any]:
        """
        构建结构化表格数据（对齐Word文档格式）

        Args:
            table_id: 表格ID (docN格式)
            table_data: 表格数据 (二维数组)
            bbox_data: 每个单元格的边界框数据 (二维数组)
            page_num: 页码
            cells_bbox: 单元格边界框列表

        Returns:
            结构化表格字典
        """
        if not table_data:
            return {}

        num_cols = len(table_data[0]) if table_data else 0

        # 1. 提取表头（第一行）
        header_row = table_data[0] if table_data else []

        # 2. 构建列定义（使用表头作为列名）
        columns = []
        for col_idx, header_text in enumerate(header_row):
            columns.append({
                "id": f"c{col_idx + 1:03d}",
                "index": col_idx,
                "name": header_text  # 列名来自表头
            })

        # 3. 构建行数据（从第二行开始，跳过表头）
        # 注意：row_id从r002开始，因为r001被表头占用
        rows = []
        for row_idx, row_data in enumerate(table_data[1:], start=2):  # 从2开始，表头占用了r001
            row_id = f"r{row_idx:03d}"

            # rowPath: 使用第一列的内容作为行标识（通常是序号或主键）
            row_first_cell = row_data[0] if row_data else ""

            cells = []
            for col_idx, cell_content in enumerate(row_data):
                col_id = f"c{col_idx + 1:03d}"
                cell_id = f"{table_id}-{row_id}-{col_id}"

                # cellPath: 只使用列表头（列名），数组格式支持多层树结构
                col_name = header_row[col_idx] if col_idx < len(header_row) else ""

                # 获取单元格的bbox坐标（row_idx从2开始，bbox_data索引从0开始）
                bbox_row_idx = row_idx - 1  # 调整索引以匹配bbox_data
                cell_bbox = None
                if bbox_row_idx < len(bbox_data) and col_idx < len(bbox_data[bbox_row_idx]):
                    bbox_tuple = bbox_data[bbox_row_idx][col_idx]
                    if bbox_tuple:
                        cell_bbox = list(bbox_tuple)  # 转换为列表便于JSON序列化

                cell_obj = {
                    "id": cell_id,
                    "row_id": row_id,
                    "col_id": col_id,
                    "rowPath": [row_first_cell] if row_first_cell else [],  # 行路径（数组），支持多层
                    "cellPath": [col_name] if col_name else [],              # 列路径（数组），支持多层
                    "content": cell_content,
                    "bbox": cell_bbox,  # 单元格边界框坐标 (x0, y0, x1, y1)
                    # TODO: 嵌套表格检测
                    # PDF中嵌套表格需要通过bbox包含关系判断
                    # 可能需要：1.检测单元格内是否有其他表格bbox 2.递归提取
                    "nested_tables": []
                }

                cells.append(cell_obj)

            rows.append({
                "id": row_id,
                "rowPath": [row_first_cell] if row_first_cell else [],  # 行路径（数组），支持多层
                "cells": cells
            })

        # 3. 构建完整表格对象
        return {
            "type": "table",
            "id": table_id,
            "level": 1,  # 顶层表格
            "parent_table_id": None,
            "page": page_num,
            "columns": columns,
            "rows": rows,
            "method": "hybrid (pdfplumber cells + pymupdf text)"
        }

    def _find_index(self, coord: float, coords_list: list) -> int:
        """
        辅助函数：找到坐标在坐标列表中的索引位置

        Args:
            coord: 要查找的坐标
            coords_list: 已排序的坐标列表

        Returns:
            索引位置
        """
        for i in range(len(coords_list) - 1):
            if coords_list[i] <= coord < coords_list[i + 1]:
                return i
        return len(coords_list) - 2 if coords_list else 0

    def extract_tables_with_pdfplumber(self) -> List[Dict[str, Any]]:
        """
        使用pdfplumber提取表格（仅用于对比，推荐使用extract_tables_hybrid）

        Returns:
            提取的表格列表，每个表格包含页码和表格数据
        """
        tables_data = []

        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                # 提取当前页面的所有表格
                tables = page.extract_tables()

                for table_idx, table in enumerate(tables):
                    if table:  # 确保表格不为空
                        tables_data.append({
                            "page": page_num,
                            "table_index": table_idx,
                            "method": "pdfplumber only",
                            "rows": len(table),
                            "columns": len(table[0]) if table else 0,
                            "data": table
                        })

        return tables_data

    def extract_tables_with_pymupdf(self) -> List[Dict[str, Any]]:
        """
        使用PyMuPDF提取表格信息（主要用于获取表格位置等元数据）

        Returns:
            提取的表格元数据列表
        """
        tables_metadata = []

        doc = fitz.open(self.pdf_path)

        for page_num in range(len(doc)):
            page = doc[page_num]

            # PyMuPDF可以获取页面中的文本块和位置信息
            # 这里我们使用它来辅助pdfplumber的结果
            text_blocks = page.get_text("dict")

            tables_metadata.append({
                "page": page_num + 1,
                "method": "pymupdf",
                "width": page.rect.width,
                "height": page.rect.height,
                "blocks_count": len(text_blocks.get("blocks", []))
            })

        doc.close()
        return tables_metadata

    def extract_all_content(self) -> Dict[str, Any]:
        """
        综合提取PDF中的所有内容（表格+段落）
        按页面顺序和y坐标排序，统一分配docN编号

        Returns:
            包含所有内容的字典
        """
        # 提取表格（不增加block_counter，稍后统一编号）
        tables_raw = self.extract_tables_hybrid()

        # 提取段落
        paragraphs_raw = self.extract_paragraphs()

        # 合并所有内容块，添加排序键
        all_blocks = []

        # 添加表格
        for table in tables_raw:
            # 计算表格的y0（用于排序）
            # 使用表格第一个单元格的y0，或者使用bbox
            table_y0 = table.get("rows", [{}])[0].get("cells", [{}])[0].get("bbox", [0, 0, 0, 0])[1] if table.get("rows") else 0
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

        # 按页面顺序和y坐标排序
        all_blocks.sort(key=lambda x: (x["page"], x["y0"]))

        # 重新分配docN编号并构建最终结构
        structured_blocks = []
        self.block_counter = 0

        for block in all_blocks:
            self.block_counter += 1
            doc_id = f"doc{self.block_counter:03d}"

            if block["type"] == "table":
                # 更新表格的id
                table_data = block["data"]
                table_data["id"] = doc_id
                # 更新所有cell的id（需要重新生成）
                for row in table_data.get("rows", []):
                    row_id = row["id"]
                    for cell in row.get("cells", []):
                        col_id = cell["col_id"]
                        cell["id"] = f"{doc_id}-{row_id}-{col_id}"

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

        # 使用PyMuPDF提取页面元数据
        metadata = self.extract_tables_with_pymupdf()

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
        综合使用pdfplumber和PyMuPDF提取表格（仅表格，不包含段落）
        使用混合方法：pdfplumber识别单元格位置 + PyMuPDF提取文本

        Returns:
            包含所有表格数据和元数据的字典
        """
        # 使用混合方法提取表格内容（避免字符重复问题）
        tables = self.extract_tables_hybrid()

        # 使用PyMuPDF提取页面元数据
        metadata = self.extract_tables_with_pymupdf()

        return {
            "pdf_file": str(self.pdf_path),
            "total_tables": len(tables),
            "tables": tables,
            "page_metadata": metadata
        }

    def save_to_json(self, output_dir: str = None, include_paragraphs: bool = True) -> Dict[str, str]:
        """
        提取内容并保存到JSON文件
        表格保存到 table.json，段落保存到 paragraph.json

        Args:
            output_dir: 输出目录路径，如果为None则保存到PDF同目录
            include_paragraphs: 是否提取并保存段落（默认True）

        Returns:
            保存的文件路径字典 {"tables": "path/to/table.json", "paragraphs": "path/to/paragraph.json"}
        """
        # 确定输出目录
        if output_dir is None:
            output_dir = self.pdf_path.parent
        else:
            output_dir = Path(output_dir)

        # 确保输出目录存在
        output_dir.mkdir(parents=True, exist_ok=True)

        result_paths = {}

        # 提取并保存表格
        tables_result = self.extract_all_tables()
        table_path = output_dir / "table.json"
        with open(table_path, 'w', encoding='utf-8') as f:
            json.dump(tables_result, f, ensure_ascii=False, indent=2)
        result_paths["tables"] = str(table_path)

        # 提取并保存段落（如果需要）
        if include_paragraphs:
            paragraphs_result = self._extract_paragraphs_only()
            paragraph_path = output_dir / "paragraph.json"
            with open(paragraph_path, 'w', encoding='utf-8') as f:
                json.dump(paragraphs_result, f, ensure_ascii=False, indent=2)
            result_paths["paragraphs"] = str(paragraph_path)

        return result_paths

    def _extract_paragraphs_only(self) -> Dict[str, Any]:
        """
        提取段落并构建结构化输出（带docN编号）

        Returns:
            包含段落数据的字典
        """
        # 提取段落
        paragraphs_raw = self.extract_paragraphs()

        # 按页面顺序和y坐标排序
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

        # 使用PyMuPDF提取页面元数据
        metadata = self.extract_tables_with_pymupdf()

        return {
            "pdf_file": str(self.pdf_path),
            "total_paragraphs": len(structured_paragraphs),
            "paragraphs": structured_paragraphs,
            "page_metadata": metadata
        }


def extract_pdf_content(pdf_path: str, output_path: str = None, include_paragraphs: bool = True) -> str:
    """
    便捷函数：提取PDF内容（表格+段落）并保存到JSON

    Args:
        pdf_path: PDF文件路径
        output_path: 输出JSON文件路径，默认为PDF同目录
        include_paragraphs: 是否包含段落（默认True）

    Returns:
        保存的JSON文件路径
    """
    extractor = PDFTableExtractor(pdf_path)
    return extractor.save_to_json(output_path, include_paragraphs=include_paragraphs)


def extract_pdf_tables(pdf_path: str, output_path: str = None) -> str:
    """
    便捷函数：仅提取PDF表格并保存到JSON（不包含段落）

    Args:
        pdf_path: PDF文件路径
        output_path: 输出JSON文件路径，默认为PDF同目录的table.json

    Returns:
        保存的JSON文件路径
    """
    extractor = PDFTableExtractor(pdf_path)
    return extractor.save_to_json(output_path, include_paragraphs=False)


def main():
    """
    主测试方法 - 直接运行此文件来测试PDF内容提取功能（表格+段落）
    """
    # 测试用的PDF文件路径
    pdf_path = r"E:\programFile\AIProgram\docxServer\pdf\task\1979102567573037058\1979102567573037058.pdf"

    print(f"开始提取PDF内容（表格+段落）...")
    print(f"PDF文件: {pdf_path}")

    try:
        # 创建提取器
        extractor = PDFTableExtractor(pdf_path)

        # 提取并保存所有内容（表格+段落）
        output_paths = extractor.save_to_json(include_paragraphs=True)

        print(f"\n[成功] 提取成功!")
        print(f"[成功] 输出文件:")

        # 显示表格摘要
        if "tables" in output_paths:
            print(f"  - 表格文件: {output_paths['tables']}")
            with open(output_paths['tables'], 'r', encoding='utf-8') as f:
                tables_result = json.load(f)
            print(f"    共提取 {tables_result['total_tables']} 个表格")
            for idx, table in enumerate(tables_result['tables'], 1):
                rows_count = len(table.get('rows', []))
                cols_count = len(table.get('columns', []))
                print(f"      {table['id']}: 页码 {table['page']}, {rows_count}行 × {cols_count}列")

        # 显示段落摘要
        if "paragraphs" in output_paths:
            print(f"\n  - 段落文件: {output_paths['paragraphs']}")
            with open(output_paths['paragraphs'], 'r', encoding='utf-8') as f:
                paragraphs_result = json.load(f)
            print(f"    共提取 {paragraphs_result['total_paragraphs']} 个段落")
            for idx, para in enumerate(paragraphs_result['paragraphs'][:10], 1):  # 只显示前10个
                content_preview = para.get('content', '')[:50]
                print(f"      {para['id']}: 页码 {para['page']}, 内容: {content_preview}...")

            if paragraphs_result['total_paragraphs'] > 10:
                print(f"      ... 还有 {paragraphs_result['total_paragraphs'] - 10} 个段落")

    except FileNotFoundError as e:
        print(f"\n[错误] 文件未找到: {e}")
    except Exception as e:
        print(f"\n[错误] 提取失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()