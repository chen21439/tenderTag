# 多层表头引入后的列数问题分析

## 问题描述

引入多层表头功能后，`table.json`中的`columns`数组长度变少了。

**典型现象**：
- 第5页第3个表格：应该是5列，但`columns`只有3列
- 第8页表格：应该是5列，但`columns`只有3列

## 数据对比

### 第8页表格（temp_009 / doc004）

#### raw.json（合并前）
```json
{
  "id": "temp_009",
  "page": 8,
  "header_info": {
    "row_levels": 2,  // 前2列是行表头
    "col_levels": 1
  },
  "columns": [
    {"id": "c003", "index": 2},  // 数据列从index=2开始
    {"id": "c004", "index": 3},
    {"id": "c005", "index": 4}
  ],
  "rows": [{
    "cells": [
      {"col_id": "c001"},  // ← 行表头列1
      {"col_id": "c002"},  // ← 行表头列2
      {"col_id": "c003"},  // ← 数据列1
      {"col_id": "c004"},  // ← 数据列2
      {"col_id": "c005"}   // ← 数据列3
    ]
  }]
}
```

#### table.json（合并后）
```json
{
  "id": "doc004",
  "page": 8,
  "header_info": {
    "row_levels": 2,
    "col_levels": 1
  },
  "columns": [
    {"id": "c003", "index": 2},  // 只有3列！
    {"id": "c004", "index": 3},
    {"id": "c005", "index": 4}
  ],
  "rows": [{
    "cells": [
      {"col_id": "c001"},  // 5个cells，正确
      {"col_id": "c002"},
      {"col_id": "c003"},
      {"col_id": "c004"},
      {"col_id": "c005"}
    ]
  }]
}
```

### 第5页第3个表格（temp_006 / doc008）

#### raw.json
```json
{
  "id": "temp_006",
  "page": 5,
  "header_info": {
    "row_levels": 2,
    "col_levels": 2
  },
  "columns": 3列 (c003, c004, c005),
  "rows": [{
    "cells": 5个 (c001, c002, c003, c004, c005)
  }]
}
```

#### table.json
```json
{
  "id": "doc008",
  "page": 5,
  "header_info": {
    "row_levels": 2,
    "col_levels": 2
  },
  "columns": 3列 (c003, c004, c005),
  "rows": [{
    "cells": 5个 (c001, c002, c003, c004, c005)
  }]
}
```

## 问题分析

### 1. 当前设计逻辑

当`row_levels > 0`时，系统将表格列分为两类：

- **行表头列**（Row Header Columns）：前`row_levels`列
  - 用于标识每行的层级路径
  - 内容存储在`rowPath`中
  - **不包含在`columns`数组中**

- **数据列**（Data Columns）：从第`row_levels`列开始
  - 实际的数据列
  - **包含在`columns`数组中**
  - `index`从`row_levels`开始

### 2. columns vs cells 的差异

| 字段 | 含义 | 当前行为 | 问题 |
|------|------|----------|------|
| `columns` | 定义数据列结构 | 只包含数据列（3列） | ❌ 与实际列数不符（5列） |
| `cells` | 单元格数据 | 包含所有列（5列） | ✅ 数据完整 |

### 3. 为什么会这样设计

**设计初衷**：
- `columns`定义的是"可变数据列"
- 行表头列（如"评审因素分类"、"评审内容"）被视为"行标识"，不是数据列
- 数据在`cells`中是完整的，包含所有列

**问题**：
- 对于下游使用者，`columns.length`不等于实际列数
- 如果依赖`columns`来确定列数，会得到错误结果（3列而非5列）

## 影响范围

### 受影响的表格

所有`row_levels > 0`的表格都会有这个问题：

- 第5页第3个表格（评审标准表）：row_levels=2, columns=3列, 实际5列
- 第8页表格（综合评审方案和承诺）：row_levels=2, columns=3列, 实际5列
- 第9页表格（服务团队）：row_levels=2, columns=3列, 实际5列

