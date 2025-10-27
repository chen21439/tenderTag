"""
表格提取器
专门负责PDF中表格的提取（包括嵌套表格）
"""
from pathlib import Path
from typing import List, Dict, Any, Tuple
import pdfplumber
import fitz  # PyMuPDF

# 兼容相对导入和直接运行
try:
    from .nested_table_handler import NestedTableHandler
    from .bbox_utils import rect, contains_with_tol
except ImportError:
    from nested_table_handler import NestedTableHandler
    from bbox_utils import rect, contains_with_tol


class TableExtractor:
    """表格提取器"""

    def __init__(self, pdf_path: str):
        """
        初始化表格提取器

        Args:
            pdf_path: PDF文件路径
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

        # 嵌套表格处理器
        self.nested_handler = NestedTableHandler(self)

    def extract_tables(self) -> List[Dict[str, Any]]:
        """
        提取PDF中的所有表格（混合方法）
        - pdfplumber: 识别表格结构和单元格位置
        - PyMuPDF: 从单元格坐标提取文本内容（避免字符重复）

        Returns:
            提取的表格列表
        """
        tables_data = []

        # 打开PyMuPDF文档
        doc_pymupdf = fitz.open(self.pdf_path)

        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                # 获取PyMuPDF的对应页面
                pymupdf_page = doc_pymupdf[page_num - 1]

                # 使用pdfplumber找到表格（优先使用lines策略，避免误合并子表）
                table_settings = {
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines",
                    "intersection_x_tolerance": 3,
                    "intersection_y_tolerance": 3
                }
                tables = page.find_tables(table_settings=table_settings)

                # 如果lines策略没找到表格，回退到默认策略
                if not tables:
                    tables = page.find_tables()

                for table_idx, table in enumerate(tables):
                    # 先用pdfplumber提取表格结构（用于获取行列结构）
                    pdfplumber_data = table.extract()

                    if not pdfplumber_data:
                        continue

                    # 获取单元格边界框
                    cells = table.cells  # cells是(x0, y0, x1, y1)的列表

                    # 构建单元格坐标到行列索引的映射
                    y_coords = sorted(set([cell[1] for cell in cells] + [cell[3] for cell in cells]))
                    x_coords = sorted(set([cell[0] for cell in cells] + [cell[2] for cell in cells]))

                    # 构建表格数据 - 使用PyMuPDF提取文本
                    table_data = []
                    bbox_data = []  # 存储每个单元格的bbox

                    for row_idx, row in enumerate(pdfplumber_data):
                        new_row = []
                        bbox_row = []
                        for col_idx in range(len(row)):
                            # 找到对应的单元格边界
                            cell_text = ""
                            cell_bbox_found = None
                            for cell_bbox in cells:
                                x0, y0, x1, y1 = cell_bbox
                                # 计算cell对应的行列索引
                                cell_row = self._find_index(y0, y_coords)
                                cell_col = self._find_index(x0, x_coords)

                                if cell_row == row_idx and cell_col == col_idx:
                                    # 使用PyMuPDF从这个bbox提取文本
                                    cell_text = self.extract_cell_text(
                                        pymupdf_page, cell_bbox
                                    )
                                    cell_bbox_found = cell_bbox
                                    break

                            new_row.append(cell_text if cell_text else "")
                            bbox_row.append(cell_bbox_found)
                        table_data.append(new_row)
                        bbox_data.append(bbox_row)

                    # 清理误吸收的子表空列
                    table_data, bbox_data, keep_cols = self._clean_spurious_columns(
                        table_data, bbox_data, cells
                    )

                    # 使用嵌套表格处理器进行检测（方案B主判 + 方案A兜底）
                    nested_map = self.nested_handler.detect_and_extract_nested_tables(
                        page, pymupdf_page, table, bbox_data
                    )

                    if table_data:  # 确保表格不为空
                        # 构建结构化表格数据
                        structured_table = self._build_structured_table(
                            table_data=table_data,
                            bbox_data=bbox_data,
                            page_num=page_num,
                            table_bbox=list(table.bbox),
                            nested_map=nested_map
                        )

                        tables_data.append(structured_table)

        doc_pymupdf.close()
        return tables_data

    def extract_cell_text(self, pymupdf_page, bbox: tuple, debug: bool = False) -> str:
        """
        使用PyMuPDF从指定边界框提取文本

        Args:
            pymupdf_page: PyMuPDF的page对象
            bbox: 边界框 (x0, y0, x1, y1)
            debug: 是否输出调试信息

        Returns:
            提取的文本内容（已移除换行符）
        """
        rect_obj = fitz.Rect(bbox)
        text = pymupdf_page.get_text("text", clip=rect_obj)

        if debug:
            print(f"\n[DEBUG] PyMuPDF提取:")
            print(f"  Bbox: {bbox}")
            print(f"  原始文本长度: {len(text)}")
            print(f"  文本预览: {repr(text[:100])}")

        # 移除所有换行符
        text = text.replace('\n', '').replace('\r', '')

        return text.strip()

    def get_table_bboxes_per_page(self) -> Dict[int, List[tuple]]:
        """
        获取每页的表格bbox列表（供段落提取器使用）

        Returns:
            {page_num: [bbox1, bbox2, ...]}
        """
        table_bboxes = {}

        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                tables = page.find_tables()
                table_bboxes[page_num] = [table.bbox for table in tables]

        return table_bboxes

    def _clean_spurious_columns(self, table_data: List[List[str]],
                                bbox_data: List[List[tuple]],
                                cells: list) -> Tuple[List[List[str]], List[List[tuple]], List[int]]:
        """
        清理外层表中误吸收的子表列（空列）

        识别逻辑：
        1. 列表头为空字符串
        2. 该列在90%以上的数据行中也为空

        Args:
            table_data: 表格数据（二维数组）
            bbox_data: bbox数据（二维数组）
            cells: 原始cells列表

        Returns:
            (清理后的table_data, 清理后的bbox_data, 保留的列索引列表)
        """
        if not table_data or len(table_data) < 2:
            return table_data, bbox_data, list(range(len(table_data[0]) if table_data else 0))

        num_cols = len(table_data[0])
        num_rows = len(table_data)
        keep_cols = []

        for col_idx in range(num_cols):
            # 获取表头
            header = (table_data[0][col_idx] or "").strip()

            # 统计该列在数据行中非空的数量
            non_empty_count = 0
            for row_idx in range(1, num_rows):
                if row_idx < len(table_data) and col_idx < len(table_data[row_idx]):
                    cell_value = (table_data[row_idx][col_idx] or "").strip()
                    if cell_value:
                        non_empty_count += 1

            # 判断是否保留：有表头 或 多于10%的数据行有值
            threshold = max(1, (num_rows - 1) * 0.1)
            if header or non_empty_count >= threshold:
                keep_cols.append(col_idx)

        # 如果所有列都保留，直接返回
        if len(keep_cols) == num_cols:
            return table_data, bbox_data, keep_cols

        # 重建table_data
        cleaned_table_data = []
        for row in table_data:
            cleaned_row = [row[j] for j in keep_cols if j < len(row)]
            cleaned_table_data.append(cleaned_row)

        # 重建bbox_data
        cleaned_bbox_data = []
        for row in bbox_data:
            cleaned_row = [row[j] for j in keep_cols if j < len(row)]
            cleaned_bbox_data.append(cleaned_row)

        return cleaned_table_data, cleaned_bbox_data, keep_cols

    def _build_structured_table(
        self,
        table_data: List[List[str]],
        bbox_data: List[List[tuple]],
        page_num: int,
        table_bbox: list,
        nested_map: Dict[tuple, List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        构建结构化表格数据

        Args:
            table_data: 表格数据 (二维数组)
            bbox_data: 每个单元格的边界框数据 (二维数组)
            page_num: 页码
            table_bbox: 表格整体的bbox
            nested_map: 嵌套表格映射

        Returns:
            结构化表格字典
        """
        if not table_data:
            return {}

        if nested_map is None:
            nested_map = {}

        # 1. 提取表头（第一行）
        header_row = table_data[0] if table_data else []

        # 2. 构建列定义
        columns = []
        for col_idx, header_text in enumerate(header_row):
            columns.append({
                "id": f"c{col_idx + 1:03d}",
                "index": col_idx,
                "name": header_text
            })

        # 3. 构建行数据（从第二行开始，跳过表头）
        rows = []
        for row_idx, row_data in enumerate(table_data[1:], start=2):
            row_id = f"r{row_idx:03d}"
            row_first_cell = row_data[0] if row_data else ""

            cells = []
            for col_idx, cell_content in enumerate(row_data):
                col_id = f"c{col_idx + 1:03d}"
                col_name = header_row[col_idx] if col_idx < len(header_row) else ""

                # 获取单元格的bbox坐标
                bbox_row_idx = row_idx - 1
                cell_bbox = None
                if bbox_row_idx < len(bbox_data) and col_idx < len(bbox_data[bbox_row_idx]):
                    bbox_tuple = bbox_data[bbox_row_idx][col_idx]
                    if bbox_tuple:
                        cell_bbox = list(bbox_tuple)

                # 获取嵌套表格
                nested_here = nested_map.get((bbox_row_idx, col_idx), [])

                cell_obj = {
                    "row_id": row_id,
                    "col_id": col_id,
                    "rowPath": [row_first_cell] if row_first_cell else [],
                    "cellPath": [col_name] if col_name else [],
                    "content": cell_content,
                    "bbox": cell_bbox
                }

                # 只有识别到嵌套表格时才添加 nested_tables 字段
                if nested_here:
                    cell_obj["nested_tables"] = nested_here

                cells.append(cell_obj)

            rows.append({
                "id": row_id,
                "rowPath": [row_first_cell] if row_first_cell else [],
                "cells": cells
            })

        return {
            "type": "table",
            "level": 1,
            "parent_table_id": None,
            "page": page_num,
            "bbox": table_bbox,
            "columns": columns,
            "rows": rows,
            "method": "hybrid (pdfplumber cells + pymupdf text)"
        }

    def _find_index(self, coord: float, coords_list: list) -> int:
        """
        找到坐标在坐标列表中的索引位置

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