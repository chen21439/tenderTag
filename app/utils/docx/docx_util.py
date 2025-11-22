import json
import re
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl


class DocxBlockExtractor:
    """提取 docx 文件中的非表格块元素及其特征"""

    def __init__(self, docx_path: str):
        self.docx_path = docx_path
        t0 = time.time()
        self.doc = Document(docx_path)
        t1 = time.time()
        print(f"[计时] 加载文档: {t1-t0:.3f}秒")
        self.font_sizes: List[float] = []
        self.upper_blanks: List[float] = []
        self.lower_blanks: List[float] = []
        self.indent_levels: List[float] = []

        # 创建 element 到 paragraph 的映射，避免 O(n²) 查找
        self.element_to_para = {para._element: para for para in self.doc.paragraphs}

    def extract_blocks(self) -> Dict:
        """提取所有非表格块"""
        start_time = time.time()
        blocks = []
        block_counter = 1

        # 收集所有段落的特征用于计算分位数
        t1 = time.time()
        self._collect_features()
        t2 = time.time()
        print(f"[计时] 收集特征: {t2-t1:.3f}秒")

        # 处理文档中的所有元素（段落和表格混合）
        t3 = time.time()
        for element in self.doc.element.body:
            if isinstance(element, CT_P):  # 段落
                para = self._get_paragraph_by_element(element)
                if para and para.text.strip():  # 跳过空段落
                    block = self._extract_paragraph_block(para, block_counter)
                    if block:
                        blocks.append(block)
                        block_counter += 1
            # 跳过表格元素 (CT_Tbl)
        t4 = time.time()
        print(f"[计时] 提取块: {t4-t3:.3f}秒")
        print(f"[计时] 总耗时: {t4-start_time:.3f}秒")

        return {"blocks": blocks}

    def _get_paragraph_by_element(self, element):
        """通过元素查找对应的段落对象 - O(1) 查找"""
        return self.element_to_para.get(element)

    def _collect_features(self):
        """收集所有段落的特征用于计算分位数"""
        prev_para = None

        for para in self.doc.paragraphs:
            if not para.text.strip():
                prev_para = para
                continue

            # 收集字号
            font_size = self._get_font_size(para)
            if font_size:
                self.font_sizes.append(font_size)

            # 收集缩进
            indent = self._get_indent_level(para)
            self.indent_levels.append(indent)

            # 收集留白（段前段后距离）
            upper_blank = self._get_space_before(para)
            lower_blank = self._get_space_after(para)

            self.upper_blanks.append(upper_blank)
            self.lower_blanks.append(lower_blank)

            prev_para = para

        # 排序用于计算分位数
        self.font_sizes.sort()
        self.upper_blanks.sort()
        self.lower_blanks.sort()
        self.indent_levels.sort()

    def _extract_paragraph_block(self, para, block_id: int) -> Optional[Dict]:
        """提取单个段落的块信息"""
        import uuid

        text = para.text.strip()
        if not text:
            return None

        features = self._extract_features(para)

        return {
            "block_id": f"D001_{block_id:04d}",
            "uuid": str(uuid.uuid4()),  # 生成 UUID 用于后续 AI 请求
            "page_index": 0,  # docx 没有明确的页面概念，统一设为 0
            "order": block_id,
            "text": text,
            "features": features
        }

    def _extract_features(self, para) -> Dict:
        """提取段落特征"""
        return {
            "font_size_rank_pct": self._get_font_size_rank(para),
            "is_bold": self._is_bold(para),
            "is_centered": self._is_centered(para),
            "indent_level_norm": self._get_indent_rank(para),
            "upper_blank_ratio": self._get_upper_blank_rank(para),
            "lower_blank_ratio": self._get_lower_blank_rank(para),
            "line_len": len(para.text.strip()),
            "numbering_tag": self._detect_numbering(para)
        }

    def _get_font_size(self, para) -> Optional[float]:
        """获取段落字号（取第一个 run 的字号）"""
        for run in para.runs:
            if run.font.size:
                return float(run.font.size.pt)
            # 尝试从样式获取
            if run.style and hasattr(run.style, 'font') and run.style.font.size:
                return float(run.style.font.size.pt)
        return 12.0  # 默认字号

    def _get_font_size_rank(self, para) -> float:
        """计算字号在全文中的分位数"""
        font_size = self._get_font_size(para)
        if not self.font_sizes or font_size is None:
            return 0.5

        # 计算分位数
        rank = sum(1 for fs in self.font_sizes if fs <= font_size)
        return round(rank / len(self.font_sizes), 2)

    def _is_bold(self, para) -> bool:
        """判断段落是否加粗（主要文字加粗即可）"""
        bold_chars = 0
        total_chars = 0

        for run in para.runs:
            text_len = len(run.text.strip())
            if text_len > 0:
                total_chars += text_len
                if run.bold or (run.font.bold and run.font.bold == True):
                    bold_chars += text_len

        return total_chars > 0 and bold_chars / total_chars > 0.5

    def _is_centered(self, para) -> bool:
        """判断段落是否居中"""
        return para.alignment == WD_ALIGN_PARAGRAPH.CENTER

    def _get_indent_level(self, para) -> float:
        """获取缩进级别（左缩进，单位：磅）"""
        if para.paragraph_format.left_indent:
            return float(para.paragraph_format.left_indent.pt)
        return 0.0

    def _get_indent_rank(self, para) -> float:
        """计算缩进在全文中的归一化值"""
        indent = self._get_indent_level(para)
        if not self.indent_levels:
            return 0.0

        max_indent = max(self.indent_levels) if self.indent_levels else 1.0
        if max_indent == 0:
            return 0.0

        return round(indent / max_indent, 2)

    def _get_space_before(self, para) -> float:
        """获取段前距离（单位：磅）"""
        if para.paragraph_format.space_before:
            return float(para.paragraph_format.space_before.pt)
        return 0.0

    def _get_space_after(self, para) -> float:
        """获取段后距离（单位：磅）"""
        if para.paragraph_format.space_after:
            return float(para.paragraph_format.space_after.pt)
        return 0.0

    def _get_upper_blank_rank(self, para) -> float:
        """计算段前留白的分位数"""
        upper_blank = self._get_space_before(para)
        if not self.upper_blanks:
            return 0.0

        rank = sum(1 for ub in self.upper_blanks if ub <= upper_blank)
        return round(rank / len(self.upper_blanks), 2)

    def _get_lower_blank_rank(self, para) -> float:
        """计算段后留白的分位数"""
        lower_blank = self._get_space_after(para)
        if not self.lower_blanks:
            return 0.0

        rank = sum(1 for lb in self.lower_blanks if lb <= lower_blank)
        return round(rank / len(self.lower_blanks), 2)

    def _detect_numbering(self, para) -> Optional[str]:
        """检测编号模式"""
        text = para.text.strip()

        # 检测各种编号模式
        patterns = [
            (r'^第[一二三四五六七八九十百千]+章', 'chapter'),  # 第X章
            (r'^第[一二三四五六七八九十百千]+节', 'section'),  # 第X节
            (r'^[一二三四五六七八九十]+、', 'chinese_num'),  # 一、二、三、
            (r'^\d+\.\d+(?:\.\d+)*[\s、]', 'decimal_num'),  # 1.1、1.1.1
            (r'^\d+[\s、．]', 'arabic_num'),  # 1、2、3、
            (r'^\([一二三四五六七八九十]+\)', 'paren_chinese'),  # (一)(二)
            (r'^\(\d+\)', 'paren_arabic'),  # (1)(2)
            (r'^[①②③④⑤⑥⑦⑧⑨⑩]', 'circled_num'),  # ①②③
        ]

        for pattern, name in patterns:
            match = re.match(pattern, text)
            if match:
                return match.group(0).strip()

        return None

    def save_to_json(self, output_path: str):
        """保存为 JSON 文件"""
        blocks_data = self.extract_blocks()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(blocks_data, f, ensure_ascii=False, indent=2)

        print(f"已提取 {len(blocks_data['blocks'])} 个非表格块")
        print(f"已保存到: {output_path}")


