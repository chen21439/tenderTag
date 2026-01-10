"""
调试box的实际格式
尝试不同的理解方式
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw

# 只看玉塘第一个元素
json_file = r"E:\models\data\Section\tender_document\test\[GMCG2024000197-A]玉塘社区医院家具及医疗家具项目.json"
image_file = r"E:\models\data\Section\tender_document\images\_GMCG2024000197-A_玉塘社区医院家具及医疗家具项目\0.png"

with open(json_file, 'r', encoding='utf-8') as f:
    elements = json.load(f)

# 第一个元素
elem = elements[0]
box = elem['box']
text = elem['text']

print(f"JSON数据:")
print(f"  text: {text}")
print(f"  box: {box}")
print()

# 读取图片
img = Image.open(image_file)
img_width, img_height = img.size

print(f"图片尺寸: {img_width} x {img_height}")
print()

# 尝试不同的box理解方式
interpretations = [
    {
        "name": "方式1: [x1, y1, x2, y2] 左上坐标系",
        "coords": (box[0], box[1], box[2], box[3])
    },
    {
        "name": "方式2: [x1, y1, x2, y2] 左下坐标系转左上",
        "coords": (box[0], img_height - box[3], box[2], img_height - box[1])
    },
    {
        "name": "方式3: [left, top, width, height]",
        "coords": (box[0], box[1], box[0] + box[2], box[1] + box[3])
    },
    {
        "name": "方式4: [x_center, y_center, width, height]",
        "coords": (box[0] - box[2]//2, box[1] - box[3]//2, box[0] + box[2]//2, box[1] + box[3]//2)
    },
]

output_dir = Path(r"E:\programFile\AIProgram\tender-tagger\pic")

for idx, interp in enumerate(interpretations):
    print(f"{interp['name']}")
    print(f"  裁剪坐标: {interp['coords']}")

    try:
        img_copy = img.copy()
        draw = ImageDraw.Draw(img_copy)

        # 绘制矩形
        draw.rectangle(interp['coords'], outline='red', width=3)

        # 保存
        output_path = output_dir / f"debug_box_方式{idx+1}.png"
        img_copy.save(output_path)

        # 裁剪
        cropped = img.crop(interp['coords'])
        crop_path = output_dir / f"debug_crop_方式{idx+1}.png"
        cropped.save(crop_path)

        print(f"  已保存: debug_box_方式{idx+1}.png 和 debug_crop_方式{idx+1}.png")
    except Exception as e:
        print(f"  失败: {e}")
    print()

print("请查看生成的图片，看哪个方式能正确框选到'招标文件信息'")
