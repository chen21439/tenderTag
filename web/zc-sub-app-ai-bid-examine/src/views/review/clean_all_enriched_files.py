import json
from pathlib import Path

# 读取 metadata.jsonl
metadata_path = Path(r"E:\models\data\Section\tender_document\runs\20251218_141436_checkpoint-3000_096b7b\metadata.jsonl")
enriched_dir = Path(r"E:\models\data\Section\tender_document\runs\20251218_141436_checkpoint-3000_096b7b\enriched")

with open(metadata_path, 'r', encoding='utf-8') as f:
    metadata = json.load(f)

print("开始处理文件...\n")

# 处理每个文件
for item in metadata:
    filename = item['filename']
    infer_range = item.get('infer_range', [])

    # 如果 infer_range 为空，跳过
    if not infer_range or len(infer_range) != 2:
        print(f"跳过 {filename}: infer_range 为空或格式不正确")
        continue

    start_page, end_page = infer_range
    enriched_file = enriched_dir / filename

    # 检查文件是否存在
    if not enriched_file.exists():
        print(f"文件不存在: {filename}")
        continue

    # 读取文件
    with open(enriched_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 检查数据结构
    if not isinstance(data, list):
        print(f"跳过 {filename}: 数据格式不是列表")
        continue

    original_count = len(data)

    # 过滤：保留 page 在 [start_page, end_page) 范围内的元素
    filtered_data = [item for item in data if 'page' in item and start_page <= int(item['page']) < end_page]

    filtered_count = len(filtered_data)
    removed_count = original_count - filtered_count

    # 只有在需要删除元素时才写入
    if removed_count > 0:
        # 写回文件
        with open(enriched_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, ensure_ascii=False, indent=2)

        print(f"[已处理] {filename}")
        print(f"  范围: [{start_page}, {end_page}), 原始: {original_count}, 保留: {filtered_count}, 删除: {removed_count}")
    else:
        print(f"[无需处理] {filename}")
        print(f"  范围: [{start_page}, {end_page}), 元素数: {original_count}")

print("\n全部处理完成!")
