"""
检查JSON坐标系与图片的对应关系
验证box坐标是左下坐标系还是左上坐标系
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# 测试文件
TEST_FILES = [
    {
        "json": r"E:\models\data\Section\tender_document\test\[GMCG2024000197-A]玉塘社区医院家具及医疗家具项目.json",
        "image_dir": r"E:\models\data\Section\tender_document\images\_GMCG2024000197-A_玉塘社区医院家具及医疗家具项目",
    },
    {
        "json": r"E:\models\data\Section\tender_document\test\泉州市实验小学足球场人造草坪采购项目.json",
        "image_dir": r"E:\models\data\Section\tender_document\images\泉州市实验小学足球场人造草坪采购项目",
    },
]


def visualize_boxes(json_path: Path, image_dir: Path, output_dir: Path, max_elements=10):
    """
    在图片上绘制box坐标，验证坐标系

    Args:
        json_path: JSON文件路径
        image_dir: 图片目录路径
        output_dir: 输出目录
        max_elements: 每页最多绘制多少个元素
    """
    # 读取JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        elements = json.load(f)

    # 按页分组
    pages = {}
    for elem in elements:
        page_num = elem.get('page', '0')
        if page_num not in pages:
            pages[page_num] = []
        pages[page_num].append(elem)

    # 为每一页生成可视化
    for page_num in sorted(pages.keys(), key=lambda x: int(x)):
        page_elements = pages[page_num][:max_elements]  # 只取前N个元素

        # 读取对应页面的图片
        image_path = image_dir / f"{page_num}.png"
        if not image_path.exists():
            print(f"[警告] 图片不存在: {image_path}")
            continue

        img = Image.open(image_path)
        img_width, img_height = img.size
        draw = ImageDraw.Draw(img)

        print(f"\n第 {page_num} 页:")
        print(f"  图片尺寸: {img_width} x {img_height}")
        print(f"  元素数量: {len(page_elements)}")

        # 尝试两种坐标系绘制
        for idx, elem in enumerate(page_elements):
            box = elem.get('box', [])
            if len(box) != 4:
                continue

            x1, y1, x2, y2 = box
            text = elem.get('text', '')[:20]
            elem_type = elem.get('class', 'unknown')

            print(f"  [{idx}] type={elem_type}, box={box}, text={text}")

            # 方案1: 假设box是左下坐标系 (PDF标准)
            # (x1, y1) = 左下角, (x2, y2) = 右上角
            # 转换到图片坐标系（左上原点，y轴向下）
            left_bottom_x1 = x1
            left_bottom_y1 = img_height - y2  # 左下的y2对应图片的top
            left_bottom_x2 = x2
            left_bottom_y2 = img_height - y1  # 左下的y1对应图片的bottom

            # 方案2: 假设box是左上坐标系
            left_top_x1 = x1
            left_top_y1 = y1
            left_top_x2 = x2
            left_top_y2 = y2

            # 用不同颜色绘制两种方案
            # 红色: 左下坐标系假设
            draw.rectangle(
                [left_bottom_x1, left_bottom_y1, left_bottom_x2, left_bottom_y2],
                outline='red',
                width=2
            )

            # 蓝色: 左上坐标系假设
            draw.rectangle(
                [left_top_x1, left_top_y1, left_top_x2, left_top_y2],
                outline='blue',
                width=2
            )

            # 标注序号
            draw.text((x1, y1), f"{idx}", fill='green')

        # 保存结果
        output_path = output_dir / f"page_{page_num}_coordinate_check.png"
        img.save(output_path)
        print(f"  [OK] 已保存: {output_path}")
        print(f"     红色框 = 左下坐标系假设")
        print(f"     蓝色框 = 左上坐标系假设")
        print(f"     正确的框应该完全覆盖文本区域")


def main():
    output_dir = Path(r"E:\programFile\AIProgram\tender-tagger\pic")
    output_dir.mkdir(exist_ok=True)

    print("=" * 80)
    print("检查JSON坐标系与图片的对应关系")
    print("=" * 80)

    for test_file in TEST_FILES:
        json_path = Path(test_file["json"])
        image_dir = Path(test_file["image_dir"])

        print(f"\n处理文件: {json_path.name}")
        print(f"图片目录: {image_dir}")

        if not json_path.exists():
            print(f"[错误] JSON文件不存在: {json_path}")
            continue

        if not image_dir.exists():
            print(f"[错误] 图片目录不存在: {image_dir}")
            continue

        visualize_boxes(json_path, image_dir, output_dir, max_elements=5)

    print("\n" + "=" * 80)
    print(f"完成！可视化结果已保存到: {output_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()
