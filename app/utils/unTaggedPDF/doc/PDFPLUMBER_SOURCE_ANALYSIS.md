# pdfplumber 表格检测源码分析

**目标**: 理解 pdfplumber 如何识别表格，为什么嵌套示例检测到2个表格而 table.pdf 只检测到1个

---

## 🔍 核心流程

### 调用链

```
page.find_tables(table_settings)
  ↓
TableFinder(page, settings)
  ↓
TableFinder.__init__()
  ├─ self.edges = self.get_edges()              # 步骤1: 获取边缘线
  ├─ self.intersections = edges_to_intersections(edges)  # 步骤2: 找交点
  ├─ self.cells = intersections_to_cells(intersections)  # 步骤3: 构建单元格
  └─ self.tables = cells_to_tables(cells)       # 步骤4: 分组成表格 ★关键
```

---

## 📋 步骤详解

### 步骤1: get_edges() - 获取边缘线

**源码位置**: `table.py:600-692`

#### Lines 策略（默认）

```python
if v_strat == "lines":
    v_base = utils.filter_edges(self.page.edges, "v")  # 从page.edges获取垂直边

if h_strat == "lines":
    h_base = utils.filter_edges(self.page.edges, "h")  # 从page.edges获取水平边
```

**关键点**: `self.page.edges` 来自哪里？

`page.edges` 是 `Container` 类的属性（在 `container.py` 中定义），它从 PDF 对象中提取边缘：
- 直线 (`line`)
- 矩形边缘 (`rect`)
- 曲线 (`curve`)

**从我们的诊断结果**:
- table.pdf: 62条水平边缘 + 72条垂直边缘 = **134条**
- 嵌套示例: 9条水平边缘 + 9条垂直边缘 = **18条**

#### Text 策略

```python
if v_strat == "text":
    v_base = words_to_edges_v(words, word_threshold=settings.min_words_vertical)

if h_strat == "text":
    h_base = words_to_edges_h(words, word_threshold=settings.min_words_horizontal)
```

**原理**:
- 从文本对齐位置推断出"隐式"边缘线
- 例如：如果至少3个单词的左边缘对齐，则在那个X坐标生成一条垂直边缘

---

### 步骤2: edges_to_intersections() - 找交点

**源码位置**: `table.py:207-231`

```python
def edges_to_intersections(edges, x_tolerance=1, y_tolerance=1):
    """给定边缘线列表，返回它们的交点"""
    intersections = {}
    v_edges, h_edges = [list(filter(...)) for o in ("v", "h")]

    for v in sorted(v_edges, key=itemgetter("x0", "top")):
        for h in sorted(h_edges, key=itemgetter("top", "x0")):
            # 检查垂直线和水平线是否相交（在容差范围内）
            if ((v["top"] <= (h["top"] + y_tolerance)) and
                (v["bottom"] >= (h["top"] - y_tolerance)) and
                (v["x0"] >= (h["x0"] - x_tolerance)) and
                (v["x0"] <= (h["x1"] + x_tolerance))):

                vertex = (v["x0"], h["top"])  # 交点坐标
                if vertex not in intersections:
                    intersections[vertex] = {"v": [], "h": []}
                intersections[vertex]["v"].append(v)
                intersections[vertex]["h"].append(h)

    return intersections
```

**输出**: 字典 `{(x, y): {"v": [垂直边], "h": [水平边]}}`

---

### 步骤3: intersections_to_cells() - 构建单元格

**源码位置**: `table.py:234-294`

```python
def intersections_to_cells(intersections):
    """从交点构建矩形单元格"""

    def find_smallest_cell(points, i):
        """从点i出发，找最小的矩形单元格"""
        pt = points[i]
        rest = points[i + 1:]

        # 获取正下方和正右方的点
        below = [x for x in rest if x[0] == pt[0]]
        right = [x for x in rest if x[1] == pt[1]]

        for below_pt in below:
            if not edge_connects(pt, below_pt):  # 检查是否有边连接
                continue

            for right_pt in right:
                if not edge_connects(pt, right_pt):
                    continue

                bottom_right = (right_pt[0], below_pt[1])

                # 检查是否形成完整矩形（四条边都存在）
                if ((bottom_right in intersections) and
                    edge_connects(bottom_right, right_pt) and
                    edge_connects(bottom_right, below_pt)):

                    return (pt[0], pt[1], bottom_right[0], bottom_right[1])

        return None

    # 为每个交点找最小单元格
    cells = [find_smallest_cell(points, i) for i in range(len(points))]
    return list(filter(None, cells))
```

