# HeadingExtractor - 基于 pdfplumber 的标题提取器

使用 pdfplumber 的 `extract_words` 方法实现标题检测和内容提取。

## 核心特性

### 1. 精确的文字提取
- 使用 `page.extract_words(extra_attrs=["fontname", "size"])`
- 获取每个词的字体名称和字号信息
- 字符级精度，无需手动处理 span 合并

### 2. 标题检测
- 基于字号和字体名称识别标题
- 支持多种编号格式（一、二、1、2、(1)、(2) 等）
- 自动合并同行文字片段

### 3. 内容提取
- 使用 `page.crop(...).extract_text()` 提取标题之间的文本
- 根据标题位置自动计算内容区域边界框
- 支持跨页标题的内容提取

## 使用方法

### 基本使用

```python
from app.utils.unTaggedPDF.head import HeadingExtractor

with HeadingExtractor('path/to/your.pdf') as extractor:
    # 提取标题
    headings = extractor.extract_headings()

    # 提取标题之间的内容
    contents = extractor.extract_content_between_headings(headings)

    # 转换为 JSON
    result = extractor.to_json(headings)
```

### 运行测试

```bash
# 在虚拟环境中运行
.venv\Scripts\python.exe app\utils\unTaggedPDF\head\heading_extractor.py

# 或者在 PyCharm 中右键运行
```

## 输出格式

### 标题列表

```json
{
  "doc_meta": {
    "pages": 31,
    "body_font_size": 9.6
  },
  "headings": [
    {
      "id": "h-0000",
      "page": 0,
      "level": 1,
      "text": "一、项目总体情况",
      "bbox": [33.3, 49.3, 158.0, 64.9],
      "fontname": "SimSun",
      "size": 15.6
    }
  ]
}
```

### 内容块列表

```json
{
  "contents": [
    {
      "heading_id": "h-0000",
      "heading_text": "一、项目总体情况",
      "page": 1,
      "bbox": [0, 64.9, 595.3, 200.0],
      "content": "项目的详细描述内容..."
    }
  ]
}
```

## 算法流程

### 步骤 1: 提取文字信息
```python
words = page.extract_words(extra_attrs=["fontname", "size"])
```
- 获取每个词的位置、字体、大小

### 步骤 2: 识别标题
- 字号判断：`size >= body_size * 1.3`
- 字体判断：字体名包含 'bold' 等关键词
- 编号判断：匹配 "一、"、"1、" 等模式

### 步骤 3: 合并同行文字
- 按 y 坐标分组（容差 3px）
- 按 x 坐标排序
- 拼接文本

### 步骤 4: 提取内容
```python
bbox = (0, heading_bottom, page_width, next_heading_top)
content = page.crop(bbox).extract_text()
```
- 计算标题之间的区域
- 裁剪并提取文本

## 配置参数

```python
extractor.config = {
    'body_size_range': (6, 16),       # 正文字号范围
    'heading_size_ratio': 1.3,        # 标题字号倍数
    'max_heading_length': 150,        # 标题最大长度
    'min_text_length': 2,             # 最小文本长度
    'line_tolerance': 3,              # 同行容差（像素）
}
```

## 与 PyMuPDF 方案对比

| 特性 | pdfplumber (本方案) | PyMuPDF |
|-----|-------------------|---------|
| 文字提取 | `extract_words` | `get_text("dict")` |
| 精度 | 词级，更精确 | span 级，需手动合并 |
| 字体信息 | 直接获取 fontname | 需要解析 font 属性 |
| 内容提取 | `crop().extract_text()` | 手动计算和过滤 |
| 速度 | 较慢（Python 实现） | 快（C++ 实现） |
| 适用场景 | 需要精确内容提取 | 需要高性能处理 |

## 优势

1. **代码更简洁**：无需处理复杂的 span 合并逻辑
2. **内容提取方便**：`crop()` 方法天然支持区域提取
3. **字符级精度**：extract_words 提供更精确的位置信息
4. **易于理解**：API 更符合直觉

## 适用场景

- 需要提取标题和对应内容的场景
- 需要精确字体信息的场景
- 对性能要求不高的中小型 PDF
- 需要基于标题组织文档结构的场景

## 限制

- 性能相对 PyMuPDF 较慢
- 大文档（>100页）可能耗时较长
- 复杂版式可能需要额外调整