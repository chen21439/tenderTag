"""
跨页表格合并器
负责识别和合并跨页分割的同一张表格

## 核心思路

### 问题定义
PDF表格可能被分页符打断，形成多个表段：
- 续页通常会重复表头
- 列结构保持一致
- 视觉上有延续关系（顶/底边未封口）

### 解决方案（3步法）

**Step 1**: 为每个表段生成合并指纹（Fingerprint）
  - 几何特征：列边界、表宽、边距
  - 结构特征：表头层级、列路径
  - 视觉特征：线条信息（顶/底边是否封口）

**Step 2**: 跨页匹配与打分
  - 几何对齐得分（列边界、边距）
  - 结构一致性得分（表头层级、列路径）
  - 视觉延续得分（底边开口 + 顶边开口）
  - 综合得分 ≥ 阈值则判定为同一张表

**Step 3**: 合并表段
  - 表头去重（续页表头识别与跳过）
  - 数据行拼接
  - bbox合并
  - 嵌套表继承

### 特征权重设计

| 特征组 | 权重 | 说明 |
|--------|------|------|
| 几何特征 | 0.40 | 列边界一致性最关键 |
| 结构特征 | 0.35 | 表头层级和列路径 |
| 视觉特征 | 0.25 | 顶/底边封口状态 |

总分阈值 **T = 0.70**（可调参）
"""
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import hashlib
import copy


@dataclass
class TableFingerprint:
    """表格指纹（用于跨页匹配）"""

    # 表格ID和位置
    table_id: str  # 原始表格ID（如 "doc001"）
    page_num: int  # 页码
    bbox: List[float]  # 表格bbox [x0, y0, x1, y1]

    # 几何特征（归一化到页面宽度）
    x_edges_norm: List[float]  # 归一化列边界
    table_width_norm: float  # 归一化表宽
    left_margin_norm: float  # 归一化左边距
    right_margin_norm: float  # 归一化右边距

    # 结构特征
    col_levels: int  # 列表头层数
    row_levels: int  # 行表头列数
    col_paths: List[List[str]]  # 列路径列表
    col_paths_hash: str  # 列路径的哈希（用于快速比对）

    # 视觉特征（从get_drawings()提取）
    has_top_border: Optional[bool]  # 是否有完整顶边（None=未知）
    has_bottom_border: Optional[bool]  # 是否有完整底边（None=未知）
    border_line_width: float  # 边框线宽（用于识别同一表格）

    # 表头特征（用于去重）
    first_data_row_texts: List[str]  # 第一行数据的文本（用于判断是否为重复表头）
    header_rows_texts: List[List[str]]  # 表头行文本（用于匹配续页表头）

    # 原始表格数据引用
    table_data: Dict[str, Any]  # 原始表格结构化数据


@dataclass
class MergeCandidate:
    """合并候选（两个表段的匹配结果）"""
    prev_table: TableFingerprint  # 上一页的表段
    next_table: TableFingerprint  # 下一页的表段
    score: float  # 综合匹配得分 [0, 1]

    # 详细得分（用于调试和分析）
    geometry_score: float  # 几何特征得分
    structure_score: float  # 结构特征得分
    visual_score: float  # 视觉特征得分

    # 匹配详情
    match_details: Dict[str, Any]  # 详细匹配信息


