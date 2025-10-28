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


def validate_and_fix_bbox(table_bbox: list, cells: List[Dict], page_height: float, mode: str = "full") -> list:
    """
    验证并修正表格bbox

    当pdfplumber提供的bbox无效时（负坐标、超出页面），从cells重新计算bbox

    Args:
        table_bbox: pdfplumber提供的原始bbox [x0, y0, x1, y1]
        cells: 所有单元格列表，每个cell有'bbox'字段
        page_height: 页面高度（用于验证）
        mode: 修正模式
            - "full": 完全重算（可能收缩）
            - "expand_only": 仅允许外扩，不收缩（用于保持结构完整性）

    Returns:
        修正后的bbox
    """
    x0, y0, x1, y1 = table_bbox

    # expand_only模式：仅做轻微外扩，不重新计算
    if mode == "expand_only":
        return [
            max(0, x0 - 1.5),  # 左边外扩1.5pt
            max(0, y0 - 1.0),  # 上边外扩1pt
            x1 + 1.5,          # 右边外扩1.5pt
            y1 + 1.0           # 下边外扩1pt
        ]

    # full模式：检查并重新计算
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
        cell_bbox = cell.get('bbox')
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

                # 使用pdfplumber找到表格
                # 先尝试lines策略（最准确，如果表格有完整边框）
                table_settings_lines = {
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines",
                    "intersection_x_tolerance": 3,
                    "intersection_y_tolerance": 3
                }
                tables = page.find_tables(table_settings=table_settings_lines)

                # 如果检测不到表格，尝试text策略（基于文本对齐）
                if not tables:
                    table_settings_text = {
                        "vertical_strategy": "text",
                        "horizontal_strategy": "lines",
                        "intersection_y_tolerance": 3
                    }
                    tables = page.find_tables(table_settings=table_settings_text)
                    if tables:
                        print(f"  [策略回退] 使用text策略检测到 {len(tables)} 个表格")

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

                        tables_data.append(structured_table)
                        print(f"  [表格 {table_idx + 1}] [OK] 成功添加到结果列表")
                    else:
                        print(f"  [表格 {table_idx + 1}] 跳过: table_data为空")

        doc_pymupdf.close()
        print(f"\n[表格提取] 完成，共提取 {len(tables_data)} 个表格\n")
        return tables_data

    def _extract_with_template(self,
                              page,
                              pymupdf_page,
                              bbox: List[float],
                              col_xs: List[float],
                              page_num: int) -> Dict[str, Any]:
        """
        单表强制提取（使用显式列边界模板）

        使用pdfplumber的extract_table而非find_tables，强制在指定bbox内按col_xs切分

        Args:
            page: pdfplumber页面对象
            pymupdf_page: PyMuPDF页面对象
            bbox: 表格bbox [x0, y0, x1, y1]
            col_xs: 显式列边界
            page_num: 页码

        Returns:
            结构化表格dict或None
        """
        x0, y0, x1, y1 = bbox
        page_height = pymupdf_page.rect.height

        # 构造表格提取设置
        table_settings = {
            "vertical_strategy": "explicit",
            "explicit_vertical_lines": col_xs,
            "horizontal_strategy": "lines_strict",
            "snap_tolerance": 3,
            "join_tolerance": 3,
            "edge_min_length": 3,
            "min_words_vertical": 3,
            "min_words_horizontal": 1,
        }

        # 裁剪页面到bbox区域（关键！这样extract_table只在这个区域内工作）
        cropped_page = page.within_bbox(bbox)

        # 使用extract_table（单表强制提取）
        table = cropped_page.extract_table(table_settings=table_settings)

        if not table or len(table) == 0:
            return None

        # 获取cells信息
        table_obj = cropped_page.find_tables(table_settings=table_settings)
        if not table_obj:
            return None

        cells = table_obj[0].cells
        table_bbox_extracted = list(table_obj[0].bbox)

        # 构建bbox_data（单元格坐标）
        y_coords = sorted(set([cell[1] for cell in cells] + [cell[3] for cell in cells]))
        x_coords = sorted(set([cell[0] for cell in cells] + [cell[2] for cell in cells]))

        # 使用PyMuPDF提取文本
        table_data = []
        bbox_data = []

        for row_idx, row in enumerate(table):
            new_row = []
            bbox_row = []
            for col_idx in range(len(row)):
                cell_text = ""
                cell_bbox_found = None
                for cell_bbox in cells:
                    x0_cell, y0_cell, x1_cell, y1_cell = cell_bbox
                    cell_row = self._find_index(y0_cell, y_coords)
                    cell_col = self._find_index(x0_cell, x_coords)

                    if cell_row == row_idx and cell_col == col_idx:
                        # 坐标转换：cropped坐标 → 页面坐标
                        abs_cell_bbox = (
                            cell_bbox[0] + bbox[0],
                            cell_bbox[1] + bbox[1],
                            cell_bbox[2] + bbox[0],
                            cell_bbox[3] + bbox[1]
                        )
                        cell_text = self.extract_cell_text(pymupdf_page, abs_cell_bbox)
                        cell_bbox_found = abs_cell_bbox
                        break

                new_row.append(cell_text if cell_text else "")
                bbox_row.append(cell_bbox_found)
            table_data.append(new_row)
            bbox_data.append(bbox_row)

        # 检测嵌套表格
        nested_map = self.nested_handler.detect_and_extract_nested_tables(
            page, pymupdf_page, table_obj[0], bbox_data
        )

        # 构建结构化表格（hint_row_levels=0避免把序号列当行表头）
        if table_data:
            structured_table = self._build_structured_table(
                table_data=table_data,
                bbox_data=bbox_data,
                cells_bbox=cells,
                page_num=page_num,
                table_bbox=bbox,  # 使用hint的bbox
                nested_map=nested_map,
                pymupdf_page=pymupdf_page,
                hint_row_levels=0  # 强制不把第一列识别为行表头
            )
            return structured_table

        return None

    def _text_bucket_by_cols(self,
                            pymupdf_page,
                            bbox: List[float],
                            col_xs: List[float],
                            page_num: int) -> Dict[str, Any]:
        """
        纯文本分列兜底（不依赖pdfplumber表格检测）

        原理：
        1. 用PyMuPDF在bbox内提取words
        2. 按col_xs将词分桶入列
        3. 用y方向聚类组成行
        4. 生成二维cells，调用_build_structured_table构造表格

        Args:
            pymupdf_page: PyMuPDF页面对象
            bbox: 表格bbox [x0, y0, x1, y1]
            col_xs: 列边界
            page_num: 页码

        Returns:
            结构化表格dict或None
        """
        x0, y0, x1, y1 = bbox

        # 1. 提取bbox内的所有words
        words = pymupdf_page.get_text("words", clip=(x0, y0, x1, y1))
        if not words:
            return None

        # 2. 按列分桶
        num_cols = len(col_xs) - 1  # col_xs是边界，列数=边界数-1
        col_buckets = [[] for _ in range(num_cols)]

        for word in words:
            wx0, wy0, wx1, wy1, text, block_no, line_no, word_no = word
            word_center_x = (wx0 + wx1) / 2

            # 找到word所属的列
            for col_idx in range(num_cols):
                left_edge = col_xs[col_idx]
                right_edge = col_xs[col_idx + 1]
                if left_edge <= word_center_x < right_edge:
                    col_buckets[col_idx].append({
                        'text': text,
                        'bbox': (wx0, wy0, wx1, wy1),
                        'y_center': (wy0 + wy1) / 2,
                        'y0': wy0,
                        'y1': wy1
                    })
                    break

        # 3. Y方向聚类成行（使用简单的阈值聚类）
        # 收集所有词的y_center
        all_y_centers = []
        for col_bucket in col_buckets:
            for word in col_bucket:
                all_y_centers.append(word['y_center'])

        if not all_y_centers:
            return None

        # 排序并聚类（相邻y_center差<6pt认为同一行）
        all_y_centers = sorted(set(all_y_centers))
        row_y_centers = []
        current_cluster = [all_y_centers[0]]

        for y in all_y_centers[1:]:
            if y - current_cluster[-1] < 6:  # 6pt阈值
                current_cluster.append(y)
            else:
                row_y_centers.append(sum(current_cluster) / len(current_cluster))
                current_cluster = [y]
        if current_cluster:
            row_y_centers.append(sum(current_cluster) / len(current_cluster))

        # 4. 构造二维cells
        table_data = []
        bbox_data = []

        for row_y in row_y_centers:
            row_cells = []
            row_bboxes = []

            for col_idx in range(num_cols):
                # 找该列中y_center接近row_y的词
                col_words = [w for w in col_buckets[col_idx]
                            if abs(w['y_center'] - row_y) < 6]

                if col_words:
                    # 合并该单元格内的所有词
                    texts = [w['text'] for w in col_words]
                    cell_text = ' '.join(texts)

                    # 计算cell bbox（所有词的包络）
                    min_x = min(w['bbox'][0] for w in col_words)
                    min_y = min(w['bbox'][1] for w in col_words)
                    max_x = max(w['bbox'][2] for w in col_words)
                    max_y = max(w['bbox'][3] for w in col_words)
                    cell_bbox = (min_x, min_y, max_x, max_y)
                else:
                    cell_text = ""
                    # 空单元格bbox：用列边界和行y构造
                    cell_bbox = (col_xs[col_idx], row_y - 3, col_xs[col_idx + 1], row_y + 3)

                row_cells.append(cell_text)
                row_bboxes.append(cell_bbox)

            table_data.append(row_cells)
            bbox_data.append(row_bboxes)

        # 5. 构建结构化表格
        if table_data:
            # 构造cells_bbox（pdfplumber格式）
            cells_bbox = []
            for row_bboxes in bbox_data:
                for cell_bbox in row_bboxes:
                    if cell_bbox:
                        cells_bbox.append(cell_bbox)

            structured_table = self._build_structured_table(
                table_data=table_data,
                bbox_data=bbox_data,
                cells_bbox=cells_bbox,
                page_num=page_num,
                table_bbox=bbox,
                nested_map={},  # 纯文本分列不支持嵌套表
                pymupdf_page=pymupdf_page,
                hint_row_levels=0
            )
            return structured_table

        return None

    def reextract_with_hints(self,
                            hints_by_page: Dict[int, Dict],
                            original_tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        使用续页hint重新提取指定页面的表格（显式列边界 + 两段式回退）

        策略：
        1. 主路径：使用extract_table单表强制提取
        2. 兜底A：扩大bbox 8-10pt重试
        3. 兜底B：纯文本分列（不依赖pdfplumber表格检测）

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
                page_width = pymupdf_page.rect.width

                col_xs = hint['col_xs']
                hint_bbox = hint['bbox']

                # 构造表格bbox（hint的bbox是上一页的，需要转换为当前页）
                x0, _, x1, _ = hint_bbox
                # 续页表格通常从页顶开始，到页底或某个y位置
                table_bbox = [x0, 5, x1, page_height - 5]  # 留5pt边距

                reextracted_table = None

                # ========== 主路径：extract_table单表强制提取 ==========
                print(f"  [主路径] 使用extract_table单表强制提取")
                try:
                    reextracted_table = self._extract_with_template(
                        page, pymupdf_page, table_bbox, col_xs, page_num
                    )
                    if reextracted_table:
                        print(f"  [主路径] 成功！提取到{len(reextracted_table.get('rows', []))}行")
                except Exception as e:
                    print(f"  [主路径] 失败: {e}")

                # ========== 兜底A：扩大bbox 8-10pt重试 ==========
                if not reextracted_table:
                    print(f"  [兜底A] 扩大bbox 10pt重试")
                    expanded_bbox = [
                        max(0, table_bbox[0] - 10),
                        max(0, table_bbox[1] - 10),
                        min(page_width, table_bbox[2] + 10),
                        min(page_height, table_bbox[3] + 10)
                    ]
                    try:
                        reextracted_table = self._extract_with_template(
                            page, pymupdf_page, expanded_bbox, col_xs, page_num
                        )
                        if reextracted_table:
                            print(f"  [兜底A] 成功！提取到{len(reextracted_table.get('rows', []))}行")
                    except Exception as e:
                        print(f"  [兜底A] 失败: {e}")

                # ========== 兜底B：纯文本分列（不依赖pdfplumber） ==========
                if not reextracted_table:
                    print(f"  [兜底B] 纯文本分列兜底")
                    try:
                        reextracted_table = self._text_bucket_by_cols(
                            pymupdf_page, table_bbox, col_xs, page_num
                        )
                        if reextracted_table:
                            print(f"  [兜底B] 成功！提取到{len(reextracted_table.get('rows', []))}行")
                    except Exception as e:
                        print(f"  [兜底B] 失败: {e}")

                # ========== 替换原表格（使用IoU匹配） ==========
                if reextracted_table:
                    # 找到IoU最大的原表格
                    page_tables = tables_by_page.get(page_num, [])
                    if not page_tables:
                        print(f"  警告: 页{page_num}没有原表格，跳过替换")
                        continue

                    # 计算IoU并找到最匹配的表格
                    best_match = None
                    best_iou = 0.0
                    reextracted_bbox = reextracted_table.get('raw_bbox', reextracted_table.get('bbox'))

                    for orig_table in page_tables:
                        orig_bbox = orig_table.get('raw_bbox', orig_table.get('bbox', [0,0,0,0]))
                        iou = self._calculate_iou(reextracted_bbox, orig_bbox)

                        if iou > best_iou:
                            best_iou = iou
                            best_match = orig_table

                    if best_match and best_iou > 0.3:  # IoU阈值
                        # 保留原表格的ID（用于合并链）
                        original_id = best_match.get('id')
                        reextracted_table['id'] = original_id

                        # 替换
                        for i, table in enumerate(original_tables):
                            if table.get('id') == original_id:
                                original_tables[i] = reextracted_table
                                print(f"  [OK] 替换表格 {original_id} (IoU={best_iou:.3f})")
                                print(f"       原行数: {len(best_match.get('rows', []))}行 {len(best_match.get('columns', []))}列")
                                print(f"       新行数: {len(reextracted_table.get('rows', []))}行 {len(reextracted_table.get('columns', []))}列")
                                break
                    else:
                        print(f"  警告: 未找到匹配的原表格 (最大IoU={best_iou:.3f})")
                else:
                    print(f"  警告: 所有重提取策略均失败，保留原表格")

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

        # 如果表头分析成功，使用多层路径
        if header_model:
            return self._build_table_with_multi_level_headers(
                table_data=table_data,
                bbox_data=bbox_data,
                page_num=page_num,
                table_bbox=table_bbox,
                nested_map=nested_map,
                header_model=header_model,
                page_height=page_height
            )
        else:
            # 回退到单层表头逻辑
            return self._build_table_with_single_level_headers(
                table_data=table_data,
                bbox_data=bbox_data,
                page_num=page_num,
                table_bbox=table_bbox,
                nested_map=nested_map,
                page_height=page_height
            )

    def _build_table_with_multi_level_headers(
        self,
        table_data: List[List[str]],
        bbox_data: List[List[tuple]],
        page_num: int,
        table_bbox: list,
        nested_map: Dict[tuple, List[Dict]],
        header_model,
        page_height: float
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

        # 3. 保存原始bbox和修正bbox
        all_cells = []
        for row in rows:
            all_cells.extend(row['cells'])

        # 保存原始bbox（未修正）
        raw_bbox = list(table_bbox)

        # 使用expand_only模式修正（只外扩，不收缩）
        fixed_bbox = validate_and_fix_bbox(table_bbox, all_cells, page_height, mode="expand_only")

        return {
            "type": "table",
            "level": 1,
            "parent_table_id": None,
            "page": page_num,
            "raw_bbox": raw_bbox,  # 原始未修正的bbox（用于hint生成和续页判定）
            "bbox": fixed_bbox,     # 修正后的bbox（用于渲染/裁剪）
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
        page_height: float
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

        # 4. 保存原始bbox和修正bbox
        all_cells = []
        for row in rows:
            all_cells.extend(row['cells'])

        # 保存原始bbox（未修正）
        raw_bbox = list(table_bbox)

        # 使用expand_only模式修正（只外扩，不收缩）
        fixed_bbox = validate_and_fix_bbox(table_bbox, all_cells, page_height, mode="expand_only")

        return {
            "type": "table",
            "level": 1,
            "parent_table_id": None,
            "page": page_num,
            "raw_bbox": raw_bbox,  # 原始未修正的bbox（用于hint生成和续页判定）
            "bbox": fixed_bbox,     # 修正后的bbox（用于渲染/裁剪）
            "columns": columns,
            "rows": rows,
            "header_info": {
                "col_levels": 1,
                "row_levels": 1,
                "multi_level": False
            },
            "method": "hybrid (pdfplumber cells + pymupdf text)"
        }

    def _calculate_iou(self, bbox1: List[float], bbox2: List[float]) -> float:
        """
        计算两个bbox的IoU (Intersection over Union)

        Args:
            bbox1: 第一个bbox [x0, y0, x1, y1]
            bbox2: 第二个bbox [x0, y0, x1, y1]

        Returns:
            IoU值 [0, 1]
        """
        x0_1, y0_1, x1_1, y1_1 = bbox1
        x0_2, y0_2, x1_2, y1_2 = bbox2

        # 计算交集
        x0_inter = max(x0_1, x0_2)
        y0_inter = max(y0_1, y0_2)
        x1_inter = min(x1_1, x1_2)
        y1_inter = min(y1_1, y1_2)

        # 如果没有交集
        if x1_inter <= x0_inter or y1_inter <= y0_inter:
            return 0.0

        inter_area = (x1_inter - x0_inter) * (y1_inter - y0_inter)

        # 计算并集
        area1 = (x1_1 - x0_1) * (y1_1 - y0_1)
        area2 = (x1_2 - x0_2) * (y1_2 - y0_2)
        union_area = area1 + area2 - inter_area

        if union_area <= 0:
            return 0.0

        return inter_area / union_area

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