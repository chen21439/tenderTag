# crossPageTable - 跨页表格处理模块

## 概述

该目录包含跨页表格处理的所有功能，从原来的 `cross_page_merger.py`（2036行）中逐步拆分而来。

---

## 重构进度

### ✅ 已完成

- [x] **`cell_merger.py`** - 单元格合并器（基于规则）
  - 功能：检测并合并被分页符截断的单元格内容
  - 行数：~370 行
  - 日期：2025-10-29
  - 向后兼容：保留了模块级函数 `_detect_split_cells()`, `_merge_split_cells()`, `_cell_has_horizontal_line()`

- [x] **`cell_classifier.py`** - 单元格智能分类器（基于AI）
  - 功能：使用 AI 模型判断跨页单元格/行是否应该合并
  - 行数：~630 行
  - 日期：2025-10-29
  - 特性：
    - 基于 Qwen3-32B 模型进行智能判断
    - 低温度推理（temperature=0.1）保证确定性
    - 支持**单元格级别判断**（td）和**行级别判断**（tr）
    - 支持单个/批量分类
    - 智能字符截取（取最后/最前 n 个字符）
    - 直接分析 raw.json 中的 hint 数据
    - 返回 JSON 格式（should_merge、confidence、reason）

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
- `crossPageTable/cell_merger.py` - 单元格合并器（370行，基于规则）
- `crossPageTable/cell_classifier.py` - 单元格智能分类器（400行，基于AI）

### 导入关系
```
cross_page_merger.py
    ↓ 导入
crossPageTable.cell_merger
    - _detect_split_cells()
    - _merge_split_cells()
    - _cell_has_horizontal_line()

pdf_content_extractor.py 或其他模块
    ↓ 可选导入
crossPageTable.cell_classifier
    - CrossPageCellClassifier
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
├── cell_merger.py           # 单元格合并器（基于规则） ✅
├── cell_classifier.py       # 单元格智能分类器（基于AI） ✅
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

### 新模块使用方式（已实现）

```python
from crossPageTable import CellMerger, CrossPageCellClassifier

# 方式1：基于规则的单元格合并（适用于明确的几何特征）
cell_merger = CellMerger(coverage_threshold=0.5)
split_indices = cell_merger.detect_split_cells(
    prev_last_row, next_first_row,
    prev_drawings, next_drawings
)
cell_merger.merge_split_cells(prev_row, next_row, split_indices)

# 方式2：基于AI的智能判断（适用于语义判断）
classifier = CrossPageCellClassifier()

# 单个单元格对判断
result = classifier.classify_cell_pair(
    prev_cell_content="根据投标人提供的项目技术方案，包括总体架构设计、业务架构设计、数据架构设计、技术架构设",
    next_cell_content="计、网络架构设计、与现有国土空间规划"一张图"实施监测系统及相关系统对接方案等方面进行综合评审。"
)
print(f"应该合并: {result['should_merge']}, 置信度: {result['confidence']}")

# 批量分析 raw.json 中的 hint 数据（单元格级别）
results = classifier.analyze_raw_json_with_hints(raw_json_data, hints_by_page)
print(f"分析了 {results['total_cell_pairs']} 个单元格对")
print(f"应该合并: {results['summary']['should_merge']} 个")
print(f"不应合并: {results['summary']['should_not_merge']} 个")

# 方式3：行级别判断（推荐用于跨页表格识别）
# 准备行对数据
row_pairs = [
    {
        "prev_row": {
            "第0列": "技术方案设计...",
            "第1列": "5分",
            "第2列": "优秀"
        },
        "next_row": {
            "第0列": "...后续内容",
            "第1列": "",
            "第2列": ""
        },
        "context": {
            "prev_page": 1,
            "next_page": 2,
            "hint_score": 0.95
        }
    }
]

# 批量判断（自动截取最后/最前n个字符）
row_results = classifier.classify_row_pairs_batch(row_pairs)
for result in row_results:
    print(f"应该合并: {result['should_merge']}, 置信度: {result['confidence']}")
```

---

## 测试策略

### 单元测试

每个拆分的模块都应该有对应的单元测试：

```
tests/
└── crossPageTable/
    ├── test_cell_merger.py           # ✅ 已创建模块，待添加测试
    ├── test_cell_classifier.py       # ✅ 已创建模块，待添加测试
    ├── test_fingerprint.py
    ├── test_scoring.py
    ├── test_chain_finder.py
    └── ...
```

**测试说明**：
- `cell_classifier.py` 包含内置的 `main()` 测试函数，可以直接运行：
  ```bash
  python app/utils/unTaggedPDF/crossPageTable/cell_classifier.py
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

### 2025-10-29（下午2）
- ✅ 扩展 `cell_classifier.py` 添加行级别判断功能（630行）
- ✅ 实现 `classify_row_pairs_batch()` 方法（批量行判断）
- ✅ 实现 `_truncate_text()` 方法（字符截取：最后/最前n个字符）
- ✅ 添加行级别 system_prompt
- ✅ 创建测试脚本 `test_row_classifier.py`
- ✅ 更新 README.md 文档

### 2025-10-29（下午1）
- ✅ 创建 `cell_classifier.py` 模块（400行）
- ✅ 集成 Qwen3-32B 模型用于智能判断
- ✅ 实现 `analyze_raw_json_with_hints()` 方法
- ✅ 更新 `__init__.py` 导出 `CrossPageCellClassifier`
- ✅ 更新 README.md 文档

### 2025-10-29（上午）
- ✅ 创建 `crossPageTable/` 目录
- ✅ 拆分 `cell_merger.py` 模块（370行）
- ✅ 创建 `__init__.py` 导出接口
- ✅ 创建本 README.md 文档

---

## 下一步计划

1. **集成 AI 分类器到主流程**：在 raw.json 生成后调用 `CrossPageCellClassifier`
2. 添加 `cell_merger.py` 和 `cell_classifier.py` 的单元测试
3. 拆分 `models.py`（数据结构）
4. 拆分 `utils.py`（工具函数）
5. 逐步拆分其他模块...

---

**重构原则**：稳步前进，保持系统稳定，按需拆分。