class CrossPageTableMerger:
    """跨页表格合并器"""

    def __init__(self,
                 score_threshold: float = 0.70,
                 geometry_weight: float = 0.40,
                 structure_weight: float = 0.35,
                 visual_weight: float = 0.25,
                 enable_cell_merge: bool = True):
        """
        初始化合并器

        Args:
            score_threshold: 匹配阈值（≥此值判定为同一张表）
            geometry_weight: 几何特征权重
            structure_weight: 结构特征权重
            visual_weight: 视觉特征权重
            enable_cell_merge: 是否启用跨页单元格合并（默认True）
                             当单元格被分页符截断时，自动合并内容
        """
        self.score_threshold = score_threshold
        self.geometry_weight = geometry_weight
        self.structure_weight = structure_weight
        self.visual_weight = visual_weight
        self.enable_cell_merge = enable_cell_merge

    def generate_fingerprint(self,
                            table: Dict[str, Any],
                            page_width: float,
                            page_drawings: List = None) -> TableFingerprint:
        """
        为单个表格段生成合并指纹

        Args:
            table: 结构化表格数据（来自TableExtractor）
            page_width: 页面宽度（用于归一化）
            page_drawings: PyMuPDF的get_drawings()结果（用于检测边框）

        Returns:
            TableFingerprint对象
        """
        # 1. 提取基本信息
        table_id = table.get('id', 'unknown')
        page_num = table.get('page', 1)
        bbox = table.get('bbox', [0, 0, 0, 0])
        x0, y0, x1, y1 = bbox

        # 2. 提取几何特征
        # 从columns中重建x_edges
        columns = table.get('columns', [])
        x_edges = []

        # 如果有列信息，从列的bbox推断x_edges
        if columns and 'rows' in table and table['rows']:
            # 从第一行cells的bbox提取x边界
            first_row = table['rows'][0]
            cells = first_row.get('cells', [])

            # 收集所有cell的x边界
            x_coords = set([x0])  # 表格左边界
            for cell in cells:
                cell_bbox = cell.get('bbox')
                if cell_bbox:
                    x_coords.add(cell_bbox[0])
                    x_coords.add(cell_bbox[2])
            x_coords.add(x1)  # 表格右边界

            x_edges = sorted(x_coords)
        else:
            # 降级：只用表格左右边界
            x_edges = [x0, x1]

        # 归一化
        x_edges_norm = [_normalize_to_page_width(x, page_width) for x in x_edges]
        table_width_norm = _normalize_to_page_width(x1 - x0, page_width)
        left_margin_norm = _normalize_to_page_width(x0, page_width)
        right_margin_norm = _normalize_to_page_width(page_width - x1, page_width)

        # 3. 提取结构特征
        header_info = table.get('header_info', {})
        col_levels = header_info.get('col_levels', 1)
        row_levels = header_info.get('row_levels', 0)

        # 从columns中提取col_paths
        col_paths = []
        for col in columns:
            path = col.get('path', [col.get('name', '')])
            if not path:
                path = [col.get('name', '')]
            col_paths.append(path)

        col_paths_hash = _hash_col_paths(col_paths)

        # 4. 提取视觉特征（边框检测）
        has_top_border, has_bottom_border, border_line_width = self._detect_table_borders(
            bbox, page_drawings
        )

        # 5. 提取表头和首行数据
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
            border_line_width=border_line_width,
            first_data_row_texts=first_data_row_texts,
            header_rows_texts=header_rows_texts,
            table_data=table
        )

    def _extract_header_rows(self, table: Dict[str, Any], col_levels: int) -> List[List[str]]:
        """提取表头行的文本"""
        header_texts = []
        rows = table.get('rows', [])

        # 提取前col_levels行（但这些在rows中已经被过滤掉了）
        # 所以我们从columns的name中提取
        if col_levels > 0:
            columns = table.get('columns', [])
            header_row = [col.get('name', '') for col in columns]
            header_texts.append(header_row)

        return header_texts

    def _extract_first_data_row(self, table: Dict[str, Any], col_levels: int) -> List[str]:
        """提取第一行数据的文本"""
        rows = table.get('rows', [])
        if rows:
            first_row = rows[0]
            cells = first_row.get('cells', [])
            return [cell.get('content', '') for cell in cells]
        return []

    def _detect_table_borders(self,
                             bbox: List[float],
                             page_drawings: List = None) -> Tuple[Optional[bool], Optional[bool], float]:
        """
        检测表格的顶边和底边是否有完整边框

        Args:
            bbox: 表格的边界框 [x0, y0, x1, y1]
            page_drawings: PyMuPDF的get_drawings()结果

        Returns:
            (has_top_border, has_bottom_border, avg_line_width)
            边框状态: True=有边框, False=无边框, None=未知
        """
        if not page_drawings:
            # 没有绘图数据，返回未知状态
            return None, None, 1.0

        x0, y0, x1, y1 = bbox
        table_width = x1 - x0

        # 容差：线条位置允许的偏移
        y_tolerance = 2.0  # Y方向容差
        x_overlap_threshold = 0.7  # 至少70%的宽度有线条才算"完整"

        has_top = False
        has_bottom = False
        line_widths = []
        has_any_lines = False  # 标记是否检测到任何横线

        # 遍历所有绘图元素
        for drawing in page_drawings:
            # PyMuPDF的drawing是字典，包含'rect', 'items'等
            if not isinstance(drawing, dict):
                continue

            items = drawing.get('items', [])
            for item in items:
                # 只关注直线（'l'表示line）
                if not isinstance(item, tuple) or len(item) < 2:
                    continue

                item_type = item[0]
                if item_type != 'l':  # 不是线条
                    continue

                # 线条格式: ('l', p1, p2)
                if len(item) < 3:
                    continue

                p1 = item[1]  # 起点 (x, y)
                p2 = item[2]  # 终点 (x, y)

                if not isinstance(p1, (tuple, list)) or not isinstance(p2, (tuple, list)):
                    continue
                if len(p1) < 2 or len(p2) < 2:
                    continue

                line_x0 = min(p1[0], p2[0])
                line_x1 = max(p1[0], p2[0])
                line_y0 = min(p1[1], p2[1])
                line_y1 = max(p1[1], p2[1])

                # 判断是否为横线（y坐标变化小）
                if abs(line_y1 - line_y0) > 2.0:
                    continue  # 竖线，跳过

                has_any_lines = True  # 至少检测到一条横线
                line_y = (line_y0 + line_y1) / 2
                line_width_px = line_x1 - line_x0

                # 计算线条与表格的水平重叠
                overlap_x0 = max(line_x0, x0)
                overlap_x1 = min(line_x1, x1)
                overlap_width = max(0, overlap_x1 - overlap_x0)
                overlap_ratio = overlap_width / table_width if table_width > 0 else 0

                # 检查是否是顶边
                if abs(line_y - y0) < y_tolerance and overlap_ratio >= x_overlap_threshold:
                    has_top = True
                    line_widths.append(line_width_px)

                # 检查是否是底边
                if abs(line_y - y1) < y_tolerance and overlap_ratio >= x_overlap_threshold:
                    has_bottom = True
                    line_widths.append(line_width_px)

        # 计算平均线宽（如果有的话）
        avg_line_width = sum(line_widths) / len(line_widths) if line_widths else 1.0

        # 如果没有检测到任何横线，返回未知状态
        if not has_any_lines:
            return None, None, avg_line_width

        return has_top, has_bottom, avg_line_width

    def calculate_geometry_score(self,
                                 fp1: TableFingerprint,
                                 fp2: TableFingerprint) -> Tuple[float, Dict]:
        """
        计算几何特征匹配得分

        评分维度：
        1. 列边界一致性（Jaccard相似度）
        2. 左右边距一致性
        3. 表宽一致性

        Args:
            fp1: 上一页表格指纹
            fp2: 下一页表格指纹

        Returns:
            (得分 [0, 1], 详细信息)
        """
        # 1. 列边界相似度（权重0.5）
        edges_sim = _calculate_jaccard_similarity(
            fp1.x_edges_norm,
            fp2.x_edges_norm,
            tolerance=0.02  # 归一化后允许2%误差
        )

        # 2. 左右边距一致性（各权重0.2）
        left_margin_diff = abs(fp1.left_margin_norm - fp2.left_margin_norm)
        right_margin_diff = abs(fp1.right_margin_norm - fp2.right_margin_norm)

        left_margin_score = max(0, 1.0 - left_margin_diff / 0.05)  # 5%容差
        right_margin_score = max(0, 1.0 - right_margin_diff / 0.05)

        # 3. 表宽一致性（权重0.1）
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
            'edges_similarity': round(edges_sim, 3),
            'left_margin_score': round(left_margin_score, 3),
            'right_margin_score': round(right_margin_score, 3),
            'width_score': round(width_score, 3)
        }

        return score, details

    def calculate_structure_score(self,
                                  fp1: TableFingerprint,
                                  fp2: TableFingerprint) -> Tuple[float, Dict]:
        """
        计算结构特征匹配得分

        注意：只使用纯结构特征，不使用列名文本
        原因：续页表格可能无表头或表头识别错误，文本不可靠

        评分维度：
        1. 列数一致性 (最重要)
        2. 列表头层级数一致性
        3. 行表头列数一致性

        Args:
            fp1: 上一页表格指纹
            fp2: 下一页表格指纹

        Returns:
            (得分 [0, 1], 详细信息)
        """
        # 1. 列数一致性（权重0.5）
        num_cols_1 = len(fp1.col_paths)
        num_cols_2 = len(fp2.col_paths)
        col_count_match = 1.0 if num_cols_1 == num_cols_2 else 0.0

        # 2. 列表头层级数（权重0.3）
        col_levels_match = 1.0 if fp1.col_levels == fp2.col_levels else 0.0

        # 3. 行表头列数（权重0.2）
        row_levels_match = 1.0 if fp1.row_levels == fp2.row_levels else 0.0

        score = (
            0.5 * col_count_match +
            0.3 * col_levels_match +
            0.2 * row_levels_match
        )

        details = {
            'col_count_match': bool(col_count_match),
            'num_cols': (num_cols_1, num_cols_2),
            'col_levels_match': bool(col_levels_match),
            'row_levels_match': bool(row_levels_match)
        }

        return score, details

    def calculate_visual_score(self,
                               fp1: TableFingerprint,
                               fp2: TableFingerprint) -> Tuple[float, Dict]:
        """
        计算视觉特征匹配得分

        评分维度：
        1. 上一页底边未封口 + 下一页顶边未封口 → 强延续信号
        2. 线宽一致性

        边框状态处理：
        - None（未知）→ 中性分 0.5，避免过度合并
        - True（有边框）/ False（无边框）→ 按规则计算

        Args:
            fp1: 上一页表格指纹
            fp2: 下一页表格指纹

        Returns:
            (得分 [0, 1], 详细信息)
        """
        # 1. 延续信号（权重0.7）
        # 检查边框状态（None = 未知）
        prev_bottom_unknown = fp1.has_bottom_border is None
        next_top_unknown = fp2.has_top_border is None

        # 如果有任一边框状态未知，返回中性分
        if prev_bottom_unknown or next_top_unknown:
            continuation_score = 0.5  # 中性：未知状态不给高分也不给低分
            prev_bottom_open = None
            next_top_open = None
        else:
            # 两边状态都已知，按常规逻辑计算
            prev_bottom_open = not fp1.has_bottom_border  # 底边未封口
            next_top_open = not fp2.has_top_border        # 顶边未封口

            if prev_bottom_open and next_top_open:
                # 两边都开口：强烈的延续信号
                continuation_score = 1.0
            elif prev_bottom_open or next_top_open:
                # 只有一边开口：中等延续信号
                continuation_score = 0.7
            else:
                # 两边都封口：弱延续信号（但不完全排除，因为有的PDF边框检测不准）
                continuation_score = 0.3

        # 2. 线宽一致性（权重0.3）
        width_diff = abs(fp1.border_line_width - fp2.border_line_width)
        width_score = max(0, 1.0 - width_diff / fp1.border_line_width) if fp1.border_line_width > 0 else 1.0

        score = (
            0.7 * continuation_score +
            0.3 * width_score
        )

        details = {
            'prev_bottom_open': prev_bottom_open,
            'next_top_open': next_top_open,
            'continuation_score': round(continuation_score, 3),
            'line_width_similarity': round(width_score, 3),
            'has_unknown_border': prev_bottom_unknown or next_top_unknown
        }

        return score, details

    def calculate_match_score(self,
                             fp1: TableFingerprint,
                             fp2: TableFingerprint) -> MergeCandidate:
        """
        计算两个表段的综合匹配得分

        综合得分 = geometry_weight * geometry_score
                  + structure_weight * structure_score
                  + visual_weight * visual_score

        Args:
            fp1: 上一页表格指纹
            fp2: 下一页表格指纹

        Returns:
            MergeCandidate对象（包含综合得分和详细信息）
        """
        # 计算各维度得分
        geometry_score, geo_details = self.calculate_geometry_score(fp1, fp2)
        structure_score, struct_details = self.calculate_structure_score(fp1, fp2)
        visual_score, visual_details = self.calculate_visual_score(fp1, fp2)

        # 综合得分
        total_score = (
            self.geometry_weight * geometry_score +
            self.structure_weight * structure_score +
            self.visual_weight * visual_score
        )

        return MergeCandidate(
            prev_table=fp1,
            next_table=fp2,
            score=total_score,
            geometry_score=geometry_score,
            structure_score=structure_score,
            visual_score=visual_score,
            match_details={
                'geometry': geo_details,
                'structure': struct_details,
                'visual': visual_details
            }
        )

    def find_merge_chains(self,
                         tables: List[Dict[str, Any]],
                         page_widths: Dict[int, float],
                         page_drawings: Dict[int, List] = None,
                         layout_index: Dict[int, List] = None,
                         hints_by_page: Dict[int, Dict] = None) -> List[List[str]]:
        """
        识别需要合并的表格链

        流程：
        1. 为所有表格生成指纹
        2. 对相邻页的表格进行两两匹配打分
        3. 检查正文隔断（如果两表之间有段落，拒绝合并）
        4. 找出得分≥阈值的匹配对
        5. 构建合并链（避免一对多）

        Args:
            tables: 所有提取的表格列表（按页码、bbox顺序排序）
            page_widths: {page_num: width} 页面宽度字典
            page_drawings: {page_num: drawings} 页面绘图数据
            layout_index: {page_num: [blocks]} 页面布局索引（用于检查正文隔断）

        Returns:
            合并链列表，每条链是表格ID列表，如 [["doc001", "doc005"], ["doc003", "doc007", "doc012"]]
        """
        if not tables:
            return []

        # Step 1: 为所有表格生成指纹
        fingerprints = {}
        for table in tables:
            table_id = table.get('id', 'unknown')
            page_num = table.get('page', 1)
            page_width = page_widths.get(page_num, 595.0)  # A4默认宽度
            drawings = page_drawings.get(page_num) if page_drawings else None

            fp = self.generate_fingerprint(table, page_width, drawings)
            fingerprints[table_id] = fp

        # Step 2: 按页码分组表格
        tables_by_page = {}
        for table in tables:
            page_num = table.get('page', 1)
            if page_num not in tables_by_page:
                tables_by_page[page_num] = []
            tables_by_page[page_num].append(table)

        # Step 3: 对相邻页的表格进行匹配打分
        # 存储所有匹配候选: {(prev_id, next_id): MergeCandidate}
        candidates = {}

        page_nums = sorted(tables_by_page.keys())
        for i in range(len(page_nums) - 1):
            curr_page = page_nums[i]
            next_page = page_nums[i + 1]

            # 只考虑相邻页（page_num相差1）
            if next_page - curr_page != 1:
                continue

            curr_tables = tables_by_page[curr_page]
            next_tables = tables_by_page[next_page]

            # 两两匹配
            for curr_table in curr_tables:
                curr_id = curr_table.get('id')
                curr_fp = fingerprints[curr_id]

                for next_table in next_tables:
                    next_id = next_table.get('id')
                    next_fp = fingerprints[next_id]

                    # 计算匹配得分
                    candidate = self.calculate_match_score(curr_fp, next_fp)

                    # Debug输出
                    print(f"[匹配] {curr_id}(页{curr_page}) vs {next_id}(页{next_page})")
                    print(f"  几何得分: {candidate.geometry_score:.3f} (权重{self.geometry_weight})")
                    print(f"  结构得分: {candidate.structure_score:.3f} (权重{self.structure_weight})")
                    print(f"  视觉得分: {candidate.visual_score:.3f} (权重{self.visual_weight})")
                    print(f"  综合得分: {candidate.score:.3f} (阈值{self.score_threshold})")

                    # 门槛检查（gating）：防止过度合并
                    # 注意：不检查列名文本，因为续页可能无表头
                    gate_passed = True
                    gate_reason = []

                    # 门槛1: 几何得分必须≥0.60
                    if candidate.geometry_score < 0.60:
                        gate_passed = False
                        gate_reason.append(f"几何得分{candidate.geometry_score:.3f}<0.60")

                    # 门槛2: 结构得分必须≥0.65
                    if candidate.structure_score < 0.65:
                        gate_passed = False
                        gate_reason.append(f"结构得分{candidate.structure_score:.3f}<0.65")

                    # 门槛3: 列数必须一致（硬性要求）
                    # 但在判死刑前，先尝试使用hint补齐列
                    struct_details = candidate.match_details.get('structure', {})
                    if not struct_details.get('col_count_match', False):
                        num_cols = struct_details.get('num_cols', (0, 0))

                        # ===== 列补齐逻辑 =====
                        # 如果有hint且满足条件，尝试补齐下一页的列
                        repaired = False
                        if hints_by_page and next_page in hints_by_page:
                            hint = hints_by_page[next_page]
                            repaired = self._try_repair_missing_columns(
                                curr_table, next_table, curr_fp, next_fp, hint
                            )

                            if repaired:
                                print(f"  [列补齐] 成功补齐 {next_id} 的缺失列")
                                # 重新生成next_table的指纹
                                next_fp_new = self.generate_fingerprint(
                                    next_table,
                                    page_widths.get(next_page, 595.0),
                                    page_drawings.get(next_page) if page_drawings else None
                                )
                                fingerprints[next_id] = next_fp_new

                                # 重新计算匹配得分
                                candidate = self.calculate_match_score(curr_fp, next_fp_new)
                                struct_details = candidate.match_details.get('structure', {})

                                print(f"  [列补齐后] 重新计算得分:")
                                print(f"    几何得分: {candidate.geometry_score:.3f}")
                                print(f"    结构得分: {candidate.structure_score:.3f}")
                                print(f"    视觉得分: {candidate.visual_score:.3f}")
                                print(f"    综合得分: {candidate.score:.3f}")

                        # 补齐后仍然列数不一致，才判定失败
                        if not repaired and not struct_details.get('col_count_match', False):
                            gate_passed = False
                            gate_reason.append(f"列数不一致({num_cols[0]}列 vs {num_cols[1]}列)")

                    if not gate_passed:
                        print(f"  X 未通过门槛检查: {', '.join(gate_reason)}")
                        print()
                        continue  # 直接跳过，不记录为候选

                    # 正文隔断检查（最关键的否定规则）
                    if layout_index:
                        has_para, para_reason = self._has_paragraph_between(curr_table, next_table, layout_index)
                        print(f"  [正文检查] {para_reason}")
                        if has_para:
                            print(f"  X 检测到正文隔断，拒绝合并")
                            print()
                            continue  # 有正文隔断，拒绝合并
                    else:
                        print(f"  [正文检查] 跳过（无布局索引）")

                    # 综合得分检查
                    if candidate.score >= self.score_threshold:
                        print(f"  OK 达到阈值，记录为候选")
                        candidates[(curr_id, next_id)] = candidate
                    else:
                        print(f"  X 未达到阈值")
                    print()

        # Step 4: 构建合并链（避免一对多）
        # 策略：每个表段最多有一个后继，选择得分最高的
        best_next = {}  # {prev_id: next_id}

        # 按得分降序排序
        sorted_candidates = sorted(
            candidates.items(),
            key=lambda x: x[1].score,
            reverse=True
        )

        used_prev = set()
        used_next = set()

        for (prev_id, next_id), candidate in sorted_candidates:
            # 避免一对多
            if prev_id not in used_prev and next_id not in used_next:
                best_next[prev_id] = next_id
                used_prev.add(prev_id)
                used_next.add(next_id)

        # Step 5: 从匹配对构建链
        chains = []
        visited = set()

        for table in tables:
            table_id = table.get('id')
            if table_id in visited:
                continue

            # 尝试构建从当前表开始的链
            chain = [table_id]
            visited.add(table_id)

            # 向后延伸
            curr = table_id
            while curr in best_next:
                next_id = best_next[curr]
                chain.append(next_id)
                visited.add(next_id)
                curr = next_id

            # 只记录长度≥2的链（单表不需要合并）
            if len(chain) >= 2:
                chains.append(chain)

        return chains

    def merge_tables(self,
                    tables: List[Dict[str, Any]],
                    table_ids: List[str],
                    page_drawings: Dict[int, List] = None) -> Dict[str, Any]:
        """
        合并一条链中的多个表段

        流程：
        1. 列对齐：以首段x_edges为基准
        2. 表头去重：识别并跳过续页重复的表头行
        3. 数据行拼接：按页面顺序拼接所有段的数据行
        4. 跨页单元格合并：检测并合并被分页符截断的单元格
        5. bbox合并：计算包络bbox
        6. 嵌套表继承：保留各段的nested_tables
        7. 元数据更新：记录合并来源

        Args:
            tables: 所有表格列表
            table_ids: 要合并的表格ID列表（按顺序）
            page_drawings: 页面绘图数据（用于检测单元格边线，可选）

        Returns:
            合并后的表格对象
        """
        if not table_ids:
            return None

        # Step 1: 提取要合并的表段（按table_ids顺序）
        table_map = {table.get('id'): table for table in tables}
        table_segments = [table_map[tid] for tid in table_ids if tid in table_map]

        if not table_segments:
            return None

        # Step 2: 深拷贝第一段的所有字段作为基准（保证字段完整性）
        first_table = table_segments[0]
        merged = copy.deepcopy(first_table)

        # 然后覆盖需要更新的字段
        merged['rows'] = []  # 待拼接
        # 删除 nested_tables 字段（后续根据实际情况重新添加）
        if 'nested_tables' in merged:
            del merged['nested_tables']

        # Step 2.5: 检测并恢复续页被误判为表头的数据行
        print(f"[合并] 链 {table_ids}")
        self._recover_misidentified_headers(table_segments)

        # Step 3: 拼接数据行
        for i, segment in enumerate(table_segments):
            segment_rows = segment.get('rows', [])
            segment_id = segment.get('id')
            segment_page = segment.get('page')

            if i == 0:
                # 第一段：直接添加所有行
                print(f"  第{i+1}段 {segment_id}(页{segment_page}): 添加所有 {len(segment_rows)} 行")
                merged['rows'].extend(segment_rows)
            else:
                # 续页段：检测并跳过重复表头
                prev_segment = table_segments[i - 1]
                skip_rows = self.detect_repeated_header(prev_segment, segment)

                # 添加去重后的行
                print(f"  第{i+1}段 {segment_id}(页{segment_page}): 检测到重复表头 {skip_rows} 行，添加剩余 {len(segment_rows) - skip_rows} 行")
                merged['rows'].extend(segment_rows[skip_rows:])

                # Step 3.5: 检测并合并跨页截断的单元格（可配置）
                if self.enable_cell_merge and page_drawings and len(merged['rows']) > 0 and len(segment_rows) > skip_rows:
                    # 获取上页最后一行和下页第一行
                    prev_last_row = merged['rows'][-1] if len(merged['rows']) >= len(segment_rows) - skip_rows else None
                    next_first_row = segment_rows[skip_rows] if skip_rows < len(segment_rows) else None

                    if prev_last_row and next_first_row:
                        # 获取对应页面的绘图数据
                        prev_page = prev_segment.get('page')
                        next_page = segment.get('page')
                        prev_drawings = page_drawings.get(prev_page, [])
                        next_drawings = page_drawings.get(next_page, [])

                        # 检测截断的单元格
                        split_indices = _detect_split_cells(
                            prev_last_row,
                            next_first_row,
                            prev_drawings,
                            next_drawings
                        )

                        if split_indices:
                            print(f"  [单元格合并] 检测到 {len(split_indices)} 个跨页截断的单元格")
                            # 合并截断的单元格
                            _merge_split_cells(prev_last_row, next_first_row, split_indices)
                            print(f"  [单元格合并] 完成合并")
                elif not self.enable_cell_merge and i > 0:
                    print(f"  [单元格合并] 已禁用（enable_cell_merge=False）")

            # 收集嵌套表
            nested = segment.get('nested_tables', [])
            if nested:
                if 'nested_tables' not in merged:
                    merged['nested_tables'] = []
                merged['nested_tables'].extend(nested)

        # Step 4: 合并bbox
        # 注意：跨页表格的bbox不能简单合并（不同页面Y坐标系不同）
        # 解决方案：保留第一页的bbox，并在merged_bboxes中记录所有段的bbox
        if len(table_segments) > 1:
            # 保留第一段的bbox作为主bbox（用于兼容性）
            merged['bbox'] = list(first_table.get('bbox', [0, 0, 0, 0]))

            # 记录所有段的bbox（包含页码信息）
            merged['merged_bboxes'] = [
                {
                    'page': seg.get('page'),
                    'bbox': seg.get('bbox', [0, 0, 0, 0])
                }
                for seg in table_segments
            ]

        # Step 5: 更新元数据
        # 记录合并来源和结束页
        last_table = table_segments[-1]
        merged['merged_from'] = table_ids
        merged['page_end'] = last_table.get('page')
        merged['row_count'] = len(merged['rows'])

        print(f"  合并完成: 总共 {len(merged['rows'])} 行")
        print()

        # 如果没有嵌套表，删除该字段
        if 'nested_tables' in merged and not merged['nested_tables']:
            del merged['nested_tables']

        return merged

    def _recover_misidentified_headers(self, table_segments: List[Dict[str, Any]]) -> None:
        """
        检测并恢复续页被误判为表头的数据行

        原理：
        - 如果续页的 columns 与前页的 columns 不一致
        - 说明续页的第0行被 HeaderAnalyzer 误判为表头
        - 此时被误判的数据保存在 columns 中
        - 需要从 columns 恢复这一行，并用前页的 columns 替换

        Args:
            table_segments: 要合并的表段列表（会被原地修改）
        """
        if len(table_segments) < 2:
            return

        # 使用第一段的 columns 作为基准
        base_columns = table_segments[0].get('columns', [])
        base_col_names = [col.get('name', '') for col in base_columns]

        # 检查每个续页
        for i in range(1, len(table_segments)):
            segment = table_segments[i]
            segment_id = segment.get('id')
            segment_page = segment.get('page')

            segment_columns = segment.get('columns', [])
            segment_col_names = [col.get('name', '') for col in segment_columns]

            # 比较 columns 是否一致
            if base_col_names != segment_col_names:
                # columns 不一致 → 续页被误判了表头
                print(f"  [表头恢复] {segment_id}(页{segment_page}): columns 不一致，检测到误判表头")
                print(f"    基准 columns: {base_col_names[:3]}...")
                print(f"    续页 columns: {segment_col_names[:3]}...")

                # 1. 从 columns 构建恢复行
                recovered_row = {
                    'id': 'r001',  # 固定ID，后续会重新编号
                    'rowPath': [],
                    'cells': []
                }

                for j, col in enumerate(segment_columns):
                    col_name = col.get('name', '')
                    col_id = col.get('id', f'c{j+1:03d}')

                    # 创建恢复的 cell
                    cell = {
                        'row_id': 'r001',
                        'col_id': col_id,
                        'rowPath': [],
                        'cellPath': col.get('path', [col_name]) if col_name else [],
                        'content': col_name,  # ← 关键：从 column.name 提取内容
                        'bbox': col.get('bbox'),
                        'id': f'{segment_id}-r001-{col_id}'
                    }
                    recovered_row['cells'].append(cell)

                # 2. 插入到 rows 开头
                segment['rows'].insert(0, recovered_row)

                # 3. 用基准 columns 替换续页的 columns
                segment['columns'] = copy.deepcopy(base_columns)

                print(f"    → 恢复了1行数据，当前行数: {len(segment['rows'])}")

    def detect_repeated_header(self,
                              prev_table: Dict[str, Any],
                              next_table: Dict[str, Any]) -> int:
        """
        检测续页表格开头重复的表头行数

        策略：
        1. 比较next_table前N行与prev_table的header_rows_texts
        2. 完全匹配或高相似度的行判定为重复表头

        Args:
            prev_table: 上一段表格
            next_table: 下一段表格

        Returns:
            重复表头行数（从0开始）
        """
        # 获取上一段的表头文本（从columns提取）
        prev_columns = prev_table.get('columns', [])
        if not prev_columns:
            return 0

        prev_header_row = [col.get('name', '') for col in prev_columns]

        # 获取下一段的数据行
        next_rows = next_table.get('rows', [])
        if not next_rows:
            return 0

        # 检查下一段的第一行是否与上一段的表头匹配
        first_row = next_rows[0]
        first_row_cells = first_row.get('cells', [])
        first_row_texts = [cell.get('content', '') for cell in first_row_cells]

        # 比较文本
        # 需要考虑列数可能不完全一致（有行表头时）
        min_len = min(len(prev_header_row), len(first_row_texts))
        if min_len == 0:
            return 0

        # 计算匹配度
        matched = 0
        for i in range(min_len):
            prev_text = str(prev_header_row[i]).strip()
            next_text = str(first_row_texts[i]).strip()

            # 完全匹配或都为空
            if prev_text == next_text:
                matched += 1
            # 处理空值情况（续页表头可能为空）
            elif not prev_text and not next_text:
                matched += 1

        # 匹配率 ≥ 80% 认为是重复表头
        match_ratio = matched / min_len
        if match_ratio >= 0.8:
            return 1  # 当前只检测第一行，后续可扩展为多行
        else:
            return 0

    def _has_paragraph_between(self,
                               prev_table: Dict[str, Any],
                               next_table: Dict[str, Any],
                               layout_index: Dict[int, List]) -> Tuple[bool, str]:
        """
        检查两个表格之间是否有内容隔断（段落或其他表格）

        Args:
            prev_table: 上一页的表格
            next_table: 下一页的表格
            layout_index: 页面布局索引 {page_num: [blocks]}

        Returns:
            (has_content, reason) 是否有内容隔断及原因说明
        """
        if not layout_index:
            return False, "无布局索引"

        prev_page = prev_table.get('page')
        next_page = next_table.get('page')
        prev_id = prev_table.get('id')
        next_id = next_table.get('id')
        # 使用raw_bbox进行位置判断（未修正的原始bbox）
        prev_bbox = prev_table.get('raw_bbox', prev_table.get('bbox', [0, 0, 0, 0]))
        next_bbox = next_table.get('raw_bbox', next_table.get('bbox', [0, 0, 0, 0]))

        # 只检查相邻页
        if next_page - prev_page != 1:
            return False, "非相邻页"

        # 辅助函数：判断段落是否是页码
        def is_page_number(content: str) -> bool:
            """判断内容是否是页码（过滤页码，不算文本隔断）"""
            if not content:
                return False
            content = content.strip()
            # 常见页码格式："-第X页-"、"第X页"、"- X -"、纯数字等
            import re
            patterns = [
                r'^-?\s*第?\s*\d+\s*页?\s*-?$',  # -第3页-、第3页、-3-
                r'^-?\s*Page\s*\d+\s*-?$',       # Page 3、-Page 3-
                r'^-?\s*\d+\s*-?$',               # 3、-3-
            ]
            for pattern in patterns:
                if re.match(pattern, content, re.IGNORECASE):
                    return True
            return False

        # 检查1: prev_table下方到页底是否有内容（段落或其他表格）
        prev_page_blocks = layout_index.get(prev_page, [])
        for block in prev_page_blocks:
            # 跳过自己
            if block.get('type') == 'table' and block.get('id') == prev_id:
                continue

            # 检查block是否在prev_table下方
            if block['y0'] > prev_bbox[3]:
                block_type = block['type']

                # 表格类型：直接算隔断
                if block_type == 'table':
                    block_info = block.get('id', '未知表格')
                    return True, f"页{prev_page}表{prev_id}下方有{block_info}"

                # 段落类型：过滤页码
                if block_type == 'paragraph':
                    content = block.get('content_preview', '')
                    if is_page_number(content):
                        continue  # 跳过页码
                    return True, f"页{prev_page}表{prev_id}下方有段落"

        # 检查2: 下一页页顶到next_table上方是否有内容
        next_page_blocks = layout_index.get(next_page, [])
        for block in next_page_blocks:
            # 跳过自己
            if block.get('type') == 'table' and block.get('id') == next_id:
                continue

            # 检查block是否在next_table上方
            if block['y1'] < next_bbox[1]:
                block_type = block['type']

                # 表格类型：直接算隔断
                if block_type == 'table':
                    block_info = block.get('id', '未知表格')
                    return True, f"页{next_page}表{next_id}上方有{block_info}"

                # 段落类型：过滤页码
                if block_type == 'paragraph':
                    content = block.get('content_preview', '')
                    if is_page_number(content):
                        continue  # 跳过页码
                    return True, f"页{next_page}表{next_id}上方有段落"

        return False, "无内容隔断"

    def _analyze_and_apply_headers(self, table: Dict[str, Any], debug: bool = False) -> None:
        """
        延迟表头识别：分析并应用表头

        简单实现：将第一行作为表头，更新columns定义，并从rows中移除第一行

        Args:
            table: 待分析的表格（会被原地修改）
            debug: 是否输出调试信息
        """
        rows = table.get('rows', [])
        if not rows:
            if debug:
                print(f"    没有数据行，跳过表头识别")
            return

        # 简单策略：将第一行作为表头
        header_row = rows[0]
        header_cells = header_row.get('cells', [])

        if not header_cells:
            if debug:
                print(f"    第一行没有单元格，跳过表头识别")
            return

        # 更新columns定义
        new_columns = []
        for col_idx, cell in enumerate(header_cells):
            col_id = cell.get('col_id', f'c{col_idx + 1:03d}')
            col_name = cell.get('content', '')

            new_columns.append({
                "id": col_id,
                "index": col_idx,
                "name": col_name,
                "path": [col_name] if col_name else []
            })

        table['columns'] = new_columns

        # 从rows中移除第一行（已经作为表头）
        table['rows'] = rows[1:]

        # 更新header_info
        table['header_info'] = {
            'col_levels': 1,  # 简单单层表头
            'row_levels': 0,
            'multi_level': False,
            'header_detected': True  # 标记表头已识别
        }

        # 更新method标记
        table['method'] = f"{table.get('method', 'unknown')} + delayed_header"

        if debug:
            print(f"    → 识别表头完成：{len(new_columns)}列")
            print(f"    → 列名: {[col['name'][:20] for col in new_columns[:3]]}...")
            print(f"    → 剩余数据行: {len(table['rows'])}行")

    def build_continuation_hints(self,
                                 tables: List[Dict[str, Any]],
                                 page_widths: Dict[int, float],
                                 page_heights: Dict[int, float],
                                 page_drawings: Dict[int, List] = None,
                                 layout_index: Dict[int, List] = None) -> Dict[int, Dict]:
        """
        分析第一轮提取的表格，为可能的续页生成"列模板hint"

        原理：
        - 检测页底表格（y1 > page_height * 0.8）
        - 下一页有表格且贴顶（y0 < page_height * 0.2）
        - 计算续页评分（基于宽度、右边界对齐）
        - 检查正文隔断（如果有正文则不是续页）
        - 返回 hints_by_page

        Args:
            tables: 第一轮提取的所有表格
            page_widths: 页面宽度字典
            page_heights: 页面高度字典
            page_drawings: 页面绘图数据（可选）
            layout_index: 页面布局索引（用于检查正文隔断，可选）

        Returns:
            hints_by_page: {page_num: {"col_xs": [...], "bbox": [...], "score": ...}}
        """
        hints_by_page = {}

        print(f"\n[DEBUG build_continuation_hints] 开始分析，共{len(tables)}个表格")

        # 1. 按页分组表格
        tables_by_page = {}
        for table in tables:
            page = table.get('page', 1)
            if page not in tables_by_page:
                tables_by_page[page] = []
            tables_by_page[page].append(table)

        # 2. 遍历相邻页面，检测续页模式
        sorted_pages = sorted(tables_by_page.keys())

        for i, current_page in enumerate(sorted_pages):
            # 跳过最后一页
            if i >= len(sorted_pages) - 1:
                continue

            next_page = sorted_pages[i + 1]

            # 只处理相邻页
            if next_page != current_page + 1:
                continue

            # 获取当前页的最底部表格（使用raw_bbox判断位置）
            current_tables = tables_by_page[current_page]
            bottom_table = max(current_tables, key=lambda t: t.get('raw_bbox', t.get('bbox', [0,0,0,0]))[3])

            # 获取下一页的最顶部表格（使用raw_bbox判断位置）
            next_tables = tables_by_page[next_page]
            top_table = min(next_tables, key=lambda t: t.get('raw_bbox', t.get('bbox', [0,0,0,0]))[1])

            # 获取页面尺寸
            page_height = page_heights.get(current_page, 842)  # A4默认高度
            next_page_height = page_heights.get(next_page, 842)

            # 使用raw_bbox进行位置判定（未修正的原始bbox）
            bottom_bbox = bottom_table.get('raw_bbox', bottom_table.get('bbox', [0, 0, 0, 0]))
            top_bbox = top_table.get('raw_bbox', top_table.get('bbox', [0, 0, 0, 0]))

            # 3. 检测是否是续页模式（基于raw_bbox位置）
            # 条件1：当前页表格贴底（y1 > page_height * 0.8）
            is_bottom = bottom_bbox[3] > page_height * 0.8

            # 条件2：下一页表格贴顶（y0 < page_height * 0.2）
            is_top = top_bbox[1] < next_page_height * 0.2

            print(f"[DEBUG] 检测页{current_page}→{next_page}:")
            print(f"  底表 {bottom_table.get('id')}: bbox={bottom_bbox}")
            print(f"  顶表 {top_table.get('id')}: bbox={top_bbox}")
            print(f"  is_bottom={is_bottom} ({bottom_bbox[3]} > {page_height * 0.8:.2f})")
            print(f"  is_top={is_top} ({top_bbox[1]} < {next_page_height * 0.2:.2f})")

            if not (is_bottom and is_top):
                print(f"  → 不满足贴底贴顶条件，跳过")
                continue

            # ===== 新增：检查正文隔断 =====
            if layout_index:
                has_para, para_reason = self._has_paragraph_between(bottom_table, top_table, layout_index)
                print(f"  [正文检查] {para_reason}")
                if has_para:
                    print(f"  → 检测到正文隔断，不是续页，跳过")
                    continue
            # ===== 新增结束 =====

            # 4. 计算续页评分
            score = 0.0

            # 4.1 宽度相似度（40%）
            bottom_width = bottom_bbox[2] - bottom_bbox[0]
            top_width = top_bbox[2] - top_bbox[0]
            if bottom_width > 0:
                width_ratio = min(bottom_width, top_width) / max(bottom_width, top_width)
                score += width_ratio * 0.4

            # 4.2 右边界对齐（40%）
            page_width = page_widths.get(current_page, 595)  # A4默认宽度
            right_diff = abs(bottom_bbox[2] - top_bbox[2])
            if right_diff < page_width * 0.03:  # 右边界差异 < 3%
                score += 0.4
            elif right_diff < page_width * 0.05:  # 右边界差异 < 5%
                score += 0.2

            # 4.3 底边/顶边是否封口（20%）
            if page_drawings:
                bottom_drawings = page_drawings.get(current_page, [])
                top_drawings = page_drawings.get(next_page, [])

                # 检测底边是否开口
                has_bottom_border = self._has_horizontal_border(
                    bottom_bbox, bottom_drawings, 'bottom'
                )
                # 检测顶边是否开口
                has_top_border = self._has_horizontal_border(
                    top_bbox, top_drawings, 'top'
                )

                # 如果都没有封口，说明可能是续页
                if not has_bottom_border and not has_top_border:
                    score += 0.2

            # 5. 如果评分达标，生成 hint
            if score >= 0.6:
                # 从底部表格提取列边界
                col_xs = self._extract_column_xs(bottom_table)

                # 计算期望的列数和横向边界
                expected_cols = len(col_xs) - 1 if col_xs else 0
                x0_ref = min(col_xs) if col_xs else bottom_bbox[0]
                x1_ref = max(col_xs) if col_xs else bottom_bbox[2]

                hint = {
                    "col_xs": col_xs,
                    "expected_cols": expected_cols,  # 新增：期望列数
                    "x0_ref": x0_ref,                # 新增：横向左边界
                    "x1_ref": x1_ref,                # 新增：横向右边界
                    "bbox": bottom_bbox,  # 保留作为参考
                    "score": score,
                    "source_table_id": bottom_table.get('id'),
                    "source_page": current_page
                }

                hints_by_page[next_page] = hint

                print(f"[续页检测] 页{current_page}表{bottom_table.get('id')} → 页{next_page}表{top_table.get('id')} (score={score:.2f}, expected_cols={expected_cols})")

        return hints_by_page

    def _extract_column_xs(self, table: Dict[str, Any]) -> List[float]:
        """
        从表格中提取列边界x坐标（基于raw_bbox + 全行cells聚合）

        策略：
        1. 使用raw_bbox作为强制左右边框
        2. 聚合所有行的cell边界
        3. 使用容差去重
        4. 确保返回至少包含左右边框

        Args:
            table: 表格对象（必须包含raw_bbox和rows）

        Returns:
            排序后的列边界x坐标列表
        """
        # 1. 强制边框：使用raw_bbox（未修正的原始bbox）
        raw_bbox = table.get('raw_bbox')
        if not raw_bbox:
            # 兜底：如果没有raw_bbox，使用普通bbox
            raw_bbox = table.get('bbox', [0, 0, 0, 0])

        x0_raw, y0_raw, x1_raw, y1_raw = raw_bbox

        # 初始化候选集：先放入左右边框
        x_candidates = [x0_raw, x1_raw]

        # 2. 聚合所有行的cell边界
        rows = table.get('rows', [])
        for row in rows:
            cells = row.get('cells', [])
            for cell in cells:
                cell_bbox = cell.get('bbox')
                if not cell_bbox:
                    continue

                cx0, cy0, cx1, cy1 = cell_bbox

                # 只收集落在raw_bbox横向范围内的边界
                if x0_raw <= cx0 <= x1_raw:
                    x_candidates.append(cx0)
                if x0_raw <= cx1 <= x1_raw:
                    x_candidates.append(cx1)

        # 3. 去重并排序（使用2.5pt容差）
        col_xs = self._dedup_edges(sorted(x_candidates), tolerance=2.5)

        # 4. 确保左右边框一定在列表中
        col_xs = self._ensure_frame_edges(col_xs, x0_raw, x1_raw)

        print(f"  [列边界提取] 从raw_bbox [{x0_raw:.1f}, {x1_raw:.1f}] + {len(rows)}行cells")
        print(f"  [列边界提取] 提取到 {len(col_xs)} 个列边界: {[f'{x:.1f}' for x in col_xs[:8]]}")

        return col_xs

    def _dedup_edges(self, edges: List[float], tolerance: float = 2.5) -> List[float]:
        """
        去重相近的边界（容差内的边界合并为一个）

        Args:
            edges: 排序后的边界坐标列表
            tolerance: 容差（pt）

        Returns:
            去重后的边界列表
        """
        if not edges:
            return []

        result = [edges[0]]
        for edge in edges[1:]:
            if abs(edge - result[-1]) > tolerance:
                result.append(edge)

        return result

    def _ensure_frame_edges(self, col_xs: List[float], x0: float, x1: float) -> List[float]:
        """
        确保左右边框在列边界列表中

        Args:
            col_xs: 当前列边界列表
            x0: 左边框
            x1: 右边框

        Returns:
            包含左右边框的列边界列表
        """
        result = list(col_xs)

        # 确保左边框
        if not result or result[0] > x0 + 1.0:
            result.insert(0, x0)

        # 确保右边框
        if not result or result[-1] < x1 - 1.0:
            result.append(x1)

        return result

    def _has_horizontal_border(self, bbox: List[float], drawings: List, position: str) -> bool:
        """检测表格顶部或底部是否有完整横线"""
        if not drawings:
            return False

        x0, y0, x1, y1 = bbox
        target_y = y0 if position == 'top' else y1
        tolerance = 5  # 允许5pt的误差

        # 检查是否有横线覆盖了表格宽度的大部分
        for drawing in drawings:
            if drawing.get('type') != 'l':  # line
                continue

            # 检查y坐标是否匹配
            line_y = drawing.get('rect', [0, 0, 0, 0])[1]
            if abs(line_y - target_y) > tolerance:
                continue

            # 检查x方向覆盖度
            line_x0 = drawing.get('rect', [0, 0, 0, 0])[0]
            line_x1 = drawing.get('rect', [0, 0, 0, 0])[2]

            overlap_x0 = max(x0, line_x0)
            overlap_x1 = min(x1, line_x1)
            overlap_width = max(0, overlap_x1 - overlap_x0)
            table_width = x1 - x0

            if table_width > 0 and overlap_width / table_width >= 0.8:
                return True

        return False

    def _try_repair_missing_columns(self,
                                   prev_table: Dict[str, Any],
                                   next_table: Dict[str, Any],
                                   prev_fp: TableFingerprint,
                                   next_fp: TableFingerprint,
                                   hint: Dict) -> bool:
        """
        尝试补齐下一页表格的缺失列

        触发条件：
        1. 有hint（续页检测）
        2. BBox和上一页几乎相等（容差5pt）
        3. 下一页列数 < 上一页列数
        4. hint中的expected_cols > 下一页列数

        Args:
            prev_table: 上一页表格
            next_table: 下一页表格（会被原地修改）
            prev_fp: 上一页指纹
            next_fp: 下一页指纹
            hint: 续页hint（包含col_xs、expected_cols等）

        Returns:
            是否成功补齐
        """
        # 检查列数
        prev_cols = len(prev_fp.col_paths)
        next_cols = len(next_fp.col_paths)

        if next_cols >= prev_cols:
            # 下一页列数不少于上一页，无需补齐
            return False

        expected_cols = hint.get('expected_cols', 0)
        if next_cols >= expected_cols:
            # 下一页列数已经达到hint的预期，无需补齐
            return False

        # 检查BBox是否几乎相等（容差5pt）
        prev_bbox = prev_table.get('raw_bbox', prev_table.get('bbox', [0, 0, 0, 0]))
        next_bbox = next_table.get('raw_bbox', next_table.get('bbox', [0, 0, 0, 0]))

        if not self._bbox_almost_equal(prev_bbox, next_bbox, tolerance=5.0):
            print(f"  [列补齐检查] BBox不相等，跳过")
            print(f"    prev_bbox: {prev_bbox}")
            print(f"    next_bbox: {next_bbox}")
            return False

        # 满足所有条件，开始补齐
        print(f"  [列补齐] 满足条件:")
        print(f"    prev_cols={prev_cols}, next_cols={next_cols}, expected_cols={expected_cols}")
        print(f"    bbox相等（容差5pt）")

        # 计算需要补齐的列数
        missing_cols = prev_cols - next_cols

        print(f"  [列补齐] 开始补齐 {missing_cols} 个缺失列")

        # TODO: 当前实现为简单插入空列
        # 未来改进方向：
        # 1. 从hint的col_xs中找到缺失的列边界
        # 2. 检查缺失的列宽是否与hint中的某一列宽度匹配
        # 3. 使用PyMuPDF重新切分单元格（更准确）
        #
        # 简单实现：在最左侧插入空列
        # 假设pdfplumber漏检了左侧列

        # 在columns开头插入空列
        for i in range(missing_cols):
            # 创建空列定义
            empty_col = {
                "id": f"c{i+1:03d}",
                "index": i,
                "name": "",  # 空列
                "path": [""]
            }
            next_table['columns'].insert(0, empty_col)

        # 更新所有行的列索引
        for col_idx, col in enumerate(next_table['columns']):
            col['index'] = col_idx
            col['id'] = f"c{col_idx+1:03d}"

        # 在每一行的cells开头插入空cell
        for row in next_table.get('rows', []):
            for i in range(missing_cols):
                empty_cell = {
                    "row_id": row.get('id', 'r001'),
                    "col_id": f"c{i+1:03d}",
                    "rowPath": row.get('rowPath', []),
                    "cellPath": [""],
                    "content": "",
                    "bbox": None  # 空列没有bbox
                }
                row['cells'].insert(0, empty_cell)

            # 更新所有cells的col_id
            for col_idx, cell in enumerate(row['cells']):
                cell['col_id'] = f"c{col_idx+1:03d}"

        print(f"  [列补齐] 补齐完成，现在有 {len(next_table['columns'])} 列")

        return True

    def _bbox_almost_equal(self, bbox1: List[float], bbox2: List[float], tolerance: float = 5.0) -> bool:
        """
        检查两个bbox是否几乎相等（允许容差）

        Args:
            bbox1: 第一个bbox [x0, y0, x1, y1]
            bbox2: 第二个bbox [x0, y0, x1, y1]
            tolerance: 容差（pt）

        Returns:
            是否几乎相等
        """
        if len(bbox1) != 4 or len(bbox2) != 4:
            return False

        # 检查每个坐标的差异
        for i in range(4):
            if abs(bbox1[i] - bbox2[i]) > tolerance:
                return False

        return True

    def merge_all_tables(self,
                        tables: List[Dict[str, Any]],
                        page_widths: Dict[int, float],
                        page_drawings: Dict[int, List] = None,
                        layout_index: Dict[int, List] = None,
                        hints_by_page: Dict[int, Dict] = None,
                        debug: bool = False) -> List[Dict[str, Any]]:
        """
        主入口：识别并合并所有跨页表格

        Args:
            tables: 从TableExtractor提取的所有表格
            page_widths: 页面宽度字典
            page_drawings: 页面绘图数据（可选）
            layout_index: 页面布局索引（用于检查正文隔断，可选）
            hints_by_page: 续页检测hints（用于列补齐，可选）
            debug: 是否输出调试信息

        Returns:
            合并后的表格列表（保持原有结构，未合并的表格不变）
        """
        if debug:
            print(f"\n[CrossPageMerger] 开始跨页表格合并，输入表格数: {len(tables)}")

        # Step 1: 识别合并链
        merge_chains = self.find_merge_chains(tables, page_widths, page_drawings, layout_index, hints_by_page)

        if debug:
            print(f"[CrossPageMerger] 识别到 {len(merge_chains)} 条合并链:")
            for i, chain in enumerate(merge_chains):
                print(f"  链{i+1}: {chain}")

        # Step 2: 执行合并
        merged_tables = []
        merged_ids = set()

        for chain in merge_chains:
            if len(chain) > 1:
                # 合并这条链
                merged_table = self.merge_tables(tables, chain, page_drawings)
                merged_tables.append(merged_table)
                merged_ids.update(chain)
                if debug:
                    print(f"[合并] 链 {chain} -> 合并后表格页码{merged_table.get('page')}")

        # Step 3: 添加未合并的表格
        if debug:
            print(f"\n[未合并表格] 共{len(tables)}个输入表格，其中{len(merged_ids)}个已合并")

        for table in tables:
            table_id = table.get('id')
            if table_id not in merged_ids:
                merged_tables.append(table)
                if debug:
                    print(f"  保留未合并表格: {table_id} (页{table.get('page')})")
            else:
                if debug:
                    print(f"  跳过已合并表格: {table_id} (页{table.get('page')})")

        if debug:
            print(f"\n[CrossPageMerger] 合并完成，输出表格数: {len(merged_tables)}")
            print(f"  输出表格列表:")
            for i, t in enumerate(merged_tables):
                print(f"    [{i}] id={t.get('id')}, page={t.get('page')}, rows={len(t.get('rows', []))}")

        # Step 4: 延迟表头识别 - 对未识别表头的表格进行分析
        if debug:
            print(f"\n[延迟表头识别] 开始分析未识别表头的表格")

        for table in merged_tables:
            header_info = table.get('header_info', {})
            header_detected = header_info.get('header_detected', True)

            if not header_detected:
                if debug:
                    print(f"  分析表格 {table.get('id')} (页{table.get('page')}): 未识别表头")
                self._analyze_and_apply_headers(table, debug=debug)

        return merged_tables


