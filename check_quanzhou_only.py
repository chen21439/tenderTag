"""
只检查泉州文件的坐标系
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw

json_path = Path(r"E:\models\data\Section\tender_document\test\泉州市实验小学足球场人造草坪采购项目.json")
image_dir = Path(r"E:\models\data\Section\tender_document\images\泉州市实验小学足球场人造草坪采购项目")
output_dir = Path(r"E:\programFile\AIProgram\tender-tagger\pic")

# 读取JSON
with open(json_path, 'r', encoding='utf-8') as f:
    elements = json.load(f)

# 只处理第0页
page_0_elements = [e for e in elements if e.get('page') == '0'][:5]

# 读取图片
image_path = image_dir / "0.png"
img = Image.open(image_path)
img_width, img_height = img.size
draw = ImageDraw.Draw(img)

print(f"泉州文件 - 第0页:")
print(f"  图片尺寸: {img_width} x {img_height}")
print(f"  元素数量: {len(page_0_elements)}")
print()

for idx, elem in enumerate(page_0_elements):
    box = elem.get('box', [])
    if len(box) != 4:
        continue

    x1, y1, x2, y2 = box
    text = elem.get('text', '')[:30]

    print(f"  [{idx}] box={box}")
    print(f"       text={text}")

    # 左下坐标系转换
    left_bottom_x1 = x1
    left_bottom_y1 = img_height - y2
    left_bottom_x2 = x2
    left_bottom_y2 = img_height - y1

    # 左上坐标系
    left_top_x1 = x1
    left_top_y1 = y1
    left_top_x2 = x2
    left_top_y2 = y2

    # 红色: 左下坐标系
    draw.rectangle([left_bottom_x1, left_bottom_y1, left_bottom_x2, left_bottom_y2], outline='red', width=3)

    # 蓝色: 左上坐标系
    draw.rectangle([left_top_x1, left_top_y1, left_top_x2, left_top_y2], outline='blue', width=2)

output_path = output_dir / "quanzhou_page0_check.png"
img.save(output_path)
print()
print(f"已保存: {output_path}")
print("红色框 = 左下坐标系假设")
print("蓝色框 = 左上坐标系假设")
