# 跨页表格合并实现指南

## 当前状态

✅ **已完成**：
1. 类框架创建完成（`cross_page_merger.py`）
2. 数据结构定义完成（`TableFingerprint`, `MergeCandidate`）
3. 辅助函数实现完成：
   - `_calculate_jaccard_similarity()` - 列边界相似度
   - `_calculate_col_paths_similarity()` - 列路径相似度
   - `_hash_col_paths()` - 列路径哈希
   - `_normalize_to_page_width()` - 坐标归一化

## 待实现功能清单

### 1. 指纹生成（`generate_fingerprint`）

**输入**：
- `table`: 从 `TableExtractor._build_structured_table()` 返回的表格对象
- `page_width`: 页面宽度（从PyMuPDF获取）
- `page_drawings`: PyMuPDF的 `get_drawings()` 结果

**实现步骤**：
```python
def generate_fingerprint(self, table, page_width, page_drawings=None):
    # 1. 提取基本信息
    table_id = table['id']
    page_num = table['page']
    bbox = table['bbox']  # [x0, y0, x1, y1]

    # 2. 提取几何特征
    x0, y0, x1, y1 = bbox

    # 从 columns 中提取 x_edges（需要在 TableExtractor 中保存）
    # 或从 header_info 中重建 x_edges
    x_edges = self._extract_x_edges_from_table(table)

    # 归一化
    x_edges_norm = [_normalize_to_page_width(x, page_width) for x in x_edges]
    table_width_norm = _normalize_to_page_width(x1 - x0, page_width)
    left_margin_norm = _normalize_to_page_width(x0, page_width)
    right_margin_norm = _normalize_to_page_width(page_width - x1, page_width)

    # 3. 提取结构特征
    header_info = table.get('header_info', {})
    col_levels = header_info.get('col_levels', 1)
    row_levels = header_info.get('row_levels', 0)

    # 从 columns 中提取 col_paths
    col_paths = [col.get('path', [col['name']]) for col in table.get('columns', [])]
    col_paths_hash = _hash_col_paths(col_paths)

    # 4. 提取视觉特征（从 page_drawings）
    has_top_border, has_bottom_border, line_width = self._detect_borders(
        bbox, page_drawings
    )

    # 5. 提取表头特征
    header_rows_texts = self._extract_header_rows(table, col_levels)
    first_data_row_texts = self._extract_first_data_row(table, col_levels)

    return TableFingerprint(
        table_id=table_id,
        page_num=page_num,
        bbox=bbox,
        x_edges_norm=x_edges_norm,
        table_width_norm=table_width_norm,
        left_margin_norm=left_margin_norm,
        right_margin_norm=right_margin_norm,
        col_levels=col_levels,
        row_levels=row_levels,
        col_paths=col_paths,
        col_paths_hash=col_paths_hash,
        has_top_border=has_top_border,
        has_bottom_border=has_bottom_border,
        border_line_width=line_width,
        first_data_row_texts=first_data_row_texts,
        header_rows_texts=header_rows_texts,
        table_data=table
    )
```

**辅助方法需要实现**：
- `_extract_x_edges_from_table(table)` - 从 columns 索引重建 x_edges
- `_detect_borders(bbox, drawings)` - 检测顶/底边是否封口
- `_extract_header_rows(table, col_levels)` - 提取前N行作为表头文本
- `_extract_first_data_row(table, col_levels)` - 提取第一行数据文本

---

### 2. 边框检测（`_detect_borders`）

**目的**：判断表格顶边和底边是否有完整的水平线（封口）

