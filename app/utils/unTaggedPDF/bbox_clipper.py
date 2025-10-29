"""
bbox裁剪工具
用于将bbox裁剪到页面范围内，避免跨页坐标导致提取到其他页内容（如页码）
"""
from typing import Tuple, List


def clip_bbox_to_page(bbox: list, page_width: float = 595.0, page_height: float = 842.0) -> Tuple[List[float], List[float]]:
    """
    将bbox裁剪到页面范围内（避免跨页坐标导致提取到其他页内容）

    根据 pdfplumber 的实现机制：
    - PDF从DOCX转换时，跨页表格可能使用累积坐标系统
    - 导致 y1 > page_height（如 y1=1500 表示跨越多页）
    - 如果直接用跨页bbox提取文本，会提取到其他页的内容（包括页码标记）

    解决方案：
    - 保留 raw_bbox：记录PDF原始的跨页坐标（珍贵的几何信息）
    - 生成 clipped_bbox：裁剪到当前页面范围
    - 用 clipped_bbox 进行文本提取，避免提取到其他页内容

    Args:
        bbox: 原始bbox [x0, y0, x1, y1]
        page_width: 页面宽度（默认A4宽度 595pt）
        page_height: 页面高度（默认A4高度 842pt）

    Returns:
        (raw_bbox, clipped_bbox) - 原始bbox和裁剪后的bbox
            - raw_bbox: 保留原始跨页坐标
            - clipped_bbox: 裁剪到页面范围 [x0, max(0, y0), x1, min(page_height, y1)]

    Example:
        >>> raw, clipped = clip_bbox_to_page([100, -50, 400, 1500], page_height=842)
        >>> print(f"Raw: {raw}")
        Raw: [100, -50, 400, 1500]
        >>> print(f"Clipped: {clipped}")
        Clipped: [100, 0, 400, 842]
    """
    if not bbox or len(bbox) != 4:
        return (bbox, bbox)

    x0, y0, x1, y1 = bbox
    raw_bbox = list(bbox)  # 保留原始跨页坐标

    # 裁剪到页面范围
    clipped_bbox = [
        max(0, x0),           # x0: 不能小于0
        max(0, y0),           # y0: 不能小于0（负坐标）
        min(page_width, x1),  # x1: 不能超过页面宽度
        min(page_height, y1)  # y1: 不能超过页面高度（跨页坐标）
    ]

    return (raw_bbox, clipped_bbox)


def clip_cell_bbox(cell_bbox: tuple, page_width: float = 595.0, page_height: float = 842.0) -> tuple:
    """
    裁剪单元格bbox到页面范围（简化版，只返回裁剪后的bbox）

    Args:
        cell_bbox: 单元格原始bbox (x0, y0, x1, y1)
        page_width: 页面宽度
        page_height: 页面高度

    Returns:
        裁剪后的bbox (tuple)
    """
    if not cell_bbox or len(cell_bbox) != 4:
        return cell_bbox

    x0, y0, x1, y1 = cell_bbox

    # 裁剪到页面范围
    clipped = (
        max(0.0, x0),
        max(0.0, y0),
        min(page_width, x1),
        min(page_height, y1)
    )

    return clipped