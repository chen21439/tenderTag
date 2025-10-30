"""
列边界继承策略

用于跨页表格提取时，决定是否从上一页继承列边界。

## 设计目标

解决列边界过度继承导致的问题：
- 上一页的子列（如9列）被错误继承到下一页（实际只有5列）
- 导致列分割过细，影响表格结构识别

## 策略模式

通过不同策略控制列边界继承行为，支持：
- 完全关闭继承（用于调试）
- 智能继承（基于列数相似度）
- 保守继承（仅继承主列，过滤子列）
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
