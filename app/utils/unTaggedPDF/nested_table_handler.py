"""
嵌套表格处理模块
专门处理PDF中的嵌套表格识别和提取
"""
import fitz  # PyMuPDF
from typing import List, Dict, Any, Tuple

try:
    from .bbox_utils import rect, contains_with_tol
except ImportError:
    from bbox_utils import rect, contains_with_tol


class NestedTableHandler:
    """嵌套表格处理器"""

    def __init__(self, table_extractor):
        """
        初始化嵌套表格处理器

        Args:
            table_extractor: TableExtractor实例（用于访问其方法）
        """
        self.extractor = table_extractor

    def cell_has_inner_grid(self, pymupdf_page, bbox: tuple,
                           min_h: int = 2, min_v: int = 2,
                           min_cross: int = 4, min_len: float = 8) -> bool:
        """
        用 PyMuPDF 统计 bbox 内的横/竖线段，粗判是否可能存在网格

        Args:
            pymupdf_page: PyMuPDF的page对象
            bbox: 单元格边界框 (x0, y0, x1, y1)
            min_h: 最小横线数量
            min_v: 最小竖线数量
            min_cross: 最小交点数量
            min_len: 最小线段长度

        Returns:
            是否可能存在网格
        """
        try:
            x0_box, y0_box, x1_box, y1_box = bbox
            rect_obj = fitz.Rect(bbox)

            # 单元格太小，不可能包含嵌套表格
            cell_width = x1_box - x0_box
            cell_height = y1_box - y0_box
            if cell_width < 50 or cell_height < 50:  # 最小50点（约1.8cm）
                return False

            h_lines, v_lines = [], []

            # 获取页面中的所有绘图对象
            drawings = pymupdf_page.get_drawings()
            if not drawings:
                return False

            for d in drawings:
                if not isinstance(d, dict) or "items" not in d:
                    continue

                for item in d["items"]:
                    if not isinstance(item, (list, tuple)) or len(item) < 2:
                        continue
                    if item[0] != "l":  # 只要线段
                        continue

                    line_coords = item[1]
                    if not isinstance(line_coords, (list, tuple)) or len(line_coords) < 4:
                        continue

                    x0, y0, x1, y1 = line_coords[:4]

                    # 排除单元格边框本身的线段（在边界上的线）
                    tolerance = 2.0
                    on_border = (
                        abs(y0 - y0_box) < tolerance or abs(y0 - y1_box) < tolerance or
                        abs(y1 - y0_box) < tolerance or abs(y1 - y1_box) < tolerance or
                        abs(x0 - x0_box) < tolerance or abs(x0 - x1_box) < tolerance or
                        abs(x1 - x0_box) < tolerance or abs(x1 - x1_box) < tolerance
                    )
                    if on_border:
                        continue

                    seg = fitz.Rect(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
                    if not rect_obj.intersects(seg):
                        continue
                    dx, dy = abs(x1 - x0), abs(y1 - y0)
                    length = max(dx, dy)
                    if length < min_len:
                        continue
                    if dy < 0.5:  # 横线
                        h_lines.append((x0, y0, x1, y1))
                    elif dx < 0.5:  # 竖线
                        v_lines.append((x0, y0, x1, y1))

            # 粗略交点数：以端点近似
            cross = 0
            for _, y0, _, _ in h_lines:
                for x0, _, _, _ in v_lines:
                    if rect_obj.contains(fitz.Point(x0, y0)):
                        cross += 1

            return (len(h_lines) >= min_h and len(v_lines) >= min_v and cross >= min_cross)
        except Exception:
            # 任何异常都返回False，表示没有嵌套网格
            return False

    def collect_page_tables_pymupdf(self, pymupdf_page):
        """
        使用PyMuPDF一次性获取全页的所有表格（方案B主判）

        Args:
            pymupdf_page: PyMuPDF的page对象

        Returns:
            (bbox列表, bbox到table对象的映射)
            例如: ([bbox1, bbox2], {tuple(bbox1): table1, tuple(bbox2): table2})
        """
        try:
            if not hasattr(pymupdf_page, 'find_tables'):
                return [], {}

            tf = pymupdf_page.find_tables()
            if not hasattr(tf, 'tables'):
                return [], {}

            bboxes = []
            bbox_to_table = {}
            for t in tf.tables:
                bbox = list(t.bbox)
                bboxes.append(bbox)
                # 用tuple作为字典key（list不能作为key）
                bbox_to_table[tuple(bbox)] = t

            return bboxes, bbox_to_table
        except Exception:
            return [], {}

    def assign_nested_by_containment(self, sub_bboxes: List[List[float]],
                                     bbox_data: List[List[tuple]]) -> Dict[Tuple[int, int], List[List[float]]]:
        """
        根据包含关系将子表bbox分配到父cell

        Args:
            sub_bboxes: PyMuPDF找到的子表bbox列表
            bbox_data: 父表的单元格bbox数据 (二维数组)

        Returns:
            {(r,c): [bbox, ...]} 映射
        """
        nested_hit = {}
        for sb in sub_bboxes:
            found = False
            for r in range(len(bbox_data)):
                for c in range(len(bbox_data[r])):
                    cb = bbox_data[r][c]
                    if not cb:
                        continue
                    if contains_with_tol(cb, sb, tol=1.5):
                        nested_hit.setdefault((r, c), []).append(sb)
                        found = True
                        break
                if found:
                    break
        return nested_hit

    def extract_table_from_pymupdf(self, pymupdf_table, depth: int = 1) -> Dict[str, Any]:
        """
        直接从PyMuPDF的table对象提取数据并构建结构化表格

        Args:
            pymupdf_table: PyMuPDF的table对象
            depth: 嵌套层级

        Returns:
            结构化表格字典
        """
        # 使用PyMuPDF的extract()方法获取表格数据
        data = pymupdf_table.extract()
        if not data or len(data) < 2:  # 至少需要表头+1行数据
            return None

        # 第一行是表头
        header_row = data[0]

        # 构建列定义
        columns = []
        for ci, header_text in enumerate(header_row):
            # 清理换行符（竖排文字的\n）
            clean_header = str(header_text).replace('\n', '')
            columns.append({
                "id": f"c{ci+1:03d}",
                "index": ci,
                "name": clean_header
            })

        # 构建行数据（从第二行开始）
        rows = []
        for ri, row_data in enumerate(data[1:], start=2):
            row_id = f"r{ri:03d}"
            # 清理第一列内容作为rowPath
            first_cell = str(row_data[0]).replace('\n', '') if row_data else ""

            cells = []
            for ci, cell_content in enumerate(row_data):
                # 清理换行符
                clean_content = str(cell_content).replace('\n', '')

                cells.append({
                    "id": f"nested-{row_id}-c{ci+1:03d}",
                    "row_id": row_id,
                    "col_id": f"c{ci+1:03d}",
                    "rowPath": [first_cell] if first_cell else [],
                    "cellPath": [columns[ci]["name"]] if ci < len(columns) else [],
                    "content": clean_content,
                    "bbox": None,
                    "nested_tables": []
                })

            rows.append({
                "id": row_id,
                "rowPath": [first_cell] if first_cell else [],
                "cells": cells
            })

        return {
            "type": "table",
            "level": depth + 1,
            "parent_table_id": None,  # 回填在父表
            "bbox": list(pymupdf_table.bbox),
            "columns": columns,
            "rows": rows,
            "method": f"pymupdf-direct (depth={depth+1})"
        }

    def extract_nested_tables_in_cell(self, pdf_page, pymupdf_page, cell_bbox: tuple,
                                     depth: int = 1, max_depth: int = 2) -> List[Dict[str, Any]]:
        """
        在一个 cell 的 bbox 内再次用 pdfplumber 检测表格（方案A兜底）

        Args:
            pdf_page: pdfplumber的page对象
            pymupdf_page: PyMuPDF的page对象
            cell_bbox: 单元格边界框 (x0, y0, x1, y1)
            depth: 当前递归深度
            max_depth: 最大递归深度

        Returns:
            嵌套表格列表
        """
        if depth > max_depth:
            return []

        # 先用网格迹象做快速筛选，避免无谓计算（没格就不用找）
        if not self.cell_has_inner_grid(pymupdf_page, cell_bbox):
            return []

        # 在子区域找表（先 lines，空则 text）
        sub_view = pdf_page.within_bbox(cell_bbox, relative=False)
        strategies = [
            {"vertical_strategy": "lines", "horizontal_strategy": "lines",
             "intersection_x_tolerance": 2, "intersection_y_tolerance": 2},
            {"vertical_strategy": "text", "horizontal_strategy": "text"}
        ]
        results = []

        for st in strategies:
            try:
                tables = sub_view.find_tables(table_settings=st)
                if tables:
                    for t in tables:
                        pdfplumber_data = t.extract()
                        if not pdfplumber_data or len(pdfplumber_data) < 2:
                            continue

                        rows_data = []
                        for row_cells in pdfplumber_data:
                            row = []
                            for cell_content in row_cells:
                                row.append((cell_content or "").replace('\n', '').replace('\r', '').strip())
                            rows_data.append(row)

                        # 构建嵌套表格的列定义
                        header_row = rows_data[0] if rows_data else []
                        columns = []
                        for ci, header_text in enumerate(header_row):
                            columns.append({
                                "id": f"c{ci + 1:03d}",
                                "index": ci,
                                "name": header_text
                            })

                        # 构建嵌套表格的行数据
                        nested_rows = []
                        for ri, row_data in enumerate(rows_data[1:], start=2):
                            row_id = f"r{ri:03d}"
                            row_first_cell = row_data[0] if row_data else ""

                            nested_cells = []
                            for ci, cell_content in enumerate(row_data):
                                col_id = f"c{ci + 1:03d}"
                                col_name = header_row[ci] if ci < len(header_row) else ""

                                nested_cells.append({
                                    "id": f"nested-{row_id}-{col_id}",
                                    "row_id": row_id,
                                    "col_id": col_id,
                                    "rowPath": [row_first_cell] if row_first_cell else [],
                                    "cellPath": [col_name] if col_name else [],
                                    "content": cell_content,
                                    "bbox": None,
                                    "nested_tables": []
                                })

                            nested_rows.append({
                                "id": row_id,
                                "rowPath": [row_first_cell] if row_first_cell else [],
                                "cells": nested_cells
                            })

                        results.append({
                            "type": "table",
                            "level": depth + 1,
                            "parent_table_id": None,
                            "bbox": list(t.bbox),
                            "columns": columns,
                            "rows": nested_rows,
                            "method": f"nested (depth={depth + 1})"
                        })
                    break  # lines 命中就不再跑 text
            except Exception:
                continue

        return results

    def detect_and_extract_nested_tables(self, pdf_page, pymupdf_page, table,
                                        bbox_data: List[List[tuple]]) -> Dict[Tuple[int, int], List[Dict[str, Any]]]:
        """
        完整的嵌套表格检测和提取流程（方案B主判 + 方案A兜底）

        Args:
            pdf_page: pdfplumber的page对象
            pymupdf_page: PyMuPDF的page对象
            table: pdfplumber的table对象
            bbox_data: 父表的单元格bbox数据

        Returns:
            嵌套表格映射 {(row_idx, col_idx): [nested_tables]}
        """
        # ========== 方案B 主判：PyMuPDF 全页表 + 包含关系分配 ========== #
        seed_bboxes, bbox_to_table = self.collect_page_tables_pymupdf(pymupdf_page)

        # 去掉"自身顶层表"的bbox（只过滤互相包含的，保留单向包含的子表）
        top_like = list(table.bbox)
        filtered_bboxes = []
        filtered_tables = {}

        for bb in seed_bboxes:
            # 只过滤互相包含的（同一个表）
            if (contains_with_tol(bb, top_like, tol=1.5)
                and contains_with_tol(top_like, bb, tol=1.5)):
                continue
            filtered_bboxes.append(bb)
            filtered_tables[tuple(bb)] = bbox_to_table[tuple(bb)]

        # 把 PyMuPDF 找到的表，按包含关系分配到父 cell
        hit = self.assign_nested_by_containment(filtered_bboxes, bbox_data)

        nested_map = {}  # key=(abs_row_idx, col_idx) ; value=[nested_table,...]
        for (r, c), child_bbs in hit.items():
            packs = []
            for bb in child_bbs:
                # 直接使用PyMuPDF的table对象提取数据
                pymupdf_table = filtered_tables.get(tuple(bb))
                if pymupdf_table:
                    structured_table = self.extract_table_from_pymupdf(pymupdf_table, depth=1)
                    if structured_table:
                        packs.append(structured_table)
            if packs:
                nested_map[(r, c)] = packs

        # ========== 方案A 兜底：逐 cell 检测（避免漏掉 PyMuPDF 没检出的子表） ========== #
        for r in range(len(bbox_data)):
            for c in range(len(bbox_data[r])):
                if (r, c) in nested_map:
                    continue  # 已被方案B检测到，跳过
                bb = bbox_data[r][c]
                if not bb:
                    continue
                # 检测单元格内的嵌套表格
                nested = self.extract_nested_tables_in_cell(
                    pdf_page, pymupdf_page, bb, depth=1, max_depth=2
                )
                if nested:
                    nested_map[(r, c)] = nested

        return nested_map