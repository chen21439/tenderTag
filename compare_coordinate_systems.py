"""
对比两个文件的坐标系，检查是否使用了不同的坐标系统
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw

# 两个测试文件
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

def test_coordinate_system(name, json_path, image_path):
    """测试单个文件的坐标系"""
    print(f"\n{'='*60}")
    print(f"测试文件: {name}")
    print(f"{'='*60}")

    # 读取JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        elements = json.load(f)

    # 只取第0页的前3个元素
    page_0_elements = [e for e in elements if e.get('page') == '0'][:3]

    # 读取图片
    img = Image.open(image_path)
    img_width, img_height = img.size

    print(f"图片尺寸: {img_width} x {img_height}")
    print(f"\n检查前3个元素的坐标:")

    for idx, elem in enumerate(page_0_elements):
        box = elem.get('box', [])
        if len(box) != 4:
            continue

        x1, y1, x2, y2 = box
        text = elem.get('text', '')[:30]

        print(f"\n  元素 [{idx}]:")
        print(f"    box = {box}")
        print(f"    text = {text}")

        # 分析坐标特征
        print(f"\n    坐标分析:")
        print(f"      x1={x1}, y1={y1}, x2={x2}, y2={y2}")
        print(f"      宽度 = {x2 - x1}")
        print(f"      y2 - y1 = {y2 - y1}")

        # 判断是哪种坐标系
        # 左下坐标系：y1 < y2 (y向上为正)
        # 左上坐标系：y1 < y2 (y向下为正，但y1应该是top，小于y2)

        # 关键判断：看y坐标与图片高度的关系
        if y2 > img_height / 2:
            print(f"      y2={y2} > 图片高度一半({img_height/2:.0f}) -> 可能是左下坐标系")
        else:
            print(f"      y2={y2} < 图片高度一半({img_height/2:.0f}) -> 可能是左上坐标系")

        # 计算左下坐标系转换后的位置
        left_bottom_y1 = img_height - y2
        left_bottom_y2 = img_height - y1
        print(f"\n    如果是左下坐标系，转换后:")
        print(f"      Canvas top = {left_bottom_y1:.0f}")
        print(f"      Canvas bottom = {left_bottom_y2:.0f}")

        # 计算左上坐标系的位置
        print(f"\n    如果是左上坐标系:")
        print(f"      Canvas top = {y1}")
        print(f"      Canvas bottom = {y2}")


def create_comparison_image():
    """创建对比图，同时显示两种坐标系的结果"""

    for file_info in files:
        name = file_info["name"]
        json_path = Path(file_info["json"])
        image_path = Path(file_info["image"])

        # 读取数据
        with open(json_path, 'r', encoding='utf-8') as f:
            elements = json.load(f)

        page_0_elements = [e for e in elements if e.get('page') == '0'][:3]

        # 创建图片
        img = Image.open(image_path)
        img_width, img_height = img.size
        draw = ImageDraw.Draw(img)

        for idx, elem in enumerate(page_0_elements):
            box = elem.get('box', [])
            if len(box) != 4:
                continue

            x1, y1, x2, y2 = box

            # 左下坐标系（红色，粗线）
            lb_y1 = img_height - y2
            lb_y2 = img_height - y1
            draw.rectangle([x1, lb_y1, x2, lb_y2], outline='red', width=3)

            # 左上坐标系（蓝色，细线）
            draw.rectangle([x1, y1, x2, y2], outline='blue', width=2)

        output_path = output_dir / f"{name}_comparison.png"
        img.save(output_path)
        print(f"\n已保存对比图: {output_path}")


# 主程序
print("="*60)
print("对比两个文件的坐标系统")
print("="*60)

for file_info in files:
    test_coordinate_system(
        file_info["name"],
        file_info["json"],
        file_info["image"]
    )

print("\n\n" + "="*60)
print("生成对比图...")
print("="*60)
create_comparison_image()

print("\n\n" + "="*60)
print("分析完成！")
print("="*60)
print("\n说明:")
print("  红色框 = 假设是左下坐标系")
print("  蓝色框 = 假设是左上坐标系")
print("  正确的框应该完全覆盖文本")