def _calculate_jaccard_similarity(list1: List[float],
                                  list2: List[float],
                                  tolerance: float = 0.01) -> float:
    """
    计算两个浮点数列表的Jaccard相似度（允许容差）

    Args:
        list1: 第一个列表
        list2: 第二个列表
        tolerance: 允许的误差范围

    Returns:
        Jaccard相似度 [0, 1]
    """
    if not list1 and not list2:
        return 1.0
    if not list1 or not list2:
        return 0.0

    # 匹配数量（带容差）
    matched = 0
    used_indices = set()

    for val1 in list1:
        for i, val2 in enumerate(list2):
            if i not in used_indices and abs(val1 - val2) < tolerance:
                matched += 1
                used_indices.add(i)
                break

    # Jaccard = 交集 / 并集
    union_size = len(list1) + len(list2) - matched
    return matched / union_size if union_size > 0 else 0.0


def _calculate_col_paths_similarity(paths1: List[List[str]],
                                    paths2: List[List[str]]) -> float:
    """
    计算列路径相似度

    策略：
    1. 如果长度不同，按较短的计算
    2. 逐个比较路径，完全匹配计1分，部分匹配按层级比例计分

    Args:
        paths1: 第一个表的列路径
        paths2: 第二个表的列路径

    Returns:
        相似度 [0, 1]
    """
    if not paths1 and not paths2:
        return 1.0
    if not paths1 or not paths2:
        return 0.0

    # 长度不同是弱信号（可能列被截断/合并），但不完全排除
    min_len = min(len(paths1), len(paths2))
    if min_len == 0:
        return 0.0

    total_score = 0.0
    for i in range(min_len):
        path1 = paths1[i]
        path2 = paths2[i]

        # 完全匹配
        if path1 == path2:
            total_score += 1.0
        else:
            # 部分匹配（计算层级重叠）
            max_layers = max(len(path1), len(path2))
            if max_layers == 0:
                continue

            matched_layers = 0
            for j in range(min(len(path1), len(path2))):
                if path1[j] == path2[j]:
                    matched_layers += 1
                else:
                    break  # 层级匹配需要连续

            total_score += matched_layers / max_layers

    return total_score / min_len


