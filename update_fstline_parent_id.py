"""
更新 fstline 元素的 parent_id：
将 class 为 fstline 的元素的 parent_id 设置为前一个 class 为 fstline 元素的 id
"""
import json
from pathlib import Path

# 目标目录
TARGET_DIR = r"E:\models\data\Section\tender_document\runs\20251218_141436_checkpoint-3000_096b7b\enriched"

def update_fstline_parent_id(file_path):
    """更新 JSON 文件中 fstline 元素的 parent_id"""
    try:
        # 读取 JSON 文件
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 检查是否是数组
        if not isinstance(data, list):
            print(f"[SKIP] {file_path.name}: 不是 JSON 数组")
            return False

        modified = False
        prev_fstline_id = None  # 记录前一个 fstline 的 id

        for item in data:
            if isinstance(item, dict):
                # 检查当前元素是否为 fstline
                if item.get('class') == 'fstline':
                    current_id = item.get('id')

                    # 如果有前一个 fstline，设置 parent_id
                    if prev_fstline_id is not None:
                        old_parent_id = item.get('parent_id')
                        new_parent_id = prev_fstline_id

                        if old_parent_id != new_parent_id:
                            item['parent_id'] = new_parent_id
                            modified = True
                    else:
                        # 第一个 fstline，parent_id 设为空字符串
                        if item.get('parent_id') != "":
                            item['parent_id'] = ""
                            modified = True

                    # 更新 prev_fstline_id 为当前 fstline 的 id
                    prev_fstline_id = current_id

        # 如果有修改，写回文件
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[OK] {file_path.name}: 已更新 fstline 元素的 parent_id")
            return True
        else:
            print(f"[INFO] {file_path.name}: 无需更新")
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
        if update_fstline_parent_id(json_file):
            updated_count += 1

    print(f"\n{'='*60}")
    print(f"[DONE] 共更新 {updated_count}/{len(json_files)} 个文件")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