**输出**: 单元格 bbox 列表 `[(x0, y0, x1, y1), ...]`

---

### 步骤4: cells_to_tables() - 分组成表格 ★★★ 关键！

**源码位置**: `table.py:297-356`

这是决定能检测到几个表格的**关键步骤**！

```python
def cells_to_tables(cells):
    """将单元格分组成连续的表格"""

    def bbox_to_corners(bbox):
        """单元格的4个角点"""
        x0, top, x1, bottom = bbox
        return ((x0, top), (x0, bottom), (x1, top), (x1, bottom))

    remaining_cells = list(cells)
    current_corners = set()  # 当前表格的所有角点
    current_cells = []       # 当前表格的所有单元格
    tables = []

    while len(remaining_cells):
        initial_cell_count = len(current_cells)

        for cell in list(remaining_cells):
            cell_corners = bbox_to_corners(cell)

            # 如果是第一个单元格，直接加入
            if len(current_cells) == 0:
                current_corners |= set(cell_corners)
                current_cells.append(cell)
                remaining_cells.remove(cell)
            else:
                # 计算与当前表格共享的角点数
                corner_count = sum(c in current_corners for c in cell_corners)

                # 如果至少共享1个角点，则属于同一个表格
                if corner_count > 0:
                    current_corners |= set(cell_corners)
                    current_cells.append(cell)
                    remaining_cells.remove(cell)

        # 如果本轮没有找到更多单元格，则开始新表格
        if len(current_cells) == initial_cell_count:
            tables.append(list(current_cells))
            current_corners.clear()
            current_cells.clear()

    # 存储最后一个表格
    if len(current_cells):
        tables.append(list(current_cells))

    # 排序和过滤（至少2个单元格才算表格）
    _sorted = sorted(tables, key=lambda t: min((c[1], c[0]) for c in t))
    filtered = [t for t in _sorted if len(t) > 1]
    return filtered
```

**关键判断**:
```python
corner_count = sum(c in current_corners for c in cell_corners)
if corner_count > 0:  # 至少共享1个角点
    # 属于同一个表格
```

**分组逻辑**:
1. 遍历所有单元格
2. 如果单元格与当前表格**共享至少1个角点**，则归入当前表格
3. 如果一轮遍历后没有新单元格加入，则**开始新表格**

---

## 🎯 为什么嵌套示例检测到2个表格？

### 关键原因：单元格分组逻辑

**嵌套示例的结构**:
```
外层表格单元格:
  Cell A: (90.0, 202.74, 234.0, 217.49)
  Cell B: (234.0, 232.29, 378.0, 619.62)  ← 包含子表
  Cell C: (378.0, 232.29, 522.0, 619.62)
  ...

内层表格单元格:
  Cell 1: (239.65, 261.29, 271.50, 315.76)
  Cell 2: (271.50, 261.29, 303.35, 315.76)
  ...
```

**分组过程**:

1. **第一轮**: 外层表格的单元格互相共享角点
   - Cell A, Cell B, Cell C 都共享一些角点
   - 被分组到 **Table[0]**

2. **第二轮**: 内层表格的单元格
   - Cell 1, Cell 2 共享角点
   - 但它们**不与外层表格单元格共享角点**
   - 被分组到 **Table[1]**

**为什么不共享角点？**

看我们的诊断数据：
```
外层表格 Cell B: (234.00, 232.29, 378.00, 619.62)
  角点: (234, 232), (234, 620), (378, 232), (378, 620)

内层表格 Cell 1: (239.65, 261.29, 271.50, 315.76)
  角点: (240, 261), (240, 316), (272, 261), (272, 316)
```

