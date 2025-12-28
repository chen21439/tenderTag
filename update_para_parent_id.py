"""
更新 para 元素的 parent_id：
碰到 fstline 元素，继续向后找 para 元素：
- 第一个 para 的 parent_id 是 fstline 的 id
- 第二个 para 的 parent_id 是第一个 para 的 id
- 第三个 para 的 parent_id 是第二个 para 的 id
- 以此类推，形成链式关系
- para 元素外的其他元素 parent_id 设为空字符串
"""
import json
from pathlib import Path

# 目标目录
TARGET_DIR = r"E:\models\data\Section\tender_document\runs\20251218_141436_checkpoint-3000_096b7b\enriched"

def update_para_parent_id(file_path):
    """更新 JSON 文件中 para 元素的 parent_id"""
    try:
        # 读取 JSON 文件
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 检查是否是数组
        if not isinstance(data, list):
            print(f"[SKIP] {file_path.name}: 不是 JSON 数组")
            return False

        modified = False
        i = 0
        while i < len(data):
            current = data[i]

            # 检查当前元素是否为 fstline
            if current.get('class') == 'fstline':
                fstline_id = current.get('id')

                # 将 fstline 的 parent_id 设为空字符串
                if current.get('parent_id') != "":
                    current['parent_id'] = ""
                    modified = True

                # 向后查找所有连续的 para 元素
                j = i + 1
                prev_id = fstline_id  # 第一个 para 的 parent_id 是 fstline 的 id

                while j < len(data):
                    next_elem = data[j]

                    # 如果是 para 元素，设置 parent_id
                    if next_elem.get('class') == 'para':
                        old_parent_id = next_elem.get('parent_id')
                        new_parent_id = prev_id

                        if old_parent_id != new_parent_id:
                            next_elem['parent_id'] = new_parent_id
                            modified = True

                        # 更新 prev_id 为当前 para 的 id，供下一个 para 使用
                        prev_id = next_elem.get('id')
                        j += 1
                    else:
                        # 遇到非 para 元素，停止
                        break

                # 跳到处理后的位置
                i = j
            else:
                # 非 fstline 元素
                # 如果是 para 但没有被 fstline 处理，parent_id 设为空字符串
                if current.get('class') == 'para':
                    if current.get('parent_id') != "":
                        current['parent_id'] = ""
                        modified = True
                # 其他元素的 parent_id 也设为空字符串
                elif current.get('class') not in ['fstline', 'para']:
                    if current.get('parent_id') != "":
                        current['parent_id'] = ""
                        modified = True
                i += 1

        # 如果有修改，写回文件
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[OK] {file_path.name}: 已更新 para 元素的 parent_id")
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
        if update_para_parent_id(json_file):
            updated_count += 1

    print(f"\n{'='*60}")
    print(f"[DONE] 共更新 {updated_count}/{len(json_files)} 个文件")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