def process_docx(input_path: str, output_dir: str = None):
    """处理 docx 文件并输出 JSON"""
    input_path_obj = Path(input_path)

    if output_dir is None:
        output_dir = input_path_obj.parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    # 输出文件名与输入文件名一致，后缀改为 .json
    output_filename = input_path_obj.stem + ".json"
    output_path = output_dir / output_filename

    # 提取并保存
    extractor = DocxBlockExtractor(input_path)
    extractor.save_to_json(str(output_path))

    return str(output_path)


if __name__ == "__main__":
    # 批量处理目录中的所有 docx 文件
    input_dir = Path(r"E:\models\data")
    output_dir = input_dir  # 输出到同一目录

    # 查找所有 docx 文件
    docx_files = list(input_dir.glob("*.docx"))

    if not docx_files:
        print(f"未找到任何 docx 文件: {input_dir}")
    else:
        print(f"找到 {len(docx_files)} 个 docx 文件")
        print("=" * 60)

        for i, docx_file in enumerate(docx_files, 1):
            print(f"\n[{i}/{len(docx_files)}] 处理: {docx_file.name}")
            print("-" * 60)

            try:
                result_path = process_docx(str(docx_file), str(output_dir))
                print(f"✓ 完成: {Path(result_path).name}")
            except Exception as e:
                print(f"✗ 错误: {e}")

        print("\n" + "=" * 60)
        print("批量处理完成！")