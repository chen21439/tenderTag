"""
跨页单元格合并器
负责检测并合并被分页符截断的单元格内容

## 核心思路

当同一个单元格被分页符截断时，需要识别并将其合并为同一个单元格。

## 检测策略（基于特征的直接判断）

必须同时满足以下条件：
1. **列位置一致**：col_id 相同 或 x坐标范围重叠 > 80%
2. **上页单元格**：底边没有完整横线（覆盖率 < 50%）
3. **下页单元格**：顶边没有完整横线（覆盖率 < 50%）

## 合并策略

1. 将下页单元格的内容追加到上页单元格
2. 标记下页单元格为已合并
3. 保留上页单元格的bbox（跨页bbox不能直接合并）
4. 在元数据中记录 split_across_pages: True

## 使用示例

```python
from crossPageTable import CellMerger

merger = CellMerger(
    coverage_threshold=0.5,  # 横线覆盖率阈值
    y_tolerance=2.0,         # Y坐标容差
    x_overlap_threshold=0.8  # X坐标重叠阈值
)

# 检测截断的单元格
split_indices = merger.detect_split_cells(
    prev_last_row,
    next_first_row,
    prev_drawings,
    next_drawings
)

# 合并截断的单元格
if split_indices:
    merger.merge_split_cells(prev_row, next_row, split_indices)
```
"""
from typing import List, Dict, Tuple


