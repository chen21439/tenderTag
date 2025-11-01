
"""
PDF内容提取主协调器
协调表格提取器和段落提取器，统一编号和保存
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional
import fitz  # PyMuPDF
from datetime import datetime

try:
    from .table_extractor import TableExtractor
    from .paragraph_extractor import ParagraphExtractor
    from .cross_page_merger import CrossPageTableMerger
    from .crossPageTable import CrossPageCellClassifier
except ImportError:
    from table_extractor import TableExtractor
    from paragraph_extractor import ParagraphExtractor
    from cross_page_merger import CrossPageTableMerger
    from crossPageTable import CrossPageCellClassifier

# Qdrant 导入
try:
    import sys
    from pathlib import Path as ImportPath
    # 添加项目根目录到 sys.path（向上3级到达 table/ 目录）
    project_root = ImportPath(__file__).resolve().parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from app.utils.db.qdrant import QdrantUtil
    QDRANT_AVAILABLE = True
except ImportError as e:
    print(f"[警告] Qdrant 不可用: {e}")
    QDRANT_AVAILABLE = False


class PDFContentExtractor:
    """PDF内容提取主协调器"""

    def __init__(self,
                 pdf_path: str,
                 enable_cross_page_merge: bool = True,
                 enable_cell_merge: bool = False,
                 enable_ai_row_classification: bool = False,
                 verbose: bool = False,
                 enable_vectorization: bool = False,
                 qdrant_url: str = "http://localhost:6333",
                 embedding_model: str = "BAAI/bge-m3",
                 device: str = "auto"):
        """
        初始化PDF内容提取器

        Args:
            pdf_path: PDF文件路径
            enable_cross_page_merge: 是否启用跨页表格合并（默认True）
            enable_cell_merge: 是否启用跨页单元格合并（默认False，暂时关闭）
                              只有在 enable_cross_page_merge=True 时才有效
            enable_ai_row_classification: 是否启用AI行级别判断（默认True）
                                        用于跨页单元格内容的TR级别合并
                                        只有在 enable_cross_page_merge=True 时才有效
            verbose: 是否输出详细日志（默认False，只输出关键信息）
            enable_vectorization: 是否启用向量化（默认False）
            qdrant_url: Qdrant服务器地址（默认 http://localhost:6333）
            embedding_model: 向量化模型名称（默认 BAAI/bge-m3）
            device: 计算设备 ('auto', 'cuda', 'cpu'，默认 'auto' 自动检测）
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

        # 保存配置参数
        self.verbose = verbose
        self.enable_ai_row_classification = enable_ai_row_classification
        self.enable_vectorization = enable_vectorization

        # 初始化各个提取器
        self.table_extractor = TableExtractor(pdf_path)
        self.paragraph_extractor = ParagraphExtractor(pdf_path)

        # 初始化跨页表格合并器
        self.enable_cross_page_merge = enable_cross_page_merge
        if enable_cross_page_merge:
            self.cross_page_merger = CrossPageTableMerger(
                score_threshold=0.70,
                geometry_weight=0.40,
                structure_weight=0.35,
                visual_weight=0.25,
                enable_cell_merge=enable_cell_merge
            )
        else:
            self.cross_page_merger = None

        # 全局块计数器（用于docN编号）
        self.block_counter = 0

        # 页面宽度缓存
        self._page_widths = None
        # 页面高度缓存
        self._page_heights = None
        # 页面drawings缓存
        self._page_drawings = None

        # 初始化向量化组件（如果启用）
        self.indexer = None
        self.searcher = None
        if enable_vectorization and QDRANT_AVAILABLE:
            self._init_vectorization(qdrant_url, embedding_model, device)

    def extract_tables(self):
        """
        仅提取表格

        Returns:
            表格列表
        """
        return self.table_extractor.extract_tables()

    def extract_paragraphs(self, table_bboxes_per_page: Dict[int, list] = None):
        """
        仅提取段落

        Args:
            table_bboxes_per_page: 每页的表格bbox列表（如不提供，自动检测）

        Returns:
            段落列表
        """
        return self.paragraph_extractor.extract_paragraphs(table_bboxes_per_page)


    def extract_all_content(self) -> Dict[str, Any]:
        """
        提取所有内容（表格+段落），按页面和Y坐标排序，统一编号
        Returns:
            包含所有内容的字典
        """
        # 1. 提取表格
        tables_raw = self.table_extractor.extract_tables()

        # 1.1. 先为表格分配临时id（用于跨页合并）
        for i, table in enumerate(tables_raw):
            if 'id' not in table or table['id'] is None:
                table['id'] = f"temp_{i:03d}"

        # 1.5. 跨页表格合并（如果启用）
        if self.enable_cross_page_merge and self.cross_page_merger and tables_raw:
            page_widths = self._get_page_widths()
            page_drawings = self._get_page_drawings()
            tables_raw = self.cross_page_merger.merge_all_tables(
                tables_raw,
                page_widths,
                page_drawings=page_drawings,
                debug=False
            )

        # 2. 获取表格bbox（供段落提取使用）
        table_bboxes_per_page = self._build_table_bboxes_map(tables_raw)

        # 3. 提取段落
        paragraphs_raw = self.paragraph_extractor.extract_paragraphs(table_bboxes_per_page)

        # 4. 合并所有内容块，添加排序键
        all_blocks = []

        # 添加表格
        for table in tables_raw:
            # 计算表格的y0（用于排序）
            table_y0 = table.get("bbox", [0, 0, 0, 0])[1] if table.get("bbox") else 0
            all_blocks.append({
                "type": "table",
                "page": table["page"],
                "y0": table_y0,
                "data": table
            })

        # 添加段落
        for para in paragraphs_raw:
            all_blocks.append({
                "type": "paragraph",
                "page": para["page"],
                "y0": para["y0"],
                "data": para
            })

        # 5. 按页面顺序和y坐标排序
        all_blocks.sort(key=lambda x: (x["page"], x["y0"]))

        # 6. 重新分配docN编号
        structured_blocks = []
        self.block_counter = 0

        for block in all_blocks:
            self.block_counter += 1
            doc_id = f"doc{self.block_counter:03d}"

            if block["type"] == "table":
                # 更新表格的id
                table_data = block["data"]
                table_data["id"] = doc_id

                # 更新所有cell的id
                for row in table_data.get("rows", []):
                    row_id = row["id"]
                    for cell in row.get("cells", []):
                        col_id = cell["col_id"]
                        cell["id"] = f"{doc_id}-{row_id}-{col_id}"

                # 更新嵌套表格的parent_table_id
                for row in table_data.get("rows", []):
                    for cell in row.get("cells", []):
                        if "nested_tables" in cell:
                            for nested_table in cell["nested_tables"]:
                                nested_table["parent_table_id"] = doc_id

                structured_blocks.append(table_data)

            elif block["type"] == "paragraph":
                # 构建结构化段落
                para_data = block["data"]
                structured_blocks.append({
                    "type": "paragraph",
                    "id": doc_id,
                    "page": para_data["page"],
                    "bbox": para_data["bbox"],
                    "content": para_data["content"]
                })

        # 7. 获取页面元数据
        metadata = self._get_page_metadata()

        return {
            "pdf_file": str(self.pdf_path),
            "total_blocks": len(structured_blocks),
            "total_tables": sum(1 for b in structured_blocks if b.get("type") == "table"),
            "total_paragraphs": sum(1 for b in structured_blocks if b.get("type") == "paragraph"),
            "blocks": structured_blocks,
            "page_metadata": metadata
        }

    def extract_all_tables(self) -> Dict[str, Any]:
        """
        仅提取表格（带元数据）

        Returns:
            包含表格数据和元数据的字典
        """
        # 第一轮：正常提取（使用延迟表头识别）
        tables = self.table_extractor.extract_tables(detect_header=False)

        # 先为表格分配临时id（用于跨页合并）
        for i, table in enumerate(tables):
            if 'id' not in table or table['id'] is None:
                table['id'] = f"temp_{i:03d}"

        # 保存第一轮原始提取结果（用于调试）
        import copy
        tables_first_round = copy.deepcopy(tables)  # 真正的原始表格
        tables_before_merge = copy.deepcopy(tables)  # 将被更新为重提取后的表格
        hints_by_page = {}  # 初始化hints

        # 第二轮：使用续页hint重新提取（如果启用跨页合并）
        if self.enable_cross_page_merge and self.cross_page_merger and tables:
            page_widths = self._get_page_widths()
            page_heights = self._get_page_heights()
            page_drawings = self._get_page_drawings()

            # 构建布局索引（用于检查续页hint时的正文隔断）
            table_bboxes_per_page = self._build_table_bboxes_map(tables)
            paragraphs = self.paragraph_extractor.extract_paragraphs(table_bboxes_per_page)
            layout_index_for_hints = self._build_layout_index(tables, paragraphs)

            # 生成续页hints（传入layout_index用于正文隔断检测）
            hints_by_page = self.cross_page_merger.build_continuation_hints(
                tables,
                page_widths,
                page_heights,
                page_drawings,
                layout_index_for_hints
            )

            # 如果有hints，重新提取
            if hints_by_page:
                tables = self.table_extractor.reextract_with_hints(hints_by_page, tables)
                # 更新合并前的备份
                tables_before_merge = copy.deepcopy(tables)

        # AI 行级别判断（如果有 hints 且启用了AI判断）
        ai_row_decisions = []
        row_pairs = []  # 初始化为空列表（确保变量在作用域内）
        if hints_by_page and self.enable_ai_row_classification:
            print(f"\n[AI判断] hints_by_page 的页码: {sorted(hints_by_page.keys())}")
            # 输出hint详细信息
            for page_num, hint in sorted(hints_by_page.items()):
                print(f"  页{page_num}: expected_cols={hint.get('expected_cols', 0)}, score={hint.get('score', 0):.2f}, source=页{hint.get('source_page', 'unknown')}表{hint.get('source_table_id', 'unknown')}")
            # 输出hint耗时统计
            if hasattr(self.cross_page_merger, 'timing_stats') and 'hint_generation' in self.cross_page_merger.timing_stats:
                hint_time = self.cross_page_merger.timing_stats['hint_generation']
                print(f"  [⏱ Hint生成耗时: {hint_time:.3f}秒]")
            row_pairs = self._collect_hint_row_pairs(tables, hints_by_page)
            if row_pairs:
                print(f"\n[AI判断] 检测到 {len(row_pairs)} 个跨页行对，正在批量判断...")
                try:
                    import time
                    ai_start_time = time.time()

                    classifier = CrossPageCellClassifier(truncate_length=50)
                    ai_row_decisions = classifier.classify_row_pairs_batch(row_pairs)

                    ai_elapsed = time.time() - ai_start_time

                    # 打印判断结果（包含表格位置信息和耗时）
                    merge_count = sum(1 for d in ai_row_decisions if d.get('should_merge'))
                    no_merge_count = len(ai_row_decisions) - merge_count
                    print(f"[AI判断] 完成判断: {merge_count} 个应合并, {no_merge_count} 个不合并")
                    print(f"[AI判断] 耗时: {ai_elapsed:.2f}秒 (平均 {ai_elapsed/len(row_pairs):.2f}秒/行对)")

                    for i, (decision, pair) in enumerate(zip(ai_row_decisions, row_pairs)):
                        should_merge = decision.get('should_merge')
                        confidence = decision.get('confidence', 0)
                        reason = decision.get('reason', '')

                        # 从 pair 中获取上下文信息
                        ctx = pair.get('context', {})
                        prev_page = ctx.get('prev_page', '?')
                        next_page = ctx.get('next_page', '?')
                        prev_uuid = ctx.get('prev_table_uuid', 'N/A')[:8]  # 只显示前8位
                        next_uuid = ctx.get('next_table_uuid', 'N/A')[:8]
                        prev_row_id = ctx.get('prev_row_id', '?')
                        next_row_id = ctx.get('next_row_id', '?')

                        status = "✅ 合并" if should_merge else "❌ 不合并"
                        print(f"  行对 {i+1}: {status} (置信度: {confidence:.2f})")
                        print(f"    上页: 页{prev_page} UUID:{prev_uuid} 行:{prev_row_id}")
                        print(f"    下页: 页{next_page} UUID:{next_uuid} 行:{next_row_id}")
                        if reason:
                            print(f"    原因: {reason[:80]}")
                except Exception as e:
                    print(f"[AI判断] 错误: {e}")
                    import traceback
                    traceback.print_exc()
        elif hints_by_page and not self.enable_ai_row_classification:
            print(f"\n[AI判断] 已禁用（enable_ai_row_classification=False），跳过TR级别行合并")

        # TR 级别行合并（根据 AI 判断结果）
        if ai_row_decisions and row_pairs:
            print(f"\n[TR级别行合并] 开始根据 AI 判断结果合并跨页行...")
            tables = self._apply_tr_level_row_merge(tables, ai_row_decisions, row_pairs)
            print(f"[TR级别行合并] 完成\n")

        # 跨页表格合并（如果启用）
        if self.enable_cross_page_merge and self.cross_page_merger and tables:
            # 构建布局索引（用于检查表格间是否有正文隔断）
            table_bboxes_per_page = self._build_table_bboxes_map(tables)
            paragraphs = self.paragraph_extractor.extract_paragraphs(table_bboxes_per_page)
            layout_index = self._build_layout_index(tables, paragraphs)

            page_widths = self._get_page_widths()
            page_drawings = self._get_page_drawings()
            tables = self.cross_page_merger.merge_all_tables(
                tables,
                page_widths,
                page_drawings=page_drawings,
                layout_index=layout_index,  # 传入布局索引
                hints_by_page=hints_by_page,  # 传入hints（用于列补齐）
                debug=False  # 关闭表格合并的调试日志
            )

        # 重新分配正式的docN编号
        self.block_counter = 0
        for table in tables:
            self.block_counter += 1
            doc_id = f"doc{self.block_counter:03d}"
            table["id"] = doc_id

            # 更新cell id
            for row in table.get("rows", []):
                row_id = row["id"]
                for cell in row.get("cells", []):
                    col_id = cell["col_id"]
                    cell["id"] = f"{doc_id}-{row_id}-{col_id}"

            # 更新嵌套表格的parent_table_id
            for row in table.get("rows", []):
                for cell in row.get("cells", []):
                    if "nested_tables" in cell:
                        for nested_table in cell["nested_tables"]:
                            nested_table["parent_table_id"] = doc_id

        # 清理最终表格的文本内容（去掉 \n 等符号）
        # 注意：tables_first_round 和 tables_before_merge 保留原始 \n
        for table in tables:
            self._clean_table_content(table)

        metadata = self._get_page_metadata()

        result = {
            "pdf_file": str(self.pdf_path),
            "total_tables": len(tables),
            "tables": tables,
            "page_metadata": metadata
        }

        # 保存第一轮原始提取（用于调试）
        if tables_first_round:
            result["tables_first_round"] = tables_first_round

        # 保存重提取后、合并前的表格（用于调试）
        if tables_before_merge:
            result["tables_before_merge"] = tables_before_merge

        # 保存hints信息（用于调试）
        if hints_by_page:
            result["hints_by_page"] = hints_by_page

        # 保存AI行级别判断结果（用于调试）
        if ai_row_decisions:
            result["ai_row_decisions"] = ai_row_decisions

        return result

    def extract_all_paragraphs(self) -> Dict[str, Any]:
        """
        仅提取段落（带元数据和编号）

        Returns:
            包含段落数据和元数据的字典
        """
        # 获取表格bbox
        table_bboxes_per_page = self.table_extractor.get_table_bboxes_per_page()

        # 提取段落
        paragraphs_raw = self.paragraph_extractor.extract_paragraphs(table_bboxes_per_page)

        # 按页面和y坐标排序
        paragraphs_raw.sort(key=lambda x: (x["page"], x["y0"]))

        # 分配docN编号
        structured_paragraphs = []
        self.block_counter = 0

        for para in paragraphs_raw:
            self.block_counter += 1
            doc_id = f"doc{self.block_counter:03d}"

            structured_paragraphs.append({
                "type": "paragraph",
                "id": doc_id,
                "page": para["page"],
                "bbox": para["bbox"],
                "content": para["content"]
            })

        metadata = self._get_page_metadata()

        return {
            "pdf_file": str(self.pdf_path),
            "total_paragraphs": len(structured_paragraphs),
            "paragraphs": structured_paragraphs,
            "page_metadata": metadata
        }

    def save_to_json(self, output_dir: str = None, include_paragraphs: bool = True,
                     task_id: str = None, save_cells: bool = True) -> Dict[str, str]:
        """
        提取内容并保存到JSON文件



        Args:
            output_dir: 输出目录路径，如果为None则保存到PDF同目录
            include_paragraphs: 是否提取并保存段落
            task_id: 任务ID，用于生成文件名（如：taskId_table.json）
            save_cells: 是否同时保存单元格级别的结构化数据 (默认True)

        Returns:
            保存的文件路径字典
        """
        # 确定输出目录
        if output_dir is None:
            output_dir = self.pdf_path.parent
        else:
            output_dir = Path(output_dir)

        # 确保输出目录存在
        output_dir.mkdir(parents=True, exist_ok=True)

        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 确定文件名（带时间戳）
        if task_id:
            table_filename = f"{task_id}_table_{timestamp}.json"
            table_raw_filename = f"{task_id}_table_raw_{timestamp}.json"
            paragraph_filename = f"{task_id}_paragraph_{timestamp}.json"
            cells_filename = f"{task_id}_cells_{timestamp}.json"
        else:
            table_filename = f"table_{timestamp}.json"
            table_raw_filename = f"table_raw_{timestamp}.json"
            paragraph_filename = f"paragraph_{timestamp}.json"
            cells_filename = f"cells_{timestamp}.json"

        result_paths = {}

        # 提取并保存表格
        tables_result = self.extract_all_tables()
        tables = tables_result.get("tables", [])

        # ✨ 新增: 转换为单元格级别结构 (在写JSON前)
        cells_data = None
        if save_cells and tables:
            try:
                # 兼容两种运行方式：包导入和脚本直接运行
                try:
                    from .table_to_cells import TableToCellsConverter
                except ImportError:
                    from table_to_cells import TableToCellsConverter

                print(f"\n[单元格转换] 将表格转换为单元格结构...")
                converter = TableToCellsConverter()
                # 使用相同的时间戳构建 doc_id (确保一个批次使用同一个时间戳)
                base_doc_id = task_id if task_id else self.pdf_path.stem
                doc_id = f"{base_doc_id}_{timestamp}"
                cells = converter.convert_tables_to_cells(tables, doc_id)

                print(f"[单元格转换] ✓ 转换完成: {len(cells)} 个单元格")

                # 保存单元格 JSON
                cells_data = {
                    "doc_id": doc_id,
                    "total_cells": len(cells),
                    "cells": cells,
                    "schema": {
                        "fields": [
                            "doc_id", "table_id", "row_id", "col_id", "page",
                            "header_name", "canonical_header",
                            "cell_value_raw", "cell_value_norm",
                            "row_context", "num_value", "unit"
                        ]
                    }
                }

                cells_path = output_dir / cells_filename
                with open(cells_path, 'w', encoding='utf-8') as f:
                    json.dump(cells_data, f, ensure_ascii=False, indent=2)
                result_paths["cells"] = str(cells_path)
                print(f"[单元格转换] ✓ 已保存: {cells_path}")

                # ✨ 新增: 写入向量数据库
                try:
                    # 兼容两种运行方式：包导入和脚本直接运行
                    try:
                        from ..persistence import MilvusPersistence
                    except ImportError:
                        import sys
                        from pathlib import Path as ImportPath
                        project_root = ImportPath(__file__).resolve().parent.parent.parent.parent
                        if str(project_root) not in sys.path:
                            sys.path.insert(0, str(project_root))
                        from app.utils.persistence import MilvusPersistence

                    # 使用 MilvusPersistence 类进行持久化
                    with MilvusPersistence(
                        host="localhost",
                        port="19530",
                        collection_name="pdf",
                        embedding_model="BAAI/bge-m3",
                        vector_dim=1024,
                        device="auto"
                    ) as persistence:
                        persistence.save_cells(doc_id=doc_id, cells=cells, drop_old=False)

                except Exception as vec_error:
                    print(f"[向量库] ✗ 向量化写入失败: {vec_error}")
                    import traceback
                    traceback.print_exc()

            except Exception as e:
                print(f"[单元格转换] ✗ 转换失败: {e}")
                import traceback
                traceback.print_exc()

        # 保存完整结果（包含合并后的表格）
        table_path = output_dir / table_filename
        with open(table_path, 'w', encoding='utf-8') as f:
            json.dump(tables_result, f, ensure_ascii=False, indent=2)
        result_paths["tables"] = str(table_path)

        # 保存原始表格（table_raw.json，仅包含第一轮提取结果）
        if 'tables_first_round' in tables_result:
            raw_result = {
                "pdf_file": tables_result['pdf_file'],
                "total_tables": len(tables_result['tables_first_round']),
                "tables": tables_result['tables_first_round'],
                "page_metadata": tables_result['page_metadata']
            }

            # 添加hints信息（如果有）
            if 'hints_by_page' in tables_result:
                raw_result['hints_by_page'] = tables_result['hints_by_page']

            table_raw_path = output_dir / table_raw_filename
            with open(table_raw_path, 'w', encoding='utf-8') as f:
                json.dump(raw_result, f, ensure_ascii=False, indent=2)
            result_paths["tables_raw"] = str(table_raw_path)

        # 提取并保存段落（如果需要）
        if include_paragraphs:
            paragraphs_result = self.extract_all_paragraphs()
            paragraph_path = output_dir / paragraph_filename
            with open(paragraph_path, 'w', encoding='utf-8') as f:
                json.dump(paragraphs_result, f, ensure_ascii=False, indent=2)
            result_paths["paragraphs"] = str(paragraph_path)

        return result_paths

    def save_to_qdrant(self,
                       doc_id: str,
                       qdrant_url: str = "http://localhost:6333",
                       metadata: Dict[str, Any] = None,
                       embedding_fn=None) -> int:
        """
        提取内容并直接导入到 Qdrant 向量数据库（不写文件）

        Args:
            doc_id: 文档ID（如 "ORDOS-2025-0001"）
            qdrant_url: Qdrant 服务地址
            metadata: 额外元数据（region, agency, published_at_ts等）
            embedding_fn: 向量化函数（输入文本，返回向量）如果为None，使用占位向量

        Returns:
            成功导入的chunk数量
        """
        if not QDRANT_AVAILABLE:
            print("  [Qdrant] ❌ Qdrant 模块不可用，无法导入数据")
            return 0

        print(f"  [Qdrant] 步骤1: 初始化 Qdrant 客户端...")
        # 初始化 Qdrant 工具
        util = QdrantUtil(url=qdrant_url)

        # 确保集合存在
        print(f"  [Qdrant] 步骤1.1: 检查并初始化 tender_chunks 集合...")
        existing_collections = util.list_collections()
        if "tender_chunks" not in existing_collections:
            print(f"  [Qdrant]   集合不存在，正在创建...")
            success = util.init_tender_collection(vector_size=768)
            if not success:
                print(f"  [Qdrant]   ❌ 创建集合失败")
                return 0
            print(f"  [Qdrant]   ✅ 集合创建成功")
        else:
            print(f"  [Qdrant]   ✅ 集合已存在")

        print(f"  [Qdrant] 步骤2: 从内存提取表格...")
        # 1. 提取表格（内存）
        tables_result = self.extract_all_tables()
        tables = tables_result.get("tables", [])
        print(f"  [Qdrant]   提取到 {len(tables)} 个表格")

        print(f"  [Qdrant] 步骤3: 从内存提取段落...")
        # 2. 提取段落（内存）
        paragraphs_result = self.extract_all_paragraphs()
        paragraphs = paragraphs_result.get("paragraphs", [])
        print(f"  [Qdrant]   提取到 {len(paragraphs)} 个段落")

        print(f"  [Qdrant] 步骤4: 转换为 chunks 并批量导入...")
        # 3. 直接从内存转换为 chunks 并导入
        chunk_count = util.insert_tender_chunks_from_memory(
            doc_id=doc_id,
            tables=tables,
            paragraphs=paragraphs,
            embedding_util=embedding_fn,  # 注意：参数名是 embedding_util
            metadata=metadata
        )
        print(f"  [Qdrant] 步骤5: 导入完成，共 {chunk_count} 个 chunks")

        return chunk_count

    def _build_table_bboxes_map(self, tables):
        """
        从表格列表构建每页的bbox映射

        Args:
            tables: 表格列表

        Returns:
            {page_num: [bbox1, bbox2, ...]}
        """
        table_bboxes = {}
        for table in tables:
            page = table.get("page", 1)
            bbox = table.get("bbox")
            if bbox:
                if page not in table_bboxes:
                    table_bboxes[page] = []
                table_bboxes[page].append(tuple(bbox))
        return table_bboxes

    def _get_page_widths(self):
        """
        获取所有页面的宽度（用于跨页表格合并）

        Returns:
            {page_num: width} 字典
        """
        if self._page_widths is not None:
            return self._page_widths

        page_widths = {}
        doc = fitz.open(self.pdf_path)

        for page_num in range(len(doc)):
            page = doc[page_num]
            page_widths[page_num + 1] = page.rect.width

        doc.close()
        self._page_widths = page_widths
        return page_widths

    def _get_page_heights(self):
        """
        获取所有页面的高度（用于跨页表格合并）

        Returns:
            {page_num: height} 字典
        """
        if self._page_heights is not None:
            return self._page_heights

        page_heights = {}
        doc = fitz.open(self.pdf_path)

        for page_num in range(len(doc)):
            page = doc[page_num]
            page_heights[page_num + 1] = page.rect.height

        doc.close()
        self._page_heights = page_heights
        return page_heights

    def _get_page_drawings(self):
        """
        获取所有页面的drawings数据（用于跨页表格合并的边框检测）

        Returns:
            {page_num: drawings} 字典
        """
        if self._page_drawings is not None:
            return self._page_drawings

        page_drawings = {}
        doc = fitz.open(self.pdf_path)

        for page_num in range(len(doc)):
            page = doc[page_num]
            # 使用get_drawings()获取页面的所有矢量图形
            drawings = page.get_drawings()
            page_drawings[page_num + 1] = drawings

        doc.close()
        self._page_drawings = page_drawings
        return page_drawings

    def _get_page_metadata(self):
        """
        获取PDF页面元数据

        Returns:
            页面元数据列表
        """
        metadata = []
        doc = fitz.open(self.pdf_path)

        for page_num in range(len(doc)):
            page = doc[page_num]
            text_blocks = page.get_text("dict")

            metadata.append({
                "page": page_num + 1,
                "method": "pymupdf",
                "width": page.rect.width,
                "height": page.rect.height,
                "blocks_count": len(text_blocks.get("blocks", []))
            })

        doc.close()
        return metadata

    def _collect_hint_row_pairs(self, tables, hints_by_page):
        """
        收集所有有 hint 的跨页表格对的行数据（用于 AI 判断）

        Args:
            tables: 表格列表（重提取后的）
            hints_by_page: 续页 hint 信息

        Returns:
            行对列表，格式：[
                {
                    "prev_row": {"第0列": "...", "第1列": "...", ...},
                    "next_row": {"第0列": "...", "第1列": "...", ...},
                    "context": {
                        "prev_table_id": "temp_001",
                        "next_table_id": "temp_002",
                        "prev_table_uuid": "xxx-xxx-xxx",  # 表格UUID（用于AI匹配）
                        "next_table_uuid": "xxx-xxx-xxx",
                        "prev_row_id": "r007",  # 原始行ID（用于AI匹配）
                        "next_row_id": "r001",
                        "prev_page": 1,
                        "next_page": 2,
                        "hint_score": 0.95
                    }
                },
                ...
            ]
        """
        if not hints_by_page:
            return []

        row_pairs = []

        # 按页码分组表格
        tables_by_page = {}
        for table in tables:
            page = table.get('page', 1)
            if page not in tables_by_page:
                tables_by_page[page] = []
            tables_by_page[page].append(table)

        print(f"[AI判断] tables_by_page 的页码: {sorted(tables_by_page.keys())}")

        # 遍历有 hint 的页面
        for next_page, hint in hints_by_page.items():
            prev_page = next_page - 1
            print(f"[AI判断] 检查跨页: {prev_page} → {next_page}")

            if prev_page not in tables_by_page or next_page not in tables_by_page:
                continue

            prev_tables = tables_by_page[prev_page]
            next_tables = tables_by_page[next_page]

            # 获取上页最后一张表和下页第一张表
            if not prev_tables or not next_tables:
                continue

            prev_table = prev_tables[-1]  # 最后一张
            next_table = next_tables[0]   # 第一张

            # 获取上页最后一行和下页第一行
            prev_rows = prev_table.get('rows', [])
            next_rows = next_table.get('rows', [])

            if not prev_rows or not next_rows:
                continue

            prev_last_row = prev_rows[-1]
            next_first_row = next_rows[0]

            prev_cells = prev_last_row.get('cells', [])
            next_cells = next_first_row.get('cells', [])

            # 提取行数据（key-value 格式）
            prev_row_dict = {}
            next_row_dict = {}

            for i, cell in enumerate(prev_cells):
                col_name = f"第{i}列"
                prev_row_dict[col_name] = cell.get('content', '').strip()

            for i, cell in enumerate(next_cells):
                col_name = f"第{i}列"
                next_row_dict[col_name] = cell.get('content', '').strip()

            # 构建行对（包含完整的匹配信息）
            row_pairs.append({
                "prev_row": prev_row_dict,
                "next_row": next_row_dict,
                "context": {
                    "prev_table_id": prev_table.get('id'),
                    "next_table_id": next_table.get('id'),
                    "prev_table_uuid": prev_table.get('raw_uuid'),  # 表格UUID（用于AI匹配）
                    "next_table_uuid": next_table.get('raw_uuid'),
                    "prev_row_id": prev_last_row.get('raw_row_id'),  # 原始行ID（用于AI匹配）
                    "next_row_id": next_first_row.get('raw_row_id'),
                    "prev_page": prev_page,
                    "next_page": next_page,
                    "hint_score": hint.get('score', 0),
                    "hint_expected_cols": hint.get('expected_cols', 0),  # 期望列数
                    "hint_source_page": hint.get('source_page'),  # hint来源页
                    "hint_source_table_id": hint.get('source_table_id')  # hint来源表格ID
                }
            })

        return row_pairs

    def _build_layout_index(self, tables, paragraphs):
        """
        构建页面布局索引（用于跨页合并时检查正文隔断）

        将表格和段落按页码和Y坐标排序，记录每个内容块的位置和类型

        Args:
            tables: 表格列表
            paragraphs: 段落列表（原始格式，未编号）

        Returns:
            {page_num: [block1, block2, ...]} 每页的内容块列表
            block格式: {type: 'table'|'paragraph', bbox: [...], id: '...'}
        """
        layout_index = {}

        # 添加表格
        for table in tables:
            page = table.get('page', 1)
            bbox = table.get('bbox', [0, 0, 0, 0])

            if page not in layout_index:
                layout_index[page] = []

            layout_index[page].append({
                'type': 'table',
                'id': table.get('id'),
                'bbox': bbox,
                'y0': bbox[1],
                'y1': bbox[3]
            })

        # 添加段落
        for para in paragraphs:
            page = para.get('page', 1)
            bbox = para.get('bbox', [0, 0, 0, 0])
            content = para.get('content', '')

            if page not in layout_index:
                layout_index[page] = []

            layout_index[page].append({
                'type': 'paragraph',
                'bbox': bbox,
                'y0': bbox[1],
                'y1': bbox[3],
                'content_preview': content[:100] if content else ''
            })

        # 对每页的内容块按Y坐标排序
        for page in layout_index:
            layout_index[page].sort(key=lambda x: x['y0'])

        # Debug: 输出布局索引统计（仅在 verbose 模式下）
        if self.verbose:
            print(f"\n[布局索引] 构建完成:")
            for page_num in sorted(layout_index.keys()):
                blocks = layout_index[page_num]
                tables_count = sum(1 for b in blocks if b['type'] == 'table')
                paras_count = sum(1 for b in blocks if b['type'] == 'paragraph')
                print(f"  页{page_num}: {tables_count}个表格, {paras_count}个段落")

        return layout_index

    def _apply_tr_level_row_merge(
        self,
        tables: list,
        ai_row_decisions: list,
        row_pairs: list
    ) -> list:
        """
        根据 AI 判断结果执行 TR 级别的行合并（支持链式合并）

        逻辑：
        1. 构建合并关系图，识别连续的合并链
        2. 对每条链，将所有行合并到链头
        3. 标记链中其他行为待删除
        4. 最后统一删除所有待删除的行

        示例：
        - AI判断：(页4,r002)→(页5,r001)→(页6,r001)→(页7,r001) 都应合并
        - 识别为一条链：[(页4,r002), (页5,r001), (页6,r001), (页7,r001)]
        - 合并：将 页5,r001、页6,r001、页7,r001 的内容依次拼接到 页4,r002
        - 删除：页5,r001、页6,r001、页7,r001

        Args:
            tables: 表格列表
            ai_row_decisions: AI 判断结果列表
            row_pairs: 行对列表（包含 context）

        Returns:
            更新后的表格列表
        """
        # 构建 UUID 到表格的映射（快速查找）
        uuid_to_table = {}
        for table in tables:
            uuid = table.get('raw_uuid')
            if uuid:
                uuid_to_table[uuid] = table

        # 1. 构建合并关系图（只包含 should_merge=True 的边）
        merge_graph = {}  # {(uuid, row_id): (uuid, row_id)}
        row_to_context = {}  # 保存每个节点的上下文信息（用于日志）

        for decision, pair in zip(ai_row_decisions, row_pairs):
            if not decision.get('should_merge', False):
                continue

            ctx = pair.get('context', {})
            prev_key = (ctx.get('prev_table_uuid'), ctx.get('prev_row_id'))
            next_key = (ctx.get('next_table_uuid'), ctx.get('next_row_id'))

            merge_graph[prev_key] = next_key

            # 保存上下文信息
            if prev_key not in row_to_context:
                row_to_context[prev_key] = ctx
            if next_key not in row_to_context:
                row_to_context[next_key] = ctx

        # 2. 识别所有合并链
        chains = []
        visited = set()

        for start_key in merge_graph:
            if start_key in visited:
                continue

            # 从当前节点开始构建链
            chain = [start_key]
            visited.add(start_key)

            current = start_key
            while current in merge_graph:
                next_key = merge_graph[current]
                chain.append(next_key)
                visited.add(next_key)
                current = next_key

            # 只保留长度 >= 2 的链（至少有2个节点才需要合并）
            if len(chain) >= 2:
                chains.append(chain)

        print(f"  识别到 {len(chains)} 条合并链")

        # 3. 对每条链执行合并
        merge_count = 0
        skipped_count = 0
        rows_to_delete = []  # 记录待删除的行: [(table, row), ...]

        for chain_idx, chain in enumerate(chains, start=1):
            # 链头（合并目标）
            head_uuid, head_row_id = chain[0]
            head_table = uuid_to_table.get(head_uuid)

            if not head_table:
                print(f"  [链{chain_idx}] 跳过: 找不到表格 {head_uuid[:8]}")
                skipped_count += len(chain) - 1
                continue

            head_row = None
            for row in head_table.get('rows', []):
                if row.get('raw_row_id') == head_row_id:
                    head_row = row
                    break

            if not head_row:
                print(f"  [链{chain_idx}] 跳过: 找不到行 {head_row_id}")
                skipped_count += len(chain) - 1
                continue

            # 获取链头上下文（用于日志）
            head_ctx = row_to_context.get(chain[0], {})
            chain_pages = [head_ctx.get('prev_page', '?')]

            # 依次合并链中的后续行
            success_merges = 0
            for i in range(1, len(chain)):
                tail_uuid, tail_row_id = chain[i]
                tail_table = uuid_to_table.get(tail_uuid)

                if not tail_table:
                    print(f"  [链{chain_idx}] 跳过节点{i}: 找不到表格 {tail_uuid[:8]}")
                    skipped_count += 1
                    continue

                tail_row = None
                for row in tail_table.get('rows', []):
                    if row.get('raw_row_id') == tail_row_id:
                        tail_row = row
                        break

                if not tail_row:
                    print(f"  [链{chain_idx}] 跳过节点{i}: 找不到行 {tail_row_id}")
                    skipped_count += 1
                    continue

                # 执行合并
                try:
                    self._merge_two_rows(head_row, tail_row)
                    rows_to_delete.append((tail_table, tail_row))
                    success_merges += 1

                    # 记录页码
                    tail_ctx = row_to_context.get(chain[i], {})
                    chain_pages.append(tail_ctx.get('next_page', '?'))

                except Exception as e:
                    print(f"  [链{chain_idx}] 合并节点{i}失败: {e}")
                    skipped_count += 1

            if success_merges > 0:
                merge_count += success_merges
                pages_str = '→'.join(str(p) for p in chain_pages)
                print(f"  [链{chain_idx}] 成功: {len(chain)}个节点合并为1行 (页{pages_str})")

        # 4. 统一删除所有待删除的行
        for table, row in rows_to_delete:
            rows_list = table.get('rows', [])
            if row in rows_list:
                rows_list.remove(row)

        print(f"[TR级别行合并] 成功合并 {merge_count} 个行，跳过 {skipped_count} 个")
        print(f"[TR级别行合并] 删除了 {len(rows_to_delete)} 个行")

        return tables

    def _merge_two_rows(self, prev_row: dict, next_row: dict):
        """
        合并两行的内容（单元格级别拼接）

        Args:
            prev_row: 上页最后一行
            next_row: 下页第一行
        """
        prev_cells = prev_row.get('cells', [])
        next_cells = next_row.get('cells', [])

        # 按列对齐合并
        for i in range(min(len(prev_cells), len(next_cells))):
            prev_cell = prev_cells[i]
            next_cell = next_cells[i]

            # 拼接 content
            prev_content = prev_cell.get('content', '').strip()
            next_content = next_cell.get('content', '').strip()

            if prev_content and next_content:
                # 如果两者都有内容，拼接
                merged_content = prev_content + next_content
            elif next_content:
                # 只有下页有内容
                merged_content = next_content
            else:
                # 只有上页有内容或都为空
                merged_content = prev_content

            prev_cell['content'] = merged_content

            # TODO: 处理 bbox 合并
            # 目前保留上页的 bbox，后续需要计算合并后的完整 bbox
            # 这需要考虑跨页的情况，可能需要记录多个 bbox 片段

    def _init_vectorization(self, qdrant_url: str, embedding_model: str, device: str):
        """
        初始化向量化组件

        Args:
            qdrant_url: Qdrant 服务器地址
            embedding_model: 向量化模型名称
            device: 计算设备 ('auto', 'cuda', 'cpu')
        """
        try:
            from app.utils.db.qdrant import (
                QdrantUtil,
                get_embedding_util,
                TenderIndexer,
                TenderSearcher
            )

            print(f"[向量化] 正在初始化...")

            # 1. 初始化 Qdrant
            print(f"[向量化]   连接 Qdrant: {qdrant_url}")
            qdrant_util = QdrantUtil(url=qdrant_url)

            # 2. 初始化向量化模型
            if device == "auto":
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"

            print(f"[向量化]   加载模型: {embedding_model}")
            print(f"[向量化]   设备: {device}")
            embedding_util = get_embedding_util(
                model_name=embedding_model,
                use_fp16=True,
                device=device
            )

            # 3. 初始化索引器和搜索器
            self.indexer = TenderIndexer(qdrant_util, embedding_util)
            self.searcher = TenderSearcher(qdrant_util, embedding_util)

            print(f"[向量化] ✓ 初始化完成")

        except Exception as e:
            print(f"[向量化] ✗ 初始化失败: {e}")
            self.indexer = None
            self.searcher = None

    def extract_and_index(self,
                          doc_id: str,
                          metadata: Optional[Dict[str, Any]] = None,
                          save_json: bool = True,
                          output_dir: str = None) -> Dict[str, Any]:
        """
        提取内容并索引到向量库（一步完成）

        Args:
            doc_id: 文档ID (如 "ORDOS-2025-0001")
            metadata: 元数据 (region, agency, published_at_ts等)
            save_json: 是否同时保存JSON文件 (默认True)
            output_dir: JSON输出目录 (如果save_json=True)

        Returns:
            结果字典，包含:
            - tables_count: 表格数量
            - paragraphs_count: 段落数量
            - chunks_count: 索引的chunk数量 (如果启用了向量化)
            - json_paths: JSON文件路径 (如果save_json=True)

        示例:
            extractor = PDFContentExtractor(
                pdf_path="test.pdf",
                enable_vectorization=True,
                device="cuda"
            )

            result = extractor.extract_and_index(
                doc_id="ORDOS-2025-0001",
                metadata={"region": "内蒙古", "agency": "鄂尔多斯市政府"},
                save_json=True
            )

            print(f"索引了 {result['chunks_count']} 个 chunks")
        """
        print(f"\n{'='*80}")
        print(f"提取并索引文档: {doc_id}")
        print(f"{'='*80}\n")

        result = {}

        # 1. 提取表格
        print(f"[1/3] 提取表格...")
        tables_result = self.extract_all_tables()
        tables = tables_result.get("tables", [])
        print(f"[1/3]   ✓ 提取了 {len(tables)} 个表格")
        result["tables_count"] = len(tables)

        # 2. 提取段落
        print(f"\n[2/3] 提取段落...")
        paragraphs_result = self.extract_all_paragraphs()
        paragraphs = paragraphs_result.get("paragraphs", [])
        print(f"[2/3]   ✓ 提取了 {len(paragraphs)} 个段落")
        result["paragraphs_count"] = len(paragraphs)

        # 3. 保存JSON (如果需要)
        if save_json:
            print(f"\n[3/3] 保存JSON文件...")
            json_paths = self.save_to_json(output_dir=output_dir, task_id=doc_id)
            print(f"[3/3]   ✓ 已保存")
            result["json_paths"] = json_paths

        # 4. 索引到向量库 (如果启用)
        if self.enable_vectorization and self.indexer:
            print(f"\n[向量化] 索引到向量库...")
            chunk_count = self.indexer.index_document(
                doc_id=doc_id,
                tables=tables,
                paragraphs=paragraphs,
                metadata=metadata
            )
            result["chunks_count"] = chunk_count
            print(f"\n[向量化] ✓ 成功索引 {chunk_count} 个 chunks")
        else:
            result["chunks_count"] = 0

        print(f"\n{'='*80}")
        print(f"完成!")
        print(f"{'='*80}\n")

        return result

    def _clean_text(self, text: str) -> str:
        """
        清理文本（移除换行符、占位符等）

        复用自 HeaderAnalyzer._clean_text

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        if not text:
            return ""

        # 移除换行符
        text = text.replace('\n', '').replace('\r', '').strip()

        # 移除占位符
        if text in ['/', '—', '－', '·', '…']:
            return ""

        return text

    def _clean_table_content(self, table: Dict[str, Any]) -> None:
        """
        清理表格中所有单元格的文本内容（原地修改）

        Args:
            table: 表格对象
        """
        for row in table.get('rows', []):
            for cell in row.get('cells', []):
                if 'content' in cell:
                    cell['content'] = self._clean_text(cell['content'])

        # 递归清理嵌套表格
        for row in table.get('rows', []):
            for cell in row.get('cells', []):
                if 'nested_tables' in cell:
                    for nested_table in cell['nested_tables']:
                        self._clean_table_content(nested_table)


# 便捷函数
def extract_pdf_content(pdf_path: str, output_path: str = None, include_paragraphs: bool = True) -> Dict[str, str]:
    """
    提取PDF内容并保存到JSON

    Args:
        pdf_path: PDF文件路径
        output_path: 输出目录路径
        include_paragraphs: 是否包含段落

    Returns:
        保存的文件路径字典
    """
    extractor = PDFContentExtractor(pdf_path)
    return extractor.save_to_json(output_path, include_paragraphs=include_paragraphs)


def extract_pdf_tables(pdf_path: str, output_path: str = None) -> Dict[str, str]:
    """
    仅提取PDF表格并保存到JSON

    Args:
        pdf_path: PDF文件路径
        output_path: 输出目录路径

    Returns:
        保存的文件路径字典
    """
    extractor = PDFContentExtractor(pdf_path)
    return extractor.save_to_json(output_path, include_paragraphs=False)


# 主测试函数
def main():
    """

    主测试方法
    """
    # 从taskId构建路径
    task_id = "国土空间规划实施监测网络建设项目"
    base_dir = Path(r""
                    r"E:\programFile\AIProgram\docxServer\pdf\task\国土空间规划实施监测网络建设项目")
    pdf_path = base_dir / f"{task_id}.pdf"

    print(f"开始测试PDF内容提取...")
    print(f"Task ID: {task_id}")




    print(f"PDF文件: {pdf_path}")

    try:
        # 使用跨页合并（带正文隔断检查）- 关闭详细日志
        extractor = PDFContentExtractor(str(pdf_path), enable_cross_page_merge=True, verbose=False)

        # 保存结果，使用task_id作为文件名前缀
        print(f"\n正在提取 PDF 内容...")
        output_paths = extractor.save_to_json(include_paragraphs=True, task_id=task_id)
        print(f"✓ PDF 提取完成")

        print(f"\n提取成功!")
        print(f"输出文件:")

        # 显示表格摘要
        if "tables" in output_paths:
            print(f"  - 表格文件: {output_paths['tables']}")
            with open(output_paths['tables'], 'r', encoding='utf-8') as f:
                tables_result = json.load(f)
            print(f"    共提取 {tables_result['total_tables']} 个表格")
            print(f"\n  [表格详情]")
            for idx, table in enumerate(tables_result['tables'], start=1):
                rows_count = len(table.get('rows', []))
                cols_count = len(table.get('columns', []))
                bbox = table.get('bbox', [])
                is_merged = 'merged_from' in table

                print(f"    [{idx}] {table['id']}: 页码 {table['page']}, {rows_count}行 × {cols_count}列")
                print(f"         bbox: [{bbox[0]:.2f}, {bbox[1]:.2f}, {bbox[2]:.2f}, {bbox[3]:.2f}]")

                if is_merged:
                    merged_from = table.get('merged_from', [])
                    page_end = table.get('page_end', table['page'])
                    print(f"         [跨页合并] 页{table['page']}~{page_end}, 合并自: {merged_from}")

                # 显示前3行的第一个单元格内容预览
                for row_idx, row in enumerate(table.get('rows', [])[:3], start=1):
                    cells = row.get('cells', [])
                    if cells:
                        first_cell = cells[0]
                        content = first_cell.get('content', '')[:50]
                        print(f"         行{row_idx}: {content}...")
                    else:
                        print(f"         行{row_idx}: (无单元格)")

                print()

                # 显示嵌套表格信息
                for row in table.get('rows', []):
                    for cell in row.get('cells', []):
                        if 'nested_tables' in cell:
                            for nested in cell['nested_tables']:
                                nested_rows = len(nested.get('rows', []))
                                nested_cols = len(nested.get('columns', []))
                                print(f"        └─ 嵌套表格: {nested_rows}行 × {nested_cols}列")

        # 显示段落摘要
        if "paragraphs" in output_paths:
            print(f"\n  - 段落文件: {output_paths['paragraphs']}")
            with open(output_paths['paragraphs'], 'r', encoding='utf-8') as f:
                paragraphs_result = json.load(f)
            print(f"    共提取 {paragraphs_result['total_paragraphs']} 个段落")
            for para in paragraphs_result['paragraphs'][:5]:
                content_preview = para.get('content', '')[:50]
                print(f"      {para['id']}: 页码 {para['page']}, 内容: {content_preview}...")
            if paragraphs_result['total_paragraphs'] > 5:
                print(f"      ... 还有 {paragraphs_result['total_paragraphs'] - 5} 个段落")

    except FileNotFoundError as e:
        print(f"\n错误: 文件未找到: {e}")
    except Exception as e:
        print(f"\n错误: 提取失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()