def _hash_col_paths(col_paths: List[List[str]]) -> str:
    """
    计算列路径列表的哈希值

    Args:
        col_paths: 列路径列表

    Returns:
        MD5哈希字符串
    """
    # 将col_paths序列化为字符串后计算哈希
    path_str = "|".join(["->".join(path) for path in col_paths])
    return hashlib.md5(path_str.encode()).hexdigest()


def _normalize_to_page_width(value: float, page_width: float) -> float:
    """
    将坐标值归一化到页面宽度

    Args:
        value: 原始坐标值
        page_width: 页面宽度

    Returns:
        归一化值 [0, 1]
    """
    return value / page_width if page_width > 0 else 0


def _cell_has_horizontal_line(cell_bbox: List[float],
                               y_position: float,
                               drawings: List,
                               coverage_threshold: float = 0.5) -> bool:
    """
    检查单元格的某条边（顶边或底边）是否有完整横线

    Args:
        cell_bbox: 单元格bbox [x0, y0, x1, y1]
        y_position: 要检查的Y坐标（通常是 bbox[1] 或 bbox[3]）
        drawings: 页面线条数据
        coverage_threshold: 覆盖率阈值（默认0.5，即横线覆盖≥50%单元格宽度）

    Returns:
        True: 有完整横线
        False: 无横线或横线不完整
    """
    if not drawings or not cell_bbox:
        return False

    x0, y0, x1, y1 = cell_bbox
    cell_width = x1 - x0

    if cell_width <= 0:
        return False

    # 容差：线条位置允许的偏移
    y_tolerance = 2.0

    # 遍历所有绘图元素
    for drawing in drawings:
        if not isinstance(drawing, dict):
            continue

        items = drawing.get('items', [])
        for item in items:
            # 只关注直线（'l'表示line）
            if not isinstance(item, tuple) or len(item) < 3:
                continue

            item_type = item[0]
            if item_type != 'l':
                continue

            p1 = item[1]  # 起点 (x, y)
            p2 = item[2]  # 终点 (x, y)

            if not isinstance(p1, (tuple, list)) or not isinstance(p2, (tuple, list)):
                continue
            if len(p1) < 2 or len(p2) < 2:
                continue

            line_x0 = min(p1[0], p2[0])
            line_x1 = max(p1[0], p2[0])
            line_y0 = min(p1[1], p2[1])
            line_y1 = max(p1[1], p2[1])

            # 判断是否为横线（y坐标变化小）
            if abs(line_y1 - line_y0) > 2.0:
                continue

            line_y = (line_y0 + line_y1) / 2

            # 检查Y坐标是否匹配
            if abs(line_y - y_position) > y_tolerance:
                continue

            # 计算线条与单元格的水平重叠
            overlap_x0 = max(line_x0, x0)
            overlap_x1 = min(line_x1, x1)
            overlap_width = max(0, overlap_x1 - overlap_x0)
            overlap_ratio = overlap_width / cell_width

            # 如果覆盖率达到阈值，认为有完整横线
            if overlap_ratio >= coverage_threshold:
                return True

    return False