class CellMerger:
    """跨页单元格合并器"""

    def __init__(self,
                 coverage_threshold: float = 0.5,
                 y_tolerance: float = 2.0,
                 x_overlap_threshold: float = 0.8):
        """
        初始化单元格合并器

        Args:
            coverage_threshold: 横线覆盖率阈值（默认0.5，即横线覆盖≥50%单元格宽度）
            y_tolerance: Y坐标容差（默认2.0pt）
            x_overlap_threshold: X坐标重叠阈值（默认0.8，即80%重叠）
        """
        self.coverage_threshold = coverage_threshold
        self.y_tolerance = y_tolerance
        self.x_overlap_threshold = x_overlap_threshold

    def detect_split_cells(self,
                          prev_last_row: Dict,
                          next_first_row: Dict,
                          prev_drawings: List,
                          next_drawings: List) -> List[Tuple[int, int]]:
        """
        检测跨页截断的单元格（基于特征的直接判断）

        必须同时满足以下条件：
        1. 列位置一致：col_id 相同 或 x坐标范围重叠 > 80%
        2. 上页单元格：底边没有完整横线（覆盖率 < 50%）
        3. 下页单元格：顶边没有完整横线（覆盖率 < 50%）

        Args:
            prev_last_row: 上页最后一行（包含cells列表）
            next_first_row: 下页第一行（包含cells列表）
            prev_drawings: 上页的线条数据
            next_drawings: 下页的线条数据

        Returns:
            [(col_index_prev, col_index_next), ...] 被截断的单元格索引对
        """
        if not prev_last_row or not next_first_row:
            return []

        prev_cells = prev_last_row.get('cells', [])
        next_cells = next_first_row.get('cells', [])

        if not prev_cells or not next_cells:
            return []

        split_indices = []

        # 遍历上页最后一行的每个单元格
        for prev_idx, prev_cell in enumerate(prev_cells):
            prev_bbox = prev_cell.get('bbox')
            prev_col_id = prev_cell.get('col_id')

            if not prev_bbox or len(prev_bbox) < 4:
                continue

            prev_x0, prev_y0, prev_x1, prev_y1 = prev_bbox
            prev_width = prev_x1 - prev_x0

            if prev_width <= 0:
                continue

            # 遍历下页第一行的每个单元格，寻找匹配的列
            for next_idx, next_cell in enumerate(next_cells):
                next_bbox = next_cell.get('bbox')
                next_col_id = next_cell.get('col_id')

                if not next_bbox or len(next_bbox) < 4:
                    continue

                next_x0, next_y0, next_x1, next_y1 = next_bbox
                next_width = next_x1 - next_x0

                if next_width <= 0:
                    continue

                # 条件1：列位置一致（col_id相同 或 x坐标重叠 > 80%）
                col_match = False

                # 方式1：col_id相同
                if prev_col_id and next_col_id and prev_col_id == next_col_id:
                    col_match = True
                else:
                    # 方式2：x坐标重叠 > 80%
                    overlap_x0 = max(prev_x0, next_x0)
                    overlap_x1 = min(prev_x1, next_x1)
                    overlap_width = max(0, overlap_x1 - overlap_x0)

                    # 计算重叠率（相对于较小的单元格宽度）
                    min_width = min(prev_width, next_width)
                    overlap_ratio = overlap_width / min_width if min_width > 0 else 0

                    if overlap_ratio > self.x_overlap_threshold:
                        col_match = True

                if not col_match:
                    continue

                # 条件2：上页单元格底边没有完整横线
                prev_has_bottom = self._cell_has_horizontal_line(
                    prev_bbox,
                    prev_y1,  # 底边Y坐标
                    prev_drawings
                )

                if prev_has_bottom:
                    continue

                # 条件3：下页单元格顶边没有完整横线
                next_has_top = self._cell_has_horizontal_line(
                    next_bbox,
                    next_y0,  # 顶边Y坐标
                    next_drawings
                )

                if next_has_top:
                    continue

                # 所有条件都满足，认为这是一对被截断的单元格
                split_indices.append((prev_idx, next_idx))
                break  # 找到匹配的下页单元格后，停止内层循环

        return split_indices

    def merge_split_cells(self,
                         prev_row: Dict,
                         next_row: Dict,
                         split_indices: List[Tuple[int, int]]) -> None:
        """
        合并截断的单元格（原地修改 prev_row 和 next_row）

        操作：
        1. 将下页单元格的内容追加到上页单元格
        2. 标记下页单元格为已合并（设置特殊标记）
        3. 保留上页单元格的bbox（跨页bbox不能直接合并）
        4. 在元数据中记录 split_across_pages: True

        Args:
            prev_row: 上页最后一行（会被原地修改）
            next_row: 下页第一行（会被原地修改）
            split_indices: 被截断的单元格索引对列表
        """
        if not split_indices:
            return

        prev_cells = prev_row.get('cells', [])
        next_cells = next_row.get('cells', [])

        for prev_idx, next_idx in split_indices:
            if prev_idx >= len(prev_cells) or next_idx >= len(next_cells):
                continue

            prev_cell = prev_cells[prev_idx]
            next_cell = next_cells[next_idx]

            # 1. 合并内容
            prev_content = prev_cell.get('content', '')
            next_content = next_cell.get('content', '')

            # 智能合并策略：
            # - 如果上页内容以"、，；：-"等结尾，直接拼接
            # - 否则可能需要空格或换行分隔
            if prev_content.rstrip().endswith(('、', '，', '；', '：', '-', '续', '（')):
                merged_content = prev_content + next_content
            elif prev_content.strip() and next_content.strip():
                # 两边都有内容，用空格分隔
                merged_content = prev_content.rstrip() + ' ' + next_content.lstrip()
            else:
                # 有一边为空，直接拼接
                merged_content = prev_content + next_content

            prev_cell['content'] = merged_content

            # 2. 标记为跨页合并
            prev_cell['split_across_pages'] = True
            prev_cell['merged_from_next_page'] = True

            # 3. 标记下页单元格为已合并（内容已移至上页）
            next_cell['merged_to_prev_page'] = True
            next_cell['original_content'] = next_content  # 保留原始内容供调试
            # 清空下页单元格的内容（避免重复显示）
            next_cell['content'] = ''

            # 4. bbox保留上页的（跨页bbox无法合并）
            # 不修改 prev_cell['bbox']

    def _cell_has_horizontal_line(self,
                                  cell_bbox: List[float],
                                  y_position: float,
                                  drawings: List) -> bool:
        """
        检查单元格的某条边（顶边或底边）是否有完整横线

        Args:
            cell_bbox: 单元格bbox [x0, y0, x1, y1]
            y_position: 要检查的Y坐标（通常是 bbox[1] 或 bbox[3]）
            drawings: 页面线条数据

        Returns:
            True: 有完整横线
            False: 无横线或横线不完整
        """
        if not drawings or not cell_bbox:
            return False

        x0, y0, x1, y1 = cell_bbox
        cell_width = x1 - x0

        if cell_width <= 0:
            return False

        # 遍历所有绘图元素
        for drawing in drawings:
            if not isinstance(drawing, dict):
                continue

            items = drawing.get('items', [])
            for item in items:
                # 只关注直线（'l'表示line）
                if not isinstance(item, tuple) or len(item) < 3:
                    continue

                item_type = item[0]
                if item_type != 'l':
                    continue

                p1 = item[1]  # 起点 (x, y)
                p2 = item[2]  # 终点 (x, y)

                if not isinstance(p1, (tuple, list)) or not isinstance(p2, (tuple, list)):
                    continue
                if len(p1) < 2 or len(p2) < 2:
                    continue

                line_x0 = min(p1[0], p2[0])
                line_x1 = max(p1[0], p2[0])
                line_y0 = min(p1[1], p2[1])
                line_y1 = max(p1[1], p2[1])

                # 判断是否为横线（y坐标变化小）
                if abs(line_y1 - line_y0) > 2.0:
                    continue

                line_y = (line_y0 + line_y1) / 2

                # 检查Y坐标是否匹配
                if abs(line_y - y_position) > self.y_tolerance:
                    continue

                # 计算线条与单元格的水平重叠
                overlap_x0 = max(line_x0, x0)
                overlap_x1 = min(line_x1, x1)
                overlap_width = max(0, overlap_x1 - overlap_x0)
                overlap_ratio = overlap_width / cell_width

                # 如果覆盖率达到阈值，认为有完整横线
                if overlap_ratio >= self.coverage_threshold:
                    return True

        return False


# ===== 向后兼容：保留模块级函数 =====
# 这些函数调用 CellMerger 类的默认实例

_default_merger = CellMerger()


def _cell_has_horizontal_line(cell_bbox: List[float],
                               y_position: float,
                               drawings: List,
                               coverage_threshold: float = 0.5) -> bool:
    """
    检查单元格的某条边（顶边或底边）是否有完整横线

    注意：这是向后兼容的函数，推荐使用 CellMerger 类
    """
    merger = CellMerger(coverage_threshold=coverage_threshold)
    return merger._cell_has_horizontal_line(cell_bbox, y_position, drawings)


def _detect_split_cells(prev_last_row: Dict,
                        next_first_row: Dict,
                        prev_drawings: List,
                        next_drawings: List) -> List[Tuple[int, int]]:
    """
    检测跨页截断的单元格

    注意：这是向后兼容的函数，推荐使用 CellMerger 类
    """
    return _default_merger.detect_split_cells(
        prev_last_row, next_first_row, prev_drawings, next_drawings
    )


def _merge_split_cells(prev_row: Dict,
                       next_row: Dict,
                       split_indices: List[Tuple[int, int]]) -> None:
    """
    合并截断的单元格

    注意：这是向后兼容的函数，推荐使用 CellMerger 类
    """
    _default_merger.merge_split_cells(prev_row, next_row, split_indices)