# 跨页表格列数识别方案

## 问题描述

**案例：第5-6页表格**
- 第5页：5列，bbox x0=33.6
- 第6页：4列（错误），bbox x0=99.0
- **根本原因：第6页第一列（序号列）在PDFPlumber检测时被截掉**

## 解决方案：PyMuPDF + PDFPlumber 协同

### 方案1：使用 PyMuPDF 检测完整表格区域

```python
import fitz  # PyMuPDF
import pdfplumber

def detect_table_region_with_pymupdf(pdf_path, page_num):
    """
    使用 PyMuPDF 的 get_drawings() 检测表格完整区域

    Returns:
        完整的表格 bbox (包括所有列)
    """
    doc = fitz.open(pdf_path)
    page = doc[page_num]

    # 1. 获取所有绘图对象（包括表格线）
    drawings = page.get_drawings()

    # 2. 筛选水平线和垂直线
    h_lines = []
    v_lines = []

    for drawing in drawings:
        for item in drawing['items']:
            if item[0] == 'l':  # 线段
                p1, p2 = item[1], item[2]

                # 水平线
                if abs(p1.y - p2.y) < 2:
                    h_lines.append((min(p1.x, p2.x), max(p1.x, p2.x), p1.y))

                # 垂直线
                if abs(p1.x - p2.x) < 2:
                    v_lines.append((min(p1.y, p2.y), max(p1.y, p2.y), p1.x))

    # 3. 找到最左边的垂直线（第一列边界）
    if v_lines:
        leftmost_x = min(x for _, _, x in v_lines)
        rightmost_x = max(x for _, _, x in v_lines)
        top_y = min(y1 for y1, _, _ in v_lines)
        bottom_y = max(y2 for y2, _, _ in v_lines)

        return (leftmost_x, top_y, rightmost_x, bottom_y)

    return None


def extract_table_with_full_columns(pdf_path, page_num):
    """
    使用完整区域提取表格
    """
    # 1. 用 PyMuPDF 获取完整区域
    full_bbox = detect_table_region_with_pymupdf(pdf_path, page_num)

    if not full_bbox:
        # 回退到 PDFPlumber 默认检测
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[page_num]
            tables = page.find_tables()
            return tables[0] if tables else None

    # 2. 用 PDFPlumber 在完整区域内提取表格
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_num]

        # 裁剪到完整区域
        cropped = page.crop(full_bbox)

        # 提取表格
        tables = cropped.find_tables()

        return tables[0] if tables else None
```

### 方案2：使用续页Hints的列边界

**当前代码已经生成了hints：**

```python
# 从输出中提取的hints
hints = {
    'page': 6,
    'expected_cols': 5,
    'vertical_lines': [33.6, 99.0, 231.1, 429.1, 495.1, 561.1]
}
```

**改进：在raw.json阶段就使用hints**

```python
def extract_with_hints(pdf_path, page_num, hints):
    """
    使用hints在原始提取时就获取正确列数
    """
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_num]

        # 使用hints中的完整bbox（包括第一列）
        full_bbox = (
            hints['vertical_lines'][0],  # 最左边：33.6
            0,
            hints['vertical_lines'][-1],  # 最右边：561.1
            page.height
        )

        # 在完整区域内检测
        cropped = page.crop(full_bbox)

        # 方法A：使用explicit列边界
        table_settings = {
            'vertical_strategy': 'explicit',
            'explicit_vertical_lines': hints['vertical_lines'],
            'horizontal_strategy': 'lines_strict'
        }

        tables = cropped.find_tables(table_settings)

        # 方法B：如果explicit失败，尝试lines策略
        if not tables:
            tables = cropped.find_tables({
                'vertical_strategy': 'lines',
                'horizontal_strategy': 'lines'
            })

        return tables[0] if tables else None
```

### 方案3：混合策略（推荐）

