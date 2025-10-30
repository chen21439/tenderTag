"""
表头分析器
支持多层表头（列表头 + 行表头）的识别和解析

## 核心思路

### 1. 问题定义
PDF表格可能存在多层表头结构：
- **列表头（顶部）**：如 "药物消杀安排" → "每周/每月/工作标准"
- **行表头（左侧）**：如 "序号" → "位置" → "清洁项目"

### 2. 解决方案（4步法）
**Step 1**: 构建规则网格（TableGrid）
  - 收集所有单元格bbox，提取唯一的X/Y坐标，构建R×C网格
  - 记录每个单元格的跨度（rowspan/colspan）和覆盖范围

**Step 2**: 检测表头区域
  - **列表头检测**：检查前N行是否存在跨列合并（colspan>1）
  - **行表头检测**：检查前N列是否存在跨行合并（rowspan>1）
  - 策略：启发式检测 + 可选手动指定

**Step 3**: 构建列路径（Top-down）
  - 创建层级矩阵 H[层级][数据列]
  - 填充每层的表头文本（处理合并单元格）
  - 层级传播：
    * 纵向继承：空单元格从上层继承
    * 横向继承：合并单元格内部复制
  - 输出：每个数据列的完整路径 ["一级表头", "二级表头", ...]

**Step 4**: 构建行路径（Left-to-right）
  - 创建层级矩阵 V[数据行][层级]
  - 填充每层的表头文本
  - 层级传播：横向继承 + 纵向继承（合并单元格）
  - 输出：每个数据行的完整路径 ["一级表头", "二级表头", ...]

### 3. 关键数据结构
- **SpanCell**: 单个单元格（含合并信息）
  * (r0,r1,c0,c1) - 网格索引范围
  * (rowspan,colspan) - 跨度
  * text - 文本内容
  * bbox - 原始坐标

- **TableGrid**: 规则网格模型
  * R×C 网格
  * grid[r][c] → cell_id（None=空）
  * cells - 所有SpanCell列表

- **HeaderModel**: 分析结果
  * col_levels - 列表头层数
  * row_levels - 行表头列数
  * col_paths - 每个数据列的路径列表
  * row_paths - 每个数据行的路径列表

### 4. 使用示例
```python
analyzer = HeaderAnalyzer()
header_model = analyzer.analyze_table_headers(
    cells_bbox=cells,
    table_data=table_data,
    pymupdf_page=page,
    hint_col_levels=2,  # 可选：手动指定
    hint_row_levels=3   # 可选：手动指定
)

# 结果示例
col_levels = 2  # 顶部2行是列表头
row_levels = 3  # 左侧3列是行表头
col_paths = [
    ["药物消杀安排", "每周"],
    ["药物消杀安排", "每月"],
    ["工作标准"]
]
row_paths = [
    ["1", "卫生间", "蜂蜡"],
    ["1", "卫生间", "取、蜂"],
    ["2", "污水池", "老鼠"]
]
```
"""
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass


@dataclass
class SpanCell:
    """跨度单元格（支持合并单元格）"""
    r0: int  # 起始行索引
    r1: int  # 结束行索引（不含）
    c0: int  # 起始列索引
    c1: int  # 结束列索引（不含）
    rowspan: int  # 跨行数
    colspan: int  # 跨列数
    text: str  # 单元格文本
    bbox: tuple  # 单元格bbox


@dataclass
class TableGrid:
    """规则网格模型"""
    R: int  # 总行数
    C: int  # 总列数
    x_edges: List[float]  # X坐标边界（长度=C+1）
    y_edges: List[float]  # Y坐标边界（长度=R+1）
    grid: List[List[Optional[int]]]  # R×C 网格，存储cell_id（None表示空）
    cells: List[SpanCell]  # 所有单元格列表


@dataclass
class HeaderModel:
    """表头模型"""
    col_levels: int  # 列表头层数（顶部有多少行是表头）
    row_levels: int  # 行表头列数（左侧有多少列是表头）
    col_paths: List[List[str]]  # 每个数据列的完整路径（长度=C-row_levels）
    row_paths: List[List[str]]  # 每个数据行的完整路径（长度=R-col_levels）