**实现思路**：
```python
def _detect_borders(self, bbox, page_drawings):
    """
    检测表格的顶边和底边是否封口

    策略：
    1. 从 page_drawings 中筛选出 bbox 范围内的线段
    2. 识别接近顶边/底边的水平线
    3. 判断线段是否覆盖整个表格宽度（允许小间隙）
    """
    if not page_drawings:
        # 没有绘图数据，假设都有边框
        return True, True, 1.0

    x0, y0, x1, y1 = bbox
    table_width = x1 - x0

    # 筛选水平线段（接近顶边/底边，容差3px）
    top_lines = []
    bottom_lines = []

    for item in page_drawings:
        if item['type'] != 'l':  # 只处理线段
            continue

        line = item['rect']  # (x0, y0, x1, y1)
        lx0, ly0, lx1, ly1 = line

        # 检查是否为水平线（高度接近0）
        if abs(ly1 - ly0) > 2:
            continue

        # 检查是否在bbox宽度范围内
        if lx1 < x0 - 5 or lx0 > x1 + 5:
            continue

        # 检查是否接近顶边
        if abs(ly0 - y0) < 3:
            top_lines.append((lx0, lx1, item.get('width', 1.0)))

        # 检查是否接近底边
        if abs(ly0 - y1) < 3:
            bottom_lines.append((lx0, lx1, item.get('width', 1.0)))

    # 判断是否封口（线段覆盖≥80%宽度）
    has_top = _check_line_coverage(top_lines, x0, x1, table_width)
    has_bottom = _check_line_coverage(bottom_lines, x0, x1, table_width)

    # 提取线宽（取平均值）
    all_widths = [w for _, _, w in top_lines + bottom_lines]
    avg_width = sum(all_widths) / len(all_widths) if all_widths else 1.0

    return has_top, has_bottom, avg_width


def _check_line_coverage(lines, x0, x1, table_width):
    """检查线段是否覆盖表格宽度"""
    if not lines:
        return False

    # 合并重叠线段
    segments = sorted(lines, key=lambda l: l[0])
    merged = []

    for lx0, lx1, _ in segments:
        if not merged or lx0 > merged[-1][1] + 5:  # 允许5px间隙
            merged.append([lx0, lx1])
        else:
            merged[-1][1] = max(merged[-1][1], lx1)

    # 计算覆盖长度
    covered_length = sum(max(0, min(seg[1], x1) - max(seg[0], x0))
                        for seg in merged)

    coverage_ratio = covered_length / table_width
    return coverage_ratio >= 0.80
```

---

### 3. 几何特征打分（`calculate_geometry_score`）

```python
def calculate_geometry_score(self, fp1, fp2):
    """
    评分维度（权重）：
    1. 列边界 Jaccard 相似度 (0.5)
    2. 左边距一致性 (0.2)
    3. 右边距一致性 (0.2)
    4. 表宽一致性 (0.1)
    """
    # 1. 列边界相似度
    edges_sim = _calculate_jaccard_similarity(
        fp1.x_edges_norm,
        fp2.x_edges_norm,
        tolerance=0.01  # 归一化后允许1%误差
    )

    # 2. 边距一致性（差异越小得分越高）
    left_margin_diff = abs(fp1.left_margin_norm - fp2.left_margin_norm)
    right_margin_diff = abs(fp1.right_margin_norm - fp2.right_margin_norm)

    left_margin_score = max(0, 1.0 - left_margin_diff / 0.05)  # 5%容差
    right_margin_score = max(0, 1.0 - right_margin_diff / 0.05)

    # 3. 表宽一致性
    width_diff = abs(fp1.table_width_norm - fp2.table_width_norm)
    width_score = max(0, 1.0 - width_diff / 0.03)  # 3%容差

    # 综合得分
    score = (
        0.5 * edges_sim +
        0.2 * left_margin_score +
        0.2 * right_margin_score +
        0.1 * width_score
    )

    details = {
        'edges_similarity': edges_sim,
        'left_margin_score': left_margin_score,
        'right_margin_score': right_margin_score,
        'width_score': width_score
    }

    return score, details
```

---

### 4. 结构特征打分（`calculate_structure_score`）

```python
def calculate_structure_score(self, fp1, fp2):
    """
    评分维度（权重）：
    1. col_levels 一致性 (0.3)
    2. row_levels 一致性 (0.2)
    3. col_paths 相似度 (0.5)
    """
    # 1. 列表头层级数
    col_levels_match = 1.0 if fp1.col_levels == fp2.col_levels else 0.0

    # 2. 行表头列数
    row_levels_match = 1.0 if fp1.row_levels == fp2.row_levels else 0.0

    # 3. 列路径相似度
    # 优先用哈希快速比对
    if fp1.col_paths_hash == fp2.col_paths_hash:
        paths_sim = 1.0
    else:
        paths_sim = _calculate_col_paths_similarity(fp1.col_paths, fp2.col_paths)

    score = (
        0.3 * col_levels_match +
        0.2 * row_levels_match +
        0.5 * paths_sim
    )

    details = {
        'col_levels_match': col_levels_match,
        'row_levels_match': row_levels_match,
        'col_paths_similarity': paths_sim
    }

    return score, details
```

---

### 5. 视觉特征打分（`calculate_visual_score`）

