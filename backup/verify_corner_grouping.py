"""
验证脚本：分析角点分组逻辑
对比 table.pdf 和嵌套示例的单元格角点分布
"""

import pdfplumber
from pathlib import Path
import sys
import io
from collections import defaultdict


def get_corners(bbox):
    """获取bbox的4个角点"""
    x0, y0, x1, y1 = bbox
    return [
        (round(x0, 2), round(y0, 2)),  # 左上
        (round(x1, 2), round(y0, 2)),  # 右上
        (round(x0, 2), round(y1, 2)),  # 左下
        (round(x1, 2), round(y1, 2))   # 右下
    ]


def analyze_corner_sharing(pdf_path: str, page_num: int = 0):
    """分析单元格的角点共享情况"""

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

        print(f"[1] pdfplumber 检测结果")
        print("-" * 80)
        print(f"检测到 {len(tables)} 个表格\n")

        # [2] 分析每个表格的单元格
        print(f"[2] 表格单元格分析")
        print("-" * 80)

        all_corners = []  # 所有角点
        table_cells_corners = []  # 每个表格的单元格角点

        for table_idx, table in enumerate(tables):
            cells = table.cells
            print(f"\n表格[{table_idx}]:")
            print(f"  bbox: {table.bbox}")
            print(f"  单元格数: {len(cells)}")

            cells_corners = []
            for cell_idx, cell_bbox in enumerate(cells):
                corners = get_corners(cell_bbox)
                cells_corners.append({
                    'cell_idx': cell_idx,
                    'bbox': cell_bbox,
                    'corners': corners
                })
                all_corners.extend(corners)

            table_cells_corners.append(cells_corners)

            # 显示前5个单元格的角点
            print(f"\n  前5个单元格的角点:")
            for i, cell_info in enumerate(cells_corners[:5]):
                bbox = cell_info['bbox']
                corners = cell_info['corners']
                print(f"    单元格[{i}]: bbox=({bbox[0]:.2f}, {bbox[1]:.2f}, {bbox[2]:.2f}, {bbox[3]:.2f})")
                print(f"              角点={corners}")

        # [3] 检查角点共享情况
        print(f"\n[3] 角点共享分析")
        print("-" * 80)

        # 统计角点出现次数
        corner_count = defaultdict(int)
        for corner in all_corners:
            corner_count[corner] += 1

        # 找出共享的角点（出现次数 > 1）
        shared_corners = {corner: count for corner, count in corner_count.items() if count > 1}

        print(f"总角点数（含重复）: {len(all_corners)}")
        print(f"唯一角点数: {len(corner_count)}")
        print(f"共享角点数: {len(shared_corners)}")

        if shared_corners:
            print(f"\n共享角点详情（出现次数 > 1）:")
            # 按出现次数排序
            sorted_shared = sorted(shared_corners.items(), key=lambda x: x[1], reverse=True)
            for corner, count in sorted_shared[:10]:  # 显示前10个
                print(f"  {corner}: 出现 {count} 次")

        # [4] 如果有多个表格，检查它们之间是否共享角点
        if len(tables) >= 2:
            print(f"\n[4] 跨表格角点共享检查")
            print("-" * 80)

            for i in range(len(tables)):
                for j in range(i + 1, len(tables)):
                    corners_i = set()
                    corners_j = set()

                    for cell_info in table_cells_corners[i]:
                        corners_i.update(cell_info['corners'])

                    for cell_info in table_cells_corners[j]:
                        corners_j.update(cell_info['corners'])

                    shared = corners_i.intersection(corners_j)

                    print(f"\n表格[{i}] vs 表格[{j}]:")
                    print(f"  表格[{i}] 角点数: {len(corners_i)}")
                    print(f"  表格[{j}] 角点数: {len(corners_j)}")
                    print(f"  共享角点数: {len(shared)}")

                    if shared:
                        print(f"  ❌ 两个表格共享 {len(shared)} 个角点（不应该！）")
                        print(f"  共享角点示例（前5个）:")
                        for corner in list(shared)[:5]:
                            print(f"    {corner}")
                    else:
                        print(f"  ✅ 两个表格不共享角点（正确的嵌套）")

        # [5] 分析坐标分布
        print(f"\n[5] 坐标分布分析")
        print("-" * 80)

        # 提取所有唯一的 X 和 Y 坐标
        x_coords = set()
        y_coords = set()
        for corner in corner_count.keys():
            x_coords.add(corner[0])
            y_coords.add(corner[1])

        x_sorted = sorted(x_coords)
        y_sorted = sorted(y_coords)

        print(f"唯一 X 坐标数: {len(x_sorted)}")
        print(f"唯一 Y 坐标数: {len(y_sorted)}")

        print(f"\nX 坐标分布（前10个）:")
        for x in x_sorted[:10]:
            print(f"  X = {x}")

        print(f"\nY 坐标分布（前10个）:")
        for y in y_sorted[:10]:
            print(f"  Y = {y}")

        # [6] 模拟 cells_to_tables 分组逻辑
        if len(tables) == 1:
            print(f"\n[6] 分组逻辑模拟")
            print("-" * 80)
            print("只有1个表格，无法验证分组逻辑")
            print("\n推测原因：")
            print("  所有单元格通过共享角点被分组到同一个表格")
            print("  即使内部有复杂布局，也因为角点连续而无法分离")
        else:
            print(f"\n[6] 分组逻辑验证")
            print("-" * 80)
            print(f"✅ pdfplumber 正确识别出 {len(tables)} 个独立表格")
            print("原因：不同表格的单元格不共享角点")

        print()


def compare_two_pdfs(pdf1_path: str, pdf2_path: str):
    """对比两个PDF的特征"""

    print("\n" + "="*80)
    print("对比分析：复合表格 vs 嵌套表格")
    print("="*80)

    # 分析两个PDF
    analyze_corner_sharing(pdf1_path, page_num=0)
    analyze_corner_sharing(pdf2_path, page_num=0)

    # 总结
    print("\n" + "="*80)
    print("[总结] 嵌套表格的判断特征")
    print("="*80)
    print("""
✅ 真正的嵌套表格（检测到 2+ 个表格）:
  1. 子表单元格的角点与父表单元格的角点不重合
  2. 使用独立的坐标系统（X/Y 坐标不同）
  3. pdfplumber 能检测到多个独立表格
  4. 跨表格角点共享数 = 0

❌ 复合表格（只检测到 1 个表格）:
  1. 内部单元格的角点与外层单元格的角点重合或连续
  2. 使用共享的坐标系统（X/Y 坐标相同）
  3. pdfplumber 只能检测到 1 个大表格
  4. 所有单元格通过共享角点被分组在一起

核心判断逻辑（pdfplumber 的 cells_to_tables）:
  - 如果两个单元格共享至少 1 个角点 → 属于同一个表格
  - 如果两个单元格不共享任何角点 → 属于不同表格
    """)


def main():
    # 设置UTF-8编码
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    pdf1 = r"E:\programFile\AIProgram\docxServer\pdf\task\1979102567573037058\table.pdf"
    pdf2 = r"E:\programFile\AIProgram\docxServer\pdf\task\1979102567573037058\真正的嵌套表格-示例.pdf"

    compare_two_pdfs(pdf1, pdf2)


if __name__ == "__main__":
    main()