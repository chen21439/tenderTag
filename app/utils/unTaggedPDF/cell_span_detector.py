"""
单元格合并（colspan/rowspan）检测器
基于bbox几何位置和列栅格推断合并单元格
"""
from typing import List, Tuple, Dict, Any


class CellSpanDetector:
    """单元格跨列/跨行检测器"""

    def __init__(self, tolerance: float = 2.0):
        """
        初始化检测器

        Args:
            tolerance: 边界对齐容差（points），默认2.0pt
        """
        self.tolerance = tolerance

    def build_column_grid(self, cells_bbox: list) -> List[float]:
        """
        根据所有单元格的bbox构建列栅格（col_x_edges）

        Args:
            cells_bbox: pdfplumber的cells列表 [(x0, y0, x1, y1), ...]

        Returns:
            排序后的列边界x坐标列表 [x0, x1, x2, ..., xN]
        """
        if not cells_bbox:
            return []

        # 收集所有x边界
        x_edges = set()
        for bbox in cells_bbox:
            if bbox and len(bbox) >= 4:
                x0, _, x1, _ = bbox
                x_edges.add(x0)
                x_edges.add(x1)

        # 排序并聚类（合并相近的边界）
        x_edges_sorted = sorted(x_edges)

        if not x_edges_sorted:
            return []

        # 聚类：如果两个边界相距小于tolerance，合并为一个
        clustered = [x_edges_sorted[0]]
        for x in x_edges_sorted[1:]:
            if x - clustered[-1] > self.tolerance:
                clustered.append(x)
            else:
                # 取平均值
                clustered[-1] = (clustered[-1] + x) / 2

        return clustered

    def build_row_grid(self, cells_bbox: list) -> List[float]:
        """
        根据所有单元格的bbox构建行栅格（row_y_edges）

        Args:
            cells_bbox: pdfplumber的cells列表 [(x0, y0, x1, y1), ...]

        Returns:
            排序后的行边界y坐标列表 [y0, y1, y2, ..., yN]
        """
        if not cells_bbox:
            return []

        # 收集所有y边界
        y_edges = set()
        for bbox in cells_bbox:
            if bbox and len(bbox) >= 4:
                _, y0, _, y1 = bbox
                y_edges.add(y0)
                y_edges.add(y1)

        # 排序并聚类
        y_edges_sorted = sorted(y_edges)

        if not y_edges_sorted:
            return []

        # 聚类
        clustered = [y_edges_sorted[0]]
        for y in y_edges_sorted[1:]:
            if y - clustered[-1] > self.tolerance:
                clustered.append(y)
            else:
                clustered[-1] = (clustered[-1] + y) / 2

        return clustered

    def detect_cell_span(
        self,
        cell_bbox: tuple,
        col_x_edges: List[float],
        row_y_edges: List[float]
    ) -> Dict[str, Any]:
        """
        检测单个单元格的跨列/跨行信息

        Args:
            cell_bbox: 单元格bbox (x0, y0, x1, y1)
            col_x_edges: 列栅格边界
            row_y_edges: 行栅格边界

        Returns:
            包含跨列/跨行信息的字典:
            {
                'start_col': int,  # 起始列索引（0-based）
                'end_col': int,    # 结束列索引（闭区间）
                'start_row': int,  # 起始行索引（0-based）
                'end_row': int,    # 结束行索引（闭区间）
                'colspan': int,    # 跨列数
                'rowspan': int,    # 跨行数
                'span_type': str   # 'colspan' | 'rowspan' | 'both' | None
            }
        """
        if not cell_bbox or len(cell_bbox) < 4:
            return {
                'start_col': None,
                'end_col': None,
                'start_row': None,
                'end_row': None,
                'colspan': 1,
                'rowspan': 1,
                'span_type': None
            }

        x0, y0, x1, y1 = cell_bbox

        # 查找起始列和结束列
        start_col = self._find_col_index(x0, col_x_edges, is_start=True)
        end_col = self._find_col_index(x1, col_x_edges, is_start=False)

        # 查找起始行和结束行
        start_row = self._find_row_index(y0, row_y_edges, is_start=True)
        end_row = self._find_row_index(y1, row_y_edges, is_start=False)

        # 计算跨度
        colspan = end_col - start_col + 1 if (start_col is not None and end_col is not None) else 1
        rowspan = end_row - start_row + 1 if (start_row is not None and end_row is not None) else 1

        # 确定span类型
        span_type = None
        if colspan > 1 and rowspan > 1:
            span_type = 'both'
        elif colspan > 1:
            span_type = 'colspan'
        elif rowspan > 1:
            span_type = 'rowspan'

        return {
            'start_col': start_col,
            'end_col': end_col,
            'start_row': start_row,
            'end_row': end_row,
            'colspan': colspan,
            'rowspan': rowspan,
            'span_type': span_type
        }

    def _find_col_index(self, x: float, col_x_edges: List[float], is_start: bool) -> int:
        """
        找到x坐标对应的列索引

        Args:
            x: x坐标
            col_x_edges: 列边界列表
            is_start: True表示查找起始列，False表示查找结束列

        Returns:
            列索引（0-based），找不到返回None
        """
        if not col_x_edges or len(col_x_edges) < 2:
            return None

        # 对于起始位置，找到第一个大于等于x的边界
        # 对于结束位置，找到最后一个小于等于x的边界

        for i, edge in enumerate(col_x_edges):
            if abs(x - edge) <= self.tolerance:
                # 对于起始列，返回当前索引
                # 对于结束列，返回前一个索引（因为列索引是区间的起点）
                if is_start:
                    return i
                else:
                    return max(0, i - 1)

        # 如果没有精确匹配，找最接近的
        if is_start:
            for i in range(len(col_x_edges) - 1):
                if col_x_edges[i] <= x < col_x_edges[i + 1]:
                    return i
            return len(col_x_edges) - 2  # 最后一列
        else:
            for i in range(len(col_x_edges) - 1, 0, -1):
                if col_x_edges[i - 1] < x <= col_x_edges[i]:
                    return i - 1
            return 0  # 第一列

    def _find_row_index(self, y: float, row_y_edges: List[float], is_start: bool) -> int:
        """
        找到y坐标对应的行索引

        Args:
            y: y坐标
            row_y_edges: 行边界列表
            is_start: True表示查找起始行，False表示查找结束行

        Returns:
            行索引（0-based），找不到返回None
        """
        if not row_y_edges or len(row_y_edges) < 2:
            return None

        for i, edge in enumerate(row_y_edges):
            if abs(y - edge) <= self.tolerance:
                if is_start:
                    return i
                else:
                    return max(0, i - 1)

        # 如果没有精确匹配，找最接近的
        if is_start:
            for i in range(len(row_y_edges) - 1):
                if row_y_edges[i] <= y < row_y_edges[i + 1]:
                    return i
            return len(row_y_edges) - 2
        else:
            for i in range(len(row_y_edges) - 1, 0, -1):
                if row_y_edges[i - 1] < y <= row_y_edges[i]:
                    return i - 1
            return 0

    def annotate_table_cells(
        self,
        bbox_data: List[List[tuple]],
        cells_bbox: list
    ) -> Dict[str, Any]:
        """
        为整张表格的所有单元格标注跨列/跨行信息

        Args:
            bbox_data: 二维数组的bbox数据 [[cell_bbox, ...], ...]
            cells_bbox: pdfplumber的原始cells列表

        Returns:
            {
                'col_x_edges': List[float],  # 列栅格
                'row_y_edges': List[float],  # 行栅格
                'cell_spans': List[List[Dict]]  # 每个单元格的span信息
            }
        """
        # 构建列栅格和行栅格
        col_x_edges = self.build_column_grid(cells_bbox)
        row_y_edges = self.build_row_grid(cells_bbox)

        # 为每个单元格检测span
        cell_spans = []
        for row in bbox_data:
            row_spans = []
            for cell_bbox in row:
                if cell_bbox:
                    span_info = self.detect_cell_span(cell_bbox, col_x_edges, row_y_edges)
                else:
                    span_info = {
                        'start_col': None,
                        'end_col': None,
                        'start_row': None,
                        'end_row': None,
                        'colspan': 1,
                        'rowspan': 1,
                        'span_type': None
                    }
                row_spans.append(span_info)
            cell_spans.append(row_spans)

        return {
            'col_x_edges': col_x_edges,
            'row_y_edges': row_y_edges,
            'cell_spans': cell_spans
        }
