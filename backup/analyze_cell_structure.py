"""
分析单元格内部结构
对比复合表格和普通表格的 cell 内容差异
"""

import pdfplumber
import sys
import io
from pathlib import Path


def analyze_cell_structure(pdf_path: str, page_num: int = 0):
    """分析PDF中的单元格内部结构"""

    print(f"\n{'='*80}")
    print(f"[分析] {Path(pdf_path).name}")
    print(f"{'='*80}\n")

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_num]

        # 检测表格
        table_settings = {
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
            "intersection_x_tolerance": 3,
            "intersection_y_tolerance": 3
        }
        tables = page.find_tables(table_settings=table_settings)

        print(f"[1] 表格检测结果")
        print("-" * 80)
        print(f"检测到 {len(tables)} 个表格\n")

        for table_idx, table in enumerate(tables):
            print(f"表格[{table_idx}]:")
            print(f"  bbox: {table.bbox}")
            print(f"  单元格数: {len(table.cells)}")

            # 找出最大的几个单元格
            cells_with_area = []
            for cell_idx, cell_bbox in enumerate(table.cells):
                x0, y0, x1, y1 = cell_bbox
                width = x1 - x0
                height = y1 - y0
                area = width * height
                cells_with_area.append({
                    'idx': cell_idx,
                    'bbox': cell_bbox,
                    'width': width,
                    'height': height,
                    'area': area
                })

            # 按面积排序
            cells_sorted = sorted(cells_with_area, key=lambda x: x['area'], reverse=True)

            # 分析前5个最大的单元格
            print(f"\n[2] 最大的5个单元格内部结构分析")
            print("-" * 80)

            for i, cell_info in enumerate(cells_sorted[:5]):
                cell_bbox = cell_info['bbox']
                print(f"\n单元格[{cell_info['idx']}]:")
                print(f"  bbox: ({cell_bbox[0]:.2f}, {cell_bbox[1]:.2f}, {cell_bbox[2]:.2f}, {cell_bbox[3]:.2f})")
                print(f"  尺寸: {cell_info['width']:.2f} × {cell_info['height']:.2f} (面积: {cell_info['area']:.2f})")

                # 创建子视图
                sub_view = page.within_bbox(cell_bbox, relative=False)

                # 1. 提取文本
                text = sub_view.extract_text()
                text_lines = text.split('\n') if text else []
                print(f"\n  文本内容:")
                print(f"    总字符数: {len(text) if text else 0}")
                print(f"    行数: {len(text_lines)}")
                if text_lines:
                    print(f"    文本预览（前5行）:")
                    for line in text_lines[:5]:
                        print(f"      {repr(line)}")

                # 2. 字符对象
                chars = sub_view.chars
                print(f"\n  字符对象:")
                print(f"    总数: {len(chars)}")
                if len(chars) > 0:
                    # 统计字符的 Y 坐标（看是否有多行）
                    y_coords = set()
                    x_coords = set()
                    for char in chars:
                        y_coords.add(round(char['top'], 1))
                        x_coords.add(round(char['x0'], 1))
                    print(f"    唯一 Y 坐标数（行数估计）: {len(y_coords)}")
                    print(f"    唯一 X 坐标数（列对齐）: {len(x_coords)}")

                    # 显示前3个字符的位置
                    print(f"    前3个字符示例:")
                    for char in chars[:3]:
                        print(f"      '{char['text']}' at ({char['x0']:.2f}, {char['top']:.2f})")

                # 3. 矩形对象
                rects = sub_view.rects
                print(f"\n  矩形对象:")
                print(f"    总数: {len(rects)}")
                if len(rects) > 0:
                    print(f"    前3个矩形:")
                    for rect in rects[:3]:
                        print(f"      bbox: ({rect['x0']:.2f}, {rect['top']:.2f}, {rect['x1']:.2f}, {rect['bottom']:.2f})")

                # 4. 线段对象
                edges = sub_view.edges
                h_edges = [e for e in edges if e['orientation'] == 'h']
                v_edges = [e for e in edges if e['orientation'] == 'v']
                print(f"\n  边缘线:")
                print(f"    水平边缘: {len(h_edges)} 条")
                print(f"    垂直边缘: {len(v_edges)} 条")

                # 5. 尝试检测子表格（lines策略）
                try:
                    sub_tables_lines = sub_view.find_tables(table_settings={
                        "vertical_strategy": "lines",
                        "horizontal_strategy": "lines",
                        "intersection_x_tolerance": 3,
                        "intersection_y_tolerance": 3
                    })
                    print(f"\n  子表格检测（lines策略）:")
                    print(f"    检测到: {len(sub_tables_lines)} 个子表格")
                    if sub_tables_lines:
                        for st_idx, st in enumerate(sub_tables_lines):
                            print(f"      子表格[{st_idx}]: bbox={st.bbox}, 单元格数={len(st.cells)}")
                except Exception as e:
                    print(f"\n  子表格检测（lines策略）:")
                    print(f"    错误: {e}")

                # 6. 尝试检测子表格（text策略）
                try:
                    sub_tables_text = sub_view.find_tables(table_settings={
                        "vertical_strategy": "text",
                        "horizontal_strategy": "text"
                    })
                    print(f"\n  子表格检测（text策略）:")
                    print(f"    检测到: {len(sub_tables_text)} 个子表格")
                    if sub_tables_text:
                        for st_idx, st in enumerate(sub_tables_text):
                            print(f"      子表格[{st_idx}]: bbox={st.bbox}, 单元格数={len(st.cells)}")
                except Exception as e:
                    print(f"\n  子表格检测（text策略）:")
                    print(f"    错误: {e}")

                # 7. 文本对齐分析（检测是否有规则的列对齐）
                if len(chars) > 0:
                    # 按 x0 分组，看是否有垂直对齐的文本列
                    from collections import defaultdict
                    x_groups = defaultdict(list)
                    for char in chars:
                        x_rounded = round(char['x0'], 0)  # 1pt容差
                        x_groups[x_rounded].append(char)

                    # 找出包含多个字符的列（可能是对齐的列）
                    aligned_columns = {x: len(chars) for x, chars in x_groups.items() if len(chars) >= 3}
                    print(f"\n  文本列对齐分析:")
                    print(f"    检测到 {len(aligned_columns)} 个对齐列（≥3个字符）")
                    if aligned_columns:
                        sorted_cols = sorted(aligned_columns.items(), key=lambda x: x[1], reverse=True)
                        print(f"    前3个对齐列:")
                        for x, count in sorted_cols[:3]:
                            print(f"      X={x}: {count}个字符")

                print("\n" + "-" * 80)


