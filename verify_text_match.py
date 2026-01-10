"""
详细验证每个框是否真的对应上了文本
"""
import json
from pathlib import Path

files = [
    {
        "name": "玉塘社区医院",
        "json": r"E:\models\data\Section\tender_document\test\[GMCG2024000197-A]玉塘社区医院家具及医疗家具项目.json",
    },
    {
        "name": "泉州实验小学",
        "json": r"E:\models\data\Section\tender_document\test\泉州市实验小学足球场人造草坪采购项目.json",
    },
]

for file_info in files:
    print(f"\n{'='*70}")
    print(f"{file_info['name']}")
    print(f"{'='*70}")

    with open(file_info['json'], 'r', encoding='utf-8') as f:
        elements = json.load(f)

    page_0 = [e for e in elements if e.get('page') == '0'][:5]

    print(f"图片高度: 842 (已知)")
    print(f"\n前5个元素的详细信息：\n")

    for idx, elem in enumerate(page_0):
        box = elem.get('box', [])
        if len(box) != 4:
            continue

        x1, y1, x2, y2 = box
        text = elem.get('text', '')
        elem_type = elem.get('class', '')

        print(f"[{idx}] {elem_type}")
        print(f"    text: {text}")
        print(f"    box: [{x1}, {y1}, {x2}, {y2}]")
        print(f"    y1={y1}, y2={y2}")

        # 判断在页面的位置
        mid_y = (y1 + y2) / 2
        if mid_y < 842 / 3:
            position = "上部"
        elif mid_y < 842 * 2 / 3:
            position = "中部"
        else:
            position = "下部"

        print(f"    y中点={mid_y:.0f}, 位置判断: {position}")
        print()

print("\n" + "="*70)
print("请对照图片，检查每个框的位置是否和text、位置判断相符")
print("="*70)
