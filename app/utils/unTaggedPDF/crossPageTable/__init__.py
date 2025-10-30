"""
crossPageTable - 跨页表格处理模块

该模块负责处理跨页表格的识别、合并和单元格内容合并。

## 模块结构

- `cell_merger.py` - 单元格合并器（已拆分）
- `cell_classifier.py` - 单元格智能分类器（使用AI模型判断）
- `column_boundary_strategy.py` - 列边界继承策略
- 其他模块待拆分...

## 使用示例

```python
from crossPageTable import CellMerger, CrossPageCellClassifier

# 单元格合并（基于规则）
merger = CellMerger()
split_indices = merger.detect_split_cells(prev_row, next_row, prev_drawings, next_drawings)
merger.merge_split_cells(prev_row, next_row, split_indices)

# 单元格智能分类（使用AI模型）
classifier = CrossPageCellClassifier()
result = classifier.classify_cell_pair(prev_content, next_content)
if result['should_merge']:
    print(f"应该合并，置信度: {result['confidence']}")
```
"""

# 导出单元格合并器
from .cell_merger import CellMerger

# 导出单元格智能分类器
# from .cell_classifier import CrossPageCellClassifier  # Temporarily disabled due to encoding issue


# 导出列边界继承策略
from .column_boundary_strategy import (
    ColumnBoundaryInheritanceStrategy,
    DisabledInheritanceStrategy,
    ConservativeInheritanceStrategy,
    SmartInheritanceStrategy,
    DEFAULT_STRATEGY
)


# 导出重提取策略
from .reextraction_strategy import (
    ReextractionStrategy,
    DisabledReextractionStrategy,
    ConservativeReextractionStrategy,
    AggressiveReextractionStrategy,
    SmartReextractionStrategy,
    DEFAULT_REEXTRACTION_STRATEGY
)

# 导出向后兼容的函数
from .cell_merger import (
    _cell_has_horizontal_line,
    _detect_split_cells,
    _merge_split_cells
)

__all__ = [
    'CellMerger',
    # 'CrossPageCellClassifier',  # Temporarily disabled
    'ColumnBoundaryInheritanceStrategy',
    'DisabledInheritanceStrategy',
    'ConservativeInheritanceStrategy',
    'SmartInheritanceStrategy',
    'DEFAULT_STRATEGY',
    'ReextractionStrategy',
    'DisabledReextractionStrategy',
    'ConservativeReextractionStrategy',
    'AggressiveReextractionStrategy',
    'SmartReextractionStrategy',
    'DEFAULT_REEXTRACTION_STRATEGY',

    '_cell_has_horizontal_line',
    '_detect_split_cells',
    '_merge_split_cells',
]