class HeaderAnalyzer:
    """表头分析器"""

    def __init__(self):
        """初始化分析器"""
        self.table_count = 0  # 表格计数器，用于debug

    def build_grid_and_spans(self, cells_bbox: list, table_data: List[List[str]],
                            pymupdf_page=None, debug: bool = False) -> Tuple[TableGrid, List[SpanCell]]:
        """
        Step 1: 构建规则网格与跨度映射

        Args:
            cells_bbox: pdfplumber的cells列表 [(x0,y0,x1,y1), ...]
            table_data: 表格文本数据（二维数组）- 仅用于兜底
            pymupdf_page: PyMuPDF页面对象（用于提取文本）
            debug: 是否输出调试信息

        Returns:
            (TableGrid, List[SpanCell])
        """
        if not cells_bbox:
            return None, []

        # 1. 收集所有唯一的X和Y坐标
        x_coords = set()
        y_coords = set()
        for bbox in cells_bbox:
            x0, y0, x1, y1 = bbox
            x_coords.add(x0)
            x_coords.add(x1)
            y_coords.add(y0)
            y_coords.add(y1)

        # 排序得到边界
        x_edges = sorted(x_coords)
        y_edges = sorted(y_coords)

        C = len(x_edges) - 1  # 列数
        R = len(y_edges) - 1  # 行数

        if debug:
            print(f"\n[DEBUG build_grid_and_spans] R={R}, C={C}")
            print(f"  cells_bbox总数: {len(cells_bbox)}")
            print(f"  前10个cells_bbox:")
            for i in range(min(10, len(cells_bbox))):
                print(f"    [{i}] {cells_bbox[i]}")
            print(f"  y_edges前5个: {y_edges[:5]}")
            print(f"  x_edges前5个: {x_edges[:5]}")

        # 2. 初始化网格（None表示空）
        grid = [[None for _ in range(C)] for _ in range(R)]

        # 3. 为每个单元格计算跨度并填充网格
        span_cells = []
        cell_id = 0

        for bbox in cells_bbox:
            x0, y0, x1, y1 = bbox

            # 找到对应的网格索引
            r0 = self._find_index(y0, y_edges)
            r1 = self._find_index(y1, y_edges)
            c0 = self._find_index(x0, x_edges)
            c1 = self._find_index(x1, x_edges)

            # 计算跨度
            rowspan = r1 - r0
            colspan = c1 - c0

            # 提取文本 - 直接从PyMuPDF使用bbox提取（避免grid索引与table_data索引不匹配）
            text = ""
            if pymupdf_page:
                try:
                    import fitz
                    rect_obj = fitz.Rect(bbox)
                    text = pymupdf_page.get_text("text", clip=rect_obj)
                    # 注意：不在这里清理文本，保留原始 \n，延迟到 pdf_content_extractor 中清理
                    # text = text.replace('\n', '').replace('\r', '').strip()
                    text = text.strip()  # 只去掉首尾空格
                except Exception:
                    # 失败时尝试从table_data兜底
                    if r0 < len(table_data) and c0 < len(table_data[r0]):
                        text = table_data[r0][c0] if table_data[r0][c0] else ""
            else:
                # 没有pymupdf_page时从table_data获取（兜底）
                if r0 < len(table_data) and c0 < len(table_data[r0]):
                    text = table_data[r0][c0] if table_data[r0][c0] else ""

            # 调试：打印前5个单元格的详细信息
            if debug and cell_id < 5:
                print(f"  [Cell {cell_id}] bbox={bbox}")
                print(f"    y0={y0:.2f} -> r0={r0}, y1={y1:.2f} -> r1={r1}, rowspan={rowspan}")
                print(f"    x0={x0:.2f} -> c0={c0}, x1={x1:.2f} -> c1={c1}, colspan={colspan}")
                print(f"    text='{self._clean_text(text)}'")
                print(f"    填充grid范围: rows[{r0}:{r1}] x cols[{c0}:{c1}]")
                if rowspan == 0 or colspan == 0:
                    print(f"    ⚠️ WARNING: rowspan={rowspan}, colspan={colspan} - 不会填充grid!")

            # 创建SpanCell
            # 注意：不在这里清理文本，保留原始 \n，延迟到 pdf_content_extractor 中清理
            span_cell = SpanCell(
                r0=r0, r1=r1, c0=c0, c1=c1,
                rowspan=rowspan, colspan=colspan,
                text=text,  # 保留原始文本，不调用 _clean_text()
                bbox=bbox
            )
            span_cells.append(span_cell)

            # 填充网格（所有被覆盖的格子都指向这个cell_id）
            for r in range(r0, r1):
                for c in range(c0, c1):
                    if r < R and c < C:
                        grid[r][c] = cell_id

            cell_id += 1

        # 4. 构建TableGrid
        table_grid = TableGrid(
            R=R, C=C,
            x_edges=x_edges,
            y_edges=y_edges,
            grid=grid,
            cells=span_cells
        )

        return table_grid, span_cells

    def detect_header_regions(self, grid: TableGrid, span_cells: List[SpanCell],
                             hint_col_levels: Optional[int] = None,
                             hint_row_levels: Optional[int] = None) -> Tuple[int, int]:
        """
        Step 2: 检测表头区域

        Args:
            grid: 表格网格
            span_cells: 跨度单元格列表
            hint_col_levels: 手动指定列表头层数
            hint_row_levels: 手动指定行表头列数

        Returns:
            (col_levels, row_levels)
        """
        # 如果有手动提示，直接使用
        if hint_col_levels is not None and hint_row_levels is not None:
            return hint_col_levels, hint_row_levels

        # 启发式检测
        col_levels = self._detect_col_header_levels(grid, span_cells)
        row_levels = self._detect_row_header_levels(grid, span_cells)

        return col_levels, row_levels

    def build_col_paths(self, grid: TableGrid, span_cells: List[SpanCell],
                       col_levels: int, row_levels: int) -> List[List[str]]:
        """
        Step 3: 构建列表头层级（Top-down）

        Args:
            grid: 表格网格
            span_cells: 跨度单元格列表
            col_levels: 列表头层数
            row_levels: 行表头列数

        Returns:
            col_paths: 每个数据列的完整路径
        """
        R, C = grid.R, grid.C
        data_cols = C - row_levels  # 数据区列数

        if data_cols <= 0:
            return []

        # 初始化层级矩阵 H[层级][列]
        H = [['' for _ in range(data_cols)] for _ in range(col_levels)]

        # 遍历每一层表头
        for r in range(col_levels):
            for j in range(row_levels, C):  # 从row_levels开始是数据列
                # 找到覆盖 grid[r][j] 的单元格
                cell_id = grid.grid[r][j]
                if cell_id is not None:
                    cell = span_cells[cell_id]
                    text = cell.text
                    # 写入矩阵
                    data_col_idx = j - row_levels
                    H[r][data_col_idx] = text

        # 层级传播（处理合并造成的空白）
        for r in range(col_levels):
            for k in range(data_cols):
                # 纵向继承（从上层继承）
                if not H[r][k] and r > 0:
                    H[r][k] = H[r-1][k]

                # 横向继承（从左侧继承，如果属于同一合并块）
                if not H[r][k] and k > 0:
                    # 检查是否属于同一个合并单元格
                    curr_cell_id = grid.grid[r][k + row_levels]
                    left_cell_id = grid.grid[r][k - 1 + row_levels]
                    if curr_cell_id == left_cell_id:
                        H[r][k] = H[r][k-1]

        # 构建路径（从上到下合并各层）
        col_paths = []
        for k in range(data_cols):
            path = []
            for r in range(col_levels):
                text = H[r][k]
                if text and text not in path:  # 去重
                    path.append(text)
            col_paths.append(path)

        return col_paths

    def build_row_paths(self, grid: TableGrid, span_cells: List[SpanCell],
                       col_levels: int, row_levels: int, debug: bool = False) -> List[List[str]]:
        """
        Step 4: 构建行表头层级（Left-to-right）

        Args:
            grid: 表格网格
            span_cells: 跨度单元格列表
            col_levels: 列表头层数
            row_levels: 行表头列数
            debug: 是否输出调试信息

        Returns:
            row_paths: 每个数据行的完整路径
        """
        R, C = grid.R, grid.C
        data_rows = R - col_levels  # 数据区行数

        if debug:
            print(f"\n[DEBUG build_row_paths] R={R}, C={C}, col_levels={col_levels}, row_levels={row_levels}, data_rows={data_rows}")
            print(f"  grid.grid前3行前3列:")
            for r in range(min(3, R)):
                print(f"    行{r}: {grid.grid[r][:min(3, C)]}")
            print(f"  span_cells前5个text:")
            for i in range(min(5, len(span_cells))):
                print(f"    cell{i}: '{span_cells[i].text}' at ({span_cells[i].r0},{span_cells[i].c0})")

        if data_rows <= 0:
            return []

        # 初始化层级矩阵 V[行][层级]
        V = [['' for _ in range(row_levels)] for _ in range(data_rows)]

        # 遍历每一行（数据区）
        for i in range(col_levels, R):
            for c in range(row_levels):  # 左侧表头列
                # 找到覆盖 grid[i][c] 的单元格
                cell_id = grid.grid[i][c]
                if cell_id is not None:
                    cell = span_cells[cell_id]
                    text = cell.text
                    # 写入矩阵
                    data_row_idx = i - col_levels
                    V[data_row_idx][c] = text
                    if debug and data_row_idx < 3:
                        print(f"  V[{data_row_idx}][{c}] = '{text}' (cell_id={cell_id})")

        if debug:
            print(f"  V矩阵(前3行):")
            for i in range(min(3, data_rows)):
                print(f"    V[{i}]: {V[i]}")

        # 层级传播
        for i in range(data_rows):
            for c in range(row_levels):
                # 横向继承（从左侧继承）
                if not V[i][c] and c > 0:
                    V[i][c] = V[i][c-1]

                # 纵向继承（从上行继承，如果属于同一合并块）
                if not V[i][c] and i > 0:
                    curr_cell_id = grid.grid[i + col_levels][c]
                    above_cell_id = grid.grid[i - 1 + col_levels][c]
                    if curr_cell_id == above_cell_id:
                        V[i][c] = V[i-1][c]

        # 构建路径（从左到右合并各列）
        row_paths = []
        for i in range(data_rows):
            path = []
            for c in range(row_levels):
                text = V[i][c]
                if text and text not in path:  # 去重
                    path.append(text)
            row_paths.append(path)

        if debug:
            print(f"  最终row_paths(前3个): {row_paths[:3]}")

        return row_paths

    def analyze_table_headers(self, cells_bbox: list, table_data: List[List[str]],
                             pymupdf_page=None,
                             hint_col_levels: Optional[int] = None,
                             hint_row_levels: Optional[int] = None) -> Optional[HeaderModel]:
        """
        完整的表头分析流程（Steps 1-4）

        Args:
            cells_bbox: pdfplumber的cells列表
            table_data: 表格文本数据
            pymupdf_page: PyMuPDF页面对象
            hint_col_levels: 手动指定列表头层数
            hint_row_levels: 手动指定行表头列数

        Returns:
            HeaderModel 或 None（如果分析失败）
        """
        try:
            # 判断是否是第一个表格（启用debug）
            self.table_count += 1
            is_first_table = (self.table_count == 1)

            # Step 1: 构建网格和跨度（第一个表格启用debug）
            grid, span_cells = self.build_grid_and_spans(
                cells_bbox, table_data, pymupdf_page, debug=is_first_table
            )
            if not grid:
                return None

            # Step 2: 检测表头区域
            col_levels, row_levels = self.detect_header_regions(
                grid, span_cells, hint_col_levels, hint_row_levels
            )

            # Step 3: 构建列路径
            col_paths = self.build_col_paths(grid, span_cells, col_levels, row_levels)

            # Step 4: 构建行路径（第一个表格启用debug）
            row_paths = self.build_row_paths(
                grid, span_cells, col_levels, row_levels, debug=is_first_table
            )

            # 构建HeaderModel
            header_model = HeaderModel(
                col_levels=col_levels,
                row_levels=row_levels,
                col_paths=col_paths,
                row_paths=row_paths
            )

            return header_model

        except Exception as e:
            # 分析失败，返回None（回退到单层表头）
            print(f"[WARNING] 表头分析失败: {e}")
            return None

    def _detect_col_header_levels(self, grid: TableGrid, span_cells: List[SpanCell]) -> int:
        """
        启发式检测列表头层数

        策略：
        1. 检测前N行，看是否存在跨列合并
        2. 如果第一行有跨列，至少是2层
        3. 统计连续的表头行数
        """
        R, C = grid.R, grid.C
        max_check_rows = min(5, R)  # 最多检查前5行

        # 统计每行的跨列单元格数量
        colspan_counts = []
        for r in range(max_check_rows):
            colspan_count = 0
            checked_cells = set()

            for c in range(C):
                cell_id = grid.grid[r][c]
                if cell_id is not None and cell_id not in checked_cells:
                    cell = span_cells[cell_id]
                    if cell.colspan > 1:
                        colspan_count += 1
                    checked_cells.add(cell_id)

            colspan_counts.append(colspan_count)

        # 如果第一行有跨列，至少2层
        if colspan_counts and colspan_counts[0] > 0:
            # 连续统计有跨列的行数
            levels = 1
            for count in colspan_counts[1:]:
                if count > 0:
                    levels += 1
                else:
                    break
            return max(2, levels)

        # 默认1层
        return 1

    def _detect_row_header_levels(self, grid: TableGrid, span_cells: List[SpanCell]) -> int:
        """
        启发式检测行表头列数

        策略：
        1. 检测前N列，看是否存在跨行合并
        2. 统计连续的表头列数
        3. 只有检测到跨行合并时，才认为有行表头
        """
        R, C = grid.R, grid.C
        max_check_cols = min(5, C)

        # 统计每列的跨行单元格数量
        rowspan_counts = []
        for c in range(max_check_cols):
            rowspan_count = 0
            checked_cells = set()

            for r in range(R):
                cell_id = grid.grid[r][c]
                if cell_id is not None and cell_id not in checked_cells:
                    cell = span_cells[cell_id]
                    if cell.rowspan > 1:
                        rowspan_count += 1
                    checked_cells.add(cell_id)

            rowspan_counts.append(rowspan_count)

        # 如果第一列有跨行，至少2列
        if rowspan_counts and rowspan_counts[0] > 0:
            # 连续统计有跨行的列数
            levels = 1
            for count in rowspan_counts[1:]:
                if count > 0:
                    levels += 1
                else:
                    break
            return max(2, levels)

        # 没有检测到跨行合并，返回0（没有行表头）
        return 0

    def _find_index(self, coord: float, coords_list: List[float]) -> int:
        """
        找到坐标在坐标列表中的索引位置

        Args:
            coord: 要查找的坐标
            coords_list: 已排序的坐标列表

        Returns:
            索引位置
        """
        # 处理精确匹配的情况（单元格边界坐标）
        for i, edge_coord in enumerate(coords_list):
            if abs(coord - edge_coord) < 0.01:  # 浮点数比较，允许0.01的误差
                return i

        # 处理区间匹配的情况
        for i in range(len(coords_list) - 1):
            if coords_list[i] <= coord < coords_list[i + 1]:
                return i

        # 兜底：返回最后一个有效索引
        return len(coords_list) - 2 if len(coords_list) >= 2 else 0

    def _clean_text(self, text: str) -> str:
        """
        清理文本（移除换行符、占位符等）

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        if not text:
            return ""

        # 移除换行符
        text = text.replace('\n', '').replace('\r', '').strip()

        # 移除占位符
        if text in ['/', '—', '－', '·', '…']:
            return ""

        return text