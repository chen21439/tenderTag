"""
Bbox工具类
提供bbox相关的通用方法
"""
import fitz  # PyMuPDF


def rect(bb: tuple) -> fitz.Rect:
    """
    将bbox转换为fitz.Rect

    Args:
        bb: bbox元组 (x0, y0, x1, y1)

    Returns:
        fitz.Rect对象
    """
    return fitz.Rect(bb[0], bb[1], bb[2], bb[3])


def contains_with_tol(outer: tuple, inner: tuple, tol: float = 1.0) -> bool:
    """
    判断outer是否包含inner（带容差）

    Args:
        outer: 外层bbox (x0, y0, x1, y1)
        inner: 内层bbox (x0, y0, x1, y1)
        tol: 容差值

    Returns:
        是否包含
    """
    o = rect((outer[0] - tol, outer[1] - tol, outer[2] + tol, outer[3] + tol))
    i = rect(inner)
    return o.contains(i)


def is_bbox_overlap(bbox1: tuple, bbox2: tuple, threshold: float = 0.5) -> bool:
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