"""
列边界继承策略

用于跨页表格提取时，决定是否从上一页继承列边界。

## 问题背景（2025-10-30）

### 原始问题：列边界过度继承

**场景**：国土空间规划实施监测网络建设项目.pdf
- 页面5：检测到10条垂直线（9列），包含子列结构
- 页面6-8：实际只需6条垂直线（5列），仅主列

**旧逻辑**：无条件继承
```python
# 旧代码（已移除）
if not pymupdf_v_lines and prev_page_table_x_coords:
    merged_v_lines = prev_page_table_x_coords  # 无条件继承
elif pymupdf_v_lines and prev_page_vertical_lines:
    merged_v_lines = self._merge_vertical_lines_with_prev_table(...)  # 总是合并
```

**导致问题**：
1. 页面6-8被强制分成9列（继承自页面5）
2. 实际只需5列，导致列分割过细
3. 影响表格结构识别和数据提取

### 解决方案：策略模式

将列继承逻辑提取为可配置的策略，支持不同场景：

```python
# 新代码
if self.column_inheritance_strategy.should_inherit(current, prev):
    merged = self.column_inheritance_strategy.merge_lines(current, prev)
else:
    merged = current  # 不继承
```

## 策略对比

### DisabledInheritanceStrategy（当前默认）
**适用场景**：
- 调试和验证阶段
- 每页表格结构完全独立
- 不存在真正的跨页表格

**优点**：
- 简单可靠，不会误继承
- 每页独立检测，结果可预测

**缺点**：
- 对于真正的跨页表格，可能导致列数不一致
- 需要在跨页合并阶段处理列对齐

**验证结果**：
- ✓ 页面6-8正确检测为5列（不再误继承9列）
- ✓ S1策略成功修复左侧列缺失
- ⚠️ 可能影响真正需要跨页的表格（待观察）

### ConservativeInheritanceStrategy
**适用场景**：
- 存在跨页表格，但列结构相对稳定
- 允许少量列数差异（<30%）

**判断逻辑**：
```python
col_diff_ratio = abs(current_cols - prev_cols) / prev_cols
if col_diff_ratio > 0.3:
    return False  # 差异过大，不继承
```

**示例**：
- 页面5: 9列，页面6: 6列 → diff=33% > 30% → 不继承 ✓
- 页面3: 3列，页面4: 3列 → diff=0% → 继承 ✓

**待验证**：
- 是否能正确处理真正的跨页表格？
- 30%阈值是否合适？

### SmartInheritanceStrategy（未实现）
**设计思路**：
- 基于表格bbox重叠度判断（y轴连续性）
- 基于表格内容相似度判断
- 基于表头结构判断

**实现建议**：
```python
def should_inherit(self, current, prev, context):
    # 1. 检查bbox是否跨页连续
    prev_table_bbox = context.get('prev_table_bbox')
    if prev_table_bbox:
        # 上一页表格在底部 且 当前页表格在顶部
        prev_bottom = prev_table_bbox[3]
        curr_top = context.get('current_table_bbox', [0, 0, 0, 0])[1]
        if prev_bottom > 600 and curr_top < 100:
            return True  # 可能是跨页表格
    
    # 2. 检查列数相似度
    col_diff = abs(len(current) - len(prev)) / len(prev)
    if col_diff < 0.1:  # 列数几乎相同
        return True
    
    return False
```

## 使用示例

```python
from crossPageTable import (
    DisabledInheritanceStrategy,
    ConservativeInheritanceStrategy
)

# 1. 完全禁用继承（当前默认）
extractor = TableExtractor(pdf_path)
extractor.column_inheritance_strategy = DisabledInheritanceStrategy()

# 2. 保守继承（允许30%列数差异）
extractor.column_inheritance_strategy = ConservativeInheritanceStrategy(
    tolerance=5.0,           # 判断同一列的容差（pt）
    max_column_diff_ratio=0.3  # 最大列数差异比例
)

# 3. 自定义阈值
extractor.column_inheritance_strategy = ConservativeInheritanceStrategy(
    max_column_diff_ratio=0.1  # 更严格：只允许10%差异
)
```

## 待讨论问题

1. **何时需要列继承？**
   - 当前禁用继承后，页面6-8列数正确（5列）
   - 但是否存在真正需要跨页继承的场景？
   - 如何自动判断是否为跨页表格？

2. **列数不一致的跨页表格如何处理？**
   - 页面5: 7列（有子列）
   - 页面6-8: 5列（主列）
   - 是否应该合并？如何对齐列？

3. **策略选择建议**：
   - 第一轮提取：DisabledInheritanceStrategy（避免误继承）
   - 跨页合并时：根据bbox/内容相似度智能判断是否为同一表格
   - 合并后重提取：ConservativeInheritanceStrategy（统一列结构）

## 参考

相关文件：
- `app/utils/unTaggedPDF/table_extractor.py`: 列继承逻辑应用点（lines 478-495）
- `app/utils/unTaggedPDF/cross_page_merger.py`: 跨页合并逻辑
- `app/utils/unTaggedPDF/pdf_content_extractor.py`: 整体流程控制
"""
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod


