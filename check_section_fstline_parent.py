"""
检查招标文档中不合理的父子关系：section的父节点是fstline
这种关系是不合理的，因为section不应该是fstline的子节点
"""
import json
from pathlib import Path
from typing import List, Dict, Any

# 基础路径
BASE_DIR = Path(r"E:\models\data\Section\tender_document\runs\20251218_141436_checkpoint-3000_096b7b")
ENRICHED_DIR = BASE_DIR / "enriched"

# 需要检查的文件（stage1/2/3都为true的文件）
FILES_TO_CHECK = [
    "[GMCG2023000147-A]五所幼儿园办公家具、班级及功能室家具.json",
    "[GMCG2024000197-A]玉塘社区医院家具及医疗家具项目.json",
    "[GMCG2025000093-A]深圳市光明区楼村第二学校宿舍家具、餐厅家具及其他家具.json",
    "[家具违规]深圳市公安局光明分局将石派出所家具购置_abf11c6b-38e2-43e3-bf87-0da8bf47f4e8.json",
    "初稿-深圳市中医院光明院区办公类家具项目.json",
    "深圳市文化广电旅游体育局深圳市青少年足球训练基地办公家具项目采购.json",
    "深圳市中医院实验类家具采购1030.json",
    "特殊模板_宝安区政府采购货物类项目采购申报书.json",
]


def check_section_fstline_relation(file_path: Path) -> List[Dict[str, Any]]:
    """
    检查文件中section父节点为fstline的不合理关系

    返回: 包含问题元素信息的列表
    """
    issues = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 遍历所有元素
        for idx, element in enumerate(data):
            element_type = element.get('type', '')
            parent_id = element.get('parent_id', '')

            # 如果当前元素是section
            if element_type == 'section':
                # 查找父节点
                parent_element = None
                for parent_candidate in data:
                    if parent_candidate.get('element_id', '') == parent_id:
                        parent_element = parent_candidate
                        break

                # 如果父节点是fstline，记录这个问题
                if parent_element and parent_element.get('type', '') == 'fstline':
                    issues.append({
                        'element_id': element.get('element_id', ''),
                        'element_type': element_type,
                        'parent_id': parent_id,
                        'parent_type': parent_element.get('type', ''),
                        'text': element.get('text', '')[:100],  # 只显示前100个字符
                        'page_idx': element.get('page_idx', ''),
                        'index_in_file': idx,
                    })

    except Exception as e:
        print(f"处理文件 {file_path.name} 时出错: {e}")

    return issues


def main():
    """主函数"""
    print("=" * 80)
    print("检查 section → fstline 不合理父子关系")
    print("=" * 80)
    print()

    total_issues = 0

    for filename in FILES_TO_CHECK:
        file_path = ENRICHED_DIR / filename

        if not file_path.exists():
            print(f"[警告] 文件不存在: {filename}")
            continue

        print(f"[检查文件] {filename}")
        issues = check_section_fstline_relation(file_path)

        if issues:
            print(f"   [发现问题] {len(issues)} 个:")
            for issue in issues:
                print(f"      - element_id: {issue['element_id']}")
                print(f"        类型: {issue['element_type']} -> 父类型: {issue['parent_type']}")
                print(f"        页码: {issue['page_idx']}, 索引: {issue['index_in_file']}")
                print(f"        文本: {issue['text']}")
                print()
            total_issues += len(issues)
        else:
            print(f"   [OK] 未发现问题")

        print()

    print("=" * 80)
    print(f"总结: 共发现 {total_issues} 个不合理的 section → fstline 关系")
    print("=" * 80)


if __name__ == "__main__":
    main()
