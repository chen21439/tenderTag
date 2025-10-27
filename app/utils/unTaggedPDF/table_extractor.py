"""
PDF表格提取器
结合pdfplumber和PyMuPDF来提取PDF中的表格内容
"""

import json
from pathlib import Path
from typing import List, Dict, Any
import pdfplumber
import fitz  # PyMuPDF

# 兼容相对导入和直接运行
try:
    from .nested_table_handler import NestedTableHandler
except ImportError:
    from nested_table_handler import NestedTableHandler


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

        # 嵌套表格处理器
        self.nested_handler = NestedTableHandler(self)

    def _cell_has_inner_grid(self, pymupdf_page, bbox, min_h=2, min_v=2, min_cross=4, min_len=8):
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
        except Exception as e:
            # 任何异常都返回False，表示没有嵌套网格
            return False

    def _extract_nested_tables_in_cell(self, pdf_page, pymupdf_page, cell_bbox, depth=1, max_depth=2):
        """
        在一个 cell 的 bbox 内再次用 pdfplumber 检测表格；必要时递归

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
        if not self._cell_has_inner_grid(pymupdf_page, cell_bbox):
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

                                # 递归：子表内部是否还有更小的表（如需要，可在此处递归调用）
                                # nested2 = self._extract_nested_tables_in_cell(pdf_page, pymupdf_page, ..., depth=depth+1)

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
            except Exception as e:
                # 子表检测失败不影响主流程
                continue

        return results

    def _rect(self, bb):
        """辅助函数：将bbox转换为fitz.Rect"""
        return fitz.Rect(bb[0], bb[1], bb[2], bb[3])

    def _contains_with_tol(self, outer, inner, tol=1.0):
        """
        判断outer是否包含inner（带容差）

        Args:
            outer: 外层bbox (x0, y0, x1, y1)
            inner: 内层bbox (x0, y0, x1, y1)
            tol: 容差值

        Returns:
            是否包含
        """
        o = self._rect((outer[0]-tol, outer[1]-tol, outer[2]+tol, outer[3]+tol))
        i = self._rect(inner)
        return o.contains(i)

    def _collect_page_tables_pymupdf(self, pymupdf_page):
        """
        使用PyMuPDF一次性获取全页的所有表格bbox（方案B主判）

        注意：此方法已废弃，请使用nested_handler.collect_page_tables_pymupdf

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

    def _assign_nested_by_containment(self, sub_bboxes, bbox_data):
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

    def _extract_table_by_bbox(self, pdf_page, pymupdf_page, bbox, depth=1):
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
                                cell_row = self._find_index(y0, y_coords)
                                cell_col = self._find_index(x0, x_coords)

                                if cell_row == row_idx and cell_col == col_idx:
                                    # 使用PyMuPDF从这个bbox提取文本
                                    cell_text = self.extract_cell_text_with_pymupdf(
                                        pymupdf_page, cell_bbox
                                    )
                                    cell_height = y1 - y0
                                    break

                            new_row.append(cell_text if cell_text else "")
                            row_heights.append(cell_height)
                        table_data.append(new_row)
                        bbox_heights.append(sum(row_heights) / len(row_heights) if row_heights else 0)

                    # 合并被错误拆分的行（针对竖排文字等情况）
                    table_data = self.nested_handler.merge_split_rows(table_data, bbox_heights)

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

    def _clean_spurious_columns(self, table_data: List[List[str]], bbox_data: List[List[tuple]], cells: list):
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
            threshold = max(1, (num_rows - 1) * 0.1)  # 至少1行有值，或超过10%
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

    def extract_tables_with_pymupdf_native(self) -> List[Dict[str, Any]]:
        """
        使用PyMuPDF原生的find_tables()方法提取表格（v1.23.0+）
        测试对比pdfplumber的效果

        Returns:
            提取的表格列表
        """
        print("\n" + "="*60)
        print("使用 PyMuPDF 原生 find_tables() 方法")
        print("="*60)

        tables_data = []
        doc = fitz.open(self.pdf_path)

        for page_num in range(len(doc)):
            page = doc[page_num]
            print(f"\n处理第 {page_num + 1} 页...")

            # 使用PyMuPDF的find_tables()
            try:
                # 检查是否有find_tables方法
                if not hasattr(page, 'find_tables'):
                    print(f"  [警告] PyMuPDF版本不支持find_tables()，当前版本: {fitz.version}")
                    continue

                tables = page.find_tables()
                print(f"  发现 {len(tables.tables) if hasattr(tables, 'tables') else 0} 个表格")

                if hasattr(tables, 'tables'):
                    for table_idx, table in enumerate(tables.tables):
                        print(f"\n  表格 {table_idx + 1}:")
                        print(f"    行数: {table.row_count}")
                        print(f"    列数: {table.col_count}")
                        print(f"    bbox: {table.bbox}")

                        # 提取表格数据
                        extracted_data = table.extract()
                        print(f"    提取的行数: {len(extracted_data)}")

                        if extracted_data:
                            print(f"    表头: {extracted_data[0][:3] if len(extracted_data[0]) >= 3 else extracted_data[0]}")

                            # 构建结构化表格
                            self.block_counter += 1
                            table_id = f"doc{self.block_counter:03d}"

                            header_row = extracted_data[0]
                            columns = []
                            for col_idx, header_text in enumerate(header_row):
                                columns.append({
                                    "id": f"c{col_idx + 1:03d}",
                                    "index": col_idx,
                                    "name": str(header_text or "")
                                })

                            rows = []
                            for row_idx, row_data in enumerate(extracted_data[1:], start=2):
                                row_id = f"r{row_idx:03d}"
                                row_first_cell = str(row_data[0] if row_data else "")

                                cells = []
                                for col_idx, cell_content in enumerate(row_data):
                                    col_id = f"c{col_idx + 1:03d}"
                                    cell_id = f"{table_id}-{row_id}-{col_id}"
                                    col_name = str(header_row[col_idx] if col_idx < len(header_row) else "")

                                    cells.append({
                                        "id": cell_id,
                                        "row_id": row_id,
                                        "col_id": col_id,
                                        "rowPath": [row_first_cell] if row_first_cell else [],
                                        "cellPath": [col_name] if col_name else [],
                                        "content": str(cell_content or "").replace('\n', '').replace('\r', '').strip(),
                                        "bbox": None
                                    })

                                rows.append({
                                    "id": row_id,
                                    "rowPath": [row_first_cell] if row_first_cell else [],
                                    "cells": cells
                                })

                            tables_data.append({
                                "type": "table",
                                "id": table_id,
                                "level": 1,
                                "parent_table_id": None,
                                "page": page_num + 1,
                                "columns": columns,
                                "rows": rows,
                                "method": "pymupdf native find_tables()"
                            })
                            print(f"    ✓ 已构建表格 {table_id}")

            except Exception as e:
                print(f"  [错误] PyMuPDF find_tables() 失败: {e}")
                import traceback
                traceback.print_exc()

        doc.close()
        print(f"\n{'='*60}")
        print(f"PyMuPDF 方法完成，共提取 {len(tables_data)} 个表格")
        print(f"{'='*60}\n")
        return tables_data

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

                    # 清理误吸收的子表空列
                    table_data, bbox_data, keep_cols = self._clean_spurious_columns(
                        table_data, bbox_data, cells
                    )

                    # 使用嵌套表格处理器进行检测（方案B主判 + 方案A兜底）
                    nested_map = self.nested_handler.detect_and_extract_nested_tables(
                        page, pymupdf_page, table, bbox_data
                    )

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
                            cells_bbox=cells,
                            nested_map=nested_map
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
        cells_bbox: list,
        nested_map: Dict[tuple, List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        构建结构化表格数据（对齐Word文档格式）

        Args:
            table_id: 表格ID (docN格式)
            table_data: 表格数据 (二维数组)
            bbox_data: 每个单元格的边界框数据 (二维数组)
            page_num: 页码
            cells_bbox: 单元格边界框列表
            nested_map: 嵌套表格映射，key=(row_idx, col_idx), value=[nested_tables]

        Returns:
            结构化表格字典
        """
        if not table_data:
            return {}

        if nested_map is None:
            nested_map = {}

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

                # 获取嵌套表格（注意：bbox_row_idx 与 nested_map 的 r 对齐）
                nested_here = nested_map.get((bbox_row_idx, col_idx), [])
                # 回填 parent_table_id
                for nt in nested_here:
                    nt["parent_table_id"] = table_id

                cell_obj = {
                    "id": cell_id,
                    "row_id": row_id,
                    "col_id": col_id,
                    "rowPath": [row_first_cell] if row_first_cell else [],  # 行路径（数组），支持多层
                    "cellPath": [col_name] if col_name else [],              # 列路径（数组），支持多层
                    "content": cell_content,
                    "bbox": cell_bbox  # 单元格边界框坐标 (x0, y0, x1, y1)
                }

                # 只有识别到嵌套表格时才添加 nested_tables 字段
                if nested_here:
                    cell_obj["nested_tables"] = nested_here

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
    主测试方法 - 对比测试 PyMuPDF native vs pdfplumber
    """
    # 测试用的PDF文件路径
    pdf_path = r"E:\programFile\AIProgram\docxServer\pdf\task\1979102567573037058\真正的嵌套表格-示例.pdf"

    print(f"开始对比测试...")
    print(f"PDF文件: {pdf_path}")

    try:
        # 创建提取器
        extractor = PDFTableExtractor(pdf_path)

        # 方法1：测试 PyMuPDF 原生 find_tables()
        print("\n" + "█"*60)
        print("方法1：PyMuPDF 原生 find_tables()")
        print("█"*60)
        extractor.block_counter = 0  # 重置计数器
        pymupdf_tables = extractor.extract_tables_with_pymupdf_native()

        # 方法2：测试 pdfplumber + PyMuPDF 混合方法
        print("\n" + "█"*60)
        print("方法2：pdfplumber + PyMuPDF 混合方法")
        print("█"*60)
        extractor.block_counter = 0  # 重置计数器
        hybrid_tables = extractor.extract_tables_hybrid()

        # 对比结果
        print("\n" + "█"*60)
        print("对比结果")
        print("█"*60)
        print(f"PyMuPDF方法提取: {len(pymupdf_tables)} 个表格")
        print(f"混合方法提取: {len(hybrid_tables)} 个表格")

        if pymupdf_tables:
            print(f"\nPyMuPDF方法 - 第一个表格:")
            print(f"  列数: {len(pymupdf_tables[0].get('columns', []))}")
            print(f"  行数: {len(pymupdf_tables[0].get('rows', []))}")
            print(f"  列名: {[c['name'] for c in pymupdf_tables[0].get('columns', [])]}")

        if hybrid_tables:
            print(f"\n混合方法 - 第一个表格:")
            print(f"  列数: {len(hybrid_tables[0].get('columns', []))}")
            print(f"  行数: {len(hybrid_tables[0].get('rows', []))}")
            print(f"  列名: {[c['name'] for c in hybrid_tables[0].get('columns', [])]}")

        # 保存结果用于检查
        output_dir = Path(pdf_path).parent

        # 保存 PyMuPDF 结果
        pymupdf_output = output_dir / "table_pymupdf.json"
        with open(pymupdf_output, 'w', encoding='utf-8') as f:
            json.dump({
                "pdf_file": str(pdf_path),
                "total_tables": len(pymupdf_tables),
                "tables": pymupdf_tables
            }, f, ensure_ascii=False, indent=2)
        print(f"\nPyMuPDF结果已保存: {pymupdf_output}")

        # 保存混合方法结果
        hybrid_output = output_dir / "table_hybrid.json"
        with open(hybrid_output, 'w', encoding='utf-8') as f:
            json.dump({
                "pdf_file": str(pdf_path),
                "total_tables": len(hybrid_tables),
                "tables": hybrid_tables
            }, f, ensure_ascii=False, indent=2)
        print(f"混合方法结果已保存: {hybrid_output}")

        # 原来的完整提取
        print("\n" + "█"*60)
        print("完整提取（表格+段落）")
        print("█"*60)
        extractor.block_counter = 0  # 重置计数器
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