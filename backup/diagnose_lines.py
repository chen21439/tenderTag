"""
诊断脚本：对比两个PDF的线条来源
分析为什么 table.pdf 无法识别嵌套表格，而 真正的嵌套表格-示例.pdf 可以
"""

import fitz  # PyMuPDF
import pdfplumber
from pathlib import Path


def analyze_pdf_lines(pdf_path: str, page_num: int = 0):
    """
    分析PDF页面的线条信息

    Args:
        pdf_path: PDF文件路径
        page_num: 页码（从0开始）
    """
    print(f"\n{'='*80}")
    print(f"[分析文件] {Path(pdf_path).name}")
    print(f"{'='*80}\n")

    # ========== 1. PyMuPDF 线条分析 ==========
    print(f"[1] PyMuPDF 线条分析 (get_drawings)")
    print("-" * 80)

    doc = fitz.open(pdf_path)
    page = doc[page_num]
    drawings = page.get_drawings()

    print(f"总绘图对象数: {len(drawings)}")

    # 统计线段
    h_lines = []  # 横线
    v_lines = []  # 竖线
    other_shapes = []  # 其他形状

    for d_idx, d in enumerate(drawings):
        if not isinstance(d, dict) or "items" not in d:
            continue

        for item in d["items"]:
            if not isinstance(item, (list, tuple)) or len(item) < 2:
                continue

            shape_type = item[0]

            if shape_type == "l":  # 线段
                line_coords = item[1]
                if len(line_coords) >= 4:
                    x0, y0, x1, y1 = line_coords[:4]
                    dx, dy = abs(x1 - x0), abs(y1 - y0)

                    if dy < 0.5:  # 横线
                        h_lines.append((x0, y0, x1, y1))
                    elif dx < 0.5:  # 竖线
                        v_lines.append((x0, y0, x1, y1))
                    else:
                        other_shapes.append((shape_type, line_coords))
            else:
                other_shapes.append((shape_type, item[1] if len(item) > 1 else None))

    print(f"  - 横线数量: {len(h_lines)}")
    print(f"  - 竖线数量: {len(v_lines)}")
    print(f"  - 其他形状: {len(other_shapes)}")

    # 显示前5条横线和竖线（采样）
    if h_lines:
        print(f"\n  横线样例（前5条）:")
        for i, (x0, y0, x1, y1) in enumerate(h_lines[:5]):
            print(f"    [{i}] ({x0:.2f}, {y0:.2f}) → ({x1:.2f}, {y1:.2f}), 长度: {abs(x1-x0):.2f}")

    if v_lines:
        print(f"\n  竖线样例（前5条）:")
        for i, (x0, y0, x1, y1) in enumerate(v_lines[:5]):
            print(f"    [{i}] ({x0:.2f}, {y0:.2f}) → ({x1:.2f}, {y1:.2f}), 长度: {abs(y1-y0):.2f}")

    # 统计其他形状类型
    if other_shapes:
        shape_types = {}
        for shape_type, _ in other_shapes:
            shape_types[shape_type] = shape_types.get(shape_type, 0) + 1
        print(f"\n  其他形状类型统计:")
        for shape_type, count in shape_types.items():
            print(f"    - {shape_type}: {count}个")

    # ========== 2. pdfplumber 表格检测 ==========
    print(f"\n[2] pdfplumber 表格检测")
    print("-" * 80)

    with pdfplumber.open(pdf_path) as pdf:
        plumber_page = pdf.pages[page_num]

        # 策略1: lines (基于线段)
        print(f"\n  策略1: lines (基于线段)")
        table_settings_lines = {
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
            "intersection_x_tolerance": 3,
            "intersection_y_tolerance": 3
        }
        tables_lines = plumber_page.find_tables(table_settings=table_settings_lines)
        print(f"    检测到表格数: {len(tables_lines)}")

        for idx, table in enumerate(tables_lines):
            bbox = table.bbox
            print(f"    表格[{idx}] bbox: ({bbox[0]:.2f}, {bbox[1]:.2f}, {bbox[2]:.2f}, {bbox[3]:.2f})")
            print(f"              尺寸: {bbox[2]-bbox[0]:.2f} × {bbox[3]-bbox[1]:.2f}")

        # 策略2: text (基于文本对齐)
        print(f"\n  策略2: text (基于文本对齐)")
        table_settings_text = {
            "vertical_strategy": "text",
            "horizontal_strategy": "text"
        }
        tables_text = plumber_page.find_tables(table_settings=table_settings_text)
        print(f"    检测到表格数: {len(tables_text)}")

        for idx, table in enumerate(tables_text):
            bbox = table.bbox
            print(f"    表格[{idx}] bbox: ({bbox[0]:.2f}, {bbox[1]:.2f}, {bbox[2]:.2f}, {bbox[3]:.2f})")
            print(f"              尺寸: {bbox[2]-bbox[0]:.2f} × {bbox[3]-bbox[1]:.2f}")

    # ========== 3. 嵌套检测模拟 ==========
    print(f"\n[3] 嵌套表格检测模拟 (_cell_has_inner_grid)")
    print("-" * 80)

    # 模拟检查第一个表格的第一个单元格
    if tables_lines:
        table = tables_lines[0]
        cells = table.cells

        if cells:
            # 取第一个单元格（通常是表头第一个单元格）
            cell_bbox = cells[0]
            print(f"\n  测试单元格: {cell_bbox}")
            print(f"  单元格尺寸: {cell_bbox[2]-cell_bbox[0]:.2f} × {cell_bbox[3]-cell_bbox[1]:.2f}")

            # 检查是否通过网格检测
            has_grid = check_cell_has_inner_grid(
                page, cell_bbox,
                min_h=2, min_v=2, min_cross=4, min_len=8
            )
            print(f"  [PASS] 通过网格检测" if has_grid else "  [FAIL] 未通过网格检测")

    doc.close()
    print()


