"""
文本处理工具函数
"""
import re
from typing import List, Dict, Any


def deduplicate_chars(text: str) -> str:
    """
    去除连续重复的字符

    处理 PDF 提取时常见的字符重复问题，如 "政政府府" -> "政府"

    Args:
        text: 原始文本

    Returns:
        去重后的文本

    Examples:
        >>> deduplicate_chars("政政府府采采购购")
        '政府采购'
        >>> deduplicate_chars("一一、、项项目目")
        '一、项目'
        >>> deduplicate_chars("正常文本")
        '正常文本'
    """
    if not text:
        return text

    # 方法1：逐字符检查，去除连续的重复字符
    result = []
    prev_char = None

    for char in text:
        # 如果当前字符与前一个字符不同，或者是第一个字符，则保留
        if char != prev_char:
            result.append(char)
            prev_char = char
        # 如果连续重复，跳过

    return ''.join(result)


def deduplicate_words(words: List[Dict[str, Any]], tolerance: float = 1.0) -> List[Dict[str, Any]]:
    """
    去除重叠的单词（基于 bbox）

    处理同一位置多次渲染的字符（常见于加粗效果）

    Args:
        words: 单词列表，每个包含 text, x0, y0, x1, y1
        tolerance: 重叠容差（像素）

    Returns:
        去重后的单词列表
    """
    if not words:
        return words

    # 按页面和位置排序
    words_sorted = sorted(words, key=lambda w: (w.get('page', 0), w.get('y0', 0), w.get('x0', 0)))

    result = []

    for word in words_sorted:
        # 检查是否与已有单词重叠
        is_duplicate = False

        for existing in result:
            # 必须在同一页
            if word.get('page') != existing.get('page'):
                continue

            # 检查 bbox 是否重叠
            if _boxes_overlap(
                (word.get('x0', 0), word.get('y0', 0), word.get('x1', 0), word.get('y1', 0)),
                (existing.get('x0', 0), existing.get('y0', 0), existing.get('x1', 0), existing.get('y1', 0)),
                tolerance
            ):
                # 重叠：保留文本较长的
                if len(word.get('text', '')) > len(existing.get('text', '')):
                    # 替换
                    result.remove(existing)
                    result.append(word)
                is_duplicate = True
                break

        if not is_duplicate:
            result.append(word)

    return result


def _boxes_overlap(box1: tuple, box2: tuple, tolerance: float) -> bool:
    """
    判断两个 bbox 是否重叠

    Args:
        box1: (x0, y0, x1, y1)
        box2: (x0, y0, x1, y1)
        tolerance: 容差

    Returns:
        是否重叠
    """
    x0_1, y0_1, x1_1, y1_1 = box1
    x0_2, y0_2, x1_2, y1_2 = box2

    # 计算重叠区域
    x_overlap = max(0, min(x1_1, x1_2) - max(x0_1, x0_2))
    y_overlap = max(0, min(y1_1, y1_2) - max(y0_1, y0_2))

    # 如果有显著重叠（超过容差）
    if x_overlap > tolerance and y_overlap > tolerance:
        return True

    return False


def merge_text_simple(texts: List[str]) -> str:
    """
    简单合并文本（直接拼接）

    Args:
        texts: 文本列表

    Returns:
        合并后的文本
    """
    return ''.join(texts)


def merge_text_with_dedupe(texts: List[str]) -> str:
    """
    合并文本并去重

    Args:
        texts: 文本列表

    Returns:
        合并并去重后的文本
    """
    merged = ''.join(texts)
    return deduplicate_chars(merged)


def clean_heading_text(text: str) -> str:
    """
    清理标题文本

    - 去除连续重复字符
    - 去除多余空白
    - 标准化标点符号

    Args:
        text: 原始文本

    Returns:
        清理后的文本
    """
    # 去重
    text = deduplicate_chars(text)

    # 去除多余空白
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()

    return text


if __name__ == '__main__':
    # 测试
    test_cases = [
        "政政府府采采购购项项目目",
        "一一、、项项目目总总体体情情况况",
        "正常文本without重复",
        "aabbccdd",
        "",
    ]

    print("测试去重功能:")
    for test in test_cases:
        result = deduplicate_chars(test)
        print(f"  '{test}' -> '{result}'")