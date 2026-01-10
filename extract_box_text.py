"""
提取框选区域的图片
看看框到底框中了什么内容
"""
import json
from pathlib import Path
from PIL import Image

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
    print(f"\n{'='*80}")
    print(f"{file_info['name']}")
    print(f"{'='*80}\n")

    # 读取数据
    with open(file_info['json'], 'r', encoding='utf-8') as f:
        elements = json.load(f)

    page_0 = [e for e in elements if e.get('page') == '0'][:5]

    # 读取图片
    img = Image.open(file_info['image'])
    img_width, img_height = img.size

    print(f"图片尺寸: {img_width} x {img_height}\n")

    for idx, elem in enumerate(page_0):
        box = elem.get('box', [])
        if len(box) != 4:
            continue

        x1, y1, x2, y2 = box
        json_text = elem.get('text', '')

        print(f"[{idx}] JSON中的文本: {json_text}")
        print(f"     box: [{x1}, {y1}, {x2}, {y2}]")

        # 裁剪框选区域
        # PIL的crop参数是 (left, top, right, bottom)，使用左上坐标系
        try:
            cropped = img.crop((x1, y1, x2, y2))

            # 保存裁剪的小图
            crop_path = output_dir / f"{file_info['name']}_crop_{idx}.png"
            cropped.save(crop_path)

            print(f"     裁剪区域已保存: {crop_path.name}")
            print(f"     裁剪区域尺寸: {cropped.width} x {cropped.height}")

        except Exception as e:
            print(f"     裁剪失败: {e}")

        print()

print("\n" + "="*80)
print("请查看保存的裁剪图片，看看框选的是什么内容")
print(f"裁剪图片保存在: {output_dir}")
print("="*80)