```python
def detect_table_columns_hybrid(pdf_path, page_num, prev_table_info=None):
    """
    混合使用 PyMuPDF 和 PDFPlumber

    Args:
        prev_table_info: 上一页表格的信息（用于续页检测）
    """
    doc_fitz = fitz.open(pdf_path)
    page_fitz = doc_fitz[page_num]

    # 1. 使用PyMuPDF获取所有垂直线
    drawings = page_fitz.get_drawings()
    v_lines_x = set()

    for drawing in drawings:
        for item in drawing['items']:
            if item[0] == 'l':
                p1, p2 = item[1], item[2]
                if abs(p1.x - p2.x) < 2:  # 垂直线
                    v_lines_x.add(p1.x)

    # 2. 如果是续页，使用前页的列边界
    if prev_table_info:
        expected_v_lines = prev_table_info['vertical_lines']

        # 检查是否缺失列边界
        missing_lines = []
        for expected_x in expected_v_lines:
            if not any(abs(expected_x - x) < 5 for x in v_lines_x):
                missing_lines.append(expected_x)
                print(f"[警告] 第{page_num+1}页缺失列边界: x={expected_x}")

        # 补充缺失的列边界
        all_v_lines = sorted(list(v_lines_x) + missing_lines)
    else:
        all_v_lines = sorted(list(v_lines_x))

    # 3. 使用PDFPlumber提取表格
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_num]

        table_settings = {
            'vertical_strategy': 'explicit',
            'explicit_vertical_lines': all_v_lines,
            'horizontal_strategy': 'lines'
        }

        tables = page.find_tables(table_settings)

        if tables:
            return {
                'table': tables[0],
                'vertical_lines': all_v_lines,
                'column_count': len(all_v_lines) - 1
            }

    return None
```

## 实施步骤

### 1. 在 TableExtractor 中添加完整区域检测

```python
# app/utils/unTaggedPDF/table_extractor.py

class TableExtractor:

    def _detect_full_table_bbox(self, page_num):
        """使用 PyMuPDF 检测完整表格区域"""
        doc = fitz.open(self.pdf_path)
        page = doc[page_num]

        drawings = page.get_drawings()
        v_lines = []

        for drawing in drawings:
            for item in drawing['items']:
                if item[0] == 'l':
                    p1, p2 = item[1], item[2]
                    if abs(p1.x - p2.x) < 2:
                        v_lines.append(p1.x)

        doc.close()

        return sorted(set(v_lines)) if v_lines else None

    def extract_tables(self):
        """提取表格（使用完整区域）"""
        tables = []

        for page_num, page in enumerate(self.plumber_pdf.pages):
            # 1. 使用 PyMuPDF 获取完整列边界
            full_v_lines = self._detect_full_table_bbox(page_num)

            # 2. 使用完整边界提取表格
            if full_v_lines:
                table_settings = {
                    'vertical_strategy': 'explicit',
                    'explicit_vertical_lines': full_v_lines,
                    'horizontal_strategy': 'lines'
                }
                page_tables = page.find_tables(table_settings)
            else:
                page_tables = page.find_tables()

            # ... 处理表格
```

### 2. 在跨页检测时传递完整列信息

```python
# app/utils/unTaggedPDF/cross_page_merger.py

def build_continuation_hints(self, tables, page_widths, page_heights, page_drawings):
    """构建续页hints（包含完整列边界）"""

    for i in range(len(tables) - 1):
        prev_table = tables[i]
        next_table = tables[i + 1]

        # 从PyMuPDF drawings提取前页的所有垂直线
        prev_page_drawings = page_drawings.get(prev_table['page'] + 1, [])
        v_lines = self._extract_vertical_lines(prev_page_drawings)

        if self._is_continuation(prev_table, next_table):
            hints[next_table['page']] = {
                'vertical_lines': v_lines,  # 完整列边界
                'expected_cols': len(v_lines) - 1
            }
```

## 关键点总结

1. **PDFPlumber 的局限**：某些情况下会遗漏左侧或右侧的列边界
2. **PyMuPDF 的优势**：`get_drawings()` 能获取**所有**绘制的线段
3. **结合方案**：
   - 用 PyMuPDF 获取**完整的列边界**（x坐标）
   - 用 PDFPlumber 提取表格内容（基于完整列边界）
4. **在raw.json阶段**：第一次提取时就使用PyMuPDF检测的完整边界

## 预期效果

**修复前：**
```json
{
  "id": "temp_007",
  "page": 6,
  "columns": 4,  // 错误！
  "bbox": [99.0, 28.8, 561.1, 702.8]
}
```

**修复后：**
```json
{
  "id": "temp_007",
  "page": 6,
  "columns": 5,  // 正确！
  "bbox": [33.6, 28.8, 561.1, 702.8],  // 包含完整第一列
  "vertical_lines": [33.6, 99.0, 231.1, 429.1, 495.1, 561.1]
}
```