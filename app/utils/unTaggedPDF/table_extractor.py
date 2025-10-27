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
    from .header_analyzer import HeaderAnalyzer
except ImportError:
    from nested_table_handler import NestedTableHandler
    from bbox_utils import rect, contains_with_tol
    from header_analyzer import HeaderAnalyzer


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

        # 多层表头分析器
        self.header_analyzer = HeaderAnalyzer()

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

                # 使用pdfplumber找到表格（只使用lines策略，不回退到text）
                table_settings = {
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines",
                    "intersection_x_tolerance": 3,
                    "intersection_y_tolerance": 3
                }
                tables = page.find_tables(table_settings=table_settings)

                # 不再回退到默认策略（text不准确）
                # if not tables:
                #     tables = page.find_tables()

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

                    # 注释掉：现在嵌套表格识别已经不依赖空列清理
                    # 保留原始的 table_data 和 bbox_data，避免误删除行表头列
                    # table_data, bbox_data, keep_cols = self._clean_spurious_columns(
                    #     table_data, bbox_data, cells
                    # )

                    # 使用嵌套表格处理器进行检测（方案B主判 + 方案A兜底）
                    nested_map = self.nested_handler.detect_and_extract_nested_tables(
                        page, pymupdf_page, table, bbox_data
                    )

                    if table_data:  # 确保表格不为空
                        # 构建结构化表格数据
                        structured_table = self._build_structured_table(
                            table_data=table_data,
                            bbox_data=bbox_data,
                            cells_bbox=cells,
                            page_num=page_num,
                            table_bbox=list(table.bbox),
                            nested_map=nested_map,
                            pymupdf_page=pymupdf_page
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
        cells_bbox: list,
        page_num: int,
        table_bbox: list,
        nested_map: Dict[tuple, List[Dict]] = None,
        pymupdf_page = None,
        hint_col_levels: int = None,
        hint_row_levels: int = None
    ) -> Dict[str, Any]:
        """
        构建结构化表格数据（支持多层表头）

        ## 多层表头支持

        ### 输入数据
        - table_data: 原始表格文本数据（二维数组）
        - cells_bbox: pdfplumber的cells列表，包含每个单元格的bbox和合并信息
        - hint_col_levels/hint_row_levels: 可选的手动指定表头层数

        ### 处理流程
        1. **尝试多层表头分析**：调用 HeaderAnalyzer.analyze_table_headers()
           - 成功：返回 HeaderModel（包含 col_paths/row_paths）
           - 失败：返回 None，回退到单层表头

        2. **多层表头模式** (_build_table_with_multi_level_headers)：
           - 使用 HeaderModel.col_paths 构建每个数据列的路径
           - 使用 HeaderModel.row_paths 构建每个数据行的路径
           - 跳过表头区域（前col_levels行 + 前row_levels列）
           - 数据单元格的 cellPath 和 rowPath 都是多层列表

        3. **单层表头模式** (_build_table_with_single_level_headers)：
           - 第一行作为列表头
           - 第一列作为行表头
           - cellPath/rowPath 都是单元素列表（保持向后兼容）

        ### 输出格式差异

        **多层表头** (multi_level=True):
        ```json
        {
          "header_info": {
            "col_levels": 2,
            "row_levels": 3,
            "multi_level": true
          },
          "columns": [
            {"name": "每周", "path": ["药物消杀安排", "每周"]},
            {"name": "每月", "path": ["药物消杀安排", "每月"]}
          ],
          "rows": [
            {
              "rowPath": ["1", "卫生间", "蜂蜡"],
              "cells": [
                {
                  "cellPath": ["药物消杀安排", "每周"],
                  "rowPath": ["1", "卫生间", "蜂蜡"],
                  "content": "10%复方三·查斗酮..."
                }
              ]
            }
          ]
        }
        ```

        **单层表头** (multi_level=False):
        ```json
        {
          "header_info": {
            "col_levels": 1,
            "row_levels": 1,
            "multi_level": false
          },
          "columns": [
            {"name": "序号"}
          ],
          "rows": [
            {
              "rowPath": ["1"],
              "cells": [
                {
                  "cellPath": ["序号"],
                  "rowPath": ["1"],
                  "content": "1"
                }
              ]
            }
          ]
        }
        ```

        Args:
            table_data: 表格数据 (二维数组)
            bbox_data: 每个单元格的边界框数据 (二维数组)
            cells_bbox: pdfplumber的cells列表（用于表头分析）
            page_num: 页码
            table_bbox: 表格整体的bbox
            nested_map: 嵌套表格映射
            pymupdf_page: PyMuPDF页面对象
            hint_col_levels: 手动指定列表头层数
            hint_row_levels: 手动指定行表头列数

        Returns:
            结构化表格字典（带 header_info 字段指示多层表头状态）
        """
        if not table_data:
            return {}

        if nested_map is None:
            nested_map = {}

        # 尝试进行多层表头分析
        header_model = None
        try:
            header_model = self.header_analyzer.analyze_table_headers(
                cells_bbox=cells_bbox,
                table_data=table_data,
                pymupdf_page=pymupdf_page,
                hint_col_levels=hint_col_levels,
                hint_row_levels=hint_row_levels
            )

            # 调试：打印表头分析结果
            if header_model:
                print(f"\n[DEBUG] 表头分析结果 - 页码 {page_num}")
                print(f"  col_levels: {header_model.col_levels}, row_levels: {header_model.row_levels}")
                print(f"  table_data 前3行前3列:")
                for i in range(min(3, len(table_data))):
                    print(f"    行{i}: {table_data[i][:3] if len(table_data[i]) >= 3 else table_data[i]}")
                print(f"  row_paths (前5个): {header_model.row_paths[:5]}")
                print(f"  col_paths (前3个): {header_model.col_paths[:3]}")
        except Exception as e:
            print(f"[INFO] 表头分析失败，使用单层表头: {e}")
            import traceback
            traceback.print_exc()

        # 如果表头分析成功，使用多层路径
        if header_model:
            return self._build_table_with_multi_level_headers(
                table_data=table_data,
                bbox_data=bbox_data,
                page_num=page_num,
                table_bbox=table_bbox,
                nested_map=nested_map,
                header_model=header_model
            )
        else:
            # 回退到单层表头逻辑
            return self._build_table_with_single_level_headers(
                table_data=table_data,
                bbox_data=bbox_data,
                page_num=page_num,
                table_bbox=table_bbox,
                nested_map=nested_map
            )

    def _build_table_with_multi_level_headers(
        self,
        table_data: List[List[str]],
        bbox_data: List[List[tuple]],
        page_num: int,
        table_bbox: list,
        nested_map: Dict[tuple, List[Dict]],
        header_model
    ) -> Dict[str, Any]:
        """
        使用多层表头模型构建表格

        Args:
            table_data: 表格数据
            bbox_data: bbox数据
            page_num: 页码
            table_bbox: 表格bbox
            nested_map: 嵌套表格映射
            header_model: HeaderModel对象

        Returns:
            结构化表格字典
        """
        col_levels = header_model.col_levels
        row_levels = header_model.row_levels
        col_paths = header_model.col_paths
        row_paths = header_model.row_paths

        # 1. 构建列定义（使用第一层表头）
        columns = []
        header_row = table_data[0] if table_data else []

        # 数据列从row_levels开始
        for data_col_idx in range(len(col_paths)):
            actual_col_idx = row_levels + data_col_idx
            col_name = header_row[actual_col_idx] if actual_col_idx < len(header_row) else ""

            columns.append({
                "id": f"c{actual_col_idx + 1:03d}",
                "index": actual_col_idx,
                "name": col_name,
                "path": col_paths[data_col_idx]  # 多层路径
            })

        # 2. 构建行数据（从col_levels行之后开始，即数据区）
        rows = []
        data_start_row = col_levels

        for data_row_idx in range(len(row_paths)):
            actual_row_idx = data_start_row + data_row_idx

            # 跳过超出table_data范围的行
            if actual_row_idx >= len(table_data):
                break

            row_id = f"r{actual_row_idx + 1:03d}"
            row_data = table_data[actual_row_idx]

            # 获取该行的多层行路径
            row_path = row_paths[data_row_idx]

            cells = []
            for data_col_idx in range(len(col_paths)):
                actual_col_idx = row_levels + data_col_idx

                # 跳过超出行数据范围的列
                if actual_col_idx >= len(row_data):
                    continue

                col_id = f"c{actual_col_idx + 1:03d}"
                cell_content = row_data[actual_col_idx]

                # 获取该列的多层列路径
                cell_path = col_paths[data_col_idx]

                # 获取单元格的bbox坐标
                cell_bbox = None
                if actual_row_idx < len(bbox_data) and actual_col_idx < len(bbox_data[actual_row_idx]):
                    bbox_tuple = bbox_data[actual_row_idx][actual_col_idx]
                    if bbox_tuple:
                        cell_bbox = list(bbox_tuple)

                # 获取嵌套表格
                nested_here = nested_map.get((actual_row_idx, actual_col_idx), [])

                cell_obj = {
                    "row_id": row_id,
                    "col_id": col_id,
                    "rowPath": row_path,  # 多层行路径
                    "cellPath": cell_path,  # 多层列路径
                    "content": cell_content,
                    "bbox": cell_bbox
                }

                # 只有识别到嵌套表格时才添加 nested_tables 字段
                if nested_here:
                    cell_obj["nested_tables"] = nested_here

                cells.append(cell_obj)

            rows.append({
                "id": row_id,
                "rowPath": row_path,  # 多层行路径
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
            "header_info": {
                "col_levels": col_levels,
                "row_levels": row_levels,
                "multi_level": True
            },
            "method": "hybrid (pdfplumber cells + pymupdf text + multi-level headers)"
        }

    def _build_table_with_single_level_headers(
        self,
        table_data: List[List[str]],
        bbox_data: List[List[tuple]],
        page_num: int,
        table_bbox: list,
        nested_map: Dict[tuple, List[Dict]]
    ) -> Dict[str, Any]:
        """
        使用单层表头构建表格（回退逻辑）

        Args:
            table_data: 表格数据
            bbox_data: bbox数据
            page_num: 页码
            table_bbox: 表格bbox
            nested_map: 嵌套表格映射

        Returns:
            结构化表格字典
        """
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
            "header_info": {
                "col_levels": 1,
                "row_levels": 1,
                "multi_level": False
            },
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