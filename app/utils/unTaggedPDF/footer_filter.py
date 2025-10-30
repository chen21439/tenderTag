"""
页脚/页码过滤工具
用于在表格提取时避免提取到页面底部的页码和页脚内容
"""
import re
from typing import List, Dict, Any, Tuple
import fitz  # PyMuPDF


class FooterConfig:
    """页脚过滤配置"""

    def __init__(
        self,
        mode: str = "fixed",              # 模式: "fixed"固定高度 / "auto"自动检测 / "none"不过滤
        fixed_points: float = 30.0,       # mode=fixed 时使用的固定高度
        scan_bottom_ratio: float = 0.10,  # auto 扫描底部比例（10%页面高度）
        min_points: float = 18.0,         # auto 探测出的最小安全高度
        max_points: float = 96.0,         # auto 探测出的最大安全高度（防炸）
        remove_page_number: bool = True,  # 是否过滤"第 X 页"/纯数字页码
        page_number_regex: str = r"^\s*-?\s*第?\s*\d+\s*页\s*-?\s*$|^\s*\d+\s*$"
    ):
        self.mode = mode
        self.fixed_points = fixed_points
        self.scan_bottom_ratio = scan_bottom_ratio
        self.min_points = min_points
        self.max_points = max_points
        self.remove_page_number = remove_page_number
        self.page_number_regex = page_number_regex


class FooterFilter:
    """页脚/页码过滤器"""

    def __init__(self, config: FooterConfig = None):
        """
        初始化页脚过滤器

        Args:
            config: 过滤配置，默认使用 fixed 模式 30pt
        """
        self.config = config or FooterConfig()

    def detect_footer_height(
        self,
        fitz_page: fitz.Page,
        scan_ratio: float = None,
        min_pts: float = None,
        max_pts: float = None
    ) -> float:
        """
        在页面底部自动检测页脚高度

        原理：在页面底部 scan_ratio 高度的区域中找文本块，估算页脚高度：
        - 若检测不到文本，返回 0
        - 若检测到，取最上缘的 y0 作为页脚上边界，page.h - y0 即高度
        - 并用 [min_pts, max_pts] 夹住

        Args:
            fitz_page: PyMuPDF 页面对象
            scan_ratio: 扫描底部比例，默认使用 config 中的值
            min_pts: 最小页脚高度，默认使用 config 中的值
            max_pts: 最大页脚高度，默认使用 config 中的值

        Returns:
            检测到的页脚高度（pt）
        """
        scan_ratio = scan_ratio or self.config.scan_bottom_ratio
        min_pts = min_pts or self.config.min_points
        max_pts = max_pts or self.config.max_points

        rect = fitz_page.rect
        h = rect.height

        # 扫描底部区域
        scan_rect = fitz.Rect(rect.x0, rect.y1 - h * scan_ratio, rect.x1, rect.y1)
        blocks = fitz_page.get_text("blocks", clip=scan_rect)

        if not blocks:
            return 0.0

        # 找到最上方的文本块
        topmost_y0 = min(b[1] for b in blocks)
        footer_h = h - topmost_y0

        # 合理区间裁剪
        footer_h = max(min_pts, min(max_pts, footer_h))

        return float(footer_h)

    def get_footer_height(self, fitz_page: fitz.Page) -> float:
        """
        根据配置获取页脚高度

        Args:
            fitz_page: PyMuPDF 页面对象

        Returns:
            页脚高度（pt）
        """
        if self.config.mode == "fixed":
            return float(max(0.0, self.config.fixed_points))
        elif self.config.mode == "auto":
            return self.detect_footer_height(fitz_page)
        else:  # mode == "none"
            return 0.0

    def get_safe_page_rect(self, fitz_page: fitz.Page) -> fitz.Rect:
        """
        获取去掉页脚后的安全页面区域

        Args:
            fitz_page: PyMuPDF 页面对象

        Returns:
            安全区域的 Rect（不包含页脚）
        """
        rect = fitz_page.rect
        footer_h = self.get_footer_height(fitz_page)
        page_num = fitz_page.number + 1

        # 页脚安全区：从页面底部向上收缩 footer_h
        safe_rect = fitz.Rect(
            rect.x0,
            rect.y0,
            rect.x1,
            max(0.0, rect.y1 - footer_h)
        )

        # [DEBUG] 第6页调试日志
        if page_num == 6:
            print(f"\n[DEBUG get_safe_page_rect] 页码={page_num}")
            print(f"  页面 rect: {rect}")
            print(f"  页脚高度 footer_h: {footer_h}pt")
            print(f"  计算方式: y1 - footer_h = {rect.y1} - {footer_h} = {rect.y1 - footer_h}")
            print(f"  safe_rect: {safe_rect}")

        return safe_rect

    def clip_to_safe_area(self, cell_rect: fitz.Rect, fitz_page: fitz.Page) -> fitz.Rect:
        """
        将 cell bbox 裁剪到安全区域（去掉页脚）

        Args:
            cell_rect: 单元格的 Rect
            fitz_page: PyMuPDF 页面对象

        Returns:
            裁剪后的 Rect
        """
        safe_rect = self.get_safe_page_rect(fitz_page)
        clipped = cell_rect & safe_rect  # 交集运算

        # 检查是否为空矩形
        if clipped.is_empty or clipped.width <= 0 or clipped.height <= 0:
            return fitz.Rect(0, 0, 0, 0)

        return clipped

    def filter_page_number(self, text: str) -> str:
        """
        过滤文本中的页码模式

        Args:
            text: 原始文本

        Returns:
            过滤后的文本
        """
        if not self.config.remove_page_number:
            return text
        return text
        # # 移除页码模式（如：-第4页-、第4页、- 4 -、4 等）
        # pattern = re.compile(self.config.page_number_regex)
        #
        # # 按空格分词，过滤每个词
        # tokens = text.split()
        # filtered_tokens = [tok for tok in tokens if not pattern.match(tok)]
        #
        # return " ".join(filtered_tokens)

    def extract_cell_text_safe(
        self,
        fitz_page: fitz.Page,
        cell_bbox: tuple,
        debug: bool = False
    ) -> str:
        """
        从单元格 bbox 安全地提取文本（自动避开页脚区域）

        Args:
            fitz_page: PyMuPDF 页面对象
            cell_bbox: 单元格边界框 (x0, y0, x1, y1)
            debug: 是否输出调试信息

        Returns:
            提取的文本内容
        """
        page_rect = fitz_page.rect
        page_num = fitz_page.number + 1  # PyMuPDF的页码从0开始

        # [DEBUG] 第6页调试日志
        if page_num == 6:
            print(f"\n[DEBUG extract_cell_text_safe] 页码={page_num}")
            print(f"  原始 cell_bbox: {cell_bbox}")
            print(f"  page_rect: {page_rect}")

        # 1. 裁剪 cell bbox 到页面范围
        cell_rect = fitz.Rect(cell_bbox)
        clipped_rect = cell_rect & page_rect

        if page_num == 6:
            print(f"  cell_rect: {cell_rect}")
            print(f"  clipped_rect (第一次裁剪到页面): {clipped_rect}")
            print(f"  clipped_rect.is_empty: {clipped_rect.is_empty}")

        if clipped_rect.is_empty:
            if page_num == 6:
                print(f"  返回空字符串（clipped_rect 为空）")
            return ""

        # 2. 进一步裁剪到安全区域（去掉页脚）
        safe_rect = self.clip_to_safe_area(clipped_rect, fitz_page)

        if page_num == 6:
            print(f"  safe_rect (第二次裁剪到安全区): {safe_rect}")
            print(f"  safe_rect.is_empty: {safe_rect.is_empty}")

        if safe_rect.is_empty:
            if page_num == 6:
                print(f"  返回空字符串（safe_rect 为空）")
            return ""

        if debug:
            footer_h = self.get_footer_height(fitz_page)
            print(f"\n[FooterFilter DEBUG]")
            print(f"  模式: {self.config.mode}")
            print(f"  页脚高度: {footer_h:.2f}pt")
            print(f"  原始 cell bbox: {cell_bbox}")
            print(f"  裁剪到页面: {clipped_rect}")
            print(f"  裁剪到安全区: {safe_rect}")

        # 3. 提取文本
        text = fitz_page.get_text("text", clip=safe_rect)

        if page_num == 6:
            print(f"  提取的原始文本长度: {len(text)}")
            print(f"  提取的原始文本预览: '{text[:100]}'")

        # 4. 移除换行符
        text = text.replace('\n', '').replace('\r', '')

        # 5. 过滤页码模式（兜底保险）
        text = self.filter_page_number(text)

        if page_num == 6:
            print(f"  最终返回的文本长度: {len(text.strip())}")
            print(f"  最终返回的文本预览: '{text.strip()[:100]}'")

        return text.strip()


