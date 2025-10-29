"""
基于 pdfplumber 的标题提取器
使用 extract_words 方法提取文字和字体信息，精确定位标题
"""
import re
import statistics
from collections import defaultdict
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

import pdfplumber

# 导入文本工具
try:
    from .text_utils import clean_heading_text, deduplicate_words
except ImportError:
    from text_utils import clean_heading_text, deduplicate_words


class HeadingExtractor:
    """基于 pdfplumber 的标题提取器"""

    def __init__(self, pdf_path: str):
        """
        初始化标题提取器

        Args:
            pdf_path: PDF文件路径
        """
        self.pdf_path = pdf_path
        self.pdf = pdfplumber.open(pdf_path)

        # 全局统计信息
        self.body_size = 0.0  # 正文字号
        self.all_words = []  # 所有文字信息

        # 配置参数
        self.config = {
            'body_size_range': (6, 16),  # 正文字号范围
            'heading_size_ratio': 1.3,  # 标题字号相对正文的倍数
            'max_heading_length': 150,  # 标题最大字符数
            'min_text_length': 2,  # 最小文本长度
            'line_tolerance': 3,  # 同一行的容差（像素）
        }

    def extract_headings(self) -> List[Dict[str, Any]]:
        """
        提取所有标题

        Returns:
            标题列表，每个标题包含：page, text, size, fontname, bbox, level
        """
        # 1. 提取所有页面的文字信息
        self._extract_all_words()

        # 2. 估计正文字号
        self._estimate_body_size()

        # 3. 识别标题候选
        candidates = self._identify_heading_candidates()

        # 4. 合并同行标题片段
        merged = self._merge_heading_lines(candidates)

        # 5. 过滤噪音
        filtered = self._filter_noise(merged)

        # 6. 确定层级
        headings = self._determine_levels(filtered)

        # 7. 排序
        headings.sort(key=lambda x: (x['page'], x['bbox'][1]))

        return headings

    def extract_content_between_headings(self, headings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        提取标题之间的内容

        Args:
            headings: 标题列表

        Returns:
            内容块列表，每个包含：heading_id, page, bbox, content
        """
        contents = []

        for i, heading in enumerate(headings):
            page_num = heading['page']
            page = self.pdf.pages[page_num]

            # 确定内容区域的边界
            y0 = heading['bbox'][3]  # 标题底部

            # 确定 y1：下一个标题的顶部或页面底部
            if i + 1 < len(headings):
                next_heading = headings[i + 1]
                if next_heading['page'] == page_num:
                    # 同页：下一个标题的顶部
                    y1 = next_heading['bbox'][1]
                else:
                    # 不同页：当前页底部
                    y1 = page.height
            else:
                # 最后一个标题：页面底部
                y1 = page.height

            # 裁剪并提取文本
            if y1 > y0:  # 确保有有效区域
                bbox = (0, y0, page.width, y1)
                cropped = page.crop(bbox)
                content = cropped.extract_text()

                if content and content.strip():
                    # 对内容也应用去重处理
                    content_cleaned = clean_heading_text(content)

                    contents.append({
                        'heading_id': heading.get('id', f"h-{i:04d}"),
                        'heading_text': heading['text'],
                        'page': page_num,
                        'bbox': list(bbox),
                        'content': content_cleaned
                    })

        return contents

    def _extract_all_words(self):
        """提取所有页面的文字信息"""
        self.all_words = []

        for page_num, page in enumerate(self.pdf.pages):
            # 提取文字及其字体和大小信息
            words = page.extract_words(
                extra_attrs=["fontname", "size"],
                keep_blank_chars=False
            )

            for word in words:
                self.all_words.append({
                    'page': page_num,
                    'text': word['text'],
                    'x0': word['x0'],
                    'y0': word['top'],  # pdfplumber 使用 'top'
                    'x1': word['x1'],
                    'y1': word['bottom'],  # pdfplumber 使用 'bottom'
                    'fontname': word.get('fontname', ''),
                    'size': float(word.get('size', 0)),
                })

    def _estimate_body_size(self):
        """估计正文字号"""
        if not self.all_words:
            self.body_size = 10.5
            return

        # 收集所有字号
        sizes = [w['size'] for w in self.all_words if w['size'] > 0]

        if not sizes:
            self.body_size = 10.5
            return

        # 只考虑合理范围内的字号
        size_min, size_max = self.config['body_size_range']
        valid_sizes = [s for s in sizes if size_min <= s <= size_max]

        if valid_sizes:
            self.body_size = statistics.median(valid_sizes)
        else:
            self.body_size = statistics.median(sizes)

    def _identify_heading_candidates(self) -> List[Dict[str, Any]]:
        """识别标题候选"""
        candidates = []

        for word in self.all_words:
            if self._is_heading_candidate(word):
                candidates.append(word)

        return candidates

    def _is_heading_candidate(self, word: Dict[str, Any]) -> bool:
        """判断单词是否为标题候选"""
        text = word['text']

        # 基础过滤
        if not text or len(text) < self.config['min_text_length']:
            return False

        # 过滤：表单字段（以冒号结尾）
        if text.endswith(('：', ':')):
            return False

        # 过滤：仅标点符号
        if text.strip() in ('、', '，', ',', '。', '.'):
            return False

        # 字号判断
        size = word['size']
        if size <= 0:
            return False

        is_large = size >= self.body_size * self.config['heading_size_ratio']

        # 加粗判断（通过字体名）
        is_bold = self._is_bold(word['fontname'])

        # 编号判断
        has_numbering = self._has_heading_numbering(text)

        # 召回策略
        if is_large:
            return True
        elif is_bold and has_numbering:
            return True
        else:
            return False

    def _is_bold(self, fontname: str) -> bool:
        """判断字体是否加粗"""
        if not fontname:
            return False

        font_lower = fontname.lower()
        bold_keywords = ['bold', 'black', 'semibold', 'heavy']
        return any(kw in font_lower for kw in bold_keywords)

    def _has_heading_numbering(self, text: str) -> bool:
        """判断文本是否包含标题编号"""
        patterns = [
            r'^[一二三四五六七八九十百千]+[、\.]',
            r'^\([一二三四五六七八九十百千]+\)',
            r'^\d+[、\.]',
            r'^\(\d+\)',
            r'^第[一二三四五六七八九十百千]+[章节条款部分]',
            r'^[A-Z][、\.]',
            r'^\([A-Z]\)',
            r'^附录[A-Z一二三四五六七八九十]',
        ]

        for pattern in patterns:
            if re.match(pattern, text):
                return True

        return False

    def _merge_heading_lines(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合并同一行的标题片段"""
        if not candidates:
            return []

        # 按页面和 y 坐标分组
        grouped = defaultdict(list)
        tolerance = self.config['line_tolerance']

        for word in candidates:
            # 使用 y0 的近似值作为分组键
            page = word['page']
            y_key = round(word['y0'] / tolerance) * tolerance
            grouped[(page, y_key)].append(word)

        # 合并每组
        merged = []
        for (page, y), words in grouped.items():
            # 按 x0 排序
            words.sort(key=lambda w: w['x0'])

            # 合并文本并去重
            text_parts = [w['text'] for w in words]
            merged_text = ''.join(text_parts)
            merged_text = clean_heading_text(merged_text)  # 去除重复字符

            # 跳过过长的文本
            if len(merged_text) > self.config['max_heading_length']:
                continue

            # 计算合并后的 bbox
            x0 = min(w['x0'] for w in words)
            y0 = min(w['y0'] for w in words)
            x1 = max(w['x1'] for w in words)
            y1 = max(w['y1'] for w in words)

            # 取第一个词的字号和字体
            size = words[0]['size']
            fontname = words[0]['fontname']

            merged.append({
                'page': page,
                'text': merged_text,
                'bbox': (x0, y0, x1, y1),
                'size': size,
                'fontname': fontname,
            })

        return merged

    def _filter_noise(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤噪音"""
        filtered = []

        for candidate in candidates:
            text = candidate['text']

            # 过滤：页码（纯数字且很短）
            if text.strip().isdigit() and len(text) <= 4:
                continue

            # 过滤：纯数字或百分比
            if re.match(r'^[\d.,]+%?$', text.strip()):
                continue

            # 过滤：不以句号等结束
            if text.endswith(('。', '.', '；', ';')):
                continue

            filtered.append(candidate)

        return filtered

    def _determine_levels(self, headings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """确定标题层级"""
        if not headings:
            return []

        # 提取所有不同的字号并排序（从大到小）
        sizes = sorted(set(round(h['size'], 1) for h in headings), reverse=True)

        # 创建字号到层级的映射
        size_to_level = {size: idx + 1 for idx, size in enumerate(sizes)}

        # 为每个标题分配层级
        for heading in headings:
            base_level = size_to_level[round(heading['size'], 1)]

            # 微调：加粗标题层级提升
            if self._is_bold(heading['fontname']):
                base_level = max(1, base_level - 1)

            heading['level'] = base_level

        return headings

    def to_json(self, headings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """转换为 JSON 格式"""
        return {
            'doc_meta': {
                'pages': len(self.pdf.pages),
                'body_font_size': round(self.body_size, 2),
            },
            'headings': [
                {
                    'id': f'h-{idx:04d}',
                    'page': h['page'],
                    'level': h['level'],
                    'text': h['text'],
                    'bbox': list(h['bbox']),
                    'fontname': h['fontname'],
                    'size': round(h['size'], 2),
                }
                for idx, h in enumerate(headings)
            ]
        }

    def close(self):
        """关闭 PDF"""
        if self.pdf:
            self.pdf.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def main():
    """主测试函数"""
    import json
    from pathlib import Path
    from datetime import datetime

    # 测试路径
    task_id = "鄂尔多斯市政府网站群集约化平台升级改造项目"
    base_dir = Path(r"E:\programFile\AIProgram\docxServer\pdf\task\鄂尔多斯市政府网站群集约化平台升级改造项目")
    pdf_path = base_dir / f"{task_id}.pdf"

    print(f"开始测试 pdfplumber 标题提取...")
    print(f"Task ID: {task_id}")
    print(f"PDF文件: {pdf_path}")

    try:
        with HeadingExtractor(str(pdf_path)) as extractor:
            # 提取标题
            print("\n[1] 提取标题...")
            headings = extractor.extract_headings()

            # 转换为 JSON
            result = extractor.to_json(headings)

            # 显示元数据
            print(f"\n[文档元数据]")
            print(f"  - 文档页数: {result['doc_meta']['pages']}")
            print(f"  - 正文字号: {result['doc_meta']['body_font_size']}")
            print(f"  - 标题数量: {len(headings)}")

            # 层级统计
            level_stats = {}
            for h in result['headings']:
                level = h['level']
                level_stats[level] = level_stats.get(level, 0) + 1

            print(f"\n层级统计:")
            for level in sorted(level_stats.keys()):
                print(f"  H{level}: {level_stats[level]} 个")

            # 显示标题列表
            print(f"\n标题列表:")
            for h in result['headings'][:30]:
                indent = "  " * (h['level'] - 1)
                page_info = f"[页{h['page']+1}]"
                font_info = f"[{h['size']}pt]"
                print(f"{indent}H{h['level']} {page_info} {font_info} {h['text']}")

            if len(result['headings']) > 30:
                print(f"\n... (还有 {len(result['headings']) - 30} 个标题)")

            # 提取标题之间的内容
            print(f"\n[2] 提取标题之间的内容...")
            contents = extractor.extract_content_between_headings(headings)
            print(f"  提取到 {len(contents)} 个内容块")

            # 显示前3个内容块预览
            print(f"\n内容块预览:")
            for content in contents[:3]:
                print(f"\n  [{content['heading_id']}] {content['heading_text']}")
                print(f"  页码: {content['page'] + 1}")
                preview = content['content'][:100].replace('\n', ' ')
                print(f"  内容: {preview}...")

            # 保存结果
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 保存标题
            headings_file = base_dir / f"{task_id}_headings_plumber_{timestamp}.json"
            with open(headings_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n标题已保存到: {headings_file}")

            # 保存内容
            contents_file = base_dir / f"{task_id}_contents_plumber_{timestamp}.json"
            with open(contents_file, 'w', encoding='utf-8') as f:
                json.dump({'contents': contents}, f, ensure_ascii=False, indent=2)
            print(f"内容已保存到: {contents_file}")

    except FileNotFoundError as e:
        print(f"\n错误: 文件未找到: {e}")
    except Exception as e:
        print(f"\n错误: 提取失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()