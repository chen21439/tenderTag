import json
from pathlib import Path

# 测试单个文件
filename = "[GMCG2023000147-A]五所幼儿园办公家具、班级及功能室家具.json"
infer_range = [0, 28]
enriched_file = Path(r"E:\models\data\Section\tender_document\runs\20251218_141436_checkpoint-3000_096b7b\enriched") / filename

# 读取文件
with open(enriched_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"原始数据: {len(data)} 个元素")

# 统计页码分布
from collections import Counter
page_counter = Counter(int(item['page']) for item in data if 'page' in item)
print(f"页码范围: {min(page_counter.keys())} - {max(page_counter.keys())}")
print(f"infer_range: {infer_range}")

# 过滤：保留 page 在 [start_page, end_page) 范围内的元素
start_page, end_page = infer_range
filtered_data = [item for item in data if 'page' in item and start_page <= int(item['page']) < end_page]

print(f"过滤后: {len(filtered_data)} 个元素")
print(f"删除了: {len(data) - len(filtered_data)} 个元素")

# 显示前几个和最后几个元素的 page 信息
print("\n前5个元素的page:")
for item in filtered_data[:5]:
    print(f"  line_id: {item['line_id']}, page: {item['page']}, text: {item['text'][:30]}")

print("\n最后5个元素的page:")
for item in filtered_data[-5:]:
    print(f"  line_id: {item['line_id']}, page: {item['page']}, text: {item['text'][:30]}")

# 写入文件
with open(enriched_file, 'w', encoding='utf-8') as f:
    json.dump(filtered_data, f, ensure_ascii=False, indent=2)
print("\n✓ 文件已更新")
