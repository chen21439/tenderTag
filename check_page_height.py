"""
检查两份PDF的页面高度是否一致
"""
from PIL import Image

files = [
    {
        "name": "玉塘社区医院",
        "image": r"E:\models\data\Section\tender_document\images\_GMCG2024000197-A_玉塘社区医院家具及医疗家具项目\0.png",
    },
    {
        "name": "泉州实验小学",
        "image": r"E:\models\data\Section\tender_document\images\泉州市实验小学足球场人造草坪采购项目\0.png",
    },
]

print("PDF页面高度对比:\n")

for file_info in files:
    img = Image.open(file_info['image'])
    print(f"{file_info['name']}:")
    print(f"  PNG尺寸: {img.width} x {img.height}")
    print(f"  高度: {img.height}")
    print()

print("注意：PNG高度可能和PDF高度不完全一致")
print("从日志看，泉州PDF高度是 841.90002441")
