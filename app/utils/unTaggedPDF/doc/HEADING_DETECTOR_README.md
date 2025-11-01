# 标题检测器 (HeadingDetector)

基于 PyMuPDF 和 pdfplumber 协同识别 PDF 中的标题及层级。

## 功能特性

- **全局字体画像**: 自动分析文档字体特征，估计正文字号
- **多通道召回**: 基于字号、字重、样式等特征识别标题候选
- **智能去噪**: 自动过滤页眉页脚、表格内文本、页码等干扰
- **标题合并**: 合并同一行或跨行的标题片段
- **层级判定**: 基于字号聚类自动判定标题层级（H1/H2/H3...）
- **目录对齐**: 可选与 PDF 书签目录对比

## 使用方法

### 基本使用

```python
from app.utils.unTaggedPDF.heading_detector import HeadingDetector

# 方式1: 使用上下文管理器（推荐）
with HeadingDetector('path/to/your.pdf') as detector:
    headings = detector.extract_headings()
    result = detector.to_json(headings)

# 方式2: 手动管理
detector = HeadingDetector('path/to/your.pdf')
headings = detector.extract_headings()
result = detector.to_json(headings)
detector.close()
```

### 测试脚本

```bash
# 使用测试脚本
python test_heading_detector.py path/to/your.pdf

# 或在虚拟环境中
.venv\Scripts\python.exe test_heading_detector.py path/to/your.pdf
```

### 输出格式

```json
{
  "doc_meta": {
    "pages": 120,
    "body_font_size": 10.5
  },
  "headings": [
    {
      "id": "h-0001",
      "page": 2,
      "level": 1,
      "text": "第一章 总则",
      "bbox": [72.0, 96.2, 523.4, 118.7],
      "font": "ABCDEE+TimesNewRomanPS-BoldMT",
      "size": 18.0,
      "flags": 4,
      "color": 0
    }
  ]
}
```

## 配置参数

可以通过修改 `detector.config` 来调整检测参数：

```python
detector = HeadingDetector('path/to/your.pdf')

# 调整配置
detector.config['heading_size_ratio'] = 1.4  # 标题字号倍数
detector.config['max_heading_length'] = 120  # 标题最大长度
detector.config['header_footer_margin'] = 40  # 页眉页脚边距

headings = detector.extract_headings()
```

### 配置说明

| 参数 | 默认值 | 说明 |
|-----|-------|------|
| `body_size_range` | (6, 16) | 正文字号范围（用于估计） |
| `heading_size_ratio` | 1.3 | 标题字号相对正文的倍数 |
| `max_heading_length` | 150 | 标题最大字符数 |
| `x_gap_merge_ratio` | 0.5 | 同行合并的 x 间距比例 |
| `header_footer_margin` | 30 | 页眉页脚边距（像素） |
| `min_text_length` | 2 | 最小文本长度 |

## 核心算法

### 1. 全局字体画像

- 遍历所有页面，收集所有文本的字号信息
- 使用中位数估计正文字号，避免大标题干扰
- 只统计合理范围（6-16pt）内的字号

### 2. 标题候选召回（多通道）

满足以下任一条件即为候选：

- **字号通道**: 字号 ≥ 正文字号 × 1.3
- **字重通道**: 文本加粗（flags 或字体名含 bold）
- **格式通道**: 行长 ≤ 150 字符 且 不以句号结束

### 3. 去噪过滤

自动过滤：

- **页眉页脚**: 位于页面顶部/底部 30px 区域
- **表格内文本**: 落在表格边界框内
- **页码**: 纯数字且长度 ≤ 4

### 4. 标题合并

- 同一行、字号/字体/flags 相同且 x 间距小于阈值 → 合并
- 扩展边界框，拼接文本

### 5. 层级判定

- 按字号从大到小聚类，分配初始层级
- 加粗标题层级提升（数字减小）
- 最终层级范围: H1, H2, H3...

## 适用场景

- 学术论文
- 技术文档
- 合同文档
- 政府报告
- 企业年报

## 限制与注意

1. **扫描 PDF**: 需要先 OCR 处理
2. **复杂版式**: 多栏版式可能需要额外处理
3. **特殊字体**: 某些自定义字体可能无法正确识别加粗
4. **无空格 CJK**: 中文文档依赖 bbox 连续性判断

## 依赖

- `PyMuPDF (fitz)`: 快速文本提取和字体分析
- `pdfplumber`: 表格检测和精确字符级提取

## 扩展

### 与目录对比

```python
detector = HeadingDetector('path/to/your.pdf')
headings = detector.extract_headings()

# 计算与目录的相似度
for h in headings:
    similarity = detector.get_toc_similarity(h['text'])
    if similarity > 0.8:
        print(f"标题 '{h['text']}' 与目录匹配度: {similarity:.2f}")
```

### 自定义过滤

```python
class CustomHeadingDetector(HeadingDetector):
    def _is_heading_candidate(self, span):
        # 自定义判断逻辑
        if '附录' in span['text']:
            return False
        return super()._is_heading_candidate(span)
```

## 常见问题

**Q: 检测到的标题太多？**
A: 调大 `heading_size_ratio` 或减小 `max_heading_length`

**Q: 漏检了一些标题？**
A: 调小 `heading_size_ratio` 或检查是否被表格过滤

**Q: 层级不准确？**
A: 检查字号分布，可能需要自定义层级判定逻辑

**Q: 表格内容被识别为标题？**
A: 确保 pdfplumber 能正确检测表格，或调整表格过滤逻辑