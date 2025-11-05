"""
Phase A: H1 全局探测提示词
用于识别文档中的一级标题（H1）候选
"""

SYSTEM_PROMPT = """你是文档结构化专家。请根据给定的"分块文本 + 相对版式特征"判断本篇文档的一级标题（H1）候选。你的任务仅输出 JSON，严禁任何解释性文字。

**输入格式**
每个 block 包含：
- block_id: 唯一标识
- text: 文本内容
- features: 相对版式特征
  - font_size_rank_pct: 字号分位数 [0,1]，越大字越大
  - is_bold: 是否加粗
  - is_centered: 是否居中
  - indent_level_norm: 缩进归一化值 [0,1]
  - upper_blank_ratio: 段前留白分位数 [0,1]
  - lower_blank_ratio: 段后留白分位数 [0,1]
  - line_len: 文本长度
  - numbering_tag: 编号标签（如"第一章"、"1."等）

**判断标准**
H1 通常具备以下特征（权重递减）：
1. 高优先级特征：
   - 包含明确章节编号（"第X章"、"第X节"等）
   - 字号显著大于正文（font_size_rank_pct > 0.8）
   - 居中对齐 (is_centered=true)
   - 文本简短（通常 < 30 字符）

2. 中优先级特征：
   - 加粗 (is_bold=true)
   - 段前/段后留白较大（upper_blank_ratio > 0.7 或 lower_blank_ratio > 0.7）
   - 无缩进或缩进很小（indent_level_norm < 0.2）

3. 排除规则：
   - 文本过长（> 50 字符）通常不是标题
   - 包含详细说明、条款内容的不是标题
   - 纯数字、日期、页码等不是标题

**输出格式（严格 JSON）**
必须使用 ```json 代码块包裹，格式如下：

```json
{
  "h1_candidates": [
    {
      "block_id": "D001_0001",
      "score": 0.95,
      "rationale_bullets": ["包含'第一章'编号", "字号最大", "居中对齐"]
    }
  ],
  "style_notes": "本文H1均包含章节编号，居中对齐，字号显著大于正文"
}
```

**注意事项**
- score 范围 [0,1]，>0.7 才输出为候选
- rationale_bullets 每条不超过 10 字
- 只返回高置信度的 H1 候选（通常不超过 20 个）
- 必须使用 ```json 代码块格式，不要输出其他内容"""


USER_PROMPT_TEMPLATE = """请分析以下文档块，识别一级标题（H1）候选：

```json
{blocks_json}
```

请严格按照 JSON 格式输出结果，不要有任何解释。"""


def generate_h1_detection_prompt(blocks_data: dict) -> tuple[str, str, dict]:
    """
    生成 H1 探测的完整提示词

    Args:
        blocks_data: 包含 blocks 列表的字典

    Returns:
        (system_prompt, user_prompt, uuid_mapping) 元组
        uuid_mapping: {uuid -> original_block_id} 的映射
    """
    import json
    import uuid

    # 可以选择性地过滤一些明显不是标题的块
    filtered_blocks = []
    uuid_mapping = {}  # uuid -> original_block_id

    for block in blocks_data.get("blocks", []):
        features = block.get("features", {})
        text = block.get("text", "")

        # 快速过滤：文本太长、字号太小的一般不是 H1
        if (len(text) > 100 or
            features.get("font_size_rank_pct", 0) < 0.3):
            continue

        # 生成 UUID 并保存映射
        original_block_id = block.get("block_id")
        block_uuid = str(uuid.uuid4())
        uuid_mapping[block_uuid] = original_block_id

        # 创建新的 block，使用 UUID 替换 block_id
        new_block = block.copy()
        new_block["block_id"] = block_uuid

        filtered_blocks.append(new_block)

    # 如果过滤后还是太多，可以进一步限制
    if len(filtered_blocks) > 100:
        # 只保留字号较大的前 100 个
        filtered_blocks.sort(
            key=lambda x: x.get("features", {}).get("font_size_rank_pct", 0),
            reverse=True
        )
        # 同时更新 uuid_mapping，移除被过滤掉的
        kept_uuids = {block["block_id"] for block in filtered_blocks[:100]}
        uuid_mapping = {k: v for k, v in uuid_mapping.items() if k in kept_uuids}
        filtered_blocks = filtered_blocks[:100]

    blocks_json = json.dumps(
        {"blocks": filtered_blocks},
        ensure_ascii=False,
        indent=2
    )

    user_prompt = USER_PROMPT_TEMPLATE.format(blocks_json=blocks_json)

    return SYSTEM_PROMPT, user_prompt, uuid_mapping


