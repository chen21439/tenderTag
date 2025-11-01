# CrossPageTableMerger 重构方案

## 当前问题
`cross_page_merger.py` 文件有 2036 行代码，包含了太多功能，不便于维护和测试。

## CrossPageTableMerger 功能清单

### 1. **数据结构** (Lines 48-95)
- `TableFingerprint` - 表格指纹数据类
- `MergeCandidate` - 合并候选数据类

### 2. **指纹生成** (Lines 124-218)
- `generate_fingerprint()` - 生成表格指纹
- `_extract_header_rows()` - 提取表头行
- `_extract_first_data_row()` - 提取首行数据
- `_detect_table_borders()` - 检测表格顶底边框

### 3. **得分计算** (Lines 339-545)
- `calculate_geometry_score()` - 几何特征得分（列边界、边距、表宽）
- `calculate_structure_score()` - 结构特征得分（列数、表头层级）
- `calculate_visual_score()` - 视觉特征得分（边框开口状态）
- `calculate_match_score()` - 综合匹配得分

### 4. **合并链识别** (Lines 547-754)
- `find_merge_chains()` - 识别需要合并的表格链
  - 生成指纹
  - 两两匹配打分
  - 门槛检查
  - 正文隔断检查
  - 列补齐逻辑
  - 构建合并链

### 5. **表格合并** (Lines 756-889)
- `merge_tables()` - 合并一条链中的多个表段
  - 表头恢复
  - 数据行拼接
  - 跨页单元格合并（可配置）
  - bbox合并
  - 元数据更新

### 6. **表头处理** (Lines 891-1016, 1114-1171)
- `_recover_misidentified_headers()` - 恢复被误判为表头的数据行
- `detect_repeated_header()` - 检测续页重复表头
- `_analyze_and_apply_headers()` - 延迟表头识别（新增）

### 7. **正文隔断检查** (Lines 1018-1112)
- `_has_paragraph_between()` - 检查表格间是否有正文隔断

### 8. **续页提示生成** (Lines 1173-1461)
- `build_continuation_hints()` - 生成续页列模板hint
- `_extract_column_xs()` - 提取列边界
- `_dedup_edges()` - 去重边界
- `_ensure_frame_edges()` - 确保左右边框
- `_has_horizontal_border()` - 检测横线
- `_try_repair_missing_columns()` - 尝试补齐缺失列
- `_bbox_almost_equal()` - 检查bbox是否相等

### 9. **主入口** (Lines 1589-1667)
- `merge_all_tables()` - 协调所有功能的主入口

### 10. **模块级工具函数** (Lines 1670-2036)
- `_calculate_jaccard_similarity()` - Jaccard相似度
- `_calculate_col_paths_similarity()` - 列路径相似度
- `_hash_col_paths()` - 列路径哈希
- `_normalize_to_page_width()` - 坐标归一化
- **单元格合并**：
  - `_cell_has_horizontal_line()` - 检测单元格横线
  - `_detect_split_cells()` - 检测截断单元格
  - `_merge_split_cells()` - 合并截断单元格

---

## 重构方案：拆分到 `crossPageTable/` 目录

### 目录结构
```
app/utils/unTaggedPDF/
├── crossPageTable/
│   ├── __init__.py                  # 导出主类和数据结构
│   ├── models.py                    # 数据结构（TableFingerprint, MergeCandidate）
│   ├── fingerprint.py               # 指纹生成
│   ├── scoring.py                   # 得分计算
│   ├── chain_finder.py              # 合并链识别
│   ├── table_merger.py              # 表格合并逻辑
│   ├── header_handler.py            # 表头处理
│   ├── cell_merger.py               # 单元格合并（可选功能）
│   ├── continuation_hint.py         # 续页提示生成
│   ├── utils.py                     # 工具函数
│   └── merger.py                    # 主协调类（CrossPageTableMerger）
```

---

## 各模块职责

### 1. `models.py` - 数据结构
```python
from dataclasses import dataclass

@dataclass
class TableFingerprint:
    """表格指纹"""
    ...

@dataclass
class MergeCandidate:
    """合并候选"""
    ...
```

### 2. `fingerprint.py` - 指纹生成器
```python
class FingerprintGenerator:
    """表格指纹生成器"""

    def generate(self, table, page_width, page_drawings) -> TableFingerprint:
        """生成表格指纹"""

    def _detect_table_borders(self, bbox, page_drawings):
        """检测表格边框"""

    def _extract_header_rows(self, table, col_levels):
        """提取表头行"""

    def _extract_first_data_row(self, table, col_levels):
        """提取首行数据"""
```

### 3. `scoring.py` - 得分计算器
```python
class TableScorer:
    """表格匹配得分计算器"""

    def calculate_geometry_score(self, fp1, fp2):
        """几何特征得分"""

    def calculate_structure_score(self, fp1, fp2):
        """结构特征得分"""

    def calculate_visual_score(self, fp1, fp2):
        """视觉特征得分"""

    def calculate_match_score(self, fp1, fp2) -> MergeCandidate:
        """综合匹配得分"""
```

### 4. `chain_finder.py` - 合并链识别器
```python
class ChainFinder:
    """合并链识别器"""

    def __init__(self, fingerprint_gen, scorer, ...):
        self.fingerprint_gen = fingerprint_gen
        self.scorer = scorer

    def find_merge_chains(self, tables, page_widths, ...):
        """识别需要合并的表格链"""

    def _has_paragraph_between(self, prev_table, next_table, layout_index):
        """检查正文隔断"""
```

