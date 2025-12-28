"""
在整个数据集中查找所有 section → fstline 的关系
帮助理解训练日志中显示的这7个样本来自哪里
"""
import json
from pathlib import Path
from typing import List, Dict, Any

# 扫描所有可能的数据目录
SEARCH_DIRS = [
    Path(r"E:\models\data\Section\tender_document\runs\20251218_141436_checkpoint-3000_096b7b\enriched"),
    Path(r"E:\models\data\Section\tender_document\test"),
    Path(r"E:\models\data\Section\tender_document"),
]


def check_section_fstline_in_file(file_path: Path) -> List[Dict[str, Any]]:
    """检查单个文件中的 section → fstline 关系"""
    issues = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 构建 element_id -> element 的映射，提高查找效率
        id_to_element = {elem.get('element_id', ''): elem for elem in data if 'element_id' in elem}

        # 遍历所有元素
        for idx, element in enumerate(data):
            element_type = element.get('type', '')
            parent_id = element.get('parent_id', '')

            # 如果当前元素是section且有parent_id
            if element_type == 'section' and parent_id:
                parent_element = id_to_element.get(parent_id)

                # 如果父节点是fstline，记录
                if parent_element and parent_element.get('type', '') == 'fstline':
                    issues.append({
                        'element_id': element.get('element_id', ''),
                        'parent_id': parent_id,
                        'text': element.get('text', '')[:80],
                        'page_idx': element.get('page_idx', ''),
                        'index': idx,
                    })

    except Exception as e:
        # 忽略无法解析的文件
        pass

    return issues


def scan_directory(directory: Path, max_depth=3, current_depth=0) -> Dict[str, List[Dict[str, Any]]]:
    """递归扫描目录查找JSON文件"""
    results = {}

    if not directory.exists() or current_depth > max_depth:
        return results

    try:
        for item in directory.iterdir():
            if item.is_file() and item.suffix == '.json':
                issues = check_section_fstline_in_file(item)
                if issues:
                    results[str(item)] = issues
            elif item.is_dir() and current_depth < max_depth:
                # 递归扫描子目录
                sub_results = scan_directory(item, max_depth, current_depth + 1)
                results.update(sub_results)
    except PermissionError:
        pass

    return results


def main():
    """主函数"""
    print("=" * 100)
    print("查找数据集中所有 section -> fstline 关系")
    print("=" * 100)
    print()

    all_results = {}

    for search_dir in SEARCH_DIRS:
        if not search_dir.exists():
            print(f"[跳过] 目录不存在: {search_dir}")
            continue

        print(f"[扫描] {search_dir}")
        results = scan_directory(search_dir)
        all_results.update(results)
        print(f"        找到 {len(results)} 个文件包含此关系")
        print()

    # 汇总结果
    print("=" * 100)
    print(f"汇总结果：共找到 {len(all_results)} 个文件包含 section -> fstline 关系")
    print("=" * 100)
    print()

    total_count = 0
    for file_path, issues in all_results.items():
        total_count += len(issues)
        print(f"\n文件: {Path(file_path).name}")
        print(f"路径: {file_path}")
        print(f"数量: {len(issues)} 个")
        print("-" * 100)

        for i, issue in enumerate(issues, 1):
            print(f"  [{i}] element_id: {issue['element_id']}")
            print(f"      parent_id: {issue['parent_id']}")
            print(f"      page_idx: {issue['page_idx']}, index: {issue['index']}")
            print(f"      text: {issue['text']}")
            print()

    print("=" * 100)
    print(f"总计: {total_count} 个 section -> fstline 关系")
    print("=" * 100)


if __name__ == "__main__":
    main()
