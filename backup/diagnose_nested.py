"""
增强诊断：分析嵌套表格的bbox包含关系
"""

import fitz  # PyMuPDF
import pdfplumber
from pathlib import Path
import sys
import io


def analyze_table_containment(pdf_path: str, page_num: int = 0):
    """分析表格的包含关系和单元格-表格映射"""

    print(f"\n{'='*80}")
    print(f"[分析] {Path(pdf_path).name}")
    print(f"{'='*80}\n")

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_num]

        # 使用lines策略检测表格
        table_settings = {
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
            "intersection_x_tolerance": 3,
            "intersection_y_tolerance": 3
        }
        tables = page.find_tables(table_settings=table_settings)

        print(f"[1] 检测到 {len(tables)} 个表格\n")

        # 显示每个表格的基本信息
        table_infos = []
        for idx, table in enumerate(tables):
            bbox = table.bbox
            x0, y0, x1, y1 = bbox
            width = x1 - x0
            height = y1 - y0
            area = width * height

            cells = table.cells

            info = {
                'idx': idx,
                'bbox': bbox,
                'width': width,
                'height': height,
                'area': area,
                'cells_count': len(cells) if cells else 0
            }
            table_infos.append(info)

            print(f"表格[{idx}]:")
            print(f"  bbox: ({x0:.2f}, {y0:.2f}, {x1:.2f}, {y1:.2f})")
            print(f"  尺寸: {width:.2f} × {height:.2f} (面积: {area:.2f})")
            print(f"  单元格数: {info['cells_count']}")
            print()

        # [2] 分析包含关系
        print(f"[2] 表格包含关系分析\n")

        if len(tables) >= 2:
            # 检查是否有嵌套关系（小表格完全包含在大表格内）
            for i in range(len(tables)):
                for j in range(len(tables)):
                    if i == j:
                        continue

                    bbox_i = table_infos[i]['bbox']
                    bbox_j = table_infos[j]['bbox']

                    # 检查bbox_j是否完全包含在bbox_i内
                    if is_contained(bbox_j, bbox_i):
                        print(f"  ✓ 表格[{j}] 完全包含在 表格[{i}] 内")
                        print(f"    父表: {bbox_i}")
                        print(f"    子表: {bbox_j}")

                        # 找到父表中哪个单元格包含这个子表
                        parent_table = tables[i]
                        child_bbox = bbox_j

                        matching_cells = find_containing_cells(parent_table, child_bbox)
                        if matching_cells:
                            print(f"    包含子表的单元格: {len(matching_cells)}个")
                            for cell_idx, cell_bbox in enumerate(matching_cells[:3]):  # 只显示前3个
                                print(f"      单元格[{cell_idx}]: {cell_bbox}")
                        print()
        else:
            print("  只有1个表格，无嵌套关系")
            print()

        # [3] 检查大单元格（可能包含子表的候选）
        print(f"[3] 大单元格分析（候选嵌套位置）\n")

        for table_idx, table in enumerate(tables):
            cells = table.cells
            if not cells:
                continue

            print(f"表格[{table_idx}] 大单元格统计:")

            # 统计单元格尺寸
            large_cells = []
            for cell_bbox in cells:
                x0, y0, x1, y1 = cell_bbox
                width = x1 - x0
                height = y1 - y0
                area = width * height

                # 筛选较大的单元格（可能包含嵌套表格）
                if width > 100 and height > 50:  # 阈值
                    large_cells.append({
                        'bbox': cell_bbox,
                        'width': width,
                        'height': height,
                        'area': area
                    })

            if large_cells:
                # 按面积排序
                large_cells.sort(key=lambda x: x['area'], reverse=True)
                print(f"  找到 {len(large_cells)} 个大单元格（宽>100 且 高>50）")

                # 显示前5个
                for i, cell_info in enumerate(large_cells[:5]):
                    bbox = cell_info['bbox']
                    print(f"    [{i}] bbox: ({bbox[0]:.2f}, {bbox[1]:.2f}, {bbox[2]:.2f}, {bbox[3]:.2f})")
                    print(f"        尺寸: {cell_info['width']:.2f} × {cell_info['height']:.2f}")

                    # 检查是否有其他表格在这个单元格内
                    for other_idx, other_table_info in enumerate(table_infos):
                        if other_idx == table_idx:
                            continue
                        other_bbox = other_table_info['bbox']
                        if is_contained(other_bbox, bbox):
                            print(f"        ★ 包含表格[{other_idx}]!")
                print()
            else:
                print(f"  无大单元格")
                print()

        # [4] 检查pdfplumber的edges（边缘线）
        print(f"[4] pdfplumber edges分析\n")

        edges = page.edges
        h_edges = [e for e in edges if e['orientation'] == 'h']
        v_edges = [e for e in edges if e['orientation'] == 'v']

        print(f"  水平边缘: {len(h_edges)}条")
        print(f"  垂直边缘: {len(v_edges)}条")

        # 显示前5条
        if h_edges:
            print(f"\n  水平边缘样例（前5条）:")
            for i, edge in enumerate(h_edges[:5]):
                print(f"    [{i}] ({edge['x0']:.2f}, {edge['y0']:.2f}) → ({edge['x1']:.2f}, {edge.get('y1', edge['y0']):.2f})")

        if v_edges:
            print(f"\n  垂直边缘样例（前5条）:")
            for i, edge in enumerate(v_edges[:5]):
                print(f"    [{i}] ({edge['x0']:.2f}, {edge['y0']:.2f}) → ({edge.get('x1', edge['x0']):.2f}, {edge['y1']:.2f})")

        print()


