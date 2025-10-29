"""
crossPageTable - 跨页表格处理模块

该模块负责处理跨页表格的识别、合并和单元格内容合并。

## 模块结构

- `cell_merger.py` - 单元格合并器（已拆分）
- 其他模块待拆分...

## 使用示例

```python
from crossPageTable import CellMerger

# 单元格合并
merger = CellMerger()
split_indices = merger.detect_split_cells(prev_row, next_row, prev_drawings, next_drawings)
merger.merge_split_cells(prev_row, next_row, split_indices)
```
"""

# 导出单元格合并器
from .cell_merger import CellMerger

# 导出向后兼容的函数
from .cell_merger import (
    _cell_has_horizontal_line,
    _detect_split_cells,
    _merge_split_cells
)

__all__ = [
    'CellMerger',
    '_cell_has_horizontal_line',
    '_detect_split_cells',
    '_merge_split_cells',
]