# TODO: 跨页单元格合并功能

## 需求描述

当同一个单元格被分页符截断时，在跨页表格合并时需要识别并将其合并为同一个单元格。

## 场景示例

### Page 3 底部
```
┌────────┬────────┬──────────────┐
│        │        │ 长文本内容   │  ← 这个单元格被截断
│  合并  │  合并  │ 第一部分...  │
│  单元  │  单元  │ （续页）     │
│  格    │  格    ├──────────────┤  ← 没有完整底边线
└────────┴────────┴──────────────┘
```

### Page 4 顶部
```
┌────────┬────────┬──────────────┐  ← 没有完整顶边线
│        │        │ （接上页）   │  ← 这是同一单元格的第二部分
│  合并  │  合并  │ 第二部分...  │
│  单元  │  单元  │ 结束         │
│  格    │  格    │              │
└────────┴────────┴──────────────┘
```

## 特征识别

### 视觉特征（基于线条）
1. **Page 3 最后一行的某单元格**：
   - 该单元格的**底边没有完整横线**（或横线缺失）
   - 左右边界有垂直线（单元格边界完整）

2. **Page 4 第一行的对应单元格**：
   - 该单元格的**顶边没有完整横线**（或横线缺失）
   - 左右边界有垂直线（单元格边界完整）

### 结构特征
- **前几列**可能是多行合并的单元格（rowspan > 1），内容为空或重复
- **被截断的列**：内容较长，上下都没有封闭横线

## 实现方案（分步骤）

### Phase 1: 识别跨页截断单元格（简单场景）

**目标**：在合并时识别哪些单元格是被截断的

**步骤**：
1. 在 `merge_tables()` 方法中，合并两个相邻表段前：
   - 检查上页最后一行（last_row）的每个单元格
   - 检查下页第一行（first_row）的对应单元格（按列索引）

2. **单元格截断判定条件**（基于特征的直接判断）：
   ```python
   def is_cell_split_at_page_break(prev_cell, next_cell, prev_drawings, next_drawings):
       """
       判断两个单元格是否是同一单元格的跨页截断

       使用明确的特征判断（不使用打分机制）：

       必须同时满足以下条件：
       1. 列位置一致：col_id 相同 或 x坐标范围重叠 > 80%
       2. 上页单元格：底边没有完整横线（覆盖率 < 50%）
       3. 下页单元格：顶边没有完整横线（覆盖率 < 50%）

       返回：True/False（截断/非截断）
       """
   ```

3. **线条检测方法**（利用现有的 page_drawings）：
   ```python
   def cell_has_bottom_border(cell_bbox, page_drawings):
       """
       检查单元格底边是否有完整横线

       实现：
       - 从 page_drawings 中查找 cell_bbox[3] ± 阈值范围内的横线
       - 判断横线是否覆盖了单元格底边的大部分（如 ≥80%）
       """

   def cell_has_top_border(cell_bbox, page_drawings):
       """检查单元格顶边是否有完整横线"""
   ```

### Phase 2: 合并截断单元格

**操作**：
1. 当检测到单元格截断时：
   - 将下页第一行对应单元格的内容**追加**到上页最后一行对应单元格
   - **删除**下页第一行对应单元格（或标记为已合并）
   - 调整 rowspan（如果涉及多行合并）

2. **内容合并策略**：
   ```python
   merged_content = prev_cell['content'] + next_cell['content']
   # 或根据分隔符智能合并：
   # merged_content = prev_cell['content'].rstrip('，、') + next_cell['content']
   ```

3. **bbox合并**：
   - 保留上页单元格的 bbox（因为跨页，bbox不能直接合并）
   - 在元数据中记录：`"split_across_pages": True`

### Phase 3: 处理复杂场景

**扩展功能**：
1. **多列同时截断**：
   - 遍历所有列，分别检测和合并

2. **多行截断**（某个 rowspan > 1 的单元格被截断）：
   - 检测上页最后 N 行中 rowspan 跨越分页符的单元格
   - 合并时调整 rowspan 值

3. **嵌套表格截断**：
   - 如果被截断的单元格包含嵌套表格（nested_tables）
   - 需要递归处理嵌套表格的合并

## 代码位置

### 主要修改点
- **文件**：`cross_page_merger.py`
- **方法**：`merge_tables()`（lines 752-853）

### 新增辅助方法
```python
def _detect_split_cells(
    self,
    prev_last_row: Dict,
    next_first_row: Dict,
    prev_drawings: List,
    next_drawings: List
) -> List[Tuple[int, int]]:
    """
    检测跨页截断的单元格

    Returns:
        [(col_index_prev, col_index_next), ...] 被截断的单元格索引对
    """
    pass

def _merge_split_cells(
    self,
    prev_row: Dict,
    next_row: Dict,
    split_indices: List[Tuple[int, int]]
) -> None:
    """
    合并截断的单元格（原地修改 prev_row 和 next_row）
    """
    pass

def _cell_has_horizontal_line(
    self,
    cell_bbox: List[float],
    y_position: float,  # 检查的Y坐标（顶边或底边）
    drawings: List[Dict],
    coverage_threshold: float = 0.8
) -> bool:
    """
    检查单元格的某条边（顶边或底边）是否有完整横线

    Args:
        cell_bbox: 单元格bbox [x0, y0, x1, y1]
        y_position: 要检查的Y坐标（通常是 bbox[1] 或 bbox[3]）
        drawings: 页面线条数据
        coverage_threshold: 覆盖率阈值（默认0.8，即横线覆盖≥80%单元格宽度）

    Returns:
        True: 有完整横线
        False: 无横线或横线不完整
    """
    pass
```

## 测试用例

### Test Case 1: 简单单列截断
- 输入：3列表格，第3列被截断（无顶/底边线）
- 期望：第3列的两部分内容合并

### Test Case 2: 多列同时截断
- 输入：5列表格，第3、4、5列都被截断
- 期望：3个列的内容分别合并

### Test Case 3: 前列有 rowspan
- 输入：第1、2列是 rowspan=3 的合并单元格，第3列被截断
- 期望：第3列合并，rowspan 单元格不受影响

### Test Case 4: 被截断单元格本身有 rowspan
- 输入：某单元格 rowspan=2，且被分页符截断
- 期望：需要特殊处理（复杂场景，Phase 3）

## 优先级

- **P0（必须）**：Phase 1 - 识别简单的单列截断
- **P1（重要）**：Phase 2 - 合并截断单元格内容
- **P2（可选）**：Phase 3 - 处理复杂场景（多行截断、嵌套表格）

## 注意事项

1. **坐标系问题**：不同页面的Y坐标系独立，不能直接比较绝对Y值
2. **线条容差**：检测横线时需要容差（如 ±2pt），因为线条可能不完全对齐单元格边界
3. **内容格式**：合并时注意保留原始格式（如换行符、空格）
4. **向后兼容**：不影响现有的跨页表格合并逻辑（只是在合并后额外处理单元格）

## 参考资料

- 现有跨页合并逻辑：`cross_page_merger.py:752-853`（merge_tables 方法）
- 线条数据结构：`page_drawings` 参数（从 table_extractor 传入）
- 单元格数据结构：`cell = {'row_id', 'col_id', 'content', 'bbox', ...}`