def check_cell_has_inner_grid(pymupdf_page, bbox, min_h=2, min_v=2, min_cross=4, min_len=8):
    """
    模拟 _cell_has_inner_grid 的检测逻辑
    """
    try:
        x0_box, y0_box, x1_box, y1_box = bbox
        rect = fitz.Rect(bbox)

        # 单元格太小
        cell_width = x1_box - x0_box
        cell_height = y1_box - y0_box
        if cell_width < 50 or cell_height < 50:
            print(f"    → 单元格太小 (宽:{cell_width:.2f}, 高:{cell_height:.2f} < 50)")
            return False

        h_lines, v_lines = [], []
        drawings = pymupdf_page.get_drawings()

        if not drawings:
            print(f"    → 无绘图对象")
            return False

        for d in drawings:
            if not isinstance(d, dict) or "items" not in d:
                continue

            for item in d["items"]:
                if not isinstance(item, (list, tuple)) or len(item) < 2:
                    continue
                if item[0] != "l":
                    continue

                line_coords = item[1]
                if not isinstance(line_coords, (list, tuple)) or len(line_coords) < 4:
                    continue

                x0, y0, x1, y1 = line_coords[:4]

                # 排除边框线
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

        # 计算交点
        cross = 0
        for _, y0, _, _ in h_lines:
            for x0, _, _, _ in v_lines:
                if rect.contains(fitz.Point(x0, y0)):
                    cross += 1

        print(f"    → 内部横线: {len(h_lines)}, 竖线: {len(v_lines)}, 交点: {cross}")
        print(f"    → 阈值要求: 横≥{min_h}, 竖≥{min_v}, 交点≥{min_cross}")

        return (len(h_lines) >= min_h and len(v_lines) >= min_v and cross >= min_cross)

    except Exception as e:
        print(f"    → 检测异常: {e}")
        return False


def main():
    # 设置UTF-8编码
    import sys
    import io
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # 两个PDF文件路径
    pdf1 = r"E:\programFile\AIProgram\docxServer\pdf\task\1979102567573037058\table.pdf"
    pdf2 = r"E:\programFile\AIProgram\docxServer\pdf\task\1979102567573037058\真正的嵌套表格-示例.pdf"

    print("【复合表格 vs 嵌套表格】线条来源对比")
    print("目标: 分析为什么 table.pdf 无法识别嵌套表格\n")

    # 分析第一个PDF（复合表格）
    analyze_pdf_lines(pdf1, page_num=0)

    # 分析第二个PDF（真正的嵌套表格）
    analyze_pdf_lines(pdf2, page_num=0)

    # 总结
    print(f"\n{'='*80}")
    print("[分析总结]")
    print(f"{'='*80}\n")
    print("关键差异：")
    print("1. 线条数量：table.pdf 的线条数量明显少于嵌套表格示例")
    print("2. 线条来源：table.pdf 可能是位图/复合路径，无法被 get_drawings() 提取")
    print("3. 检测策略：需要增加基于文本对齐的兜底策略")
    print()


if __name__ == "__main__":
    main()