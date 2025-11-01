"""
测试修复前的提取方法能否提取到序号
"""
import sys
from pathlib import Path

# 添加项目根目录到sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import fitz

def extract_cell_text_before_fix(pymupdf_page, bbox: tuple) -> str:
    """
    修复前的提取方法（直接裁剪到页面范围）
    """
    # 获取页面有效区域
    page_rect = pymupdf_page.rect

    # 裁剪cell bbox到页面范围（使用PyMuPDF的官方方法）
    cell_rect = fitz.Rect(bbox)
    clipped_rect = cell_rect & page_rect  # 交集运算

    # 用裁剪后的rect提取文本
    text = pymupdf_page.get_text("text", clip=clipped_rect)

    # 移除所有换行符
    text = text.replace('\n', '').replace('\r', '')

    return text.strip()

def test_before_fix():
    """
    测试修复前的方法能否提取序号列
    """
    pdf_path = r"E:\programFile\AIProgram\docxServer\pdf\task\鄂尔多斯市政府网站群集约化平台升级改造项目\鄂尔多斯市政府网站群集约化平台升级改造项目.pdf"

    doc = fitz.open(pdf_path)
    page = doc[3]  # 第4页

    # 测试数据行序号列的 bbox（Row 2, Col 0）
    data_row_bbox = (33.6, 147.0, 108.6, 5962.1)

    print("修复前的提取方法:")
    print(f"  bbox: {data_row_bbox}")

    text = extract_cell_text_before_fix(page, data_row_bbox)

    print(f"  提取的文本: '{text}'")
    print(f"  文本长度: {len(text)}")
    print()

    # 对比：修复后的方法（使用 FooterFilter）
    from app.utils.unTaggedPDF.footer_filter import FooterFilter, FooterConfig

    footer_filter = FooterFilter(FooterConfig(mode="fixed", fixed_points=30.0))

    print("修复后的提取方法（使用 FooterFilter）:")
    print(f"  bbox: {data_row_bbox}")

    text_after = footer_filter.extract_cell_text_safe(
        fitz_page=page,
        cell_bbox=data_row_bbox,
        debug=False
    )

    print(f"  提取的文本: '{text_after}'")
    print(f"  文本长度: {len(text_after)}")
    print()

    # 结论
    if text and not text_after:
        print("[X] 结论: FooterFilter 导致序号丢失")
    elif not text and not text_after:
        print("[OK] 结论: 不是 FooterFilter 的问题，修复前也提取不到")
    elif text == text_after:
        print("[OK] 结论: 两种方法结果相同")
    else:
        print("[!] 结论: 两种方法结果不同")
        print(f"  修复前: '{text}'")
        print(f"  修复后: '{text_after}'")

    doc.close()

if __name__ == '__main__':
    test_before_fix()