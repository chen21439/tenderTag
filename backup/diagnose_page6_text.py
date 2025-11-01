"""
诊断第6页序号列文本位置
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import fitz

def diagnose_text_location():
    """
    诊断第6页序号列的文本实际位置
    """
    pdf_path = r"E:\programFile\AIProgram\docxServer\pdf\task\1978018096320905217\1978018096320905217.pdf"

    doc = fitz.open(pdf_path)
    page = doc[5]  # 第6页 (0-indexed)

    print(f"第6页分析")
    print(f"页面大小: {page.rect}")
    print()

    # 原始 bbox (跨页)
    original_bbox = (33.601423097625, -1423.0049125751245, 108.622351003875, 4392.017251294126)
    print(f"原始跨页 bbox: {original_bbox}")
    print(f"  x0={original_bbox[0]:.2f}, y0={original_bbox[1]:.2f}")
    print(f"  x1={original_bbox[2]:.2f}, y1={original_bbox[3]:.2f}")
    print()

    # 测试1: 提取整页文本
    print("=" * 80)
    print("测试1: 提取整页文本")
    print("=" * 80)
    all_text = page.get_text("text")
    print(f"整页文本长度: {len(all_text)}")
    print(f"整页文本预览: '{all_text[:200]}'")
    print()

    # 测试2: 提取序号列范围的文本 (只看 x 范围，y 取整页)
    print("=" * 80)
    print("测试2: 提取序号列X范围的文本 (y=0~842)")
    print("=" * 80)
    col0_rect = fitz.Rect(33.60, 0.0, 108.62, 842.0)
    col0_text = page.get_text("text", clip=col0_rect)
    print(f"序号列范围文本长度: {len(col0_text)}")
    print(f"序号列范围文本: '{col0_text}'")
    print()

    # 测试3: 获取页面上所有文本块的位置
    print("=" * 80)
    print("测试3: 检查序号列范围内的文本块")
    print("=" * 80)
    blocks = page.get_text("dict")["blocks"]

    col0_x0 = 33.60
    col0_x1 = 108.62

    found_blocks = []
    for block in blocks:
        if block.get("type") == 0:  # 文本块
            bbox = block["bbox"]
            # 检查是否在序号列X范围内
            if bbox[0] >= col0_x0 and bbox[2] <= col0_x1:
                found_blocks.append({
                    "bbox": bbox,
                    "text": "".join(
                        span["text"]
                        for line in block.get("lines", [])
                        for span in line.get("spans", [])
                    )
                })

    print(f"找到 {len(found_blocks)} 个文本块在序号列范围内:")
    for i, block in enumerate(found_blocks):
        print(f"  块 {i+1}:")
        print(f"    bbox: {block['bbox']}")
        print(f"    text: '{block['text']}'")
    print()

    # 测试4: 提取去掉页脚后的区域 (y=0~812)
    print("=" * 80)
    print("测试4: 提取序号列X范围 + 去页脚 (y=0~812)")
    print("=" * 80)
    safe_rect = fitz.Rect(33.60, 0.0, 108.62, 812.0)
    safe_text = page.get_text("text", clip=safe_rect)
    print(f"安全区域文本长度: {len(safe_text)}")
    print(f"安全区域文本: '{safe_text}'")
    print()

    # 测试5: 检查是否有文本在页脚区域 (y=812~842)
    print("=" * 80)
    print("测试5: 检查序号列的页脚区域 (y=812~842)")
    print("=" * 80)
    footer_rect = fitz.Rect(33.60, 812.0, 108.62, 842.0)
    footer_text = page.get_text("text", clip=footer_rect)
    print(f"页脚区域文本长度: {len(footer_text)}")
    print(f"页脚区域文本: '{footer_text}'")
    print()

    # 结论
    print("=" * 80)
    print("结论:")
    print("=" * 80)
    if col0_text:
        print(f"✓ 序号列范围内有文本: '{col0_text.strip()}'")
        if not safe_text and footer_text:
            print(f"✗ 问题: 文本在页脚区域被过滤掉了")
        elif not safe_text:
            print(f"? 奇怪: 整列有文本但安全区域没有")
    else:
        print(f"✗ 序号列范围内没有文本")
        print(f"  可能原因:")
        print(f"    1. 文本不在这个X范围内")
        print(f"    2. 文本在其他页面")
        print(f"    3. bbox 坐标本身有问题")

    doc.close()

if __name__ == '__main__':
    diagnose_text_location()