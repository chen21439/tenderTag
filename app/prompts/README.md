# Prompts 提示词文档

本目录存放项目中使用的所有 AI 提示词（Prompts），按功能模块组织。

---

## 📁 目录结构

```
app/prompts/
├── README.md                        # 本文档
├── templates.py                     # 通用提示词模板（当前为空）
├── cross_page_cell_prompts.py      # 跨页单元格合并提示词
├── docx/
│   └── tag_prompt.py               # DOCX 文档标签检测提示词
└── AIDocument/
    └── 笔记.md                      # AI 文档处理笔记
```

---

## 📝 提示词模块说明

### 1. `cross_page_cell_prompts.py` - 跨页单元格合并

**功能**：判断 PDF 表格在跨页时，是否需要合并上一页的最后一行和下一页的第一行。

**核心提示词**：

#### 1.1 `ROW_SYSTEM_PROMPT`
- **作用**：系统提示词，定义 AI 的角色和任务
- **角色**：PDF 表格分析专家
- **任务**：判断两行数据是否是"同一行被分页截断"

**输出格式**：
```json
{
    "should_merge": true,
    "confidence": 0.95,
    "reason": "c0列内容明显被截断，应该合并"
}
```

#### 1.2 `BATCH_ROW_USER_PROMPT_TEMPLATE`
- **作用**：批量判断多对行的用户提示词模板
- **输入**：多个行对（上页最后一行 + 下页第一行）
- **输出**：JSON 数组，每个元素包含 `pair_id`、`should_merge`、`confidence`、`reason`

**使用示例**：
```python
from app.prompts.cross_page_cell_prompts import (
    ROW_SYSTEM_PROMPT,
    build_batch_row_prompt
)

# 准备行对数据
row_pairs = [
    {
        "prev_row": {"第0列": "这是一段很长的文本...", "第1列": "123"},
        "next_row": {"第0列": "...被截断的后半部分", "第1列": "456"}
    },
    # ... 更多行对
]

# 构建用户提示词
def truncate_text(text, max_lines=3, from_end=False):
    lines = text.split('\n')
    if from_end:
        return '\n'.join(lines[-max_lines:])
    else:
        return '\n'.join(lines[:max_lines])

user_prompt = build_batch_row_prompt(row_pairs, truncate_text)

# 发送请求
from app.utils.request import AIClient
client = AIClient()
response = client.send_request(
    system_prompt=ROW_SYSTEM_PROMPT,
    user_prompt=user_prompt
)
```

**辅助函数**：
- `build_row_pair_content()`: 构建单个行对的内容
- `build_batch_row_prompt()`: 构建批量行对判断的完整提示词

---

### 2. `docx/tag_prompt.py` - DOCX 文档标签检测

**功能**：检测 DOCX 文档中的一级标题（H1）候选，基于文本内容和版式特征。

**核心提示词**：

#### 2.1 `SYSTEM_PROMPT` - H1 全局探测系统提示词
- **作用**：定义文档结构化专家的角色和判断标准
- **输入格式**：每个 block 包含 `block_id`、`text`、`features`
- **版式特征**：
  - `font_size_rank_pct`: 字号分位数 [0,1]
  - `is_bold`: 是否加粗
  - `is_centered`: 是否居中
  - `indent_level_norm`: 缩进归一化值
  - `upper_blank_ratio`: 段前留白分位数
  - `lower_blank_ratio`: 段后留白分位数
  - `line_len`: 文本长度
  - `numbering_tag`: 编号标签（如"第一章"、"1."等）

**判断标准**（权重递减）：

1. **高优先级特征**：
   - 包含明确章节编号（"第X章"、"第X节"等）
   - 字号显著大于正文（`font_size_rank_pct > 0.8`）
   - 居中对齐（`is_centered=true`）
   - 文本简短（通常 < 30 字符）

2. **中优先级特征**：
   - 加粗（`is_bold=true`）
   - 段前/段后留白较大（`upper_blank_ratio > 0.7`）
   - 无缩进或缩进很小（`indent_level_norm < 0.2`）

3. **排除规则**：
   - 文本过长（> 50 字符）通常不是标题
   - 包含详细说明、条款内容的不是标题
   - 纯数字、日期、页码等不是标题

**输出格式**：
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

#### 2.2 `USER_PROMPT_TEMPLATE`
- **作用**：用户提示词模板
- **输入**：文档块的 JSON 数据
- **要求**：严格按照 JSON 格式输出，不要有任何解释