```python
def calculate_visual_score(self, fp1, fp2):
    """
    评分维度（权重）：
    1. 延续信号（底边开口 + 顶边开口） (0.7)
    2. 线宽一致性 (0.3)
    """
    # 1. 延续信号（强证据）
    # 上一页底边未封口 且 下一页顶边未封口 → 强延续信号
    continuation_signal = (
        not fp1.has_bottom_border and not fp2.has_top_border
    )
    continuation_score = 1.0 if continuation_signal else 0.0

    # 2. 线宽一致性
    width_diff = abs(fp1.border_line_width - fp2.border_line_width)
    width_score = max(0, 1.0 - width_diff / 0.5)  # 允许0.5px误差

    score = (
        0.7 * continuation_score +
        0.3 * width_score
    )

    details = {
        'continuation_signal': continuation_signal,
        'line_width_similarity': width_score
    }

    return score, details
```

---

### 6. 合并链识别（`find_merge_chains`）

```python
def find_merge_chains(self, tables, page_widths, page_drawings=None):
    """
    识别合并链的算法：
    1. 为所有表生成指纹
    2. 对相邻页的表格两两打分
    3. 构建有向图（边=匹配对，权重=得分）
    4. 找出所有路径（避免分叉）
    """
    # 1. 生成指纹
    fingerprints = {}
    for table in tables:
        page = table['page']
        fp = self.generate_fingerprint(
            table,
            page_widths.get(page, 595),  # 默认A4宽度
            page_drawings.get(page) if page_drawings else None
        )
        fingerprints[table['id']] = fp

    # 2. 按页码分组
    tables_by_page = {}
    for table in tables:
        page = table['page']
        if page not in tables_by_page:
            tables_by_page[page] = []
        tables_by_page[page].append(table['id'])

    # 3. 对相邻页的表格进行匹配
    candidates = []  # [(score, prev_id, next_id), ...]

    sorted_pages = sorted(tables_by_page.keys())
    for i in range(len(sorted_pages) - 1):
        curr_page = sorted_pages[i]
        next_page = sorted_pages[i + 1]

        # 跳过非连续页
        if next_page != curr_page + 1:
            continue

        # 两两匹配
        for prev_id in tables_by_page[curr_page]:
            for next_id in tables_by_page[next_page]:
                fp1 = fingerprints[prev_id]
                fp2 = fingerprints[next_id]

                # 计算匹配得分
                match = self.calculate_match_score(fp1, fp2)

                if match.score >= self.score_threshold:
                    candidates.append((match.score, prev_id, next_id))

    # 4. 构建合并链（避免一对多）
    # 按得分降序排序
    candidates.sort(key=lambda x: x[0], reverse=True)

    chains = []
    used_ids = set()

    for score, prev_id, next_id in candidates:
        # 跳过已使用的表段
        if prev_id in used_ids or next_id in used_ids:
            continue

        # 尝试合并到现有链
        merged = False
        for chain in chains:
            if chain[-1] == prev_id:
                chain.append(next_id)
                used_ids.add(next_id)
                merged = True
                break

        if not merged:
            # 创建新链
            chains.append([prev_id, next_id])
            used_ids.add(prev_id)
            used_ids.add(next_id)

    return chains
```

---

### 7. 表格合并（`merge_tables`）

```python
def merge_tables(self, tables, table_ids):
    """
    合并多个表段的步骤：
    1. 提取表段并验证
    2. 检测重复表头
    3. 拼接数据行
    4. 合并bbox和列定义
    5. 更新元数据
    """
    # 1. 提取表段
    table_map = {t['id']: t for t in tables}
    segments = [table_map[tid] for tid in table_ids]

    if not segments:
        return None

    # 2. 以首段为基准
    base_table = segments[0].copy()

    # 3. 收集所有数据行
    all_rows = []

    for i, segment in enumerate(segments):
        segment_rows = segment.get('rows', [])

        if i == 0:
            # 首段：保留所有行
            all_rows.extend(segment_rows)
        else:
            # 续段：检测并跳过重复表头
            repeated_header_count = self.detect_repeated_header(
                segments[i-1], segment
            )

            # 跳过重复表头行
            all_rows.extend(segment_rows[repeated_header_count:])

    # 4. 合并bbox（包络）
    all_bboxes = [seg['bbox'] for seg in segments]
    merged_bbox = [
        min(b[0] for b in all_bboxes),  # x0
        min(b[1] for b in all_bboxes),  # y0
        max(b[2] for b in all_bboxes),  # x1
        max(b[3] for b in all_bboxes)   # y1
    ]

    # 5. 更新表格数据
    base_table['rows'] = all_rows
    base_table['bbox'] = merged_bbox
    base_table['id'] = f"{table_ids[0]}_merged"
    base_table['merged_from'] = table_ids
    base_table['method'] = base_table.get('method', '') + ' + cross_page_merged'

    return base_table
```

---

### 8. 重复表头检测（`detect_repeated_header`）