def _detect_split_cells(prev_last_row: Dict,
                        next_first_row: Dict,
                        prev_drawings: List,
                        next_drawings: List) -> List[Tuple[int, int]]:
    """
    检测跨页截断的单元格（基于特征的直接判断）

    必须同时满足以下条件：
    1. 列位置一致：col_id 相同 或 x坐标范围重叠 > 80%
    2. 上页单元格：底边没有完整横线（覆盖率 < 50%）
    3. 下页单元格：顶边没有完整横线（覆盖率 < 50%）

    Args:
        prev_last_row: 上页最后一行（包含cells列表）
        next_first_row: 下页第一行（包含cells列表）
        prev_drawings: 上页的线条数据
        next_drawings: 下页的线条数据

    Returns:
        [(col_index_prev, col_index_next), ...] 被截断的单元格索引对
    """
    if not prev_last_row or not next_first_row:
        return []

    prev_cells = prev_last_row.get('cells', [])
    next_cells = next_first_row.get('cells', [])

    if not prev_cells or not next_cells:
        return []

    split_indices = []

    # 遍历上页最后一行的每个单元格
    for prev_idx, prev_cell in enumerate(prev_cells):
        prev_bbox = prev_cell.get('bbox')
        prev_col_id = prev_cell.get('col_id')

        if not prev_bbox or len(prev_bbox) < 4:
            continue

        prev_x0, prev_y0, prev_x1, prev_y1 = prev_bbox
        prev_width = prev_x1 - prev_x0

        if prev_width <= 0:
            continue

        # 遍历下页第一行的每个单元格，寻找匹配的列
        for next_idx, next_cell in enumerate(next_cells):
            next_bbox = next_cell.get('bbox')
            next_col_id = next_cell.get('col_id')

            if not next_bbox or len(next_bbox) < 4:
                continue

            next_x0, next_y0, next_x1, next_y1 = next_bbox
            next_width = next_x1 - next_x0

            if next_width <= 0:
                continue

            # 条件1：列位置一致（col_id相同 或 x坐标重叠 > 80%）
            col_match = False

            # 方式1：col_id相同
            if prev_col_id and next_col_id and prev_col_id == next_col_id:
                col_match = True
            else:
                # 方式2：x坐标重叠 > 80%
                overlap_x0 = max(prev_x0, next_x0)
                overlap_x1 = min(prev_x1, next_x1)
                overlap_width = max(0, overlap_x1 - overlap_x0)

                # 计算重叠率（相对于较小的单元格宽度）
                min_width = min(prev_width, next_width)
                overlap_ratio = overlap_width / min_width if min_width > 0 else 0

                if overlap_ratio > 0.8:
                    col_match = True

            if not col_match:
                continue

            # 条件2：上页单元格底边没有完整横线
            prev_has_bottom = _cell_has_horizontal_line(
                prev_bbox,
                prev_y1,  # 底边Y坐标
                prev_drawings,
                coverage_threshold=0.5
            )

            if prev_has_bottom:
                continue

            # 条件3：下页单元格顶边没有完整横线
            next_has_top = _cell_has_horizontal_line(
                next_bbox,
                next_y0,  # 顶边Y坐标
                next_drawings,
                coverage_threshold=0.5
            )

            if next_has_top:
                continue

            # 所有条件都满足，认为这是一对被截断的单元格
            split_indices.append((prev_idx, next_idx))
            break  # 找到匹配的下页单元格后，停止内层循环

    return split_indices


