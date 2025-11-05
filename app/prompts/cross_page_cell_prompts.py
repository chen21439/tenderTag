"""
跨页单元格分类提示词
"""

# 行级别系统提示词
ROW_SYSTEM_PROMPT = """你是一个专业的PDF表格分析专家，擅长判断跨页行内容是否被分页符截断。

你的任务：
判断两行数据是否是"表格中同一行被分页截断"，只关注行内容本身的连续性。

输入数据格式：
- 上页最后一行：多个单元格的内容（c0, c1, c2...表示列）
- 下页第一行：多个单元格的内容（c0, c1, c2...表示列）

输出格式要求：
1. 必须使用 ```json 代码块包裹
2. 格式如下：

```json
{
    "should_merge": true,
    "confidence": 0.95,
    "reason": "c0列内容明显被截断，应该合并"
}
```

**重要**：必须使用 ```json 代码块格式，不要输出其他内容。
"""


# 批量判断的用户提示词模板
BATCH_ROW_USER_PROMPT_TEMPLATE = """请分析以下跨页表格的行对，判断每一对是否应该合并：

{row_pairs_content}

请对每一对行输出 JSON 格式的判断结果，返回一个 JSON 数组。

**输出格式要求**：
1. 必须使用 ```json 代码块包裹
2. **必须在输出中包含 pair_id 字段（从标题中的 ID 复制）用于匹配**
3. 格式如下：

```json
[
    {{
        "pair_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        "should_merge": true,
        "confidence": 0.95,
        "reason": "..."
    }},
    {{
        "pair_id": "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy",
        "should_merge": false,
        "confidence": 0.90,
        "reason": "..."
    }}
]
```

**重要**：
1. 必须使用 ```json 代码块格式，不要输出其他内容
2. 每个结果中必须包含 pair_id（从 "行对 X (ID: ...)" 中复制 UUID）
"""


def build_row_pair_content(pair_index: int, pair: dict, truncate_func) -> str:
    """
    构建单个行对的内容

    Args:
        pair_index: 行对索引（从1开始）
        pair: 行对数据
        truncate_func: 文本截断函数

    Returns:
        格式化的行对内容
    """
    import uuid

    # 生成或获取 UUID
    if 'pair_uuid' not in pair:
        pair['pair_uuid'] = str(uuid.uuid4())

    pair_uuid = pair['pair_uuid']
    content = f"## 行对 {pair_index} (ID: {pair_uuid})\n\n"

    # 上页最后一行（取最后3行）
    content += f"**上页最后一行**：\n"
    prev_row = pair.get('prev_row', {})
    for col, text in prev_row.items():
        # 将"第X列"转换为"cX"
        col_name = col.replace('第', 'c').replace('列', '') if '第' in col and '列' in col else col
        truncated = truncate_func(text, from_end=True)
        content += f"  - {col_name}: {truncated}\n"

    # 下页第一行（取最前3行）
    content += f"\n**下页第一行**：\n"
    next_row = pair.get('next_row', {})
    for col, text in next_row.items():
        # 将"第X列"转换为"cX"
        col_name = col.replace('第', 'c').replace('列', '') if '第' in col and '列' in col else col
        truncated = truncate_func(text, from_end=False)
        content += f"  - {col_name}: {truncated}\n"

    content += "\n" + "-" * 60 + "\n\n"

    return content


def build_batch_row_prompt(row_pairs: list, truncate_func) -> str:
    """
    构建批量行对判断的用户提示词

    Args:
        row_pairs: 行对列表
        truncate_func: 文本截断函数

    Returns:
        完整的用户提示词
    """
    # 构建所有行对的内容
    row_pairs_content = ""
    for i, pair in enumerate(row_pairs, start=1):
        row_pairs_content += build_row_pair_content(i, pair, truncate_func)

    # 使用模板
    return BATCH_ROW_USER_PROMPT_TEMPLATE.format(
        row_pairs_content=row_pairs_content
    )