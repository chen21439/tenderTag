"""
表格重提取策略

用于处理pdfplumber初次提取时遗漏列的情况。

## 问题背景

pdfplumber使用 `lines` 策略时，只识别有交点的垂直线。
如果某条垂直线没有与水平线相交（或交点少），会被忽略。

例如：页面6左侧列（x=33.6）的垂直线交点少，被pdfplumber忽略。

## 解决方案

使用PyMuPDF检测所有垂直线，对比pdfplumber检测结果：
- 如果检测到缺口（detected_left < table_left），触发重提取
- 使用crop + explicit lines强制形成完整网格

## 策略模式

支持不同的重提取策略，从保守到激进：
- DisabledReextractionStrategy: 完全禁用重提取
- ConservativeReextractionStrategy: 只在缺口很大时重提取
- AggressiveReextractionStrategy: 即使小缺口也重提取
"""
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod


class ReextractionStrategy(ABC):
    """重提取策略基类"""

    @abstractmethod
    def should_reextract(
        self,
        detected_left: float,
        detected_right: float,
        table_left: float,
        table_right: float,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        判断是否应该重提取

        Args:
            detected_left: PyMuPDF检测到的最左边界
            detected_right: PyMuPDF检测到的最右边界
            table_left: pdfplumber检测到的表格左边界
            table_right: pdfplumber检测到的表格右边界
            context: 额外上下文信息

        Returns:
            是否应该重提取
        """
        pass

    @abstractmethod
    def get_fallback_strategies(self) -> List[str]:
        """
        获取fallback策略列表

        Returns:
            策略名称列表，按优先级排序: ['S1', 'S2', 'S3']
        """
        pass


class DisabledReextractionStrategy(ReextractionStrategy):
    """
    禁用重提取策略

    完全不进行crop重提取，保留pdfplumber的原始结果。
    适用于：
    - 信任pdfplumber的检测结果
    - 避免过度干预
    """

    def should_reextract(
        self,
        detected_left: float,
        detected_right: float,
        table_left: float,
        table_right: float,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """永远返回False，不重提取"""
        return False

    def get_fallback_strategies(self) -> List[str]:
        """返回空列表，不使用任何fallback策略"""
        return []


class ConservativeReextractionStrategy(ReextractionStrategy):
    """
    保守重提取策略（当前默认）

    只在缺口很大时才重提取，避免误触发。

    判断逻辑：
    - 左侧缺口 > left_gap_threshold (默认10pt)
    - 右侧缺口 > right_gap_threshold (默认10pt)
    """

    def __init__(
        self,
        left_gap_threshold: float = 10.0,
        right_gap_threshold: float = 10.0,
        enabled_strategies: Optional[List[str]] = None
    ):
        """
        Args:
            left_gap_threshold: 左侧缺口阈值（pt）
            right_gap_threshold: 右侧缺口阈值（pt）
            enabled_strategies: 启用的策略列表，None表示全部启用
                               例如: ['S1', 'S2'] 只启用S1和S2
        """
        self.left_gap_threshold = left_gap_threshold
        self.right_gap_threshold = right_gap_threshold
        self.enabled_strategies = enabled_strategies or ['S1', 'S2', 'S3']

    def should_reextract(
        self,
        detected_left: float,
        detected_right: float,
        table_left: float,
        table_right: float,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """判断缺口是否超过阈值"""
        left_gap = table_left - detected_left
        right_gap = detected_right - table_right

        return (left_gap > self.left_gap_threshold or 
                right_gap > self.right_gap_threshold)

    def get_fallback_strategies(self) -> List[str]:
        """返回启用的策略列表"""
        return self.enabled_strategies


class AggressiveReextractionStrategy(ReextractionStrategy):
    """
    激进重提取策略

    即使小缺口也重提取，最大程度修复列缺失。

    判断逻辑：
    - 左侧缺口 > 5pt
    - 右侧缺口 > 5pt
    """

    def __init__(
        self,
        left_gap_threshold: float = 5.0,
        right_gap_threshold: float = 5.0,
        enabled_strategies: Optional[List[str]] = None
    ):
        self.left_gap_threshold = left_gap_threshold
        self.right_gap_threshold = right_gap_threshold
        self.enabled_strategies = enabled_strategies or ['S1', 'S2', 'S3']

    def should_reextract(
        self,
        detected_left: float,
        detected_right: float,
        table_left: float,
        table_right: float,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        left_gap = table_left - detected_left
        right_gap = detected_right - table_right

        return (left_gap > self.left_gap_threshold or 
                right_gap > self.right_gap_threshold)

    def get_fallback_strategies(self) -> List[str]:
        return self.enabled_strategies


class SmartReextractionStrategy(ReextractionStrategy):
    """
    智能重提取策略（未来扩展）

    基于更多上下文信息判断是否重提取：
    - 表格类型（简单表格 vs 复杂表格）
    - 表格大小
    - 单元格密度
    """

    def should_reextract(
        self,
        detected_left: float,
        detected_right: float,
        table_left: float,
        table_right: float,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        # TODO: 实现智能判断逻辑
        return False

    def get_fallback_strategies(self) -> List[str]:
        # TODO: 根据表格特征动态选择策略
        return ['S1']


# 默认策略：保守重提取（与当前行为一致）
DEFAULT_REEXTRACTION_STRATEGY = ConservativeReextractionStrategy(
    left_gap_threshold=10.0,
    right_gap_threshold=10.0,
    enabled_strategies=['S1', 'S2', 'S3']
)
