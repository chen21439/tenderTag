"""
表格提取器123
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
    from .cell_span_detector import CellSpanDetector
    from .crossPageTable.column_boundary_strategy import DEFAULT_STRATEGY
except ImportError:
    from nested_table_handler import NestedTableHandler
    from bbox_utils import rect, contains_with_tol
    from header_analyzer import HeaderAnalyzer
    from cell_span_detector import CellSpanDetector
    from crossPageTable.column_boundary_strategy import DEFAULT_STRATEGY


def validate_and_fix_bbox(table_bbox: list, cells: List[Dict], page_height: float) -> list:
    """
    验证并修正表格bbox

    当pdfplumber提供的bbox无效时（负坐标、超出页面），从cells重新计算bbox

    Args:
        table_bbox: pdfplumber提供的原始bbox [x0, y0, x1, y1]
        cells: 所有单元格列表，每个cell有'bbox'字段
        page_height: 页面高度（用于验证）

    Returns:
        修正后的bbox
    """
    x0, y0, x1, y1 = table_bbox

    # 检查是否有无效坐标
    is_invalid = False

    if y0 < 0 or y1 < 0 or x0 < 0 or x1 < 0:
        is_invalid = True
        print(f"  [bbox修正] 检测到负坐标: x0={x0:.2f}, y0={y0:.2f}, x1={x1:.2f}, y1={y1:.2f}")

    if (y1 - y0) > page_height * 1.5:  # 高度超过1.5倍页面高度
        is_invalid = True
        print(f"  [bbox修正] 检测到异常高度: {y1-y0:.2f} (页面高度: {page_height})")

    if not is_invalid:
        return table_bbox

    # 从cells重新计算bbox
    if not cells:
        print(f"  [bbox修正] 无cells可用，使用原始bbox")
        return table_bbox

    # 收集所有cell bbox
    all_x0, all_y0, all_x1, all_y1 = [], [], [], []

    for cell in cells:
        # 支持两种格式：
        # 1. pdfplumber原始cells：tuple (x0, y0, x1, y1)
        # 2. processed cells：dict {'bbox': (x0, y0, x1, y1)}
        if isinstance(cell, tuple) and len(cell) == 4:
            # pdfplumber原始cells格式
            cell_bbox = cell
        elif isinstance(cell, dict):
            # processed cells格式
            cell_bbox = cell.get('bbox')
        else:
            cell_bbox = None

        if cell_bbox:
            all_x0.append(cell_bbox[0])
            all_y0.append(cell_bbox[1])
            all_x1.append(cell_bbox[2])
            all_y1.append(cell_bbox[3])

    if not all_x0:
        print(f"  [bbox修正] cells中无有效bbox，使用原始bbox")
        return table_bbox

    fixed_bbox = [
        min(all_x0),
        min(all_y0),
        max(all_x1),
        max(all_y1)
    ]

    print(f"  [bbox修正] 从{len(cells)}个cells重新计算bbox:")
    print(f"    原始: [{x0:.2f}, {y0:.2f}, {x1:.2f}, {y1:.2f}]")
    print(f"    修正: [{fixed_bbox[0]:.2f}, {fixed_bbox[1]:.2f}, {fixed_bbox[2]:.2f}, {fixed_bbox[3]:.2f}]")

    return fixed_bbox


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

        # 单元格跨列/跨行检测器
        self.span_detector = CellSpanDetector(tolerance=2.0)

        # 列边界继承策略（默认：禁用）
        self.column_inheritance_strategy = DEFAULT_STRATEGY

        # 缓存每页的垂直线（用于完整列边界检测）
        self._page_vertical_lines_cache = {}

    # ==================== PyMuPDF + PDFPlumber 协同列边界检测 ====================

    def _detect_full_vertical_lines_pymupdf(self, pymupdf_page, page_num: int) -> List[float]:
        """
        使用 PyMuPDF 的 get_drawings() 检测页面中的所有垂直线（过滤表格区域）

        ## 核心逻辑

        ### 1. 收集垂直线段
        遍历 `get_drawings()` 返回的所有图形对象：
        - **'l' 类型（线段）**：直接判断 |p1.x - p2.x| < 2
        - **'re' 类型（矩形）**：判断 width < 2 且 height > 10
          * PDF可能使用细矩形绘制线条
          * 添加这个支持解决了部分垂直线检测失败的问题

        ### 2. 按x坐标分组并计算总长度
        ```python
        v_lines_segments = {
            33.6: [(100, 200), (300, 500)],  # 总长度 = 300pt
            99.0: [(100, 800)],              # 总长度 = 700pt
        }
        ```

        ### 3. 过滤条件：总长度 > 300pt
        **设计思路**：
        - 表格的列边界通常贯穿整个表格高度（几百pt）
        - 装饰性短线通常 < 100pt
        - 300pt 阈值可以有效过滤装饰线，保留列边界

        **已知问题**：
        ⚠️ 对于有子列的表格（如页面5），会检测到所有子列的垂直线
        - 页面5：检测到8条线（7列），包含子列
        - 页面6-8：检测到6条线（5列），仅主列
        
        **可能的改进方向**：
        1. 根据线段的连续性判断（是否跨越多行）
        2. 根据线段与其他线的交点数量判断（主列 vs 子列）
        3. 提高阈值到 500pt（更保守，但可能漏检短表格）

        ### 4. 缓存机制
        使用 `_page_vertical_lines_cache` 避免重复检测

        ## 改进历史

        **2025-10-30**：
        - 添加矩形('re')类型支持
        - 简化过滤逻辑：从复杂多条件 → 单一总长度阈值
        - 解决页面6左侧列缺失问题

        Args:
            pymupdf_page: PyMuPDF 页面对象
            page_num: 页码（用于缓存和日志）

        Returns:
            排序后的垂直线x坐标列表（总长度>300pt的线）
            
        Example:
            >>> lines = self._detect_full_vertical_lines_pymupdf(page, 5)
            >>> print(lines)
            [33.6, 86.4, 99.0, 231.1, 297.7, 429.1, 495.1, 561.1]
            # 8条线 = 7列（页面5有子列）
        """
        # 检查缓存
        if page_num in self._page_vertical_lines_cache:
            return self._page_vertical_lines_cache[page_num]

        # 收集垂直线段信息：{x: [(y0, y1), ...]}
        v_lines_segments = {}

        try:
            # 获取所有绘图对象
            drawings = pymupdf_page.get_drawings()

            for drawing in drawings:
                for item in drawing['items']:
                    # 'l' 表示线段
                    if item[0] == 'l':
                        p1, p2 = item[1], item[2]

                        # 判断是否为垂直线（允许2个单位的误差）
                        if abs(p1.x - p2.x) < 2:
                            x = round(p1.x, 1)  # 四舍五入到0.1
                            y0, y1 = min(p1.y, p2.y), max(p1.y, p2.y)

                            if x not in v_lines_segments:
                                v_lines_segments[x] = []
                            v_lines_segments[x].append((y0, y1))

                    # 're' 表示矩形（PDF可能使用细矩形绘制线条）
                    elif item[0] == 're':
                        rect = item[1]  # fitz.Rect对象

                        # 判断是否为垂直线（宽度很小的细矩形）
                        width = abs(rect.x1 - rect.x0)
                        height = abs(rect.y1 - rect.y0)

                        # 如果宽度 < 2pt 且高度 > 10pt，认为是垂直线
                        if width < 2 and height > 10:
                            x = round((rect.x0 + rect.x1) / 2, 1)  # 取中点
                            y0, y1 = min(rect.y0, rect.y1), max(rect.y0, rect.y1)

                            if x not in v_lines_segments:
                                v_lines_segments[x] = []
                            v_lines_segments[x].append((y0, y1))

            # 过滤：只保留总长度 > 300pt 的垂直线（表格相关的长线）
            # 这样可以过滤掉短装饰线条，同时保留有效的列边界
            table_v_lines = []

            for x, segments in v_lines_segments.items():
                # 计算总长度
                total_length = sum(y1 - y0 for y0, y1 in segments)

                # 保留条件：总长度 > 300pt
                # 这个阈值可以过滤掉大部分非表格线条，同时保留所有有效的列边界
                if total_length > 300:
                    table_v_lines.append(x)

            # 排序并缓存
            result = sorted(table_v_lines)
            self._page_vertical_lines_cache[page_num] = result

            if result:
                print(f"  [PyMuPDF列检测] 页{page_num+1}: 检测到 {len(result)} 条表格垂直线")
                print(f"    前10条: {[f'{x:.1f}' for x in result[:10]]}")

            return result

        except Exception as e:
            print(f"  [PyMuPDF列检测] 页{page_num+1}: 检测失败: {e}")
            return []

    def _detect_full_horizontal_lines_pymupdf(self, pymupdf_page, page_num: int) -> List[float]:
        """
        使用 PyMuPDF 的 get_drawings() 检测页面中的所有水平线（过滤表格区域）

        ## 核心逻辑

        与垂直线检测类似，但判断条件相反：
        - **'l' 类型**：|p1.y - p2.y| < 2（水平线）
        - **'re' 类型**：height < 2 且 width > 10（水平细矩形）
        
        **过滤条件**：总长度 > 200pt
        - 比垂直线阈值低（300pt），因为单行可能较短
        - 例如：表格最后一行可能只有200pt宽

        ## 用途

        配合垂直线使用 **S1策略（explicit V+H）** 强制形成完整网格：
        ```python
        # 页面6重提取示例
        vertical_lines = [33.6, 99.0, 231.1, 429.1, 495.1, 561.1]  # 6条
        horizontal_lines = [394.3, 548.5]  # 2条
        
        # pdfplumber会在交点处形成单元格网格
        # 网格 = (6-1) x (2-1) = 5列 x 1行
        ```

        ## 成功案例

        **页面6-8左侧列修复**：
        - 原始pdfplumber检测：bbox从99.0开始（缺失左侧列）
        - PyMuPDF检测：发现完整的6条垂直线 + 2-4条水平线
        - S1策略重提取：成功从33.6开始（完整5列）

        Args:
            pymupdf_page: PyMuPDF 页面对象
            page_num: 页码（用于日志）

        Returns:
            排序后的水平线y坐标列表（总长度>200pt的线）
            
        Example:
            >>> h_lines = self._detect_full_horizontal_lines_pymupdf(page, 6)
            >>> print(h_lines)
            [28.8, 394.3, 548.5, 702.8]
            # 4条线，crop后使用[394.3, 548.5]（2条）
        """
        # 收集水平线段信息：{y: [(x0, x1), ...]}
        h_lines_segments = {}

        try:
            # 获取所有绘图对象
            drawings = pymupdf_page.get_drawings()

            for drawing in drawings:
                for item in drawing['items']:
                    # 'l' 表示线段
                    if item[0] == 'l':
                        p1, p2 = item[1], item[2]

                        # 判断是否为水平线（允许2个单位的误差）
                        if abs(p1.y - p2.y) < 2:
                            y = round(p1.y, 1)  # 四舍五入到0.1
                            x0, x1 = min(p1.x, p2.x), max(p1.x, p2.x)

                            if y not in h_lines_segments:
                                h_lines_segments[y] = []
                            h_lines_segments[y].append((x0, x1))

                    # 're' 表示矩形（PDF可能使用细矩形绘制线条）
                    elif item[0] == 're':
                        rect = item[1]  # fitz.Rect对象

                        # 判断是否为水平线（高度很小的细矩形）
                        width = abs(rect.x1 - rect.x0)
                        height = abs(rect.y1 - rect.y0)

                        # 如果高度 < 2pt 且宽度 > 10pt，认为是水平线
                        if height < 2 and width > 10:
                            y = round((rect.y0 + rect.y1) / 2, 1)  # 取中点
                            x0, x1 = min(rect.x0, rect.x1), max(rect.x0, rect.x1)

                            if y not in h_lines_segments:
                                h_lines_segments[y] = []
                            h_lines_segments[y].append((x0, x1))

            # 过滤：只保留总长度 > 200pt 的水平线（表格相关的长线）
            # 水平线阈值比垂直线低,因为单行可能较短
            table_h_lines = []

            for y, segments in h_lines_segments.items():
                # 计算总长度
                total_length = sum(x1 - x0 for x0, x1 in segments)

                # 保留条件：总长度 > 200pt
                if total_length > 200:
                    table_h_lines.append(y)

            # 排序
            result = sorted(table_h_lines)

            if result:
                print(f"  [PyMuPDF行检测] 页{page_num+1}: 检测到 {len(result)} 条表格水平线")
                print(f"    前10条: {[f'{y:.1f}' for y in result[:10]]}")

            return result

        except Exception as e:
            print(f"  [PyMuPDF行检测] 页{page_num+1}: 检测失败: {e}")
            return []

    def _merge_vertical_lines_with_prev_table(
        self,
        pymupdf_v_lines: List[float],
        prev_table_v_lines: List[float],
        tolerance: float = 5.0
    ) -> List[float]:
        """
        合并当前页的垂直线和前一页表格的列边界

        如果当前页缺失某些列边界（如左侧第一列），从前一页补充

        Args:
            pymupdf_v_lines: 当前页 PyMuPDF 检测的垂直线
            prev_table_v_lines: 前一页表格的列边界
            tolerance: 判断两条线是否为同一条的容差

        Returns:
            合并后的垂直线列表
        """
        if not prev_table_v_lines:
            return pymupdf_v_lines

        # 找出前一页有但当前页缺失的列边界
        missing_lines = []
        for prev_x in prev_table_v_lines:
            # 检查是否在当前页的垂直线中存在
            found = any(abs(prev_x - curr_x) < tolerance for curr_x in pymupdf_v_lines)
            if not found:
                missing_lines.append(prev_x)
                print(f"    [列边界补充] 从前页补充缺失的列边界: x={prev_x:.1f}")

        # 合并并排序
        all_lines = sorted(list(set(pymupdf_v_lines + missing_lines)))
        return all_lines

    # ==================== TEXT-FALLBACK 辅助方法 ====================

    def _min_cell_x0(self, bbox_data: List[List[tuple]]) -> float:
        """获取表内所有已识别单元格的最小 x0；若无则返回 +inf"""
        import math
        m = math.inf
        for row in bbox_data or []:
            for bb in row or []:
                if bb:
                    m = min(m, bb[0])
        return m

    def _left_gap_pt(self, bbox_data: List[List[tuple]], table_bbox: list) -> float:
        """计算表左边界到最靠左单元格之间的缺口宽度（pt）"""
        if not table_bbox:
            return 0.0
        from math import isfinite
        min_x0 = self._min_cell_x0(bbox_data)
        if not isfinite(min_x0):
            return 0.0
        return max(0.0, min_x0 - table_bbox[0])

    def _iou(self, a: list, b: list) -> float:
        """两个 bbox 的 IoU（同页同坐标系）"""
        ax0, ay0, ax1, ay1 = a
        bx0, by0, bx1, by1 = b
        ix0, iy0 = max(ax0, bx0), max(ay0, by0)
        ix1, iy1 = min(ax1, bx1), min(ay1, by1)
        iw, ih = max(0, ix1 - ix0), max(0, iy1 - iy0)
        inter = iw * ih
        area_a = max(0, ax1 - ax0) * max(0, ay1 - ay0)
        area_b = max(0, bx1 - bx0) * max(0, by1 - by0)
        union = area_a + area_b - inter if (area_a + area_b - inter) > 0 else 1.0
        return inter / union

    def _reextract_with_text_strategy(
        self,
        pdf_page,           # pdfplumber page
        pymupdf_page,       # fitz page
        orig_bbox: list,
    ) -> Dict[str, Any]:
        """
        在同一页用 vertical_strategy='text' 重提取，并选 IoU 最大的表替换。
        成功则返回 structured_table；失败返回 {}。
        """
        # 1) 用 text 策略在整页找表
        text_settings = {
            "vertical_strategy": "text",
            "horizontal_strategy": "lines",   # 优先保留横线对齐
            "text_x_tolerance": 3,
            "intersection_x_tolerance": 3,
            "intersection_y_tolerance": 3,
        }
        cand_tables = pdf_page.find_tables(table_settings=text_settings)
        if not cand_tables:
            print("  [TEXT-FALLBACK] text 策略未检出任何表，放弃")
            return {}

        # 2) 选择 IoU 最大且与原 bbox 有明显重叠的那张
        best = None
        best_iou = 0.0
        for t in cand_tables:
            iou = self._iou(list(t.bbox), orig_bbox)
            if iou > best_iou:
                best, best_iou = t, iou

        if not best or best_iou < 0.25:  # IoU 过小，避免误替换
            print(f"  [TEXT-FALLBACK] 没有找到与原表 IoU 足够高的候选 (best_iou={best_iou:.2f})")
            return {}

        print(f"  [TEXT-FALLBACK] 命中候选，bbox={best.bbox}，IoU={best_iou:.2f} → 重建结构")

        # 3) 按原逻辑将 best 转成 structured_table（尽量复用你现有流程）
        pdfplumber_data = best.extract()
        cells = best.cells
        if not pdfplumber_data:
            return {}

        # 3.1 建 index 映射
        y_coords = sorted(set([c[1] for c in cells] + [c[3] for c in cells]))
        x_coords = sorted(set([c[0] for c in cells] + [c[2] for c in cells]))

        table_data, bbox_data = [], []
        for row_idx, row in enumerate(pdfplumber_data):
            new_row, bbox_row = [], []
            for col_idx in range(len(row)):
                cell_text, cell_bbox_found = "", None
                for cell_bbox in cells:
                    x0, y0, x1, y1 = cell_bbox
                    cell_row = self._find_index(y0, y_coords)
                    cell_col = self._find_index(x0, x_coords)
                    if cell_row == row_idx and cell_col == col_idx:
                        cell_text = self.extract_cell_text(pymupdf_page, cell_bbox)
                        cell_bbox_found = cell_bbox
                        break
                new_row.append(cell_text if cell_text else "")
                bbox_row.append(cell_bbox_found)
            table_data.append(new_row)
            bbox_data.append(bbox_row)

        # 3.2 嵌套表处理（与主流程一致）
        nested_map = self.nested_handler.detect_and_extract_nested_tables(
            pdf_page, pymupdf_page, best, bbox_data
        )

        # 3.3 结构化（多/单层表头自适应）
        structured = self._build_structured_table(
            table_data=table_data,
            bbox_data=bbox_data,
            cells_bbox=cells,
            page_num=pdf_page.page_number,
            table_bbox=list(best.bbox),
            nested_map=nested_map,
            pymupdf_page=pymupdf_page
        )
        return structured or {}

    # ==================== END TEXT-FALLBACK 辅助方法 ====================

    def extract_tables(self, detect_header: bool = True) -> List[Dict[str, Any]]:
        """
        提取PDF中的所有表格（混合方法）
        - pdfplumber: 识别表格结构和单元格位置
        - PyMuPDF: 从单元格坐标提取文本内容（避免字符重复）

        ## 核心流程

        ### 1. 列边界检测（每页独立）
        - 使用 PyMuPDF.get_drawings() 检测页面中的垂直线
        - 过滤条件：总长度 > 300pt 的垂直线（过滤装饰线）
        - 支持线段('l')和矩形('re')两种类型

        ### 2. 列边界继承策略（2025-10-30 重构）
        **当前策略**: DisabledInheritanceStrategy（完全不继承前页列边界）
        
        **背景问题**：
        - 之前的逻辑：无条件继承前页列边界
        - 导致问题：页面5的10条线（9列）被继承到页面6-8，但实际只需6条线（5列）
        - 解决方案：提取为策略模式，默认禁用继承

        **策略模式设计**：
        - 位置：`crossPageTable/column_boundary_strategy.py`
        - 可选策略：
          * DisabledInheritanceStrategy（当前）：完全不继承
          * ConservativeInheritanceStrategy：只继承列数相似的页面
          * SmartInheritanceStrategy（待扩展）：基于bbox/内容智能判断
        
        **已知问题**：
        ⚠️ 禁用继承后，页面6-8列数正确（5列），但可能影响真正需要跨页表格的场景

        ### 3. 左侧列缺失检测与重提取（crop + explicit lines）
        **触发条件**：
        - detected_left（PyMuPDF检测的最左边界）< table_left（pdfplumber检测的最左边界）
        - 缺口 > 10pt

        **重提取策略**（三级fallback）：
        - S1（优先）：explicit vertical lines + explicit horizontal lines（完整网格）
        - S2（次选）：explicit vertical lines + 最小2条水平线（上下边界）
        - S3（保底）：explicit vertical lines + text horizontal strategy

        **成功案例**：
        - 页面6-8：检测到左侧缺失65.4pt，S1策略成功修复
        - 修复前：bbox从99.0开始（缺失左侧列）
        - 修复后：bbox从33.6开始（完整5列）

        ### 4. 诊断元数据
        重提取成功的表格会附加 `_diagnostic` 字段到raw.json：
        ```json
        {
          "reextraction_applied": true,
          "strategy_used": "S1 (explicit V+H)",
          "original_bbox": [99.0, 28.8, 561.1, 702.8],
          "new_bbox": [33.6, 394.3, 561.1, 548.5],
          "detected_v_lines_range": [33.6, 561.1],
          "detected_v_lines_count": 6,
          "detected_h_lines_count": 2,
          "left_gap_fixed": 65.4
        }
        ```

        ## 当前验证结果（2025-10-30）

        ### 测试文件：国土空间规划实施监测网络建设项目.pdf
        
        **页面5**：
        - 检测到8条垂直线（7列）
        - 原因：页面5本身有子列结构
        
        **页面6-8**（关闭继承后）：
        - 检测到6条垂直线（5列）✓
        - 不再继承页面5的额外列
        - S1策略成功修复左侧列缺失
        - 行数正常：页6=1行，页7=3行，页8=2行

        ## 待讨论问题

        1. **列数不一致**：
           - 页面5：7列（有子列）
           - 页面6-8：5列（主列）
           - 是否需要跨页合并？还是应该各自独立？

        2. **列继承策略选择**：
           - 当前：完全禁用继承（保守）
           - 是否需要ConservativeInheritanceStrategy（只继承列数相似的）？
           - 何时需要继承？判断条件是什么？

        3. **表头识别**：
           - 延迟表头识别（detect_header=False）配合跨页合并
           - 合并后统一识别表头
           - 是否存在表头被误识别为数据行的情况？

        Args:
            detect_header: 是否检测表头（默认True）。
                          False时使用延迟表头识别模式，适用于跨页合并场景。

        Returns:
            提取的表格列表，每个表格包含：
            - columns: 列定义
            - rows: 数据行
            - bbox: 表格边界框
            - _diagnostic (可选): 重提取诊断信息
        """
        tables_data = []

        # 打开PyMuPDF文档
        doc_pymupdf = fitz.open(self.pdf_path)

        print(f"\n[表格提取] 开始提取PDF: {self.pdf_path.name}")

        # 用于跨页表格的列边界传递
        prev_page_vertical_lines = None
        prev_page_table_x_coords = None  # 上一页表格的实际列边界

        with pdfplumber.open(self.pdf_path) as pdf:
            print(f"[表格提取] PDF总页数: {len(pdf.pages)}")

            for page_num, page in enumerate(pdf.pages, start=1):
                # 获取PyMuPDF的对应页面
                pymupdf_page = doc_pymupdf[page_num - 1]

                # 使用PyMuPDF检测完整的垂直线边界
                pymupdf_v_lines = self._detect_full_vertical_lines_pymupdf(pymupdf_page, page_num - 1)

                # 使用列边界继承策略决定是否继承前页列边界
                # 默认策略：DisabledInheritanceStrategy（完全不继承）
                prev_lines = prev_page_vertical_lines or prev_page_table_x_coords
                
                if self.column_inheritance_strategy.should_inherit(
                    current_page_lines=pymupdf_v_lines,
                    prev_page_lines=prev_lines,
                    context={'page_num': page_num}
                ):
                    merged_v_lines = self.column_inheritance_strategy.merge_lines(
                        current_page_lines=pymupdf_v_lines,
                        prev_page_lines=prev_lines,
                        context={'page_num': page_num}
                    )
                    print(f"    [列继承策略] 应用策略: {type(self.column_inheritance_strategy).__name__}")
                else:
                    merged_v_lines = pymupdf_v_lines
                    print(f"    [列继承策略] 不继承前页列边界 (策略: {type(self.column_inheritance_strategy).__name__})")

                # 使用pdfplumber找到表格
                table_settings = {
                    "horizontal_strategy": "lines",
                    "intersection_x_tolerance": 3,
                    "intersection_y_tolerance": 3
                }

                # 如果检测到垂直线，使用explicit策略；否则使用lines策略
                if merged_v_lines and len(merged_v_lines) >= 2:
                    table_settings["vertical_strategy"] = "explicit"
                    table_settings["explicit_vertical_lines"] = merged_v_lines
                    print(f"  [列边界检测] 使用PyMuPDF检测到 {len(merged_v_lines)} 条垂直线")
                else:
                    table_settings["vertical_strategy"] = "lines"
                    print(f"  [列边界检测] 未检测到垂直线，使用lines策略")

                tables = page.find_tables(table_settings=table_settings)

                print(f"\n[表格提取] 页码 {page_num}: 检测到 {len(tables)} 个表格")

                # 记录当前页的列边界，用于下一页
                if merged_v_lines:
                    prev_page_vertical_lines = merged_v_lines

                # 不再回退到默认策略（text不准确）
                # if not tables:
                #     tables = page.find_tables()

                # ===== 新增：table_regions 重提取逻辑 =====
                # 检测pdfplumber是否遗漏了左侧或右侧的列（通过对比检测到的垂直线和表格bbox）
                # 如果发现缺失，使用 table_regions 参数强制在完整区域内重新提取
                tables_list = list(tables)  # 转换为列表以便替换

                for table_idx, table in enumerate(tables_list):
                    need_region_reextract = False
                    table_region = None

                    if merged_v_lines and len(merged_v_lines) >= 2:
                        # 获取检测到的垂直线范围
                        detected_left = min(merged_v_lines)
                        detected_right = max(merged_v_lines)

                        # 获取pdfplumber检测到的表格范围
                        table_left = table.bbox[0]
                        table_right = table.bbox[2]

                        # 判断是否缺失左侧列
                        left_gap = table_left - detected_left
                        if left_gap > 10:
                            print(f"  [表格 {table_idx + 1}] [列边界诊断] 检测到左侧缺失: detected_left={detected_left:.1f}, table_left={table_left:.1f}, gap={left_gap:.1f}pt")
                            need_region_reextract = True

                        # 判断是否缺失右侧列
                        right_gap = detected_right - table_right
                        if right_gap > 10:
                            print(f"  [表格 {table_idx + 1}] [列边界诊断] 检测到右侧缺失: detected_right={detected_right:.1f}, table_right={table_right:.1f}, gap={right_gap:.1f}pt")
                            need_region_reextract = True

                        # 如果需要重提取，使用显式垂直线 + 显式水平线策略（纯几何路线）
                        if need_region_reextract:
                            # 构建完整的表格区域（使用检测到的垂直线范围 + 表格的垂直范围）
                            crop_region = (
                                detected_left,       # 使用检测到的最左边界
                                table.bbox[1],       # 保留表格的顶部边界
                                detected_right,      # 使用检测到的最右边界
                                table.bbox[3]        # 保留表格的底部边界
                            )

                            print(f"  [表格 {table_idx + 1}] [显式行列重提取] 使用区域: [{crop_region[0]:.1f}, {crop_region[1]:.1f}, {crop_region[2]:.1f}, {crop_region[3]:.1f}]")

                            # 检测水平线（在crop区域内）
                            pymupdf_h_lines = self._detect_full_horizontal_lines_pymupdf(pymupdf_page, page_num - 1)

                            # 过滤：只保留在crop区域内的水平线
                            crop_h_lines = [y for y in pymupdf_h_lines if crop_region[1] <= y <= crop_region[3]]

                            print(f"  [表格 {table_idx + 1}] [水平线检测] 区域内检测到 {len(crop_h_lines)} 条水平线")
                            if crop_h_lines:
                                print(f"    水平线y坐标: {[f'{y:.1f}' for y in crop_h_lines[:10]]}")

                            # 策略S1：显式垂直线 + 显式水平线（完整网格）
                            reextracted_table = None
                            strategy_used = None

                            if len(crop_h_lines) >= 2:
                                # S1: 完整网格策略
                                print(f"  [表格 {table_idx + 1}] [策略S1] 尝试：显式垂直线 ({len(merged_v_lines)}条) + 显式水平线 ({len(crop_h_lines)}条)")

                                try:
                                    cropped_page = page.crop(crop_region)
                                    reextracted_tables = cropped_page.find_tables(table_settings={
                                        'vertical_strategy': 'explicit',
                                        'explicit_vertical_lines': merged_v_lines,
                                        'horizontal_strategy': 'explicit',
                                        'explicit_horizontal_lines': crop_h_lines,
                                        'intersection_x_tolerance': 3,
                                        'intersection_y_tolerance': 3
                                    })

                                    if reextracted_tables and len(reextracted_tables) > 0:
                                        reextracted_table = reextracted_tables[0]
                                        strategy_used = "S1 (explicit V+H)"
                                        print(f"  [表格 {table_idx + 1}] [策略S1] 成功")
                                    else:
                                        print(f"  [表格 {table_idx + 1}] [策略S1] 未检测到表格")
                                except Exception as e:
                                    print(f"  [表格 {table_idx + 1}] [策略S1] 失败: {e}")

                            # 策略S2：显式垂直线 + 最小2条水平线（上下边界）
                            if not reextracted_table and len(crop_h_lines) >= 2:
                                print(f"  [表格 {table_idx + 1}] [策略S2] 尝试：显式垂直线 + 最小水平线（上下边界）")

                                # 只使用顶部和底部的水平线
                                minimal_h_lines = [min(crop_h_lines), max(crop_h_lines)]
                                print(f"    使用水平线: {[f'{y:.1f}' for y in minimal_h_lines]}")

                                try:
                                    cropped_page = page.crop(crop_region)
                                    reextracted_tables = cropped_page.find_tables(table_settings={
                                        'vertical_strategy': 'explicit',
                                        'explicit_vertical_lines': merged_v_lines,
                                        'horizontal_strategy': 'explicit',
                                        'explicit_horizontal_lines': minimal_h_lines,
                                        'intersection_x_tolerance': 3,
                                        'intersection_y_tolerance': 3
                                    })

                                    if reextracted_tables and len(reextracted_tables) > 0:
                                        reextracted_table = reextracted_tables[0]
                                        strategy_used = "S2 (explicit V + minimal H)"
                                        print(f"  [表格 {table_idx + 1}] [策略S2] 成功")
                                    else:
                                        print(f"  [表格 {table_idx + 1}] [策略S2] 未检测到表格")
                                except Exception as e:
                                    print(f"  [表格 {table_idx + 1}] [策略S2] 失败: {e}")

                            # 策略S3：显式垂直线 + text水平策略
                            if not reextracted_table:
                                print(f"  [表格 {table_idx + 1}] [策略S3] 尝试：显式垂直线 + text水平策略")

                                try:
                                    cropped_page = page.crop(crop_region)
                                    reextracted_tables = cropped_page.find_tables(table_settings={
                                        'vertical_strategy': 'explicit',
                                        'explicit_vertical_lines': merged_v_lines,
                                        'horizontal_strategy': 'text',
                                        'text_y_tolerance': 3,
                                        'intersection_x_tolerance': 3,
                                        'intersection_y_tolerance': 3
                                    })

                                    if reextracted_tables and len(reextracted_tables) > 0:
                                        reextracted_table = reextracted_tables[0]
                                        strategy_used = "S3 (explicit V + text H)"
                                        print(f"  [表格 {table_idx + 1}] [策略S3] OK 成功")
                                    else:
                                        print(f"  [表格 {table_idx + 1}] [策略S3] ERROR 未检测到表格")
                                except Exception as e:
                                    print(f"  [表格 {table_idx + 1}] [策略S3] ERROR 失败: {e}")

                            # 检查重提取结果
                            if reextracted_table:
                                new_bbox = list(reextracted_table.bbox)
                                new_left = new_bbox[0]
                                new_right = new_bbox[2]

                                print(f"  [表格 {table_idx + 1}] [重提取结果] 策略: {strategy_used}")
                                print(f"  [表格 {table_idx + 1}] [重提取结果] 新bbox: [{new_bbox[0]:.1f}, {new_bbox[1]:.1f}, {new_bbox[2]:.1f}, {new_bbox[3]:.1f}]")

                                # 检查重提取是否改善了问题
                                improved = False
                                if left_gap > 10 and abs(new_left - detected_left) < 5:
                                    print(f"  [表格 {table_idx + 1}] [重提取结果] OK 修复了左侧缺失 (new_left={new_left:.1f})")
                                    improved = True
                                if right_gap > 10 and abs(new_right - detected_right) < 5:
                                    print(f"  [表格 {table_idx + 1}] [重提取结果] OK 修复了右侧缺失 (new_right={new_right:.1f})")
                                    improved = True

                                if improved:
                                    # 准备诊断元数据（稍后传递给 _build_structured_table）
                                    diagnostic_info = {
                                        'reextraction_applied': True,
                                        'strategy_used': strategy_used,
                                        'original_bbox': list(table.bbox),
                                        'new_bbox': new_bbox,
                                        'detected_v_lines_range': [detected_left, detected_right],
                                        'detected_v_lines_count': len(merged_v_lines),
                                        'detected_h_lines_count': len(crop_h_lines),
                                        'left_gap_fixed': left_gap if left_gap > 10 else 0,
                                        'right_gap_fixed': right_gap if right_gap > 10 else 0
                                    }

                                    # 将诊断信息附加到表格对象（使用自定义属性）
                                    reextracted_table._diagnostic = diagnostic_info

                                    # 替换原表格
                                    tables_list[table_idx] = reextracted_table
                                    print(f"  [表格 {table_idx + 1}] [重提取结果] OK 采用重提取结果")
                                else:
                                    print(f"  [表格 {table_idx + 1}] [重提取结果] ERROR 未改善，保留原结果")
                            else:
                                print(f"  [表格 {table_idx + 1}] [重提取结果] ERROR 所有策略均失败，保留原结果")

                # 使用可能已更新的表格列表
                tables = tables_list
                # ===== table_regions 重提取逻辑结束 =====

                for table_idx, table in enumerate(tables):
                    print(f"  [表格 {table_idx + 1}] bbox: {table.bbox}")

                    # 先用pdfplumber提取表格结构（用于获取行列结构）
                    pdfplumber_data = table.extract()

                    if not pdfplumber_data:
                        print(f"  [表格 {table_idx + 1}] 跳过: pdfplumber_data为空")
                        continue

                    print(f"  [表格 {table_idx + 1}] 提取到 {len(pdfplumber_data)} 行数据")

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
                            pymupdf_page=pymupdf_page,
                            detect_header=detect_header
                        )

                        # 如果table对象有诊断信息（来自crop reextraction），添加到structured_table
                        if hasattr(table, '_diagnostic'):
                            structured_table['_diagnostic'] = table._diagnostic
                            print(f"  [表格 {table_idx + 1}] [诊断信息] 已添加到structured_table")

                        # [TEXT-FALLBACK] 触发条件：左侧缺口很大 或 列索引不从0开始 或 bbox异常偏右
                        try:
                            left_gap = self._left_gap_pt(bbox_data, list(table.bbox))
                        except Exception:
                            left_gap = 0.0

                        # 检查第一列的index
                        first_col_index = structured_table.get("columns", [{}])[0].get("index", 0) if structured_table.get("columns") else 0
                        row_levels = (structured_table.get("header_info", {}) or {}).get("row_levels", 1)

                        # 检查原始table.bbox的x0是否异常偏右（说明pdfplumber漏检了左侧列）
                        orig_bbox_x0 = list(table.bbox)[0]
                        bbox_suspicious = orig_bbox_x0 > 70.0  # 正常页边距通常 < 50pt

                        # 触发条件：
                        # 1. left_gap >= 40pt
                        # 2. first_col_index > 0 (列缺失)
                        # 3. row_levels >= 2 且 left_gap >= 25pt
                        # 4. bbox的x0 > 70pt (pdfplumber原始检测就漏了左侧列)
                        need_fallback = (left_gap >= 40.0) or (first_col_index > 0) or (row_levels >= 2 and left_gap >= 25.0) or bbox_suspicious

                        if need_fallback:
                            print(f"  [TEXT-FALLBACK] 触发：left_gap={left_gap:.1f}pt, first_col_index={first_col_index}, row_levels={row_levels}, bbox_x0={orig_bbox_x0:.1f}")
                            # 注意：text策略可能检测不到目标表格（尤其是多层表头+空列的情况）
                            # 所以如果text失败，我们保留原结果
                            re_struct = self._reextract_with_text_strategy(page, pymupdf_page, list(table.bbox))
                            if re_struct:
                                # 如果重提取得到的左侧缺口更小或列更多，则采用重提取结果
                                try:
                                    re_bbox_data = [[c.get("bbox") for c in r.get("cells", [])] for r in re_struct.get("rows", [])]
                                    re_left_gap = self._left_gap_pt(re_bbox_data, re_struct.get("bbox", list(table.bbox)))
                                except Exception:
                                    re_left_gap = left_gap

                                orig_cols = len(structured_table.get("columns", []))
                                new_cols  = len(re_struct.get("columns", []))

                                better = (re_left_gap + 1e-6 < left_gap - 5.0) or (new_cols > orig_cols)

                                print(f"  [TEXT-FALLBACK] 对比：orig_gap={left_gap:.1f}, new_gap={re_left_gap:.1f}, "
                                      f"orig_cols={orig_cols}, new_cols={new_cols} → 采用{'新结果' if better else '原结果'}")

                                if better:
                                    structured_table = re_struct

                        tables_data.append(structured_table)
                        print(f"  [表格 {table_idx + 1}] [OK] 成功添加到结果列表")

                        # 记录当前表格的列边界（x_coords），用于下一页
                        if x_coords:
                            prev_page_table_x_coords = x_coords
                            print(f"    [列边界记录] 保存当前表格的 {len(x_coords)} 条列边界用于下一页")
                    else:
                        print(f"  [表格 {table_idx + 1}] 跳过: table_data为空")

        doc_pymupdf.close()
        print(f"\n[表格提取] 完成，共提取 {len(tables_data)} 个表格\n")
        return tables_data

    def reextract_with_hints(self,
                            hints_by_page: Dict[int, Dict],
                            original_tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        使用续页hint重新提取指定页面的表格（显式列边界）

        原理：
        - 对命中hint的页面，使用上一页的列边界（col_xs）强制切分
        - 使用 vertical_strategy='explicit' 避免pdfplumber漏检列

        Args:
            hints_by_page: {page_num: {"col_xs": [...], "bbox": [...], "score": ...}}
            original_tables: 第一轮提取的原始表格列表

        Returns:
            更新后的表格列表（替换了重新提取的表格）
        """
        if not hints_by_page:
            return original_tables

        print(f"\n[表格重提取] 开始对 {len(hints_by_page)} 个页面使用显式列边界重提取")

        # 按页分组原始表格
        tables_by_page = {}
        for table in original_tables:
            page = table.get('page', 1)
            if page not in tables_by_page:
                tables_by_page[page] = []
            tables_by_page[page].append(table)

        # 打开PDF
        doc_pymupdf = fitz.open(self.pdf_path)

        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, hint in hints_by_page.items():
                print(f"\n[页{page_num}] 使用hint重新提取")
                print(f"  来源: 页{hint['source_page']}表{hint['source_table_id']}")
                print(f"  评分: {hint['score']:.2f}")
                print(f"  列边界: {[f'{x:.1f}' for x in hint['col_xs'][:5]]}...")

                # 获取页面
                page = pdf.pages[page_num - 1]
                pymupdf_page = doc_pymupdf[page_num - 1]
                page_height = pymupdf_page.rect.height

                # 使用显式列边界重新查找表格
                col_xs = hint['col_xs']

                # 使用pdfplumber的显式列策略
                table_settings = {
                    "vertical_strategy": "explicit",
                    "explicit_vertical_lines": col_xs,
                    "horizontal_strategy": "lines",  # 使用lines而非lines_strict，更宽松
                    "intersection_x_tolerance": 3,
                    "intersection_y_tolerance": 3
                }

                print(f"  使用设置: {table_settings}")

                # 重新查找表格
                new_tables = page.find_tables(table_settings=table_settings)

                print(f"  重新检测到 {len(new_tables)} 个表格")

                if not new_tables:
                    print(f"  警告: 重提取失败，保留原表格")
                    continue

                # 重新提取表格数据（使用与 extract_tables 相同的逻辑）
                reextracted_tables = []
                for table_idx, table in enumerate(new_tables):
                    table_bbox = list(table.bbox)
                    pdfplumber_data = table.extract()
                    cells = table.cells

                    print(f"  [表格 {table_idx + 1}] bbox: {[f'{x:.1f}' for x in table_bbox]}")
                    print(f"  [表格 {table_idx + 1}] 行数: {len(pdfplumber_data)}")

                    # 构建单元格坐标映射（与extract_tables相同）
                    y_coords = sorted(set([cell[1] for cell in cells] + [cell[3] for cell in cells]))
                    x_coords = sorted(set([cell[0] for cell in cells] + [cell[2] for cell in cells]))

                    # 使用PyMuPDF提取文本（与extract_tables相同）
                    table_data = []
                    bbox_data = []

                    for row_idx, row in enumerate(pdfplumber_data):
                        new_row = []
                        bbox_row = []
                        for col_idx in range(len(row)):
                            cell_text = ""
                            cell_bbox_found = None
                            for cell_bbox in cells:
                                x0, y0, x1, y1 = cell_bbox
                                cell_row = self._find_index(y0, y_coords)
                                cell_col = self._find_index(x0, x_coords)

                                if cell_row == row_idx and cell_col == col_idx:
                                    cell_text = self.extract_cell_text(pymupdf_page, cell_bbox)
                                    cell_bbox_found = cell_bbox
                                    break

                            new_row.append(cell_text if cell_text else "")
                            bbox_row.append(cell_bbox_found)
                        table_data.append(new_row)
                        bbox_data.append(bbox_row)

                    # 检测嵌套表格
                    nested_map = self.nested_handler.detect_and_extract_nested_tables(
                        page, pymupdf_page, table, bbox_data
                    )

                    # 构建结构化表格
                    if table_data:
                        structured_table = self._build_structured_table(
                            table_data=table_data,
                            bbox_data=bbox_data,
                            cells_bbox=cells,
                            page_num=page_num,
                            table_bbox=table_bbox,
                            nested_map=nested_map,
                            pymupdf_page=pymupdf_page
                        )

                        if structured_table:
                            reextracted_tables.append(structured_table)
                            print(f"  [表格 {table_idx + 1}] [OK] 重提取成功")

                # 替换原表格
                if reextracted_tables:
                    # 找到这一页最顶部的表格（min y0）
                    original_top_table = min(tables_by_page.get(page_num, []),
                                            key=lambda t: t.get('bbox', [0,0,0,0])[1],
                                            default=None)

                    if original_top_table and len(reextracted_tables) > 0:
                        # 用重提取的第一个表格替换原表格
                        reextracted_table = reextracted_tables[0]

                        # 保留原表格的ID（用于合并链）
                        original_id = original_top_table.get('id')
                        reextracted_table['id'] = original_id

                        # 替换
                        for i, table in enumerate(original_tables):
                            if table.get('id') == original_id:
                                original_tables[i] = reextracted_table
                                print(f"  [OK] 替换表格 {original_id}")
                                print(f"       原行数: {len(original_top_table.get('rows', []))}")
                                print(f"       新行数: {len(reextracted_table.get('rows', []))}")
                                break

        doc_pymupdf.close()
        print(f"\n[表格重提取] 完成\n")
        return original_tables

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
        hint_row_levels: int = None,
        detect_header: bool = True
    ) -> Dict[str, Any]:
        """
        构建结构化表格数据（支持多层表头 + 延迟表头识别）

        ## 多层表头支持

        ### 输入数据
        - table_data: 原始表格文本数据（二维数组）
        - cells_bbox: pdfplumber的cells列表，包含每个单元格的bbox和合并信息
        - hint_col_levels/hint_row_levels: 可选的手动指定表头层数
        - detect_header: 是否检测表头（默认True）。False时所有行作为数据行，适用于跨页合并场景

        ### 处理流程
        1. **如果 detect_header=False（延迟表头识别模式）**：
           - 跳过表头分析，所有行都作为数据行（rows）
           - columns 为简单占位符（c001, c002, ...）
           - 保留完整的 bbox 信息
           - 适用场景：第一轮提取时，延迟到跨页合并后再分析表头

        2. **如果 detect_header=True（立即表头识别模式）**：
           - 尝试多层表头分析：调用 HeaderAnalyzer.analyze_table_headers()
             * 成功：返回 HeaderModel（包含 col_paths/row_paths）
             * 失败：返回 None，回退到单层表头

        3. **多层表头模式** (_build_table_with_multi_level_headers)：
           - 使用 HeaderModel.col_paths 构建每个数据列的路径
           - 使用 HeaderModel.row_paths 构建每个数据行的路径
           - 跳过表头区域（前col_levels行 + 前row_levels列）
           - 数据单元格的 cellPath 和 rowPath 都是多层列表

        4. **单层表头模式** (_build_table_with_single_level_headers)：
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

        # ===== 延迟表头识别模式 =====
        if not detect_header:
            # 不进行表头分析，所有行都作为数据行
            # columns 为简单占位符，保留完整 bbox
            return self._build_table_without_header_detection(
                table_data=table_data,
                bbox_data=bbox_data,
                page_num=page_num,
                table_bbox=table_bbox,
                nested_map=nested_map,
                pymupdf_page=pymupdf_page
            )

        # ===== 立即表头识别模式（原逻辑）=====

        # 检测单元格的跨列/跨行信息
        span_annotation = self.span_detector.annotate_table_cells(bbox_data, cells_bbox)
        col_x_edges = span_annotation['col_x_edges']
        row_y_edges = span_annotation['row_y_edges']
        cell_spans = span_annotation['cell_spans']

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

            # 调试：打印表头分析结果（已禁用，避免编码问题）
            # if header_model:
            #     print(f"\n[DEBUG] 表头分析结果 - 页码 {page_num}")
            #     print(f"  col_levels: {header_model.col_levels}, row_levels: {header_model.row_levels}")
        except Exception as e:
            print(f"[INFO] 表头分析失败，使用单层表头: {e}")
            import traceback
            traceback.print_exc()

        # 获取页面高度（用于bbox验证）
        page_height = pymupdf_page.rect.height if pymupdf_page else 842.0

        # TODO: 多层表头分析在某些情况下会导致列缺失问题
        # 问题场景：前2行有大量跨列合并单元格（如"评审标准"横跨多列），
        # 导致误认为只有从第N列开始的列（first_col_index > 0），丢失左侧列
        #
        # 临时解决方案：先尝试多层表头分析，如果发现first_col_index > 0，
        # 则回退到单层表头处理，避免列丢失
        #
        # 长期方案：改进HeaderAnalyzer，正确处理跨列合并的表头
        # 参考文件：app/utils/unTaggedPDF/header_analyzer.py

        # 如果表头分析成功，使用多层路径
        if header_model:
            multi_level_result = self._build_table_with_multi_level_headers(
                table_data=table_data,
                bbox_data=bbox_data,
                page_num=page_num,
                table_bbox=table_bbox,
                nested_map=nested_map,
                header_model=header_model,
                page_height=page_height,
                cells_bbox_orig=cells_bbox,  # 传递原始pdfplumber cells用于bbox修正
                col_x_edges=col_x_edges,  # 列边界坐标
                row_y_edges=row_y_edges,  # 行边界坐标
                cell_spans=cell_spans  # 单元格跨度信息
            )

            # 检查是否存在列缺失问题（columns为空 或 first_col_index > 0）
            columns = multi_level_result.get("columns", [])

            # 检查1：columns为空
            if not columns:
                print(f"  [WARNING] 多层表头分析导致所有列丢失 (columns为空)，回退到单层表头处理")
                return self._build_table_with_single_level_headers(
                    table_data=table_data,
                    bbox_data=bbox_data,
                    page_num=page_num,
                    table_bbox=table_bbox,
                    nested_map=nested_map,
                    page_height=page_height,
                    cells_bbox_orig=cells_bbox  # 传递原始pdfplumber cells用于bbox修正
                )

            # 检查2：first_col_index > 0（说明丢失了左侧列）
            first_col_index = columns[0].get("index", 0) if columns else 0
            if first_col_index > 0:
                print(f"  [WARNING] 多层表头分析导致列缺失 (first_col_index={first_col_index})，回退到单层表头处理")
                # 回退到单层表头
                return self._build_table_with_single_level_headers(
                    table_data=table_data,
                    bbox_data=bbox_data,
                    page_num=page_num,
                    table_bbox=table_bbox,
                    nested_map=nested_map,
                    page_height=page_height,
                    cells_bbox_orig=cells_bbox  # 传递原始pdfplumber cells用于bbox修正
                )

            return multi_level_result
        else:
            # 回退到单层表头逻辑
            return self._build_table_with_single_level_headers(
                table_data=table_data,
                bbox_data=bbox_data,
                page_num=page_num,
                table_bbox=table_bbox,
                nested_map=nested_map,
                page_height=page_height,
                cells_bbox_orig=cells_bbox  # 传递原始pdfplumber cells用于bbox修正
            )

    def _build_table_with_multi_level_headers(
        self,
        table_data: List[List[str]],
        bbox_data: List[List[tuple]],
        page_num: int,
        table_bbox: list,
        nested_map: Dict[tuple, List[Dict]],
        header_model,
        page_height: float,
        cells_bbox_orig: list = None,
        col_x_edges: List[float] = None,
        row_y_edges: List[float] = None,
        cell_spans: List[List[Dict]] = None
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
            page_height: 页面高度
            cells_bbox_orig: pdfplumber原始cells（用于bbox修正）
            col_x_edges: 列边界坐标
            row_y_edges: 行边界坐标
            cell_spans: 单元格跨度信息

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

                # 添加span信息（如果可用）
                if cell_spans and actual_row_idx < len(cell_spans) and actual_col_idx < len(cell_spans[actual_row_idx]):
                    span_info = cell_spans[actual_row_idx][actual_col_idx]
                    if span_info:
                        cell_obj['start_col'] = span_info.get('start_col')
                        cell_obj['end_col'] = span_info.get('end_col')
                        cell_obj['colspan'] = span_info.get('colspan', 1)
                        cell_obj['start_row'] = span_info.get('start_row')
                        cell_obj['end_row'] = span_info.get('end_row')
                        cell_obj['rowspan'] = span_info.get('rowspan', 1)

                # 只有识别到嵌套表格时才添加 nested_tables 字段
                if nested_here:
                    cell_obj["nested_tables"] = nested_here

                cells.append(cell_obj)

            rows.append({
                "id": row_id,
                "rowPath": row_path,  # 多层行路径
                "cells": cells
            })

        # 3. 验证并修正table bbox
        # 优先使用pdfplumber原始cells（避免多层表头分析导致的列缺失影响bbox计算）
        # 如果没有原始cells，则使用processed cells作为fallback
        cells_for_validation = cells_bbox_orig if cells_bbox_orig is not None else []
        if not cells_for_validation:
            # Fallback: 收集processed cells
            for row in rows:
                cells_for_validation.extend(row['cells'])

        validated_bbox = validate_and_fix_bbox(table_bbox, cells_for_validation, page_height)

        result = {
            "type": "table",
            "level": 1,
            "parent_table_id": None,
            "page": page_num,
            "bbox": validated_bbox,
            "columns": columns,
            "rows": rows,
            "header_info": {
                "col_levels": col_levels,
                "row_levels": row_levels,
                "multi_level": True
            },
            "method": "hybrid (pdfplumber cells + pymupdf text + multi-level headers)"
        }

        # 添加列边界和行边界（如果可用）
        if col_x_edges:
            result['col_x_edges'] = [round(x, 2) for x in col_x_edges]
        if row_y_edges:
            result['row_y_edges'] = [round(y, 2) for y in row_y_edges]

        return result

    def _build_table_with_single_level_headers(
        self,
        table_data: List[List[str]],
        bbox_data: List[List[tuple]],
        page_num: int,
        table_bbox: list,
        nested_map: Dict[tuple, List[Dict]],
        page_height: float,
        cells_bbox_orig: list = None
    ) -> Dict[str, Any]:
        """
        使用单层表头构建表格（回退逻辑）

        Args:
            table_data: 表格数据
            bbox_data: bbox数据
            page_num: 页码
            table_bbox: 表格bbox
            nested_map: 嵌套表格映射
            page_height: 页面高度
            cells_bbox_orig: pdfplumber原始cells（用于bbox修正）

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

        # 4. 验证并修正table bbox
        # 优先使用pdfplumber原始cells（避免列缺失影响bbox计算）
        # 如果没有原始cells，则使用processed cells作为fallback
        cells_for_validation = cells_bbox_orig if cells_bbox_orig is not None else []
        if not cells_for_validation:
            # Fallback: 收集processed cells
            for row in rows:
                cells_for_validation.extend(row['cells'])

        validated_bbox = validate_and_fix_bbox(table_bbox, cells_for_validation, page_height)

        return {
            "type": "table",
            "level": 1,
            "parent_table_id": None,
            "page": page_num,
            "bbox": validated_bbox,
            "columns": columns,
            "rows": rows,
            "header_info": {
                "col_levels": 1,
                "row_levels": 1,
                "multi_level": False
            },
            "method": "hybrid (pdfplumber cells + pymupdf text)"
        }

    def _build_table_without_header_detection(
        self,
        table_data: List[List[str]],
        bbox_data: List[List[tuple]],
        page_num: int,
        table_bbox: list,
        nested_map: Dict[tuple, List[Dict]],
        pymupdf_page = None
    ) -> Dict[str, Any]:
        """
        延迟表头识别模式：构建表格但不进行表头分析

        所有行都作为数据行（rows），列定义为简单占位符（c001, c002, ...）。
        保留完整的bbox信息，延迟到跨页合并后再分析表头。

        Args:
            table_data: 表格数据
            bbox_data: bbox数据
            page_num: 页码
            table_bbox: 表格bbox
            nested_map: 嵌套表格映射
            pymupdf_page: PyMuPDF页面对象（用于获取页面高度）

        Returns:
            结构化表格字典（所有行都是数据行，无表头分析）
        """
        if not table_data:
            return {}

        # 获取列数（从第一行推断）
        num_cols = len(table_data[0]) if table_data else 0

        # 1. 构建列定义（简单占位符，无实际表头名称）
        columns = []
        for col_idx in range(num_cols):
            columns.append({
                "id": f"c{col_idx + 1:03d}",
                "index": col_idx,
                "name": ""  # 延迟表头识别，名称留空
            })

        # 2. 构建行数据（所有行都是数据行，从第1行开始编号）
        rows = []
        for row_idx, row_data in enumerate(table_data, start=1):
            row_id = f"r{row_idx:03d}"
            row_first_cell = row_data[0] if row_data else ""

            cells = []
            for col_idx, cell_content in enumerate(row_data):
                col_id = f"c{col_idx + 1:03d}"

                # 获取单元格的bbox坐标
                bbox_row_idx = row_idx - 1  # table_data是0-based, row_idx是1-based
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
                    "cellPath": [col_id],  # 使用col_id作为占位符
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

        # 3. 验证并修正table bbox
        page_height = pymupdf_page.rect.height if pymupdf_page else 842.0
        cells_for_validation = []
        for row in rows:
            cells_for_validation.extend(row['cells'])

        validated_bbox = validate_and_fix_bbox(table_bbox, cells_for_validation, page_height)

        return {
            "type": "table",
            "level": 1,
            "parent_table_id": None,
            "page": page_num,
            "bbox": validated_bbox,
            "columns": columns,
            "rows": rows,
            "header_info": {
                "col_levels": 0,  # 0表示未识别表头
                "row_levels": 0,
                "multi_level": False,
                "header_detected": False  # 标记表头未识别
            },
            "method": "no_header_detection (delayed)"
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