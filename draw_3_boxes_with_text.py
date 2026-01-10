"""
用左下坐标系给两份文件画3个框，并提取框中的文字
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

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

    # 取前3个元素
    page_0_elements = [e for e in elements if e.get('page') == '0'][:3]

    # 读取图片
    img = Image.open(file_info['image'])
    img_width, img_height = img.size
    draw = ImageDraw.Draw(img)

    print(f"图片尺寸: {img_width} x {img_height}\n")

    # 为每个元素画框并提取文字
    for idx, elem in enumerate(page_0_elements):
        box = elem['box']
        json_text = elem['text']

        x1, y1, x2, y2 = box

        print(f"框 [{idx}]")
        print(f"  JSON中的text: {json_text}")
        print(f"  原始box(左下坐标系): [{x1}, {y1}, {x2}, {y2}]")

        # 左下坐标系转换为PIL的左上坐标系
        # box: [x1, y1, x2, y2] 其中 (x1,y1)=左下角, (x2,y2)=右上角
        # PIL需要: (left, top, right, bottom)
        left = x1
        top = img_height - y2    # 左下的y2(右上角的y) -> 左上的top
        right = x2
        bottom = img_height - y1  # 左下的y1(左下角的y) -> 左上的bottom

        crop_coords = (left, top, right, bottom)
        print(f"  转换为PIL坐标(left,top,right,bottom): {crop_coords}")

        # 画框
        draw.rectangle(crop_coords, outline='red', width=3)

        # 添加标签
        try:
            draw.text((left, top-15), f"[{idx}]", fill='blue')
        except:
            pass

        # 裁剪并保存小图
        try:
            cropped = img.crop(crop_coords)
            crop_path = output_dir / f"{file_info['name']}_框{idx}_裁剪.png"
            cropped.save(crop_path)
            print(f"  裁剪图保存: {crop_path.name}")
            print(f"  裁剪尺寸: {cropped.width} x {cropped.height}")
        except Exception as e:
            print(f"  裁剪失败: {e}")

        print()

    # 保存完整标注图
    output_path = output_dir / f"{file_info['name']}_左下坐标系_3个框.png"
    img.save(output_path)
    print(f"完整标注图保存: {output_path.name}\n")

print("="*80)
print("说明：")
print("  - 使用左下坐标系解析box")
print("  - 转换公式: top = img_height - y2, bottom = img_height - y1")
print("  - 请查看裁剪图片，看框中的文字是否和JSON中的text一致")
print("="*80)
