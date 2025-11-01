# Tender Tagger

PDF 表格和段落提取工具，用于招标文档分类和处理。

## 功能特性

- 混合使用 pdfplumber 和 PyMuPDF 提取 PDF 表格
- 支持嵌套表格识别
- 提取表格外的段落文本
- 结构化输出（JSON 格式）

## 安装依赖

```bash
poetry install
```

## 使用方法

```python
from app.utils.unTaggedPDF.table_extractor import PDFTableExtractor

# 创建提取器
extractor = PDFTableExtractor("path/to/your.pdf")

# 提取所有内容（表格 + 段落）
result = extractor.extract_all_content()

# 保存到 JSON
output_paths = extractor.save_to_json(include_paragraphs=True)
```

## 开发环境

- Python: >=3.11,<3.12
- Poetry: 2.x