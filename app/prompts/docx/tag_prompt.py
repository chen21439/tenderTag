"""
Phase A: H1 全局探测提示词
用于识别文档中的一级标题（H1）候选
"""
from typing import List

SYSTEM_PROMPT = """你是文档结构化专家。请根据给定的"分块文本 + 相对版式特征"判断本篇文档级标题候选。你的任务仅输出 JSON，严禁任何解释性文字。

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


def generate_h1_detection_prompt(
    blocks_data: dict,
    use_batching: bool = False,
    batch_manager=None
) -> tuple[str, str, dict] | List[tuple[str, str, dict]]:
    """
    生成 H1 探测的完整提示词

    Args:
        blocks_data: 包含 blocks 列表的字典
        use_batching: 是否启用智能分批（基于 token 限制）
        batch_manager: BatchManager 实例（可选，use_batching=True 时使用）

    Returns:
        如果 use_batching=False: (system_prompt, user_prompt, uuid_mapping) 元组
        如果 use_batching=True: [(system_prompt, user_prompt, uuid_mapping), ...] 列表
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

        # 使用 JSON 中已有的 UUID，如果没有则生成一个
        original_block_id = block.get("block_id")
        block_uuid = block.get("uuid")

        if not block_uuid:
            # 如果 JSON 中没有 uuid 字段，则生成一个（兼容旧数据）
            block_uuid = str(uuid.uuid4())

        uuid_mapping[block_uuid] = original_block_id

        # 创建新的 block，使用 UUID 替换 block_id
        new_block = block.copy()
        new_block["block_id"] = block_uuid

        filtered_blocks.append(new_block)

    print(f"[generate_h1_detection_prompt] 过滤后的候选块数量: {len(filtered_blocks)}")

    # 如果不使用分批，使用简单的截断策略
    if not use_batching:
        if len(filtered_blocks) > 100:
            print(f"[generate_h1_detection_prompt] 候选块过多，只保留字号最大的前 100 个")
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

    # 使用智能分批
    if batch_manager is None:
        from app.utils.request import get_default_batch_manager
        batch_manager = get_default_batch_manager()

    def build_block_content(block):
        """构建单个 block 的 JSON 内容"""
        return json.dumps(block, ensure_ascii=False, indent=2)

    # 分批
    batches = batch_manager.split_items_by_tokens(
        filtered_blocks,
        SYSTEM_PROMPT,
        build_block_content,
        prompt_header='请分析以下文档块，识别一级标题（H1）候选：\n\n```json\n{"blocks": [\n',
        prompt_footer='\n]}\n```\n\n请严格按照 JSON 格式输出结果，不要有任何解释。'
    )

    # 为每个批次生成提示词
    result_batches = []
    for batch_idx, batch in enumerate(batches, 1):
        # 为这个批次创建 uuid_mapping
        batch_uuid_mapping = {
            block["block_id"]: uuid_mapping[block["block_id"]]
            for block in batch
        }

        blocks_json = json.dumps(
            {"blocks": batch},
            ensure_ascii=False,
            indent=2
        )
        user_prompt = USER_PROMPT_TEMPLATE.format(blocks_json=blocks_json)

        result_batches.append((SYSTEM_PROMPT, user_prompt, batch_uuid_mapping))
        print(f"[generate_h1_detection_prompt] 批次 {batch_idx}: {len(batch)} 个块")

    return result_batches


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


