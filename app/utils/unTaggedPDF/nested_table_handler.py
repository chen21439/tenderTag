"""
嵌套表格处理模块
专门处理PDF中的嵌套表格识别和提取
"""
import fitz  # PyMuPDF
from typing import List, Dict, Any, Tuple


class NestedTableHandler:
    """嵌套表格处理器"""

    def __init__(self, table_extractor):
        """
        初始化嵌套表格处理器

        Args:
            table_extractor: PDFTableExtractor实例（用于访问其方法）
        """
        self.extractor = table_extractor

    def _rect(self, bb: tuple) -> fitz.Rect:
        """
        辅助函数：将bbox转换为fitz.Rect

        Args:
            bb: bbox元组 (x0, y0, x1, y1)

        Returns:
            fitz.Rect对象
        """
        return fitz.Rect(bb[0], bb[1], bb[2], bb[3])

    def _contains_with_tol(self, outer: tuple, inner: tuple, tol: float = 1.0) -> bool:
        """
        判断outer是否包含inner（带容差）

        Args:
            outer: 外层bbox (x0, y0, x1, y1)
            inner: 内层bbox (x0, y0, x1, y1)
            tol: 容差值

        Returns:
            是否包含
        """
        o = self._rect((outer[0] - tol, outer[1] - tol, outer[2] + tol, outer[3] + tol))
        i = self._rect(inner)
        return o.contains(i)

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
            rect = fitz.Rect(bbox)

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
                    if not rect.intersects(seg):
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
                    if rect.contains(fitz.Point(x0, y0)):
                        cross += 1

            return (len(h_lines) >= min_h and len(v_lines) >= min_v and cross >= min_cross)
        except Exception:
            # 任何异常都返回False，表示没有嵌套网格
            return False

    def collect_page_tables_pymupdf(self, pymupdf_page) -> List[List[float]]:
        """
        使用PyMuPDF一次性获取全页的所有表格bbox（方案B主判）

        Args:
            pymupdf_page: PyMuPDF的page对象

        Returns:
            表格bbox列表 [[x0,y0,x1,y1], ...]
        """
        try:
            if not hasattr(pymupdf_page, 'find_tables'):
                return []

            tf = pymupdf_page.find_tables()
            if not hasattr(tf, 'tables'):
                return []

            return [list(t.bbox) for t in tf.tables]
        except Exception:
            return []

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
                    if self._contains_with_tol(cb, sb, tol=1.5):
                        nested_hit.setdefault((r, c), []).append(sb)
                        found = True
                        break
                if found:
                    break
        return nested_hit

    def merge_split_rows(self, table_data: List[List[str]],
                        bbox_heights: List[float],
                        height_threshold: float = 15.0) -> List[List[str]]:
        """
        合并被错误拆分的行（针对竖排文字等情况）

        策略：如果连续的行高度都很小（< height_threshold），则合并它们

        Args:
            table_data: 表格数据（二维数组）
            bbox_heights: 每行的平均高度列表
            height_threshold: 行高度阈值（点），小于此值的行被认为是拆分的

        Returns:
            合并后的表格数据
        """
        if not table_data or len(table_data) < 2:
            return table_data

        merged_data = []
        i = 0

        while i < len(table_data):
            current_row = table_data[i]
            current_height = bbox_heights[i] if i < len(bbox_heights) else 0

            # 如果当前行高度正常，直接添加
            if current_height >= height_threshold:
                merged_data.append(current_row)
                i += 1
                continue

            # 当前行高度小，查找连续的小高度行
            merge_group = [current_row]
            j = i + 1

            while j < len(table_data):
                next_height = bbox_heights[j] if j < len(bbox_heights) else 0
                if next_height < height_threshold:
                    merge_group.append(table_data[j])
                    j += 1
                else:
                    break

            # 合并这些行的各列文本
            num_cols = len(current_row)
            merged_row = []
            for col_idx in range(num_cols):
                col_texts = []
                for row in merge_group:
                    if col_idx < len(row) and row[col_idx]:
                        col_texts.append(row[col_idx])
                merged_row.append("".join(col_texts))

            merged_data.append(merged_row)
            i = j

        return merged_data

    def extract_table_by_bbox(self, pdf_page, pymupdf_page, bbox: tuple, depth: int = 1) -> List[Dict[str, Any]]:
        """
        按给定bbox直接提取表格（跳过网格粗筛）

        Args:
            pdf_page: pdfplumber的page对象
            pymupdf_page: PyMuPDF的page对象
            bbox: 表格边界框
            depth: 当前深度

        Returns:
            提取的表格列表
        """
        sub_view = pdf_page.within_bbox(bbox, relative=False)

        # 策略优先级：lines > text
        strategies = [
            {"vertical_strategy": "lines", "horizontal_strategy": "lines",
             "intersection_x_tolerance": 2, "intersection_y_tolerance": 2},
            {"vertical_strategy": "text", "horizontal_strategy": "text"}
        ]

        for st in strategies:
            try:
                tables = sub_view.find_tables(table_settings=st)
                if not tables:
                    continue

                result = []
                for t in tables:
                    # 使用pdfplumber获取结构信息
                    pdfplumber_data = t.extract()
                    if not pdfplumber_data or len(pdfplumber_data) < 2:  # 至少需要表头+1行
                        continue

                    # 获取单元格边界框
                    cells_bbox = t.cells  # cells是(x0, y0, x1, y1)的列表

                    # 构建单元格坐标到行列索引的映射
                    y_coords = sorted(set([cell[1] for cell in cells_bbox] + [cell[3] for cell in cells_bbox]))
                    x_coords = sorted(set([cell[0] for cell in cells_bbox] + [cell[2] for cell in cells_bbox]))

                    # 使用PyMuPDF提取文本（混合方法）
                    table_data = []
                    bbox_heights = []  # 记录每行的平均高度
                    for row_idx, row in enumerate(pdfplumber_data):
                        new_row = []
                        row_heights = []
                        for col_idx in range(len(row)):
                            # 找到对应的单元格边界
                            cell_text = ""
                            cell_height = 0
                            for cell_bbox in cells_bbox:
                                x0, y0, x1, y1 = cell_bbox
                                # 计算cell对应的行列索引
                                cell_row = self.extractor._find_index(y0, y_coords)
                                cell_col = self.extractor._find_index(x0, x_coords)

                                if cell_row == row_idx and cell_col == col_idx:
                                    # 使用PyMuPDF从这个bbox提取文本
                                    cell_text = self.extractor.extract_cell_text_with_pymupdf(
                                        pymupdf_page, cell_bbox
                                    )
                                    cell_height = y1 - y0
                                    break

                            new_row.append(cell_text if cell_text else "")
                            row_heights.append(cell_height)
                        table_data.append(new_row)
                        bbox_heights.append(sum(row_heights) / len(row_heights) if row_heights else 0)

                    # 合并被错误拆分的行（针对竖排文字等情况）
                    table_data = self.merge_split_rows(table_data, bbox_heights)

                    # 构建表头
                    header = table_data[0] if table_data else []
                    columns = [
                        {"id": f"c{ci+1:03d}", "index": ci, "name": header[ci]}
                        for ci in range(len(header))
                    ]

                    # 构建行数据（从第二行开始）
                    rows = []
                    for ri, row_data in enumerate(table_data[1:], start=2):
                        row_id = f"r{ri:03d}"
                        first = row_data[0] if row_data else ""

                        cells = []
                        for ci, val in enumerate(row_data):
                            cells.append({
                                "id": f"nested-{row_id}-c{ci+1:03d}",
                                "row_id": row_id,
                                "col_id": f"c{ci+1:03d}",
                                "rowPath": [first] if first else [],
                                "cellPath": [header[ci]] if ci < len(header) and header[ci] else [],
                                "content": val,
                                "bbox": None,
                                "nested_tables": []
                            })

                        rows.append({
                            "id": row_id,
                            "rowPath": [first] if first else [],
                            "cells": cells
                        })

                    result.append({
                        "type": "table",
                        "level": depth + 1,
                        "parent_table_id": None,  # 回填在父表
                        "bbox": list(t.bbox),
                        "columns": columns,
                        "rows": rows,
                        "method": f"pymupdf-seed (depth={depth+1})"
                    })

                if result:
                    return result

            except Exception:
                continue

        return []

    def extract_nested_tables_in_cell(self, pdf_page, pymupdf_page, cell_bbox: tuple,
                                     depth: int = 1, max_depth: int = 2) -> List[Dict[str, Any]]:
        """
        在一个 cell 的 bbox 内再次用 pdfplumber 检测表格；必要时递归（方案A兜底）

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
                        # 取行列文本（仍用 PyMuPDF clip）
                        pdfplumber_data = t.extract()
                        if not pdfplumber_data or len(pdfplumber_data) < 2:  # 至少需要表头+1行数据
                            continue

                        rows_data = []
                        for row_cells in pdfplumber_data:
                            row = []
                            for cell_content in row_cells:
                                # 这里简化处理，直接使用pdfplumber的文本
                                # 如需更精确，可用PyMuPDF再次提取
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
                        for ri, row_data in enumerate(rows_data[1:], start=2):  # 跳过表头
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
                                    "bbox": None,  # 子表单元格bbox可在需要时提取
                                    "nested_tables": []  # 如需更深嵌套，在此递归
                                })

                            nested_rows.append({
                                "id": row_id,
                                "rowPath": [row_first_cell] if row_first_cell else [],
                                "cells": nested_cells
                            })

                        results.append({
                            "type": "table",
                            "level": depth + 1,  # 嵌套层级
                            "parent_table_id": None,  # 回填在父表落结构时
                            "bbox": list(t.bbox),
                            "columns": columns,
                            "rows": nested_rows,
                            "method": f"nested (depth={depth + 1})"
                        })
                    break  # lines 命中就不再跑 text
            except Exception:
                # 子表检测失败不影响主流程
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
        seed_bboxes = self.collect_page_tables_pymupdf(pymupdf_page)  # 全页表bbox

        # 去掉"自身顶层表"的bbox（只过滤互相包含的，保留单向包含的子表）
        top_like = list(table.bbox)
        seed_bboxes = [bb for bb in seed_bboxes
                       if not (self._contains_with_tol(bb, top_like, tol=1.5)
                              and self._contains_with_tol(top_like, bb, tol=1.5))]

        # 把 PyMuPDF 找到的表，按包含关系分配到父 cell
        hit = self.assign_nested_by_containment(seed_bboxes, bbox_data)

        nested_map = {}  # key=(abs_row_idx, col_idx) ; value=[nested_table,...]
        for (r, c), child_bbs in hit.items():
            packs = []
            for bb in child_bbs:
                packs.extend(self.extract_table_by_bbox(pdf_page, pymupdf_page, bb, depth=1))
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