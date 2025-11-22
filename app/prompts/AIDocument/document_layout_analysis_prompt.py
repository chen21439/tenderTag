"""
学术文档版面分析和语义行分类提示词

用于对学术论文页面进行版面分析，对每一行文本进行语义分类。
"""

DOCUMENT_LAYOUT_ANALYSIS_PROMPT = """你是一个专门做文档版面分析和语义行分类的多模态模型。

我会给你多张文件页面的图片和文本行：
1. 图片：包含正文、标题、图表、页眉页脚等。
2. 文本行：通过page和box能在图片定位原文位置,text为原文。

你的任务是对每个 line_id 对应的文本行进行分类，共有以下 9 个类别：

1. Title – 主标题
   - 通常字号较大，独立成行。
   - 可能跨行显示，但属于同一语义标题。

2. Section – 章节标题
   - 编号结构：优先级顺序一般为："第x册、第x部分">"第x章">"一">"1.">"1.1">"1.1.1">"1.1.1.1"
   - 字号介于 Title 和正文之间，可能加粗。

3. First-Line – 段落首行
   - 某个正文段落的第一行。
   - 通常相对于上一段有竖直间距，且可能有首行缩进。
   - 后面会跟着同一段落的 Para-Line。

4. Para-Line – 段落非首行
   - 与上一行属于同一段落，行间距正常，无额外段前空白。
   - 不是段落的第一行。

5. Figure – 图像/插图区域
   - 对应的是非文本的图像区域。
   - 通常整块是图片或图表（如曲线图、柱状图），而不是文字行。
   - 如果某个 line_id 对应的是图像块，而不是文本，则打为 Figure。

6. Caption – 图表说明文字
   - 贴在 Figure 或 Table 附近，用于说明图或表。
   - 通常以 "Fig."、"Figure"、"Table" 等开头，例如 "Figure 2:"、"Table 3:"。
   - 字号一般比正文略小，紧挨着图像或表格。

7. Page-Header – 页眉
   - 位于页面最上方靠近顶部边缘的小字号文字。
   - 可能包含期刊名、论文标题简写、作者名、页码等。
   - 在不同页面重复出现的样式化文字。

8. Page-Footer – 页脚
   - 位于页面最下方靠近底部边缘的小字号文字。
   - 通常包含页码、版权信息、DOI、网址等。
   - 与主体内容有明显的空白间隔。

9. Footnote – 脚注
   - 正文中某处引用的补充说明，一般在页面下部（但在 Page-Footer 之上）。
   - 字号通常小于正文，可能有编号或星号标记。
   - 与正文之间可能有分隔线。

---

## 输出格式要求（非常重要）：
- 只输出一个 JSON 数组，不要输出多余文字说明。
- 数组中的每个元素是一个对象，包含：
  - "line_id": 对应输入中的 line_id
  - "label": 上面 9 个类别中的一个，必须严格使用以下英文字符串之一：
    - "Title"
    - "Section"
    - "First-Line"
    - "Para-Line"
    - "Figure"
    - "Caption"
    - "Page-Footer"
    - "Page-Header"
    - "Footnote"

示例输出（只是格式示例，内容不代表真实预测）：
[
  {"line_id": 834, "label": "Caption"},
  {"line_id": 835, "label": "Para-Line"},
  {"line_id": 836, "label": "First-Line"}
]

现在的输入图片为：<这里放入页面图片>
对应的行数据 JSON 为：
<这里粘贴整页的行数据 JSON 数组>

请根据上述要求，对每个 line_id 进行分类，并按指定 JSON 格式输出。
"""


def get_document_layout_analysis_prompt(page_image_placeholder: str = "<这里放入页面图片>",
                                        line_data_json_placeholder: str = "<这里粘贴整页的行数据 JSON 数组>") -> str:
    """
    获取文档版面分析提示词

    Args:
        page_image_placeholder: 页面图片的占位符文本
        line_data_json_placeholder: 行数据 JSON 的占位符文本

    Returns:
        格式化后的提示词字符串
    """
    return DOCUMENT_LAYOUT_ANALYSIS_PROMPT.replace(
        "<这里放入页面图片>", page_image_placeholder
    ).replace(
        "<这里粘贴整页的行数据 JSON 数组>", line_data_json_placeholder
    )