**使用示例**：
```python
from app.prompts.docx.tag_prompt import (
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
    generate_h1_detection_prompt
)

# 准备文档块数据
blocks_data = {
    "blocks": [
        {
            "block_id": "B001",
            "text": "第一章 总则",
            "features": {
                "font_size_rank_pct": 0.95,
                "is_bold": True,
                "is_centered": True,
                "indent_level_norm": 0.0,
                "upper_blank_ratio": 0.8,
                "lower_blank_ratio": 0.8,
                "line_len": 8,
                "numbering_tag": "第一章"
            }
        },
        # ... 更多 blocks
    ]
}

# 生成提示词（不分批）
system_prompt, user_prompt, uuid_mapping = generate_h1_detection_prompt(
    blocks_data=blocks_data,
    use_batching=False
)

# 发送请求
from app.utils.request import AIClient
client = AIClient()
response = client.send_request(
    system_prompt=system_prompt,
    user_prompt=user_prompt
)
```

**智能分批支持**：
```python
from app.utils.request import get_default_batch_manager

# 生成提示词（启用分批）
batches = generate_h1_detection_prompt(
    blocks_data=blocks_data,
    use_batching=True,
    batch_manager=get_default_batch_manager()
)

# batches 是一个列表，每个元素为 (system_prompt, user_prompt, uuid_mapping)
for system_prompt, user_prompt, uuid_mapping in batches:
    # 发送请求...
    pass
```

**辅助函数**：
- `generate_h1_detection_prompt()`: 生成 H1 探测的完整提示词，支持智能分批

---

### 3. `templates.py` - 通用提示词模板

**当前状态**：空文件，预留用于存放通用提示词模板。

**建议用途**：
- 通用的 JSON 解析提示词
- 通用的文本分类提示词
- 通用的信息提取提示词

---

## 🎯 提示词设计原则

### 1. 结构清晰
- 使用明确的 **角色定义**（"你是XXX专家"）
- 分离 **系统提示词** 和 **用户提示词**
- 使用 **标题和分段** 增强可读性

### 2. 输出格式严格
- 要求使用 **```json 代码块** 包裹输出
- 明确 **字段名称和类型**
- 提供 **完整的输出示例**

### 3. 任务明确
- 清晰定义 **输入格式**
- 列出 **判断标准**（优先级递减）
- 说明 **排除规则**

### 4. 支持批量处理
- 提供 **单个项目** 和 **批量项目** 的模板
- 使用 **UUID 或 ID** 追踪每个项目
- 确保输出包含 **匹配 ID**

---

## 🔧 提示词工具函数

### 内容构建函数

用于 `BatchManager.split_items_by_tokens()`：

```python
def build_item_content(item):
    """
    构建单个项目的内容（用于分批）

    Args:
        item: 单个项目数据

    Returns:
        格式化的文本内容
    """
    return f"## Block {item['id']}\n{item['text']}\n"
```

### 响应解析函数

用于 `BatchProcessor.process_batches()`：

```python
def parse_response(response_text: str, context: dict) -> dict:
    """
    解析 AI 响应（从 ```json 代码块提取）

    Args:
        response_text: AI 返回的原始文本
        context: 上下文信息

    Returns:
        解析后的 JSON 数据
    """
    import json

    # 提取 JSON 代码块
    if "```json" in response_text:
        json_str = response_text.split("```json")[1].split("```")[0].strip()
    else:
        json_str = response_text.strip()

    # 解析 JSON
    result = json.loads(json_str)
    return result
```

### 结果合并函数

用于 `BatchProcessor.process_batches()`：

```python
def merge_results(all_results: list) -> dict:
    """
    合并多个批次的结果

    Args:
        all_results: 所有批次的结果列表

    Returns:
        合并后的最终结果
    """
    from app.utils.request import merge_candidates_with_dedup

    return merge_candidates_with_dedup(
        all_results=all_results,
        candidates_key="candidates",
        id_key="id",
        score_key="score"
    )
```

---

## 📋 完整工作流示例

### 示例 1: H1 标题检测（带分批）

```python
from app.prompts.docx.tag_prompt import generate_h1_detection_prompt
from app.utils.request import (
    AIClient,
    BatchProcessor,
    get_default_batch_manager
)
import json

# 1. 准备数据
blocks_data = {
    "blocks": [
        # ... 数百个 blocks
    ]
}

# 2. 生成分批提示词
batches = generate_h1_detection_prompt(
    blocks_data=blocks_data,
    use_batching=True,
    batch_manager=get_default_batch_manager()
)

# 3. 初始化处理器
processor = BatchProcessor(max_workers=10)

# 4. 定义解析和合并函数
def parse_response(response_text: str, context: dict) -> dict:
    if "```json" in response_text:
        json_str = response_text.split("```json")[1].split("```")[0].strip()
    else:
        json_str = response_text.strip()
    return json.loads(json_str)

def merge_results(all_results: list) -> dict:
    from app.utils.request import merge_candidates_with_dedup
    return merge_candidates_with_dedup(
        all_results=all_results,
        candidates_key="h1_candidates",
        id_key="block_id",
        score_key="score"
    )