**没有一个角点坐标相同！** 因此被识别为两个独立表格。

---

## 🎯 为什么 table.pdf 只检测到1个表格？

### 推测：内部布局的边缘与外层表格边缘共享角点

**从诊断结果**:
- table.pdf: 134条边缘（62水平 + 72垂直）
- 找到4个大单元格，但没有检测到子表

**可能的结构**:
```
所有单元格的边缘互相连接或共享角点
→ cells_to_tables() 将它们全部分组到一个表格
```

**为什么内部布局没有形成独立表格？**

可能原因：
1. **边缘线连续**: 内部布局的边缘线与外层表格的边缘线相连
2. **共享角点**: 内部单元格与外层单元格共享角点
3. **没有完整的独立边界**: 内部区域没有形成完全独立的矩形网格

---

## 💡 验证假设

### 验证方法1: 打印 cells_to_tables 的中间结果

修改诊断脚本，查看：
1. 从 `intersections_to_cells()` 返回了多少个单元格？
2. `cells_to_tables()` 是如何分组的？
3. 是否有单元格因为不共享角点而被分到不同表格？

### 验证方法2: 检查 edges 的分布

在 table.pdf 中：
- 外层表格的边缘线坐标是什么？
- 内部布局的边缘线坐标是什么？
- 它们是否连续或重叠？

---

## 📊 总结：pdfplumber 的表格识别逻辑

| 步骤 | 功能 | 输入 | 输出 |
|------|------|------|------|
| 1. get_edges() | 提取边缘线 | PDF对象 | edges列表 |
| 2. edges_to_intersections() | 找交点 | edges | intersections字典 |
| 3. intersections_to_cells() | 构建单元格 | intersections | cells列表 |
| 4. cells_to_tables() | **分组成表格** | cells | **tables列表** ★ |

**关键点**:
- **lines 策略**: 依赖 `page.edges`（从PDF矢量对象提取）
- **text 策略**: 从文本对齐推断隐式边缘
- **多表格识别**: 基于**单元格是否共享角点**
- **嵌套表格**: 如果子表的单元格与父表的单元格**不共享角点**，则被识别为独立表格

---

## 🔧 复合表格无法识别的原因

### 根本原因

**table.pdf 的所有单元格（包括内部布局）共享角点**
→ `cells_to_tables()` 将它们全部分组到一个表格
→ 无法识别"嵌套"关系

### 解决方案

**当前实现的问题**:
```python
def _extract_nested_tables_in_cell(self, pdf_page, pymupdf_page, cell_bbox, ...):
    # 问题: 依赖 _cell_has_inner_grid() 的线段检测
    if not self._cell_has_inner_grid(pymupdf_page, cell_bbox):
        return []  # 直接返回，跳过检测
```

**改进方案**:
1. **移除快速筛选**: 在所有大单元格内强制尝试 `within_bbox + find_tables`
2. **降级策略**: 如果 lines 策略失败，尝试 text 策略
3. **验证结果**: 只保留至少2行2列的有效子表

---

## 📌 下一步验证

### 实验1: 打印 cells_to_tables 的分组过程

创建诊断脚本，在 table.pdf 上：
1. 打印所有单元格的坐标
2. 打印 `cells_to_tables()` 的分组过程
3. 查看是否有单元格被分到不同表格

### 实验2: 在大单元格内强制调用 find_tables

```python
# 在大单元格内再次检测
for large_cell in large_cells:
    sub_view = page.within_bbox(large_cell['bbox'])
    sub_tables = sub_view.find_tables(table_settings)
    print(f"子视图检测到 {len(sub_tables)} 个表格")
```

### 实验3: 对比 edges 分布

比较：
- 嵌套示例: 外层表格的 edges vs 内层表格的 edges
- table.pdf: 外层表格的 edges vs 内部布局的 edges

查看它们是否连续或重叠。

---

**分析完成**

_生成时间: 2025-10-27_
_源码版本: pdfplumber 0.11.7_