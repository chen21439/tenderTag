"""
对比分析两份文件的坐标系差异
找出为什么一个能正常高亮，一个不能
"""
import json
from pathlib import Path

# 旧数据（能正常高亮）
old_file = {
    "name": "玉塘社区医院（旧数据，能高亮）",
    "path": r"E:\models\data\Section\tender_document\test\[GMCG2024000197-A]玉塘社区医院家具及医疗家具项目.json",
    "image": r"E:\models\data\Section\tender_document\images\_GMCG2024000197-A_玉塘社区医院家具及医疗家具项目\0.png",
}

# 新数据（不能正常高亮）
new_file = {
    "name": "泉州实验小学（新数据，不能高亮）",
    "path": r"E:\models\data\Section\tender_document\test\泉州市实验小学足球场人造草坪采购项目.json",
    "image": r"E:\models\data\Section\tender_document\images\泉州市实验小学足球场人造草坪采购项目\0.png",
}

def analyze_coordinates(file_info):
    """分析坐标系特征"""
    print(f"\n{'='*70}")
    print(f"文件: {file_info['name']}")
    print(f"{'='*70}")

    with open(file_info['path'], 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 只分析第0页的前10个元素
    page_0 = [e for e in data if e.get('page') == '0'][:10]

    # 获取图片尺寸
    from PIL import Image
    img = Image.open(file_info['image'])
    img_width, img_height = img.size

    print(f"\n[图片尺寸] {img_width} x {img_height}")
    print(f"[元素总数] 第0页: {len([e for e in data if e.get('page') == '0'])}")
    print(f"\n分析前10个元素的坐标特征:\n")

    # 统计数据
    y_greater_than_half = 0  # y坐标大于图片高度一半的数量
    y_less_than_half = 0

    print(f"{'序号':<5} {'类型':<10} {'box':<30} {'y坐标分析':<30}")
    print("-" * 80)

    for idx, elem in enumerate(page_0):
        box = elem.get('box', [])
        if len(box) != 4:
            continue

        x1, y1, x2, y2 = box
        elem_type = elem.get('class', 'unknown')

        # 判断y坐标特征
        mid_y = (y1 + y2) / 2
        if mid_y > img_height / 2:
            y_analysis = f"y中点={mid_y:.0f} > {img_height/2:.0f} (下半)"
            y_greater_than_half += 1
        else:
            y_analysis = f"y中点={mid_y:.0f} < {img_height/2:.0f} (上半)"
            y_less_than_half += 1

        print(f"{idx:<5} {elem_type:<10} {str(box):<30} {y_analysis:<30}")

    print("\n" + "=" * 80)
    print(f"统计结果:")
    print(f"  y坐标在下半部分: {y_greater_than_half} 个")
    print(f"  y坐标在上半部分: {y_less_than_half} 个")

    # 判断坐标系
    if y_greater_than_half > y_less_than_half:
        print(f"\n[OK] 结论: 可能是【左下坐标系】（y值大 = 靠近页面顶部）")
    else:
        print(f"\n[!!] 结论: 可能是【左上坐标系】（y值小 = 靠近页面顶部）")

    return {
        'img_height': img_height,
        'y_greater': y_greater_than_half,
        'y_less': y_less_than_half
    }

# 分析两份文件
print("\n" + "开始对比分析..." + "\n")

old_result = analyze_coordinates(old_file)
new_result = analyze_coordinates(new_file)

# 总结对比
print("\n\n" + "="*80)
print("📋 对比总结")
print("="*80)

print(f"\n旧数据（能高亮）:")
print(f"  图片高度: {old_result['img_height']}")
print(f"  y坐标在下半: {old_result['y_greater']} 个")
print(f"  y坐标在上半: {old_result['y_less']} 个")
print(f"  推测坐标系: {'左下' if old_result['y_greater'] > old_result['y_less'] else '左上'}")

print(f"\n新数据（不能高亮）:")
print(f"  图片高度: {new_result['img_height']}")
print(f"  y坐标在下半: {new_result['y_greater']} 个")
print(f"  y坐标在上半: {new_result['y_less']} 个")
print(f"  推测坐标系: {'左下' if new_result['y_greater'] > new_result['y_less'] else '左上'}")

print("\n" + "="*80)
if (old_result['y_greater'] > old_result['y_less']) == (new_result['y_greater'] > new_result['y_less']):
    print("[?] 两份文件的坐标系特征相同，但高亮表现不同")
    print("   可能原因：")
    print("   1. needsConversion 处理逻辑有问题")
    print("   2. 图片高度不同导致转换计算不同")
    print("   3. quadPoints 构建方式有问题")
else:
    print("[!] 两份文件使用了不同的坐标系！")
    print("   解决方案：需要在代码中自动检测坐标系类型")
print("="*80)
