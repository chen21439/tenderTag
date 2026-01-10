"""
对比两份文件：都使用原始坐标（不翻转）绘制
这样可以清楚看到坐标系的差异
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

files = [
    {
        "name": "玉塘社区医院（旧数据）",
        "json": r"E:\models\data\Section\tender_document\test\[GMCG2024000197-A]玉塘社区医院家具及医疗家具项目.json",
        "image": r"E:\models\data\Section\tender_document\images\_GMCG2024000197-A_玉塘社区医院家具及医疗家具项目\0.png",
    },
    {
        "name": "泉州实验小学（新数据）",
        "json": r"E:\models\data\Section\tender_document\test\泉州市实验小学足球场人造草坪采购项目.json",
        "image": r"E:\models\data\Section\tender_document\images\泉州市实验小学足球场人造草坪采购项目\0.png",
    },
]

output_dir = Path(r"E:\programFile\AIProgram\tender-tagger\pic")

for file_info in files:
    print(f"\n处理: {file_info['name']}")

    # 读取数据
    with open(file_info['json'], 'r', encoding='utf-8') as f:
        elements = json.load(f)

    page_0 = [e for e in elements if e.get('page') == '0'][:5]  # 取前5个元素

    # 读取图片
    img = Image.open(file_info['image'])
    img_width, img_height = img.size
    draw = ImageDraw.Draw(img)

    print(f"  图片尺寸: {img_width} x {img_height}")
    print(f"  标注前5个元素:\n")

    for idx, elem in enumerate(page_0):
        box = elem.get('box', [])
        if len(box) != 4:
            continue

        x1, y1, x2, y2 = box
        text = elem.get('text', '')[:30]
        elem_type = elem.get('class', 'unknown')

        print(f"  [{idx}] {elem_type:<10} box={box}")
        print(f"       text={text}")

        # 直接使用原始坐标绘制（不做任何转换）
        draw.rectangle([x1, y1, x2, y2], outline='red', width=3)

        # 标注序号
        try:
            draw.text((x1, y1), f"{idx}", fill='green')
        except:
            pass

    # 保存
    output_path = output_dir / f"{file_info['name']}_原始坐标标注.png"
    img.save(output_path)
    print(f"\n  [OK] 已保存: {output_path.name}\n")

print("\n" + "="*70)
print("说明：")
print("  两份文件都使用原始坐标（box值直接绘制）")
print("  如果框正确覆盖文本 -> 数据是左上坐标系")
print("  如果框位置错误 -> 数据是左下坐标系")
print("="*70)
