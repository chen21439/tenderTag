"""
为所有元素添加 'is_meta' 和 'relation' 字段
- is_meta: 默认值为空字符串
- relation: 默认值为空字符串
"""
import json
from pathlib import Path

# 目标目录
TARGET_DIR = r"E:\models\data\Section\tender_document\runs\20251218_141436_checkpoint-3000_096b7b\enriched"

def add_meta_relation_fields(file_path):
    """为 JSON 文件中的所有元素添加 is_meta 和 relation 字段"""
    try:
        # 读取 JSON 文件
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 检查是否是数组
        if not isinstance(data, list):
            print(f"[SKIP] {file_path.name}: 不是 JSON 数组")
            return False

        # 为每个元素添加字段
        modified = False
        for item in data:
            if isinstance(item, dict):
                # 添加 is_meta 字段（默认空字符串）
                if 'is_meta' not in item:
                    item['is_meta'] = ""
                    modified = True
                # 如果已存在但是 false，也改为空字符串
                elif item.get('is_meta') == False:
                    item['is_meta'] = ""
                    modified = True

                # 添加 relation 字段（默认空字符串）
                if 'relation' not in item:
                    item['relation'] = ""
                    modified = True

        # 如果有修改，写回文件
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[OK] {file_path.name}: 已添加 is_meta 和 relation 字段（共 {len(data)} 个元素）")
            return True
        else:
            print(f"[INFO] {file_path.name}: 所有元素已有这些字段")
            return False

    except json.JSONDecodeError as e:
        print(f"[ERROR] 解析错误 {file_path.name}: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] 处理错误 {file_path.name}: {e}")
        return False

def main():
    target_path = Path(TARGET_DIR)

    # 检查目录是否存在
    if not target_path.exists():
        print(f"[ERROR] 目录不存在: {TARGET_DIR}")
        return

    print(f"扫描目录: {TARGET_DIR}\n")

    # 获取所有 JSON 文件（不递归）
    json_files = list(target_path.glob("*.json"))

    if not json_files:
        print("[WARN] 未找到 JSON 文件")
        return

    print(f"找到 {len(json_files)} 个 JSON 文件\n")

    # 处理每个文件
    updated_count = 0
    for json_file in sorted(json_files):
        if add_meta_relation_fields(json_file):
            updated_count += 1

    print(f"\n{'='*60}")
    print(f"[DONE] 共更新 {updated_count}/{len(json_files)} 个文件")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
