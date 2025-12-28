"""
为 JSON 文件中的元素正确设置 parent_id
建立层级关系：section -> title -> para/table/其他元素
"""
import json
from pathlib import Path
import sys

def populate_parent_ids(elements):
    """
    根据文档结构设置 parent_id

    层级规则：
    1. section: parent_id = null (顶级节点)
    2. title: parent_id = 最近的 section 的 line_id
    3. 其他元素: parent_id = 最近的 title 或 section 的 line_id
    """
    current_section = None
    current_title = None
    modified_count = 0

    for element in elements:
        class_type = element.get('class', '').lower()
        old_parent = element.get('parent_id')

        if class_type == 'section':
            # section 是顶级节点
            element['parent_id'] = None
            current_section = element['line_id']
            current_title = None  # 新的 section 重置 title

        elif class_type == 'title':
            # title 的父节点是最近的 section
            element['parent_id'] = current_section
            current_title = element['line_id']

        else:
            # 其他元素的父节点是最近的 title，如果没有 title 则是 section
            element['parent_id'] = current_title if current_title else current_section

        # 统计修改数量
        if old_parent != element.get('parent_id'):
            modified_count += 1

    return modified_count

def process_file(file_path):
    """处理单个 JSON 文件"""
    try:
        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 检查是否是数组
        if not isinstance(data, list):
            print(f"[SKIP] {file_path.name}: 不是 JSON 数组")
            return False

        # 设置 parent_id
        modified_count = populate_parent_ids(data)

        # 写回文件
        if modified_count > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"[OK] {file_path.name}: 更新了 {modified_count}/{len(data)} 个元素的 parent_id")
            return True
        else:
            print(f"[INFO] {file_path.name}: parent_id 已是最新，无需更新")
            return False

    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON 解析错误 {file_path.name}: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] 处理错误 {file_path.name}: {e}")
        return False

def process_directory(directory):
    """处理目录中的所有 JSON 文件"""
    dir_path = Path(directory)

    if not dir_path.exists():
        print(f"[ERROR] 目录不存在: {directory}")
        return

    print(f"扫描目录: {directory}\n")

    # 获取所有 JSON 文件
    json_files = list(dir_path.glob("*.json"))

    if not json_files:
        print("[WARN] 未找到 JSON 文件")
        return

    print(f"找到 {len(json_files)} 个 JSON 文件\n")

    # 处理每个文件
    updated_count = 0
    for json_file in sorted(json_files):
        if process_file(json_file):
            updated_count += 1

    print(f"\n{'='*60}")
    print(f"[DONE] 共更新 {updated_count}/{len(json_files)} 个文件")
    print(f"{'='*60}")

def main():
    """主函数"""
    if len(sys.argv) > 1:
        # 如果提供了路径参数，处理该路径
        target = sys.argv[1]
        target_path = Path(target)

        if target_path.is_file():
            # 处理单个文件
            print(f"处理单个文件: {target}\n")
            process_file(target_path)
        elif target_path.is_dir():
            # 处理目录
            process_directory(target)
        else:
            print(f"[ERROR] 无效的路径: {target}")
    else:
        # 默认目录
        default_dir = r"E:\models\data\Section\tender_document\runs\20251218_141436_checkpoint-3000_096b7b\enriched"
        process_directory(default_dir)

if __name__ == "__main__":
    main()