# 用于解析 AI 返回的 JSON 响应
def parse_h1_response(
    response_text: str,
    blocks_data: dict = None,
    uuid_mapping: dict = None
) -> dict:
    """
    解析 AI 返回的 H1 检测结果

    支持以下格式：
    1. ```json ... ``` 代码块（优先）
    2. 包含 <think>...</think> 标签的响应（移除后提取）
    3. 纯 JSON 文本

    Args:
        response_text: AI 返回的文本
        blocks_data: 原始 blocks 数据（用于补充 text 字段）
        uuid_mapping: {uuid -> original_block_id} 的映射（用于还原原始 ID）

    Returns:
        解析后的字典，包含 h1_candidates 和 style_notes
        每个 h1_candidate 包含: block_id (原始ID), score, rationale_bullets, text
    """
    import json
    import re

    # 方法1：尝试提取 ```json ... ``` 代码块
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1).strip()
        print(f"[parse_h1_response] 从 ```json``` 代码块中提取 JSON")
    else:
        # 方法2：移除 <think>...</think> 标签（如果存在）
        cleaned_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL).strip()

        # 方法3：尝试再次提取 JSON 对象（可能没有代码块标记）
        json_obj_match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
        if json_obj_match:
            json_str = json_obj_match.group(0).strip()
            print(f"[parse_h1_response] 从清理后的文本中提取 JSON 对象")
        else:
            # 直接使用清理后的文本
            json_str = cleaned_text
            print(f"[parse_h1_response] 使用清理后的完整文本")

    try:
        result = json.loads(json_str)
        print(f"[parse_h1_response] JSON 解析成功")

        # 创建 block_id 到 text 的映射（使用原始 block_id）
        block_id_to_text = {}
        if blocks_data:
            for block in blocks_data.get("blocks", []):
                block_id = block.get("block_id")
                text = block.get("text", "")
                if block_id:
                    block_id_to_text[block_id] = text

        # 处理每个 h1_candidate
        for candidate in result.get("h1_candidates", []):
            ai_returned_id = candidate.get("block_id")

            # 步骤1：如果有 uuid_mapping，将 UUID 还原为原始 block_id
            if uuid_mapping and ai_returned_id in uuid_mapping:
                original_block_id = uuid_mapping[ai_returned_id]
                candidate["block_id"] = original_block_id
                print(f"[parse_h1_response] 还原 UUID {ai_returned_id[:8]}... -> {original_block_id}")
            else:
                original_block_id = ai_returned_id

            # 步骤2：添加 text 字段
            if original_block_id in block_id_to_text:
                candidate["text"] = block_id_to_text[original_block_id]
            else:
                candidate["text"] = ""  # 未找到对应的 text
                print(f"[parse_h1_response] 警告: 未找到 block_id={original_block_id} 的 text")

        print(f"[parse_h1_response] 已为 {len(result.get('h1_candidates', []))} 个候选添加 text 字段")

        return result
    except json.JSONDecodeError as e:
        print(f"[parse_h1_response] JSON 解析失败: {e}")
        print(f"[parse_h1_response] 尝试解析的文本 (前500字): {json_str[:500]}")
        raise ValueError(f"无法解析 AI 返回的 JSON: {e}\n提取的文本: {json_str[:200]}...")


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # 添加项目根目录到路径
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

    from app.utils.request import AIClient

    # 测试示例
    sample_blocks = {
        "blocks": [
            {
                "block_id": "D001_0001",
                "text": "第一章 项目概述",
                "features": {
                    "font_size_rank_pct": 0.95,
                    "is_bold": True,
                    "is_centered": True,
                    "indent_level_norm": 0.0,
                    "upper_blank_ratio": 0.9,
                    "lower_blank_ratio": 0.85,
                    "line_len": 9,
                    "numbering_tag": "第一章"
                }
            },
            {
                "block_id": "D001_0002",
                "text": "本项目旨在采购实验室家具，包括实验台、通风柜等设备。采购总预算为 500 万元人民币。",
                "features": {
                    "font_size_rank_pct": 0.45,
                    "is_bold": False,
                    "is_centered": False,
                    "indent_level_norm": 0.3,
                    "upper_blank_ratio": 0.2,
                    "lower_blank_ratio": 0.2,
                    "line_len": 42,
                    "numbering_tag": None
                }
            },
            {
                "block_id": "D001_0003",
                "text": "第二章 技术规格",
                "features": {
                    "font_size_rank_pct": 0.95,
                    "is_bold": True,
                    "is_centered": True,
                    "indent_level_norm": 0.0,
                    "upper_blank_ratio": 0.9,
                    "lower_blank_ratio": 0.85,
                    "line_len": 8,
                    "numbering_tag": "第二章"
                }
            }
        ]
    }

    # 生成提示词（返回包含 uuid_mapping）
    system_prompt, user_prompt, uuid_mapping = generate_h1_detection_prompt(sample_blocks)

    print("=== System Prompt (前200字) ===")
    print(system_prompt[:200] + "...")
    print("\n=== User Prompt (前500字) ===")
    print(user_prompt[:500] + "...")
    print(f"\n总 tokens 估算: ~{(len(system_prompt) + len(user_prompt)) // 4}")
    print(f"\nUUID 映射数量: {len(uuid_mapping)}")

    # 使用 AIClient 发送请求
    print("\n" + "=" * 80)
    print("使用 AIClient 发送请求示例")
    print("=" * 80)

    try:
        # 初始化客户端
        client = AIClient(
            temperature=0.1,  # H1 检测需要较低的温度以保证稳定性
            max_tokens=4096
        )

        # 发送请求
        response_text = client.send_request(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            verbose=True
        )

        # 解析结果（传入 blocks_data 和 uuid_mapping）
        print("\n" + "=" * 80)
        print("解析 H1 检测结果")
        print("=" * 80)
        result = parse_h1_response(
            response_text,
            blocks_data=sample_blocks,
            uuid_mapping=uuid_mapping
        )

        print(f"\n找到 {len(result.get('h1_candidates', []))} 个 H1 候选:")
        for candidate in result.get('h1_candidates', []):
            print(f"\n  Block ID: {candidate['block_id']}")
            print(f"  Text: {candidate.get('text', 'N/A')}")
            print(f"  Score: {candidate['score']}")
            print(f"  理由: {', '.join(candidate['rationale_bullets'])}")

        print(f"\n风格说明: {result.get('style_notes', 'N/A')}")

    except Exception as e:
        print(f"\n请求失败: {e}")
        print("\n提示：如果API不可用，可以将提示词复制到其他AI平台测试")