class ColumnBoundaryInheritanceStrategy(ABC):
    """列边界继承策略基类"""

    @abstractmethod
    def should_inherit(
        self,
        current_page_lines: List[float],
        prev_page_lines: List[float],
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        判断是否应该继承前页的列边界

        Args:
            current_page_lines: 当前页检测到的垂直线
            prev_page_lines: 前一页的列边界
            context: 额外上下文信息（如表格bbox、页码等）

        Returns:
            是否应该继承
        """
        pass

    @abstractmethod
    def merge_lines(
        self,
        current_page_lines: List[float],
        prev_page_lines: List[float],
        context: Optional[Dict[str, Any]] = None
    ) -> List[float]:
        """
        合并当前页和前页的列边界

        Args:
            current_page_lines: 当前页检测到的垂直线
            prev_page_lines: 前一页的列边界
            context: 额外上下文信息

        Returns:
            合并后的列边界列表
        """
        pass


class DisabledInheritanceStrategy(ColumnBoundaryInheritanceStrategy):
    """
    禁用继承策略

    完全不继承前页列边界，每页独立检测。
    适用于调试和验证场景。
    """

    def should_inherit(
        self,
        current_page_lines: List[float],
        prev_page_lines: List[float],
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """永远返回False，不继承"""
        return False

    def merge_lines(
        self,
        current_page_lines: List[float],
        prev_page_lines: List[float],
        context: Optional[Dict[str, Any]] = None
    ) -> List[float]:
        """返回当前页的线，不合并"""
        return current_page_lines


class ConservativeInheritanceStrategy(ColumnBoundaryInheritanceStrategy):
    """
    保守继承策略

    只继承前页中"主要列边界"（长线），过滤子列。

    判断逻辑：
    - 如果前页列数远多于当前页（>30%差异），只继承当前页已有的列
    - 否则补充当前页缺失的列边界
    """

    def __init__(self, tolerance: float = 5.0, max_column_diff_ratio: float = 0.3):
        """
        Args:
            tolerance: 判断两条线是否为同一条的容差（pt）
            max_column_diff_ratio: 最大列数差异比例，超过则不继承
        """
        self.tolerance = tolerance
        self.max_column_diff_ratio = max_column_diff_ratio

    def should_inherit(
        self,
        current_page_lines: List[float],
        prev_page_lines: List[float],
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        判断是否应该继承

        规则：
        1. 如果当前页无线，不继承（避免强制）
        2. 如果列数差异过大，不继承
        """
        if not current_page_lines:
            # 当前页无检测结果，不强制继承
            return False

        if not prev_page_lines:
            return False

        # 计算列数（线数-1）
        current_cols = len(current_page_lines) - 1 if len(current_page_lines) > 1 else 0
        prev_cols = len(prev_page_lines) - 1 if len(prev_page_lines) > 1 else 0

        if prev_cols == 0:
            return False

        # 如果列数差异超过阈值，不继承
        col_diff_ratio = abs(current_cols - prev_cols) / prev_cols
        if col_diff_ratio > self.max_column_diff_ratio:
            print(f"    [列继承策略] 列数差异过大: current={current_cols}, prev={prev_cols}, "
                  f"diff_ratio={col_diff_ratio:.2f} > {self.max_column_diff_ratio}, 不继承")
            return False

        return True

    def merge_lines(
        self,
        current_page_lines: List[float],
        prev_page_lines: List[float],
        context: Optional[Dict[str, Any]] = None
    ) -> List[float]:
        """
        保守合并：只补充当前页缺失的列边界

        规则：
        - 对于前页的每条线，检查当前页是否存在
        - 如果不存在且在tolerance范围内，补充
        """
        if not self.should_inherit(current_page_lines, prev_page_lines, context):
            return current_page_lines

        # 找出前页有但当前页缺失的列边界
        missing_lines = []
        for prev_x in prev_page_lines:
            # 检查是否在当前页存在
            found = any(abs(prev_x - curr_x) < self.tolerance for curr_x in current_page_lines)
            if not found:
                missing_lines.append(prev_x)
                print(f"    [列继承策略] 补充缺失列边界: x={prev_x:.1f}")

        # 合并并排序
        merged = sorted(list(set(current_page_lines + missing_lines)))
        print(f"    [列继承策略] 合并结果: {len(current_page_lines)}条 + {len(missing_lines)}条 = {len(merged)}条")
        return merged


class SmartInheritanceStrategy(ColumnBoundaryInheritanceStrategy):
    """
    智能继承策略（未来扩展）

    可以基于更多上下文信息（如表格内容、bbox重叠度等）
    智能决定是否继承列边界。
    """

    def should_inherit(
        self,
        current_page_lines: List[float],
        prev_page_lines: List[float],
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        # TODO: 实现智能判断逻辑
        return False

    def merge_lines(
        self,
        current_page_lines: List[float],
        prev_page_lines: List[float],
        context: Optional[Dict[str, Any]] = None
    ) -> List[float]:
        # TODO: 实现智能合并逻辑
        return current_page_lines


# 默认策略：禁用继承（用于调试）
DEFAULT_STRATEGY = DisabledInheritanceStrategy()
