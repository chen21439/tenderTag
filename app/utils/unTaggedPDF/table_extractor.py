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

        print(f"\n[表格提取] 开始提取PDF: {self.pdf_path.name}")

        with pdfplumber.open(self.pdf_path) as pdf:
            print(f"[表格提取] PDF总页数: {len(pdf.pages)}")

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

                print(f"\n[表格提取] 页码 {page_num}: 检测到 {len(tables)} 个表格")

                # 不再回退到默认策略（text不准确）
                # if not tables:
                #     tables = page.find_tables()

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
                            pymupdf_page=pymupdf_page
                        )

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
                    "horizontal_strategy": "lines_strict",  # 或 "text"
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
                cells_bbox_orig=cells_bbox  # 传递原始pdfplumber cells用于bbox修正
            )

            # 检查是否存在列缺失问题（first_col_index > 0）
            first_col_index = multi_level_result.get("columns", [{}])[0].get("index", 0) if multi_level_result.get("columns") else 0

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
        cells_bbox_orig: list = None
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

        # 3. 验证并修正table bbox
        # 优先使用pdfplumber原始cells（避免多层表头分析导致的列缺失影响bbox计算）
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