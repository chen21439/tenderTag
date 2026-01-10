"""
将泉州文件的box从左下坐标系转换为左上坐标系
"""
import json
from pathlib import Path

# 文件路径
enriched_file = Path(r"E:\models\data\Section\tender_document\runs\20251218_141436_checkpoint-3000_096b7b\enriched\泉州市实验小学足球场人造草坪采购项目.json")
image_file = Path(r"E:\models\data\Section\tender_document\images\泉州市实验小学足球场人造草坪采购项目\0.png")

# 获取页面高度
from PIL import Image
img = Image.open(image_file)
page_height = img.height

print(f"页面高度: {page_height}")
print(f"处理文件: {enriched_file.name}\n")

# 读取JSON
with open(enriched_file, 'r', encoding='utf-8') as f:
    elements = json.load(f)

# 转换所有元素的box
converted_count = 0
for elem in elements:
    box = elem.get('box', [])
    if len(box) == 4:
        x1, y1, x2, y2 = box

        # 左下 -> 左上转换
        new_y1 = page_height - y2
        new_y2 = page_height - y1

        elem['box'] = [x1, new_y1, x2, new_y2]
        converted_count += 1

        if converted_count <= 3:
            print(f"元素 {elem.get('id', '?')}:")
            print(f"  text: {elem.get('text', '')[:40]}")
            print(f"  原始box: [{x1}, {y1}, {x2}, {y2}]")
            print(f"  转换后:  [{x1}, {new_y1}, {x2}, {new_y2}]")
            print()

# 保存转换后的文件
backup_file = enriched_file.with_suffix('.json.backup')
enriched_file.rename(backup_file)
print(f"备份原文件: {backup_file.name}")

with open(enriched_file, 'w', encoding='utf-8') as f:
    json.dump(elements, f, ensure_ascii=False, indent=2)

print(f"✅ 转换完成！共转换 {converted_count} 个元素")
print(f"   保存到: {enriched_file.name}")