### 不受影响的表格

`row_levels = 0`的表格（无行表头）：
- columns数量 = 实际列数
- 不受影响

## 修复方案选项

### 方案1：columns包含所有列（推荐）

**修改点**：`table_extractor.py`中的`_build_table_with_multi_level_headers`

**修改内容**：
```python
# 当前：只添加数据列到columns
for data_col_idx in range(len(col_paths)):
    actual_col_idx = row_levels + data_col_idx
    columns.append({
        "id": f"c{actual_col_idx + 1:03d}",
        "index": actual_col_idx,
        ...
    })

# 修改为：添加所有列到columns
# 1. 先添加行表头列
for row_col_idx in range(row_levels):
    columns.append({
        "id": f"c{row_col_idx + 1:03d}",
        "index": row_col_idx,
        "name": "",  # 行表头列名为空
        "path": [],
        "is_row_header": True  # 标记为行表头列
    })

# 2. 再添加数据列
for data_col_idx in range(len(col_paths)):
    actual_col_idx = row_levels + data_col_idx
    columns.append({
        "id": f"c{actual_col_idx + 1:03d}",
        "index": actual_col_idx,
        "name": col_paths[data_col_idx][-1] if col_paths[data_col_idx] else "",
        "path": col_paths[data_col_idx],
        "is_row_header": False
    })
```

**优点**：
- ✅ `columns.length`等于实际列数
- ✅ 下游使用者可以正确获取列数
- ✅ 可以通过`is_row_header`区分行表头列和数据列

**缺点**：
- ⚠️ 需要修改下游代码，适配`is_row_header`字段

### 方案2：添加total_columns字段

**修改点**：在`header_info`中添加`total_columns`字段

```python
{
  "header_info": {
    "row_levels": 2,
    "col_levels": 2,
    "data_columns": 3,      // 数据列数
    "total_columns": 5      // 总列数（新增）
  },
  "columns": [...]  // 仍然只包含数据列
}
```

**优点**：
- ✅ 不改变`columns`的语义
- ✅ 提供完整信息

**缺点**：
- ⚠️ 下游需要知道使用`total_columns`而不是`columns.length`

### 方案3：回退多层表头功能

**最简单的方案**：revert到引入多层表头之前

**优点**：
- ✅ 恢复原有行为
- ✅ 不需要处理复杂的行列表头逻辑

**缺点**：
- ❌ 失去多层表头支持
- ❌ 复杂表格（如评审标准表）的结构化会变差

## 建议

### 短期建议（推荐方案1）

修改`columns`数组，包含所有列（行表头列+数据列），并添加`is_row_header`标记：

```json
{
  "columns": [
    {"id": "c001", "index": 0, "name": "", "is_row_header": true},
    {"id": "c002", "index": 1, "name": "", "is_row_header": true},
    {"id": "c003", "index": 2, "name": "评审标准", "is_row_header": false},
    {"id": "c004", "index": 3, "name": "分值", "is_row_header": false},
    {"id": "c005", "index": 4, "name": "客观/主观", "is_row_header": false}
  ]
}
```

### 长期建议

考虑是否需要多层表头功能：
- 如果下游系统不需要行列表头的层级信息，可以关闭该功能
- 如果需要，建议完善多层表头的文档和示例，避免理解偏差

## 相关文件

- `app/utils/unTaggedPDF/table_extractor.py:825-992` - `_build_table_with_multi_level_headers`方法
- `app/utils/unTaggedPDF/header_analyzer.py` - 多层表头识别算法
- `app/utils/unTaggedPDF/cross_page_merger.py:857-897` - 跨页合并时的表头恢复逻辑

## Commit记录

如需回退，revert以下相关的多层表头功能commits（按实际commit hash查找）：
- feat: 添加多层表头支持
- refactor: 完善各个py功能划分
- feature: 支持纯嵌套表格的文字提取