```python
def detect_repeated_header(self, prev_table, next_table):
    """
    检测续页开头重复的表头行数

    策略：
    1. 获取 prev_table 的 header_info
    2. 提取 next_table 前 N 行的文本
    3. 逐行比对，连续匹配的行数即为重复表头数
    """
    # 获取预期的表头层数
    col_levels = prev_table.get('header_info', {}).get('col_levels', 1)

    # 提取首表的表头文本
    prev_header_texts = self._extract_header_rows(prev_table, col_levels)

    # 提取续表前N行
    next_rows = next_table.get('rows', [])
    if not next_rows:
        return 0

    repeated_count = 0
    for i in range(min(col_levels, len(next_rows))):
        next_row_text = [cell.get('content', '')
                        for cell in next_rows[i].get('cells', [])]

        # 比对是否与表头行匹配（允许部分差异）
        if i < len(prev_header_texts):
            similarity = self._calculate_row_similarity(
                prev_header_texts[i],
                next_row_text
            )

            if similarity >= 0.85:  # 85%以上相似度认为是重复表头
                repeated_count += 1
            else:
                break  # 连续匹配中断，停止检测

    return repeated_count


def _calculate_row_similarity(self, row1, row2):
    """计算两行文本的相似度"""
    if len(row1) != len(row2):
        return 0.0

    matches = sum(1 for t1, t2 in zip(row1, row2) if t1 == t2)
    return matches / len(row1) if row1 else 1.0
```

---

## 集成到 PDFContentExtractor

在 `pdf_content_extractor.py` 中添加：

```python
from .cross_page_merger import CrossPageTableMerger

class PDFContentExtractor:
    def __init__(self, pdf_path: str):
        # ... 现有代码 ...
        self.cross_page_merger = CrossPageTableMerger(
            score_threshold=0.70,
            geometry_weight=0.40,
            structure_weight=0.35,
            visual_weight=0.25
        )

    def extract_all_content(self) -> Dict[str, Any]:
        # ... 现有代码提取表格和段落 ...

        # 跨页表格合并（在统一编号之前）
        if self.enable_cross_page_merge:
            tables = self.cross_page_merger.merge_all_tables(
                tables=tables,
                page_widths=self.page_widths,  # 需要收集
                page_drawings=self.page_drawings,  # 需要收集
                debug=True
            )

        # ... 后续处理 ...
```

---

## 需要的前置修改

### TableExtractor 需要保存额外信息

在 `_build_structured_table()` 中保存 x_edges：

```python
def _build_structured_table(self, ...):
    # ... 现有代码 ...

    # 新增：保存x_edges用于跨页合并
    if header_model:
        result['x_edges'] = header_model.grid.x_edges

    return result
```

### PDFContentExtractor 需要收集页面元数据

```python
def __init__(self, pdf_path: str):
    # ... 现有代码 ...
    self.page_widths = {}  # {page_num: width}
    self.page_drawings = {}  # {page_num: drawings}

def extract_all_content(self):
    with pdfplumber.open(self.pdf_path) as pdf:
        doc_pymupdf = fitz.open(self.pdf_path)

        for page_num, page in enumerate(pdf.pages, start=1):
            # 收集页面宽度
            self.page_widths[page_num] = page.width

            # 收集页面绘图（可选）
            pymupdf_page = doc_pymupdf[page_num - 1]
            self.page_drawings[page_num] = pymupdf_page.get_drawings()

            # ... 现有提取逻辑 ...
```

---

## 测试建议

1. **单元测试**：
   - 测试 `_calculate_jaccard_similarity`
   - 测试 `_calculate_col_paths_similarity`
   - 测试 `calculate_geometry_score`
   - 测试 `calculate_structure_score`

2. **集成测试**：
   - 准备跨页表格的PDF样本
   - 验证 `find_merge_chains` 的识别准确率
   - 验证 `merge_tables` 的合并正确性

3. **调参**：
   - 调整 `score_threshold`（从0.70开始）
   - 调整各特征权重
   - 调整容差参数（tolerance, margin_diff容差等）

---

## 总结

当前已完成：
1. ✅ 类框架和数据结构
2. ✅ 核心辅助函数（Jaccard、列路径相似度）
3. ✅ 打分函数实现指南
4. ✅ 合并逻辑实现指南

待实现：
1. 指纹生成（依赖 TableExtractor 增强）
2. 边框检测（依赖 PyMuPDF get_drawings）
3. 合并链识别
4. 表格合并
5. 集成到主流程

**建议优先级**：
1. 先完成指纹生成和边框检测
2. 然后实现打分机制并用样本测试
3. 最后实现合并逻辑并集成

所有TODO的地方都标注了详细的实现思路，可以按需逐步实现！