def is_contained(inner_bbox, outer_bbox, tolerance=5.0):
    """
    检查inner_bbox是否完全包含在outer_bbox内

    Args:
        inner_bbox: (x0, y0, x1, y1)
        outer_bbox: (x0, y0, x1, y1)
        tolerance: 容差（点）
    """
    ix0, iy0, ix1, iy1 = inner_bbox
    ox0, oy0, ox1, oy1 = outer_bbox

    return (ix0 >= ox0 - tolerance and
            iy0 >= oy0 - tolerance and
            ix1 <= ox1 + tolerance and
            iy1 <= oy1 + tolerance)


def find_containing_cells(table, target_bbox, overlap_threshold=0.8):
    """
    找到包含目标bbox的单元格

    Args:
        table: pdfplumber Table对象
        target_bbox: 目标bbox (x0, y0, x1, y1)
        overlap_threshold: 重叠阈值（相对于目标bbox的面积）
    """
    cells = table.cells
    if not cells:
        return []

    matching_cells = []
    target_area = (target_bbox[2] - target_bbox[0]) * (target_bbox[3] - target_bbox[1])

    for cell_bbox in cells:
        # 计算重叠面积
        overlap = calculate_overlap(cell_bbox, target_bbox)
        overlap_ratio = overlap / target_area if target_area > 0 else 0

        if overlap_ratio >= overlap_threshold:
            matching_cells.append(cell_bbox)

    return matching_cells


def calculate_overlap(bbox1, bbox2):
    """计算两个bbox的重叠面积"""
    x0 = max(bbox1[0], bbox2[0])
    y0 = max(bbox1[1], bbox2[1])
    x1 = min(bbox1[2], bbox2[2])
    y1 = min(bbox1[3], bbox2[3])

    if x1 <= x0 or y1 <= y0:
        return 0.0

    return (x1 - x0) * (y1 - y0)


def main():
    # 设置UTF-8编码（只设置一次）
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    pdf1 = r"E:\programFile\AIProgram\docxServer\pdf\task\1979102567573037058\table.pdf"
    pdf2 = r"E:\programFile\AIProgram\docxServer\pdf\task\1979102567573037058\真正的嵌套表格-示例.pdf"

    print("\n" + "="*80)
    print("嵌套表格诊断：bbox包含关系分析")
    print("="*80)

    # 分析两个PDF
    analyze_table_containment(pdf1, page_num=0)
    analyze_table_containment(pdf2, page_num=0)

    print("\n" + "="*80)
    print("[总结]")
    print("="*80)
    print("""
关键发现：
1. 嵌套表格必须满足：小表格的bbox完全包含在父表格的某个单元格内
2. pdfplumber能检测到多个独立表格（基于edges边缘）
3. 复合表格：外层表格检测正常，但内部子区域没有形成独立表格边界
4. 下一步：需要在大单元格内强制使用within_bbox再次检测
    """)


if __name__ == "__main__":
    main()