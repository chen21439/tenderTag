"""
crossPageTable - 跨页表格处理模块

该模块负责处理跨页表格的识别、合并和行级别内容判断。

## 模块结构

- `cell_merger.py` - 单元格合并器（基于规则）
- `cell_classifier.py` - 跨页行智能分类器（使用AI模型判断行级别合并）
- 其他模块待拆分...

## 使用示例

```python
from crossPageTable import CellMerger, CrossPageCellClassifier

# 单元格合并（基于规则）
merger = CellMerger()
split_indices = merger.detect_split_cells(prev_row, next_row, prev_drawings, next_drawings)
merger.merge_split_cells(prev_row, next_row, split_indices)

# 行级别智能判断（使用AI模型）
classifier = CrossPageCellClassifier()
row_pairs = [
    {
        "prev_row": {"第0列": "内容...", "第1列": "5分"},
        "next_row": {"第0列": "...后续内容", "第1列": ""},
        "context": {"prev_page": 1, "next_page": 2, "hint_score": 0.95}
    }
]
results = classifier.classify_row_pairs_batch(row_pairs)
for result in results:
    if result['should_merge']:
        print(f"应该合并，置信度: {result['confidence']}")
```
"""

# 导出单元格合并器
from .cell_merger import CellMerger

# 导出单元格智能分类器（行级别判断）
from .cell_classifier import CrossPageCellClassifier

__all__ = [
    'CellMerger',
    'CrossPageCellClassifier',
]