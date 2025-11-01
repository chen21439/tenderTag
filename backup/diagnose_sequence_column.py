"""
诊断序号列丢失问题
"""
import sys
from pathlib import Path

# 添加项目根目录到sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import fitz
from app.utils.unTaggedPDF.footer_filter import FooterFilter, FooterConfig

def diagnose_sequence_column():
    """
    诊断第4页表格序号列为什么提取为空
    """
    pdf_path = r"E:\programFile\AIProgram\docxServer\pdf\task\鄂尔多斯市政府网站群集约化平台升级改造项目\鄂尔多斯市政府网站群集约化平台升级改造项目.pdf"

    # 打开PDF
    doc = fitz.open(pdf_path)
    page = doc[3]  # 第4页（0-indexed）

    print(f"页面高度: {page.rect.height}")
    print(f"页面宽度: {page.rect.width}")
    print()

    # 测试序号列单元格 bbox（Row 2, Col 0）
    # 从之前的分析，这个单元格的 bbox 是异常的
    abnormal_bbox = (33.60, 147.03, 108.62, 5962.06)

    print(f"异常 bbox: {abnormal_bbox}")
    print(f"  Y范围: {abnormal_bbox[1]:.2f} ~ {abnormal_bbox[3]:.2f}")
    print(f"  高度: {abnormal_bbox[3] - abnormal_bbox[1]:.2f}")
    print()

    # 初始化 FooterFilter
    footer_filter = FooterFilter(FooterConfig(mode="fixed", fixed_points=30.0))

    # 方法1：使用 FooterFilter 提取（当前实现）
    print("=" * 80)
    print("方法1：使用 FooterFilter（当前实现）")
    print("=" * 80)
    text_with_filter = footer_filter.extract_cell_text_safe(
        fitz_page=page,
        cell_bbox=abnormal_bbox,
        debug=True
    )
    print(f"提取的文本: '{text_with_filter}'")
    print(f"文本长度: {len(text_with_filter)}")
    print()

    # 方法2：直接裁剪到页面（修复前的方法）
    print("=" * 80)
    print("方法2：直接裁剪到页面（修复前）")
    print("=" * 80)
    page_rect = page.rect
    cell_rect = fitz.Rect(abnormal_bbox)
    clipped_rect = cell_rect & page_rect
    print(f"裁剪后 rect: {clipped_rect}")

    text_direct = page.get_text("text", clip=clipped_rect)
    text_direct = text_direct.replace('\n', '').replace('\r', '').strip()
    print(f"提取的文本: '{text_direct}'")
    print(f"文本长度: {len(text_direct)}")
    print()

    # 方法3：使用更小的 bbox（只在序号列的 X 范围内）
    print("=" * 80)
    print("方法3：使用精确的 bbox（X范围33~109, Y范围147~842）")
    print("=" * 80)
    precise_bbox = (33.60, 147.03, 108.62, 842.0)
    precise_rect = fitz.Rect(precise_bbox)
    text_precise = page.get_text("text", clip=precise_rect)
    text_precise = text_precise.replace('\n', '').replace('\r', '').strip()
    print(f"提取的文本: '{text_precise}'")
    print(f"文本长度: {len(text_precise)}")
    print()

    # 方法4：只搜索表格开始位置附近的文本
    print("=" * 80)
    print("方法4：只搜索表格第一行区域（Y范围147~180）")
    print("=" * 80)
    first_row_bbox = (33.60, 147.03, 108.62, 180.0)
    first_row_rect = fitz.Rect(first_row_bbox)
    text_first_row = page.get_text("text", clip=first_row_rect)
    text_first_row = text_first_row.replace('\n', '').replace('\r', '').strip()
    print(f"提取的文本: '{text_first_row}'")
    print(f"文本长度: {len(text_first_row)}")
    print()

    # 方法5：提取整个序号列区域的所有文本块（用于调试）
    print("=" * 80)
    print("方法5：提取序号列区域的所有文本块（dict模式）")
    print("=" * 80)
    blocks = page.get_text("dict", clip=fitz.Rect(33.60, 147.03, 108.62, 842.0))
    print(f"文本块数量: {len(blocks.get('blocks', []))}")
    for i, block in enumerate(blocks.get('blocks', [])[:5]):  # 只显示前5个
        if block.get('type') == 0:  # 文本块
            bbox = block.get('bbox', [])
            lines = block.get('lines', [])
            text_in_block = ""
            for line in lines:
                for span in line.get('spans', []):
                    text_in_block += span.get('text', '')
            print(f"  Block {i}: bbox={[f'{x:.1f}' for x in bbox]}, text='{text_in_block[:50]}'")
    print()

    doc.close()

if __name__ == '__main__':
    diagnose_sequence_column()