def compare_pdfs(pdf1_path: str, pdf2_path: str):
    """对比两个PDF的单元格结构"""

    print("\n" + "="*80)
    print("单元格结构对比分析")
    print("="*80)

    # 分析两个PDF
    analyze_cell_structure(pdf1_path, page_num=0)
    analyze_cell_structure(pdf2_path, page_num=0)

    # 总结
    print("\n" + "="*80)
    print("[总结] 复合表格 vs 普通表格的 cell 差异")
    print("="*80)
    print("""
预期差异：

复合表格的 cell 可能特征:
  1. 包含多行文本（行数 > 1）
  2. 字符对象有多个 Y 坐标（多行布局）
  3. 可能有规则的 X 坐标对齐（列对齐）
  4. 有较多的内部边缘线（但不形成子表格）
  5. text策略可能检测到"伪表格"

普通表格的 cell 可能特征:
  1. 简单文本内容（单行或少量行）
  2. 字符对象 Y 坐标较少
  3. 没有明显的列对齐
  4. 边缘线较少
  5. 不会检测到子表格
    """)


def main():
    # 设置UTF-8编码
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    pdf1 = r"E:\programFile\AIProgram\docxServer\pdf\task\table\复合表格.pdf"
    pdf2 = r"E:\programFile\AIProgram\docxServer\pdf\task\table\普通表格.pdf"

    compare_pdfs(pdf1, pdf2)


if __name__ == "__main__":
    main()