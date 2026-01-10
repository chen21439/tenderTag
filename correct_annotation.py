"""
正确的标注脚本：
直接使用box坐标 [x1, y1, x2, y2] 绘制矩形
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw

files = [
    {
        "name": "玉塘社区医院（旧数据-左上坐标系）",
        "json": r"E:\models\data\Section\tender_document\test\[GMCG2024000197-A]玉塘社区医院家具及医疗家具项目.json",
        "image": r"E:\models\data\Section\tender_document\images\_GMCG2024000197-A_玉塘社区医院家具及医疗家具项目\0.png",
    },
    {
        "name": "泉州实验小学（新数据-左下坐标系）",
        "json": r"E:\models\data\Section\tender_document\test\泉州市实验小学足球场人造草坪采购项目.json",
        "image": r"E:\models\data\Section\tender_document\images\泉州市实验小学足球场人造草坪采购项目\0.png",
    },
]

output_dir = Path(r"E:\programFile\AIProgram\tender-tagger\pic")

for file_info in files:
    print(f"\n{'='*70}")
    print(f"处理: {file_info['name']}")
    print(f"{'='*70}")

    # 读取数据
    with open(file_info['json'], 'r', encoding='utf-8') as f:
        elements = json.load(f)

    page_0 = [e for e in elements if e.get('page') == '0'][:5]

    # 读取图片
    img = Image.open(file_info['image'])
    img_width, img_height = img.size
    draw = ImageDraw.Draw(img)

    print(f"图片尺寸: {img_width} x {img_height}\n")

    for idx, elem in enumerate(page_0):
        box = elem.get('box', [])
        if len(box) != 4:
            continue

        x1, y1, x2, y2 = box
        text = elem.get('text', '')[:40]

        print(f"[{idx}] box=[{x1}, {y1}, {x2}, {y2}]")
        print(f"     text={text}")
        print(f"     直接绘制矩形: ({x1},{y1}) -> ({x2},{y2})")
        print()

        # 直接使用box的4个值绘制矩形
        # draw.rectangle([x1, y1, x2, y2])
        # 参数是 [left, top, right, bottom]
        draw.rectangle([x1, y1, x2, y2], outline='red', width=3)

    # 保存
    output_path = output_dir / f"{file_info['name']}_直接绘制.png"
    img.save(output_path)
    print(f"已保存: {output_path.name}\n")

print("\n" + "="*70)
print("说明:")
print("  直接使用 draw.rectangle([x1, y1, x2, y2])")
print("  如果是左上坐标系 -> 红框应该正确")
print("  如果是左下坐标系 -> 红框应该在错误位置（镜像翻转）")
print("="*70)