### 5. `table_merger.py` - 表格合并器
```python
class TableMerger:
    """表格合并器"""

    def __init__(self, enable_cell_merge=False):
        self.enable_cell_merge = enable_cell_merge

    def merge_tables(self, tables, table_ids, page_drawings):
        """合并一条链中的多个表段"""
```

### 6. `header_handler.py` - 表头处理器
```python
class HeaderHandler:
    """表头处理器"""

    def recover_misidentified_headers(self, table_segments):
        """恢复被误判为表头的数据行"""

    def detect_repeated_header(self, prev_table, next_table):
        """检测续页重复表头"""

    def analyze_and_apply_headers(self, table, debug=False):
        """延迟表头识别"""
```

### 7. `cell_merger.py` - 单元格合并器（独立可选模块）
```python
class CellMerger:
    """跨页单元格合并器"""

    def detect_split_cells(self, prev_last_row, next_first_row, prev_drawings, next_drawings):
        """检测截断的单元格"""

    def merge_split_cells(self, prev_row, next_row, split_indices):
        """合并截断的单元格"""

    def _cell_has_horizontal_line(self, cell_bbox, y_position, drawings):
        """检测单元格横线"""
```

### 8. `continuation_hint.py` - 续页提示生成器
```python
class ContinuationHintBuilder:
    """续页提示生成器"""

    def build_hints(self, tables, page_widths, page_heights, ...):
        """生成续页hints"""

    def _extract_column_xs(self, table):
        """提取列边界"""

    def _try_repair_missing_columns(self, prev_table, next_table, ...):
        """尝试补齐缺失列"""
```

### 9. `utils.py` - 工具函数
```python
def calculate_jaccard_similarity(list1, list2, tolerance=0.01):
    """Jaccard相似度"""

def normalize_to_page_width(value, page_width):
    """坐标归一化"""

def hash_col_paths(col_paths):
    """列路径哈希"""
```

### 10. `merger.py` - 主协调类
```python
class CrossPageTableMerger:
    """跨页表格合并器（主协调类）"""

    def __init__(self, score_threshold=0.70, ..., enable_cell_merge=False):
        # 组合所有子模块
        self.fingerprint_gen = FingerprintGenerator()
        self.scorer = TableScorer(...)
        self.chain_finder = ChainFinder(...)
        self.table_merger = TableMerger(enable_cell_merge)
        self.header_handler = HeaderHandler()
        self.cell_merger = CellMerger() if enable_cell_merge else None
        self.hint_builder = ContinuationHintBuilder()

    def merge_all_tables(self, tables, page_widths, ...):
        """主入口：识别并合并所有跨页表格"""
        # 1. 识别合并链
        chains = self.chain_finder.find_merge_chains(...)

        # 2. 执行合并
        merged = []
        for chain in chains:
            merged_table = self.table_merger.merge_tables(...)
            merged.append(merged_table)

        # 3. 延迟表头识别
        for table in merged:
            if not table.get('header_info', {}).get('header_detected'):
                self.header_handler.analyze_and_apply_headers(table)

        return merged
```

---

## 重构优势

### 1. **职责清晰**
每个模块只负责一个功能领域，便于理解和维护。

### 2. **可测试性强**
每个子模块可以独立测试，不需要构造完整的表格数据。

### 3. **可扩展性好**
- 需要新的得分算法？修改 `scoring.py`
- 需要新的单元格合并策略？修改 `cell_merger.py`
- 不影响其他模块

### 4. **可配置性强**
- `CellMerger` 可以作为独立模块，按需启用/禁用
- 各个模块的参数可以独立配置

### 5. **代码复用**
- `FingerprintGenerator` 可以被其他表格分析功能复用
- `TableScorer` 可以用于其他表格匹配场景

---

## 向后兼容

保留原有的导入路径：

```python
# app/utils/unTaggedPDF/__init__.py
from .crossPageTable import CrossPageTableMerger

# 或者保留旧的导入方式
from .cross_page_merger import CrossPageTableMerger  # 标记为 deprecated
```

---

## 迁移步骤

1. ✅ 创建 `crossPageTable/` 目录
2. ✅ 创建各子模块文件（先空实现）
3. ✅ 迁移数据结构到 `models.py`
4. ✅ 迁移指纹生成逻辑到 `fingerprint.py`
5. ✅ 迁移得分计算逻辑到 `scoring.py`
6. ✅ 迁移其他模块...
7. ✅ 更新主类 `merger.py`，组合所有子模块
8. ✅ 更新导入路径
9. ✅ 测试所有功能
10. ✅ 标记 `cross_page_merger.py` 为 deprecated

---

## 是否执行重构？

这是一个较大的重构任务，需要：
- 创建 10+ 个新文件
- 迁移 2000+ 行代码
- 更新所有导入路径
- 全面测试

**建议**：
- 如果当前代码工作正常且不需要频繁修改，可以暂缓重构
- 如果需要频繁添加新功能或修改逻辑，建议尽快重构
- 可以采用**渐进式重构**：先拆分最独立的模块（如 `cell_merger.py`），逐步完成

---

**你的选择是什么？**
1. 立即执行完整重构
2. 渐进式重构（先拆分某个模块）
3. 暂缓重构，只创建目录结构和文档