def process_h1_detection_with_batching(
    blocks_data: dict,
    ai_client=None,
    use_batching: bool = True,
    batch_manager=None,
    batch_processor=None,
    verbose: bool = True,
    **request_params
) -> dict:
    """
    完整的 H1 检测流程（支持智能分批）

    Args:
        blocks_data: 包含 blocks 列表的字典
        ai_client: AIClient 实例（如果为 None，将创建默认客户端）
        use_batching: 是否启用智能分批
        batch_manager: BatchManager 实例（可选）
        batch_processor: BatchProcessor 实例（可选）
        verbose: 是否打印详细信息
        **request_params: 传递给 AIClient.send_request 的参数（如 temperature, max_tokens 等）

    Returns:
        合并后的结果字典，包含:
        - h1_candidates: 所有批次的 H1 候选（已去重）
        - style_notes: 风格说明（合并自所有批次）
        - batch_count: 批次数量
        - total_candidates: 总候选数（去重前）
        - unique_candidates: 去重后的候选数
    """
    from app.utils.request import (
        AIClient,
        BatchProcessor,
        get_default_batch_processor
    )

    # 初始化 AI 客户端
    if ai_client is None:
        ai_client = AIClient(
            temperature=0.1,  # H1 检测需要较低的温度
            max_tokens=4096
        )

    # 初始化批量处理器
    if batch_processor is None:
        batch_processor = get_default_batch_processor(
            ai_client=ai_client,
            batch_manager=batch_manager,
            verbose=verbose
        )

    # 生成提示词（可能返回单个或批次列表）
    prompt_result = generate_h1_detection_prompt(
        blocks_data,
        use_batching=use_batching,
        batch_manager=batch_manager
    )

    # 判断是单个还是批次列表
    if use_batching and isinstance(prompt_result, list):
        batches = prompt_result
    else:
        # 单个批次，包装成列表
        batches = [prompt_result]

    # 定义解析函数（业务相关）
    def parse_func(response_text: str, context: dict) -> dict:
        """解析单个批次的响应"""
        uuid_mapping = context  # context 就是 uuid_mapping
        return parse_h1_response(
            response_text,
            blocks_data=blocks_data,
            uuid_mapping=uuid_mapping
        )

    # 定义合并函数（业务相关）
    def merge_func(all_results: List[dict]) -> dict:
        """合并多个批次的结果"""
        all_candidates = []
        all_style_notes = []

        # 收集所有候选和风格说明
        for batch_idx, result in enumerate(all_results, 1):
            candidates = result.get("h1_candidates", [])
            all_candidates.extend(candidates)

            style_note = result.get("style_notes", "")
            if style_note:
                all_style_notes.append(f"批次{batch_idx}: {style_note}")

        # 去重（基于 block_id）
        seen_ids = set()
        unique_candidates = []

        for candidate in all_candidates:
            block_id = candidate.get("block_id")
            if block_id not in seen_ids:
                seen_ids.add(block_id)
                unique_candidates.append(candidate)
            elif verbose:
                print(f"[去重] 跳过重复的 block_id: {block_id}")

        if verbose:
            print(f"\n[合并] 去重前: {len(all_candidates)} 个候选，去重后: {len(unique_candidates)} 个候选")

        # 按 score 降序排序
        unique_candidates.sort(key=lambda x: x.get("score", 0), reverse=True)

        return {
            "h1_candidates": unique_candidates,
            "style_notes": " | ".join(all_style_notes) if all_style_notes else "",
            "total_candidates": len(all_candidates),
            "unique_candidates": len(unique_candidates)
        }

    # 使用通用的批量处理器
    result = batch_processor.process_batches(
        batches=batches,
        parse_response_func=parse_func,
        merge_results_func=merge_func,
        **request_params
    )

    # 添加批次数量
    result["batch_count"] = len(batches)

    if verbose:
        print(f"\n{'=' * 80}")
        print(f"[完成] H1 检测完成")
        print(f"  - 批次数: {result['batch_count']}")
        print(f"  - 总候选数: {result['total_candidates']}")
        print(f"  - 去重后: {result['unique_candidates']}")
        if result['h1_candidates']:
            print(f"  - 最高分: {result['h1_candidates'][0].get('score', 0)}")
        print(f"{'=' * 80}\n")

    return result


if __name__ == "__main__":
    import sys
    import json
    from pathlib import Path

    # 添加项目根目录到路径
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

    # 读取真实的 JSON 文件
    json_file_path = r"E:\models\data\深圳市中医院实验类家具采购1030.json"

    print(f"读取文件: {json_file_path}")
    with open(json_file_path, 'r', encoding='utf-8') as f:
        blocks_data = json.load(f)

    print(f"加载完成，共 {len(blocks_data.get('blocks', []))} 个 blocks\n")

    # 使用完整流程（支持智能分批和自动合并）
    print("=" * 80)
    print("开始 H1 检测（智能分批）")
    print("=" * 80)

    try:
        result = process_h1_detection_with_batching(
            blocks_data=blocks_data,
            use_batching=True,  # 启用智能分批
            verbose=True,
            temperature=0.1,
            max_tokens=4096
        )

        # 输出结果
        print("\n" + "=" * 80)
        print("H1 检测结果")
        print("=" * 80)
        print(f"批次数: {result['batch_count']}")
        print(f"总候选数: {result['total_candidates']}")
        print(f"去重后: {result['unique_candidates']}")
        print(f"\n找到 {len(result['h1_candidates'])} 个 H1 候选:\n")

        for idx, candidate in enumerate(result['h1_candidates'], 1):
            print(f"{idx}. Block ID: {candidate['block_id']}")
            print(f"   Text: {candidate.get('text', 'N/A')}")
            print(f"   Score: {candidate['score']}")
            print(f"   理由: {', '.join(candidate['rationale_bullets'])}")
            print()

        if result.get('style_notes'):
            print(f"风格说明: {result['style_notes']}")

    except Exception as e:
        import traceback
        print(f"\n处理失败: {e}")
        print("\n完整错误信息:")
        traceback.print_exc()
        print("\n提示：如果API不可用，可以将提示词复制到其他AI平台测试")