# crossPageTable - 跨页表格处理模块

## 概述

该目录包含跨页表格处理的所有功能，从原来的 `cross_page_merger.py`（2036行）中逐步拆分而来。

---

## 重构进度

### ✅ 已完成

- [x] **`cell_merger.py`** - 单元格合并器
  - 功能：检测并合并被分页符截断的单元格内容
  - 行数：~370 行
  - 日期：2025-10-29
  - 向后兼容：保留了模块级函数 `_detect_split_cells()`, `_merge_split_cells()`, `_cell_has_horizontal_line()`

### 🔜 待拆分

按优先级排序：

1. **`models.py`** - 数据结构
   - `TableFingerprint` - 表格指纹数据类
   - `MergeCandidate` - 合并候选数据类
   - 预计行数：~50 行

2. **`utils.py`** - 工具函数
   - `calculate_jaccard_similarity()` - Jaccard相似度
   - `normalize_to_page_width()` - 坐标归一化
   - `hash_col_paths()` - 列路径哈希
   - 预计行数：~80 行

3. **`fingerprint.py`** - 指纹生成器
   - `FingerprintGenerator` 类
   - 功能：为表格生成几何/结构/视觉特征指纹
   - 预计行数：~250 行

4. **`scoring.py`** - 得分计算器
   - `TableScorer` 类
   - 功能：计算表格匹配得分（几何、结构、视觉）
   - 预计行数：~250 行

5. **`header_handler.py`** - 表头处理器
   - `HeaderHandler` 类
   - 功能：表头恢复、去重、延迟识别
   - 预计行数：~300 行

6. **`continuation_hint.py`** - 续页提示生成器
   - `ContinuationHintBuilder` 类
   - 功能：生成续页hints，补齐缺失列
   - 预计行数：~400 行

7. **`chain_finder.py`** - 合并链识别器
   - `ChainFinder` 类
   - 功能：识别需要合并的表格链，检查正文隔断
   - 预计行数：~300 行

8. **`table_merger.py`** - 表格合并器
   - `TableMerger` 类
   - 功能：合并表段，拼接数据行
   - 预计行数：~200 行

9. **`merger.py`** - 主协调类
   - `CrossPageTableMerger` 类（重构版）
   - 功能：组合所有子模块，提供统一入口
   - 预计行数：~150 行

---

## 重构策略

### 渐进式重构

采用"按需拆分"策略：
- **不一次性重构所有代码**（避免大规模改动风险）
- **在需要修改某个功能时，优先拆分该模块**
- **保持向后兼容**，避免影响现有代码

### 拆分原则

1. **单一职责**：每个模块只负责一个功能领域
2. **低耦合**：模块间依赖尽量少
3. **高内聚**：相关功能聚合在一起
4. **向后兼容**：保留旧的函数签名，标记为 deprecated

---

## 当前架构

### 原始文件（未拆分部分）
- `cross_page_merger.py` - 主文件（1666行剩余）
  - 仍包含：指纹生成、得分计算、合并链识别、表格合并、表头处理、续页提示等

### 已拆分模块
- `crossPageTable/cell_merger.py` - 单元格合并器（370行）

### 导入关系
```
cross_page_merger.py
    ↓ 导入
crossPageTable.cell_merger
    - _detect_split_cells()
    - _merge_split_cells()
    - _cell_has_horizontal_line()
```

---

## 目标架构（完整拆分后）

```
crossPageTable/
├── __init__.py              # 导出所有公共接口
├── README.md                # 本文档
│
├── models.py                # 数据结构
├── utils.py                 # 工具函数
│
├── fingerprint.py           # 指纹生成器
├── scoring.py               # 得分计算器
├── chain_finder.py          # 合并链识别器
├── table_merger.py          # 表格合并器
├── header_handler.py        # 表头处理器
├── cell_merger.py           # 单元格合并器 ✅
├── continuation_hint.py     # 续页提示生成器
│
└── merger.py                # 主协调类
```

---

## 使用示例

### 当前使用方式（未完全拆分）

```python
from cross_page_merger import CrossPageTableMerger

# 创建合并器（enable_cell_merge 控制单元格合并）
merger = CrossPageTableMerger(
    score_threshold=0.70,
    enable_cell_merge=False  # 默认关闭
)

# 执行合并
merged_tables = merger.merge_all_tables(
    tables,
    page_widths,
    page_drawings,
    layout_index
)
```

### 未来使用方式（完全拆分后）

```python
from crossPageTable import CrossPageTableMerger, CellMerger

# 方式1：使用主协调类（推荐）
merger = CrossPageTableMerger(enable_cell_merge=False)
merged_tables = merger.merge_all_tables(...)

# 方式2：直接使用单元格合并器（细粒度控制）
cell_merger = CellMerger(coverage_threshold=0.5)
split_indices = cell_merger.detect_split_cells(...)
cell_merger.merge_split_cells(...)
```

---

## 测试策略

### 单元测试

每个拆分的模块都应该有对应的单元测试：

```
tests/
└── crossPageTable/
    ├── test_cell_merger.py           # ✅ 已创建模块，待添加测试
    ├── test_fingerprint.py
    ├── test_scoring.py
    ├── test_chain_finder.py
    └── ...
```

### 集成测试

确保重构后功能与原来完全一致：
- 使用相同的测试PDF
- 对比重构前后的输出结果
- 行数、列数、内容完全匹配

---

## 贡献指南

### 如何拆分一个新模块？

1. **识别功能边界**
   - 找到相关的方法/函数
   - 确定依赖关系

2. **创建新文件**
   - 在 `crossPageTable/` 目录下创建新模块
   - 编写清晰的文档字符串

3. **迁移代码**
   - 从 `cross_page_merger.py` 复制相关代码
   - 封装成类或函数
   - 保留向后兼容的接口

4. **更新导入**
   - 在 `__init__.py` 中导出新模块
   - 更新 `cross_page_merger.py` 的导入

5. **测试**
   - 运行原有测试，确保功能不变
   - 添加新模块的单元测试

6. **更新文档**
   - 更新本 README.md
   - 标记已完成的模块

---

## 注意事项

### 向后兼容

- ⚠️ **不要删除**原来的 `cross_page_merger.py` 文件
- ⚠️ **保留**所有公共函数的签名
- ✅ **可以标记**为 deprecated，但不能删除

### 导入路径

```python
# ✅ 推荐：从新模块导入
from crossPageTable import CellMerger

# ✅ 兼容：从旧文件导入（内部重定向到新模块）
from cross_page_merger import _detect_split_cells
```

---

## 重构收益

### 代码质量
- ✅ 文件大小：从 2036 行拆分为多个 < 400 行的模块
- ✅ 可读性：职责清晰，易于理解
- ✅ 可维护性：修改某个功能只需修改对应模块

### 开发效率
- ✅ 可测试性：每个模块可独立测试
- ✅ 可扩展性：添加新功能无需修改主文件
- ✅ 协作友好：多人可并行开发不同模块

---

## 更新日志

### 2025-10-29
- ✅ 创建 `crossPageTable/` 目录
- ✅ 拆分 `cell_merger.py` 模块（370行）
- ✅ 创建 `__init__.py` 导出接口
- ✅ 创建本 README.md 文档

---

## 下一步计划

1. 添加 `cell_merger.py` 的单元测试
2. 拆分 `models.py`（数据结构）
3. 拆分 `utils.py`（工具函数）
4. 逐步拆分其他模块...

---

**重构原则**：稳步前进，保持系统稳定，按需拆分。