def compute_table_rect_on_page(
    cells: List[tuple],
    page_width: float,
    page_height: float
) -> fitz.Rect:
    """
    仅使用与当前页有交集的 cells 计算"该页内的表格边界"

    Args:
        cells: pdfplumber 的 cells 列表 [(x0, y0, x1, y1), ...]
        page_width: 页面宽度
        page_height: 页面高度

    Returns:
        页内表格边界 Rect
    """
    # 过滤出与当前页有交集的 cells
    inter_cells = [
        c for c in cells
        if (c[1] < page_height and c[3] > 0 and c[2] > 0 and c[0] < page_width)
    ]

    if not inter_cells:
        # 找不到就退回整页
        return fitz.Rect(0, 0, page_width, page_height)

    x0 = max(0.0, min(c[0] for c in inter_cells))
    y0 = max(0.0, min(c[1] for c in inter_cells))
    x1 = min(page_width, max(c[2] for c in inter_cells))
    y1 = min(page_height, max(c[3] for c in inter_cells))

    # 保护性纠正（避免 y0>=y1 等非法矩形）
    if y1 <= y0:
        y0 = max(0.0, min(y0, page_height - 1.0))
        y1 = min(page_height, max(y1, y0 + 1.0))
    if x1 <= x0:
        x0 = max(0.0, min(x0, page_width - 1.0))
        x1 = min(page_width, max(x1, x0 + 1.0))

    return fitz.Rect(x0, y0, x1, y1)