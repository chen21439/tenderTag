"""
段落提取器
专门负责提取PDF中表格外的段落文本
"""
from pathlib import Path
from typing import List, Dict, Any
import fitz  # PyMuPDF
import pdfplumber

try:
    from .bbox_utils import is_bbox_overlap
except ImportError:
    from bbox_utils import is_bbox_overlap


class ParagraphExtractor:
    """段落提取器"""

    def __init__(self, pdf_path: str):
        """
        初始化段落提取器

        Args:
            pdf_path: PDF文件路径
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

    def extract_paragraphs(self, table_bboxes_per_page: Dict[int, List[tuple]] = None) -> List[Dict[str, Any]]:
        """
        提取PDF中表格外的段落文本

        Args:
            table_bboxes_per_page: 每页的表格bbox列表，格式: {page_num: [bbox1, bbox2, ...]}
                                  用于过滤掉表格区域

        Returns:
            提取的段落列表
        """
        paragraphs_data = []

        # 打开PyMuPDF文档
        doc_pymupdf = fitz.open(self.pdf_path)

        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                # 获取PyMuPDF的对应页面
                pymupdf_page = doc_pymupdf[page_num - 1]

                # 获取当前页的表格bbox列表
                if table_bboxes_per_page and page_num in table_bboxes_per_page:
                    table_bboxes = table_bboxes_per_page[page_num]
                else:
                    # 如果没有提供表格bbox，使用pdfplumber自动查找
                    tables = page.find_tables()
                    table_bboxes = [table.bbox for table in tables]

                # 使用PyMuPDF提取文本块
                # get_text("blocks") 返回: (x0, y0, x1, y1, "text", block_no, block_type)
                text_blocks = pymupdf_page.get_text("blocks")

                for block in text_blocks:
                    if len(block) < 7:
                        continue

                    x0, y0, x1, y1, text, block_no, block_type = block
                    block_bbox = (x0, y0, x1, y1)

                    # 过滤掉图像块（block_type=1是图像，0是文本）
                    if block_type != 0:
                        continue

                    # 检查是否与表格重叠
                    is_in_table = False
                    for table_bbox in table_bboxes:
                        if is_bbox_overlap(block_bbox, table_bbox, threshold=0.5):
                            is_in_table = True
                            break

                    # 如果不在表格内，则认为是段落
                    if not is_in_table:
                        # 移除换行符
                        text_clean = text.replace('\n', '').replace('\r', '').strip()

                        if text_clean:  # 只保存非空段落
                            paragraphs_data.append({
                                "page": page_num,
                                "bbox": list(block_bbox),
                                "content": text_clean,
                                "y0": y0  # 用于排序
                            })

        doc_pymupdf.close()
        return paragraphs_data