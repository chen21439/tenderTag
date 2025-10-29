"""
PDF 标题检测器
基于 PyMuPDF 和 pdfplumber 协同识别标题及层级
"""
import re
import statistics
from collections import defaultdict
from typing import List, Dict, Any, Tuple, Optional
from difflib import SequenceMatcher

import fitz  # PyMuPDF
import pdfplumber


class HeadingDetector:
    """PDF 标题检测器"""

    # 字体属性标记位
    BOLD_MASK = 1 << 2  # 加粗标记位

    def __init__(self, pdf_path: str):
        """
        初始化标题检测器

        Args:
            pdf_path: PDF文件路径
        """
        self.pdf_path = pdf_path
        self.pymupdf_doc = fitz.open(pdf_path)

        # 全局统计信息
        self.body_size = 0.0  # 正文字号
        self.all_sizes = []  # 所有字号集合
        self.page_spans = []  # 每页的 span 数据
        self.toc = []  # 目录信息

        # 阈值配置
        self.config = {
            'body_size_range': (6, 16),  # 正文字号范围
            'heading_size_ratio': 1.3,  # 标题字号相对正文的倍数
            'max_heading_length': 150,  # 标题最大字符数
            'x_gap_merge_ratio': 0.5,  # 同行合并的 x 间距比例（相对字高）
            'header_footer_margin': 30,  # 页眉页脚边距（像素）
            'min_text_length': 2,  # 最小文本长度
        }

    def extract_headings(self) -> List[Dict[str, Any]]:
        """
        提取所有标题

        Returns:
            标题列表，每个标题包含：page, text, size, font, flags, color, bbox, level
        """
        # 1. 全局字体画像
        self._build_global_font_profile()

        # 2. 标题候选召回
        candidates = self._recall_heading_candidates()

        # 3. 去噪过滤
        filtered = self._filter_noise(candidates)

        # 4. 标题合并
        merged = self._merge_headings(filtered)

        # 5. 层级判定
        headings = self._determine_levels(merged)

        # 6. 排序
        headings.sort(key=lambda x: (x['page'], x['bbox'][1]))

        return headings

    def _build_global_font_profile(self):
        """构建全局字体画像：收集所有 span 信息，估计正文字号"""
        # 读取目录
        self.toc = self._read_toc()

        # 遍历所有页面收集 span
        for page_num in range(len(self.pymupdf_doc)):
            page = self.pymupdf_doc[page_num]
            spans = list(self._iter_spans(page))
            self.page_spans.append(spans)

            # 收集字号
            for span in spans:
                if span['text']:
                    self.all_sizes.append(span['size'])

        # 估计正文字号（取中位数）
        if self.all_sizes:
            # 只考虑合理范围内的字号
            size_min, size_max = self.config['body_size_range']
            valid_sizes = [s for s in self.all_sizes if size_min <= s <= size_max]

            if valid_sizes:
                self.body_size = statistics.median(valid_sizes)
            else:
                self.body_size = statistics.median(self.all_sizes)
        else:
            self.body_size = 10.5  # 默认值

    def _read_toc(self) -> List[Tuple[int, str, int]]:
        """
        读取 PDF 目录

        Returns:
            [(level, title, page_num), ...]
        """
        toc = self.pymupdf_doc.get_toc() or []
        return [(lvl, title.strip(), pg - 1) for lvl, title, pg, *_ in toc]

    def _iter_spans(self, page: fitz.Page) -> List[Dict[str, Any]]:
        """
        遍历页面中的所有 span

        Args:
            page: PyMuPDF 页面对象

        Yields:
            span 信息字典
        """
        text_dict = page.get_text("dict", sort=True)

        for block in text_dict.get("blocks", []):
            if block.get("type") != 0:  # 只处理文本块
                continue

            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    yield {
                        'text': span['text'].strip(),
                        'size': float(span['size']),
                        'font': span['font'],
                        'flags': int(span['flags']),
                        'color': span.get('color', 0),
                        'bbox': span['bbox'],
                    }

    def _recall_heading_candidates(self) -> List[Dict[str, Any]]:
        """
        召回标题候选（多通道召回）

        Returns:
            候选标题列表
        """
        candidates = []

        for page_num, spans in enumerate(self.page_spans):
            for span in spans:
                if self._is_heading_candidate(span):
                    candidates.append({
                        'page': page_num,
                        'text': span['text'],
                        'size': span['size'],
                        'font': span['font'],
                        'flags': span['flags'],
                        'color': span['color'],
                        'bbox': span['bbox'],
                    })

        return candidates

    def _is_heading_candidate(self, span: Dict[str, Any]) -> bool:
        """
        判断是否为标题候选（基于特征）

        Args:
            span: span 信息

        Returns:
            是否为候选标题
        """
        text = span['text']

        # 基础过滤：文本长度
        if not text or len(text) < self.config['min_text_length']:
            return False

        # 过滤：表单字段模式（以冒号结尾）
        if text.endswith(('：', ':')):
            return False

        # 过滤：仅包含序号的文本（如 "、"）
        if text.strip() in ('、', '，', ','):
            return False

        # 特征1：字号大于正文
        is_large = span['size'] >= self.body_size * self.config['heading_size_ratio']

        # 特征2：加粗
        is_bold = self._is_bold(span)

        # 特征3：行长限制（不能太长）
        is_short = len(text) <= self.config['max_heading_length']

        # 特征4：不以句号等结束（标题一般不以句号结束）
        not_sentence_end = not text.endswith(('。', '.', '；', ';'))

        # 特征5：包含标题编号模式
        has_numbering = self._has_heading_numbering(text)

        # 召回策略：
        # 1. 字号明显大于正文（无论是否加粗）
        # 2. 或者：加粗 + 有编号 + 满足格式要求
        if is_large:
            return is_short and not_sentence_end
        elif is_bold and has_numbering:
            return is_short and not_sentence_end
        else:
            return False

    def _is_bold(self, span: Dict[str, Any]) -> bool:
        """
        判断是否加粗

        Args:
            span: span 信息

        Returns:
            是否加粗
        """
        # 方式1：通过 flags 位判断
        if span['flags'] & self.BOLD_MASK:
            return True

        # 方式2：通过字体名判断
        font_lower = span['font'].lower()
        bold_keywords = ['bold', 'black', 'semibold', 'heavy']
        return any(kw in font_lower for kw in bold_keywords)

    def _has_heading_numbering(self, text: str) -> bool:
        """
        判断文本是否包含标题编号模式

        Args:
            text: 文本内容

        Returns:
            是否包含标题编号
        """
        # 常见标题编号模式
        patterns = [
            r'^[一二三四五六七八九十百千]+[、\.]',  # 一、 二、 或 一. 二.
            r'^\([一二三四五六七八九十百千]+\)',  # （一） （二）
            r'^\d+[、\.]',  # 1、 2、 或 1. 2.
            r'^\(\d+\)',  # (1) (2)
            r'^第[一二三四五六七八九十百千]+[章节条款部分]',  # 第一章 第二节
            r'^[A-Z][、\.]',  # A、 B、 或 A. B.
            r'^\([A-Z]\)',  # (A) (B)
            r'^附录[A-Z一二三四五六七八九十]',  # 附录A 附录一
        ]

        for pattern in patterns:
            if re.match(pattern, text):
                return True

        return False

    def _filter_noise(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        去噪过滤：过滤页眉页脚、表格内文本等

        Args:
            candidates: 候选标题列表

        Returns:
            过滤后的候选列表
        """
        # 获取表格区域
        table_bboxes_by_page = self._get_table_bboxes()

        filtered = []

        with pdfplumber.open(self.pdf_path) as pdf:
            for candidate in candidates:
                page_num = candidate['page']

                if page_num >= len(pdf.pages):
                    continue

                page = pdf.pages[page_num]
                bbox = candidate['bbox']
                y_top = bbox[1]

                # 过滤1：页眉页脚（位于页面顶部或底部）
                margin = self.config['header_footer_margin']
                if y_top < margin or y_top > (page.height - margin):
                    continue

                # 过滤2：表格内文本
                if self._is_in_table(bbox, table_bboxes_by_page.get(page_num, [])):
                    continue

                # 过滤3：页码（纯数字且很短）
                if candidate['text'].strip().isdigit() and len(candidate['text']) <= 4:
                    continue

                filtered.append(candidate)

        return filtered

    def _get_table_bboxes(self) -> Dict[int, List[Tuple[float, float, float, float]]]:
        """
        获取所有页面的表格边界框

        Returns:
            {page_num: [bbox, ...]}
        """
        table_bboxes = defaultdict(list)

        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # 查找表格
                tables = page.find_tables()
                if tables:
                    for table in tables:
                        table_bboxes[page_num].append(table.bbox)

        return table_bboxes

    def _is_in_table(self, bbox: Tuple[float, float, float, float],
                     table_bboxes: List[Tuple[float, float, float, float]]) -> bool:
        """
        判断 bbox 是否在表格内

        Args:
            bbox: 文本边界框 (x0, y0, x1, y1)
            table_bboxes: 表格边界框列表

        Returns:
            是否在表格内
        """
        x0, y0, x1, y1 = bbox

        for tx0, ty0, tx1, ty1 in table_bboxes:
            # 判断是否在表格内（中心点在表格内即可）
            center_x = (x0 + x1) / 2
            center_y = (y0 + y1) / 2

            if tx0 <= center_x <= tx1 and ty0 <= center_y <= ty1:
                return True

        return False

    def _merge_headings(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        合并同一行或跨行的标题片段

        Args:
            candidates: 候选标题列表

        Returns:
            合并后的标题列表
        """
        if not candidates:
            return []

        # 按页面和 y 坐标分组
        grouped = defaultdict(list)
        for candidate in candidates:
            key = (candidate['page'], round(candidate['bbox'][1], 1))
            grouped[key].append(candidate)

        merged = []

        for (page, y), group in grouped.items():
            # 按 x 坐标排序
            group.sort(key=lambda x: x['bbox'][0])

            # 合并同一行中间距较小的片段
            i = 0
            while i < len(group):
                current = group[i]
                merged_text = current['text']
                merged_bbox = list(current['bbox'])

                # 尝试向右合并
                j = i + 1
                while j < len(group):
                    next_span = group[j]

                    # 检查是否应该合并
                    if self._should_merge_spans(current, next_span):
                        merged_text += next_span['text']
                        merged_bbox[2] = next_span['bbox'][2]  # 扩展右边界
                        j += 1
                    else:
                        break

                # 添加合并后的标题
                merged.append({
                    'page': current['page'],
                    'text': merged_text,
                    'size': current['size'],
                    'font': current['font'],
                    'flags': current['flags'],
                    'color': current['color'],
                    'bbox': tuple(merged_bbox),
                })

                i = j

        return merged

    def _should_merge_spans(self, span1: Dict[str, Any], span2: Dict[str, Any]) -> bool:
        """
        判断两个 span 是否应该合并

        Args:
            span1: 第一个 span
            span2: 第二个 span

        Returns:
            是否应该合并
        """
        # 字号、字体、flags 必须相同
        if (span1['size'] != span2['size'] or
            span1['font'] != span2['font'] or
            span1['flags'] != span2['flags']):
            return False

        # x 方向间距不能太大
        x_gap = span2['bbox'][0] - span1['bbox'][2]
        char_height = span1['bbox'][3] - span1['bbox'][1]
        max_gap = char_height * self.config['x_gap_merge_ratio']

        return x_gap <= max_gap

    def _determine_levels(self, headings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        确定标题层级（基于字号聚类）

        Args:
            headings: 标题列表

        Returns:
            添加了 level 字段的标题列表
        """
        if not headings:
            return []

        # 提取所有不同的字号并排序（从大到小）
        sizes = sorted(set(round(h['size'], 1) for h in headings), reverse=True)

        # 创建字号到层级的映射
        size_to_level = {size: idx + 1 for idx, size in enumerate(sizes)}

        # 为每个标题分配层级
        for heading in headings:
            base_level = size_to_level[round(heading['size'], 1)]

            # 微调：加粗的标题层级提升（数字减小）
            if self._is_bold(heading):
                base_level = max(1, base_level - 1)

            heading['level'] = base_level

        return headings

    def get_toc_similarity(self, text: str) -> float:
        """
        计算文本与目录中标题的相似度

        Args:
            text: 待检测文本

        Returns:
            最高相似度（0-1）
        """
        if not self.toc:
            return 0.0

        best_ratio = 0.0
        text_lower = text.lower()

        for _, title, _ in self.toc:
            ratio = SequenceMatcher(None, text_lower, title.lower()).ratio()
            best_ratio = max(best_ratio, ratio)

        return best_ratio

    def to_json(self, headings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        将标题列表转换为 JSON 格式

        Args:
            headings: 标题列表

        Returns:
            JSON 格式的结果
        """
        return {
            'doc_meta': {
                'pages': len(self.pymupdf_doc),
                'body_font_size': round(self.body_size, 2),
            },
            'headings': [
                {
                    'id': f'h-{idx:04d}',
                    'page': h['page'],
                    'level': h['level'],
                    'text': h['text'],
                    'bbox': list(h['bbox']),
                    'font': h['font'],
                    'size': round(h['size'], 2),
                    'flags': h['flags'],
                    'color': h['color'],
                }
                for idx, h in enumerate(headings)
            ]
        }

    def close(self):
        """关闭 PDF 文档"""
        if self.pymupdf_doc:
            self.pymupdf_doc.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def save_to_json(self, output_dir: str = None, task_id: str = None) -> str:
        """
        提取标题并保存到JSON文件

        Args:
            output_dir: 输出目录路径，如果为None则保存到PDF同目录
            task_id: 任务ID，用于生成文件名（如：taskId_headings.json）

        Returns:
            保存的文件路径
        """
        from pathlib import Path
        from datetime import datetime
        import json

        # 确定输出目录
        if output_dir is None:
            output_dir = Path(self.pdf_path).parent
        else:
            output_dir = Path(output_dir)

        # 确保输出目录存在
        output_dir.mkdir(parents=True, exist_ok=True)

        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 确定文件名（带时间戳）
        if task_id:
            filename = f"{task_id}_headings_{timestamp}.json"
        else:
            filename = f"headings_{timestamp}.json"

        # 提取标题
        headings = self.extract_headings()

        # 转换为JSON格式
        result = self.to_json(headings)

        # 保存文件
        output_path = output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return str(output_path)


# 主测试函数
def main():
    """
    主测试方法
    """
    import json
    from pathlib import Path

    # 从taskId构建路径（与pdf_content_extractor保持一致）
    task_id = "鄂尔多斯市政府网站群集约化平台升级改造项目"
    base_dir = Path(r"E:\programFile\AIProgram\docxServer\pdf\task\鄂尔多斯市政府网站群集约化平台升级改造项目")
    pdf_path = base_dir / f"{task_id}.pdf"

    print(f"开始测试PDF标题检测...")
    print(f"Task ID: {task_id}")
    print(f"PDF文件: {pdf_path}")

    try:
        # 使用上下文管理器
        with HeadingDetector(str(pdf_path)) as detector:
            # 保存结果，使用task_id作为文件名前缀
            output_path = detector.save_to_json(task_id=task_id)

            print(f"\n检测成功!")
            print(f"输出文件: {output_path}")

            # 读取并显示结果摘要
            with open(output_path, 'r', encoding='utf-8') as f:
                result = json.load(f)

            # 显示元数据
            print(f"\n[文档元数据]")
            print(f"  - 文档页数: {result['doc_meta']['pages']}")
            print(f"  - 正文字号: {result['doc_meta']['body_font_size']}")
            print(f"  - 标题数量: {len(result['headings'])}")

            # 显示标题预览（按层级组织）
            print(f"\n[标题预览]")
            print("-" * 80)

            # 统计各层级标题数量
            level_stats = {}
            for h in result['headings']:
                level = h['level']
                level_stats[level] = level_stats.get(level, 0) + 1

            print(f"\n层级统计:")
            for level in sorted(level_stats.keys()):
                print(f"  H{level}: {level_stats[level]} 个")

            # 显示前30个标题
            print(f"\n标题列表:")
            for h in result['headings'][:30]:
                indent = "  " * (h['level'] - 1)
                page_info = f"[页{h['page']+1}]"
                font_info = f"[{h['size']}pt]"
                print(f"{indent}H{h['level']} {page_info} {font_info} {h['text']}")

            if len(result['headings']) > 30:
                print(f"\n... (还有 {len(result['headings']) - 30} 个标题)")

            # 显示前几个标题的详细信息
            print(f"\n[详细信息示例]")
            for h in result['headings'][:3]:
                print(f"\n  标题ID: {h['id']}")
                print(f"  页码: {h['page'] + 1}")
                print(f"  层级: H{h['level']}")
                print(f"  文本: {h['text']}")
                print(f"  字号: {h['size']}pt")
                print(f"  字体: {h['font']}")
                print(f"  Flags: {h['flags']}")
                print(f"  Bbox: {h['bbox']}")

    except FileNotFoundError as e:
        print(f"\n错误: 文件未找到: {e}")
    except Exception as e:
        print(f"\n错误: 检测失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()