# 5. 并行处理
final_result = processor.process_batches(
    batches=batches,
    parse_response_func=parse_response,
    merge_results_func=merge_results,
    parallel=True,
    temperature=0.0
)

print(f"检测到 {final_result['unique_candidates']} 个 H1 候选")
```

### 示例 2: 跨页单元格合并

```python
from app.prompts.cross_page_cell_prompts import (
    ROW_SYSTEM_PROMPT,
    build_batch_row_prompt
)
from app.utils.request import AIClient
import json

# 1. 准备行对数据
row_pairs = [
    {
        "prev_row": {"第0列": "...", "第1列": "..."},
        "next_row": {"第0列": "...", "第1列": "..."}
    },
    # ... 更多行对
]

# 2. 构建提示词
def truncate_text(text, max_lines=3, from_end=False):
    lines = text.split('\n')
    if from_end:
        return '\n'.join(lines[-max_lines:])
    else:
        return '\n'.join(lines[:max_lines])

user_prompt = build_batch_row_prompt(row_pairs, truncate_text)

# 3. 发送请求
client = AIClient()
response = client.send_request(
    system_prompt=ROW_SYSTEM_PROMPT,
    user_prompt=user_prompt
)

# 4. 解析结果
if "```json" in response:
    json_str = response.split("```json")[1].split("```")[0].strip()
else:
    json_str = response.strip()

results = json.loads(json_str)

# 5. 处理结果
for result in results:
    pair_id = result["pair_id"]
    should_merge = result["should_merge"]
    confidence = result["confidence"]
    reason = result["reason"]
    print(f"Pair {pair_id}: merge={should_merge}, conf={confidence}, reason={reason}")
```

---

## 🎓 最佳实践

### 1. 提示词设计
- **明确输出格式**：要求使用 ```json 代码块
- **提供完整示例**：让 AI 理解期望的输出结构
- **列出判断标准**：按优先级排序
- **说明排除规则**：避免误判

### 2. 批量处理
- **使用 UUID 追踪**：在批量处理中，为每个项目分配唯一 ID
- **要求返回 ID**：确保响应中包含匹配的 ID
- **智能分批**：使用 `BatchManager` 避免超过 token 限制

### 3. 错误处理
- **JSON 解析**：先尝试从代码块提取，再尝试直接解析
- **失败重试**：使用 `AIClient` 的重试机制
- **默认值**：使用 `send_request_safe()` 提供默认响应

### 4. 性能优化
- **并行处理**：对于独立任务，使用 `BatchProcessor` 并行处理
- **文本截断**：对于长文本，只传递关键部分（如前/后 N 行）
- **去重合并**：使用 `merge_candidates_with_dedup` 避免重复结果

---

## 📚 相关文档

- [Request 工具类文档](../utils/request/README.md)
- OpenAI API 最佳实践: https://platform.openai.com/docs/guides/prompt-engineering
- JSON Schema: https://json-schema.org/

---

## 🔍 常见问题

### Q1: 如何设计一个新的提示词？

**A**: 遵循以下结构：

```python
# 1. 系统提示词
SYSTEM_PROMPT = """你是XXX专家。

你的任务：
<明确的任务描述>

输入格式：
<输入数据的格式说明>

输出格式：
<必须使用 ```json 代码块>

```json
{
  "field1": "...",
  "field2": "..."
}
```

**重要**：必须使用 ```json 代码块格式，不要输出其他内容。
"""

# 2. 用户提示词模板
USER_PROMPT_TEMPLATE = """请分析以下数据：

{data}

请严格按照 JSON 格式输出结果，不要有任何解释。"""

# 3. 生成函数
def generate_prompt(data):
    import json
    return (
        SYSTEM_PROMPT,
        USER_PROMPT_TEMPLATE.format(data=json.dumps(data, ensure_ascii=False))
    )
```

### Q2: 如何处理超长输入？

**A**: 使用 `BatchManager` 智能分批：

```python
from app.utils.request import get_default_batch_manager

manager = get_default_batch_manager()
batches = manager.split_items_by_tokens(
    items=items,
    system_prompt=SYSTEM_PROMPT,
    build_item_content_func=lambda item: f"{item['text']}\n",
    prompt_header="请分析以下数据：\n",
    prompt_footer="\n请输出 JSON 格式"
)
```

### Q3: 如何提高 AI 输出的稳定性？

**A**:
1. 使用 **```json 代码块** 要求
2. 提供 **完整的输出示例**
3. 设置 **temperature=0.0**（更确定性）
4. 添加 **"严禁任何解释性文字"** 的强调

---

**更新日期**: 2025-11-22
