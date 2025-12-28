#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import sys

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 标准标签集
standard_labels = {
    "采购包",
    "项目基本信息",
    "投标人资格条件",
    "采购需求",
    "商务要求",
    "投标文件格式",
    "投标报价要求",
    "评审办法",
    "拟签订的合同文本",
    "投标人应当提供的资格、资信证明文件",
    "废标条款",
    "定标",
    "政府采购政策功能",
    "答疑会、现场考察",
}

# 获取两个任务的标签
def get_labels(task_id):
    # 使用正确的 API 路径
    url = f"http://localhost:9801/python/api/pdf/task/{task_id}/result?result_type=ontology"
    try:
        response = requests.get(url)
        result = response.json()
        # 数据在 data.dataList 中
        data = result.get('data', {})
        data_list = data.get('dataList', [])

        # 递归提取所有节点的 label
        labels = set()

        def extract_labels(nodes):
            for node in nodes:
                if node.get('label') and node['label'].strip():
                    labels.add(node['label'].strip())
                # 递归处理子节点
                if 'children' in node and node['children']:
                    extract_labels(node['children'])

        extract_labels(data_list)
        return labels
    except Exception as e:
        print(f"Error fetching {task_id}: {e}")
        return set()

# 获取两个任务的标签
labels_1 = get_labels("25121719540659434569")
labels_2 = get_labels("25120110030711023313")

print("=" * 60)
print("标准标签集 ({}个):".format(len(standard_labels)))
print("=" * 60)
for label in sorted(standard_labels):
    print("  {}".format(label))

print("\n" + "=" * 60)
print("任务 25121719540659434569 的标签 ({}个):".format(len(labels_1)))
print("=" * 60)
for label in sorted(labels_1):
    print("  {}".format(label))

print("\n" + "=" * 60)
print("任务 25120110030711023313 的标签 ({}个):".format(len(labels_2)))
print("=" * 60)
for label in sorted(labels_2):
    print("  {}".format(label))

print("\n" + "=" * 60)
print("标签集比较分析:")
print("=" * 60)

# 标准集 - 任务1 (标准集中有但任务1没有的)
missing_in_1 = standard_labels - labels_1
print("\n标准集中有但任务1缺失的标签 ({}个):".format(len(missing_in_1)))
for label in sorted(missing_in_1):
    print("  [X] {}".format(label))

# 标准集 - 任务2 (标准集中有但任务2没有的)
missing_in_2 = standard_labels - labels_2
print("\n标准集中有但任务2缺失的标签 ({}个):".format(len(missing_in_2)))
for label in sorted(missing_in_2):
    print("  [X] {}".format(label))

# 任务1 - 标准集 (任务1独有的标签)
extra_in_1 = labels_1 - standard_labels
print("\n任务1独有的标签(不在标准集中) ({}个):".format(len(extra_in_1)))
for label in sorted(extra_in_1):
    print("  [+] {}".format(label))

# 任务2 - 标准集 (任务2独有的标签)
extra_in_2 = labels_2 - standard_labels
print("\n任务2独有的标签(不在标准集中) ({}个):".format(len(extra_in_2)))
for label in sorted(extra_in_2):
    print("  [+] {}".format(label))

# 两个任务都有但标准集没有的
both_have = labels_1 & labels_2 - standard_labels
print("\n两个任务都有但标准集没有的标签 ({}个):".format(len(both_have)))
for label in sorted(both_have):
    print("  [*] {}".format(label))

# 任务1有但任务2没有的
only_in_1 = labels_1 - labels_2
print("\n只在任务1中出现的标签 ({}个):".format(len(only_in_1)))
for label in sorted(only_in_1):
    print("  [1] {}".format(label))

# 任务2有但任务1没有的
only_in_2 = labels_2 - labels_1
print("\n只在任务2中出现的标签 ({}个):".format(len(only_in_2)))
for label in sorted(only_in_2):
    print("  [2] {}".format(label))

print("\n" + "=" * 60)
print("汇总:")
print("=" * 60)
print("标准标签集: {} 个".format(len(standard_labels)))
print("任务1标签: {} 个".format(len(labels_1)))
print("任务2标签: {} 个".format(len(labels_2)))
print("所有标签并集: {} 个".format(len(standard_labels | labels_1 | labels_2)))
