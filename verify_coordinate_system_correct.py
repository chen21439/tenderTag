"""
正确的坐标系验证方法：
不做任何转换，直接在原始坐标上标注，看哪个正确
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw

files = [
    {
        "name": "玉塘社区医院",
        "json": r"E:\models\data\Section\tender_document\test\[GMCG2024000197-A]玉塘社区医院家具及医疗家具项目.json",
        "image": r"E:\models\data\Section\tender_document\images\_GMCG2024000197-A_玉塘社区医院家具及医疗家具项目\0.png",
    },
    {
        "name": "泉州实验小学",
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

    page_0 = [e for e in elements if e.get('page') == '0'][:3]

    # 读取图片
    img = Image.open(file_info['image'])
    img_width, img_height = img.size

    print(f"  图片尺寸: {img_width} x {img_height}")
    print(f"  检查前3个元素:")

    # 创建两张图：一张用原始坐标，一张用翻转坐标
    img_original = img.copy()
    img_flipped = img.copy()

    draw_orig = ImageDraw.Draw(img_original)
    draw_flip = ImageDraw.Draw(img_flipped)

    for idx, elem in enumerate(page_0):
        box = elem.get('box', [])
        if len(box) != 4:
            continue

        x1, y1, x2, y2 = box
        text = elem.get('text', '')[:20]

        print(f"\n  [{idx}] box={box}")
        print(f"       text={text}")

        # 方案1: 直接使用原始坐标（假设是左上坐标系）
        draw_orig.rectangle([x1, y1, x2, y2], outline='red', width=3)

        # 方案2: Y轴翻转（假设是左下坐标系，转换到Canvas左上）
        flip_y1 = img_height - y2
        flip_y2 = img_height - y1
        draw_flip.rectangle([x1, flip_y1, x2, flip_y2], outline='blue', width=3)

    # 保存两张图
    img_original.save(output_dir / f"{file_info['name']}_原始坐标.png")
    img_flipped.save(output_dir / f"{file_info['name']}_翻转坐标.png")

    print(f"\n  已保存:")
    print(f"    {file_info['name']}_原始坐标.png (假设是左上坐标系)")
    print(f"    {file_info['name']}_翻转坐标.png (假设是左下坐标系)")

print("\n\n" + "="*70)
print("验证方法：")
print("  如果【原始坐标.png】正确 -> 数据是左上坐标系")
print("  如果【翻转坐标.png】正确 -> 数据是左下坐标系")
print("="*70)