def _merge_split_cells(prev_row: Dict,
                       next_row: Dict,
                       split_indices: List[Tuple[int, int]]) -> None:
    """
    合并截断的单元格（原地修改 prev_row 和 next_row）

    操作：
    1. 将下页单元格的内容追加到上页单元格
    2. 标记下页单元格为已合并（设置特殊标记）
    3. 保留上页单元格的bbox（跨页bbox不能直接合并）
    4. 在元数据中记录 split_across_pages: True

    Args:
        prev_row: 上页最后一行（会被原地修改）
        next_row: 下页第一行（会被原地修改）
        split_indices: 被截断的单元格索引对列表
    """
    if not split_indices:
        return

    prev_cells = prev_row.get('cells', [])
    next_cells = next_row.get('cells', [])

    for prev_idx, next_idx in split_indices:
        if prev_idx >= len(prev_cells) or next_idx >= len(next_cells):
            continue

        prev_cell = prev_cells[prev_idx]
        next_cell = next_cells[next_idx]

        # 1. 合并内容
        prev_content = prev_cell.get('content', '')
        next_content = next_cell.get('content', '')

        # 智能合并策略：
        # - 如果上页内容以"、，；：-"等结尾，直接拼接
        # - 否则可能需要空格或换行分隔
        if prev_content.rstrip().endswith(('、', '，', '；', '：', '-', '续', '（')):
            merged_content = prev_content + next_content
        elif prev_content.strip() and next_content.strip():
            # 两边都有内容，用空格分隔
            merged_content = prev_content.rstrip() + ' ' + next_content.lstrip()
        else:
            # 有一边为空，直接拼接
            merged_content = prev_content + next_content

        prev_cell['content'] = merged_content

        # 2. 标记为跨页合并
        prev_cell['split_across_pages'] = True
        prev_cell['merged_from_next_page'] = True

        # 3. 标记下页单元格为已合并（内容已移至上页）
        next_cell['merged_to_prev_page'] = True
        next_cell['original_content'] = next_content  # 保留原始内容供调试
        # 清空下页单元格的内容（避免重复显示）
        next_cell['content'] = ''

        # 4. bbox保留上页的（跨页bbox无法合并）
        # 不修改 prev_cell['bbox']