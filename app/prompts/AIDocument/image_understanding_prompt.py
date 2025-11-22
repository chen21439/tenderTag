"""
图像理解提示词模板
用于百度文心一言的图像内容分析
"""

# 基础图像理解提示词
BASIC_IMAGE_PROMPT = """请仔细观察这张图片，并详细描述图片中的内容。

请包含以下信息：
1. 图片的主要内容和主题
2. 图片中的关键元素
3. 图片的布局和结构
4. 任何值得注意的细节

请用清晰、简洁的语言描述。"""


# 文档图像理解提示词（带JSON数据）
DOCUMENT_IMAGE_WITH_JSON_PROMPT = """你是一个文档分析专家。我会给你：
1. 一张文档页面的截图
2. 从该页面提取的文本行数据（JSON格式）

你的任务是：
结合图片和文本数据，分析这个文档页面的结构和内容，并给出详细的分析结果。

**文本行数据（lines）：**
```json
{json_data}
```

请分析：
1. 页面的整体布局（标题、正文、表格、列表等）
2. 关键内容的类型和位置
3. 文本行之间的逻辑关系
4. 是否有需要特别注意的结构特征

请以JSON格式输出分析结果。"""


# 表格识别提示词
TABLE_RECOGNITION_PROMPT = """请识别这张图片中的表格。

分析以下内容：
1. 表格的行数和列数
2. 表头内容
3. 每个单元格的内容
4. 表格的边框和分隔线情况

请以JSON格式输出表格数据，格式如下：
```json
{
  "table_info": {
    "rows": 数字,
    "columns": 数字,
    "has_header": true/false
  },
  "headers": ["列1", "列2", ...],
  "data": [
    ["单元格1-1", "单元格1-2", ...],
    ["单元格2-1", "单元格2-2", ...]
  ]
}
```"""


# 标题层级识别提示词
HEADING_RECOGNITION_PROMPT = """请识别这张文档图片中的标题层级。

分析以下内容：
1. 识别所有的标题（一级、二级、三级等）
2. 判断每个标题的层级
3. 标注标题的位置和样式特征（字号、加粗、居中等）

请以JSON格式输出，格式如下：
```json
{
  "headings": [
    {
      "text": "标题文本",
      "level": 1,
      "style": {
        "bold": true,
        "centered": true,
        "font_size": "large"
      }
    }
  ]
}
```"""


# 文档布局分析提示词（多页）
DOCUMENT_LAYOUT_ANALYSIS_PROMPT = """你是一个专业的文档结构分析专家。我会给你多张文档页面的截图。

{page_descriptions}

请分析这些页面的布局和结构，包括：
1. 每个页面的主要内容类型（标题页、目录、正文、表格、附录等）
2. 页面的整体布局结构（标题、段落、列表、表格等元素的分布）
3. 各页面之间的逻辑关系和连贯性
4. 特殊的排版特征（居中、缩进、编号等）

请以JSON格式输出分析结果，格式如下：
```json
{
  "pages": [
    {
      "page_number": 页码,
      "content_type": "页面类型",
      "layout": {
        "has_title": true/false,
        "has_table": true/false,
        "has_list": true/false,
        "structure": "布局描述"
      },
      "key_elements": ["关键元素1", "关键元素2"]
    }
  ],
  "document_structure": "整体文档结构描述"
}
```"""


def build_custom_prompt(
    task_description: str,
    context: str = "",
    output_format: str = "文字描述"
) -> str:
    """
    构建自定义提示词

    Args:
        task_description: 任务描述
        context: 额外的上下文信息
        output_format: 期望的输出格式（"文字描述"、"JSON"等）

    Returns:
        完整的提示词
    """
    prompt = f"""请分析这张图片。

**任务要求：**
{task_description}
"""

    if context:
        prompt += f"""
**上下文信息：**
{context}
"""

    prompt += f"""
**输出格式：**
{output_format}
"""

    return prompt
