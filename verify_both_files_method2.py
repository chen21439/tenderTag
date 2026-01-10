"""
验证两份文件都用方式2（左下转左上）是否都能正确裁剪
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
    print(f"\n{file_info['name']}:")

    with open(file_info['json'], 'r', encoding='utf-8') as f:
        elements = json.load(f)

    elem = [e for e in elements if e.get('page') == '0'][0]
    box = elem['box']
    text = elem['text']

    img = Image.open(file_info['image'])
    img_width, img_height = img.size

    # 方式2: 左下转左上
    x1, y1, x2, y2 = box
    crop_coords = (x1, img_height - y2, x2, img_height - y1)

    print(f"  JSON text: {text}")
    print(f"  box: {box}")
    print(f"  裁剪坐标(左下转左上): {crop_coords}")

    cropped = img.crop(crop_coords)
    crop_path = output_dir / f"{file_info['name']}_方式2裁剪.png"
    cropped.save(crop_path)

    print(f"  已保存: {crop_path.name}")

print("\n请查看两个裁剪图片，看是否都正确")
