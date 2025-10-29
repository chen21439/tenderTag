"""
基于 pdfplumber 的标题检测模块
"""

from .heading_extractor import HeadingExtractor
from .text_utils import clean_heading_text, deduplicate_chars, deduplicate_words

__all__ = ['HeadingExtractor', 'clean_heading_text', 'deduplicate_chars', 'deduplicate_words']