"""
招标文档索引器 - 负责将提取的内容索引到向量数据库

职责:
1. 将 tables + paragraphs 转换为 chunks
2. 批量向量化文本
3. 组装 Qdrant Points
4. 批量写入向量数据库
"""
from typing import List, Dict, Any, Optional


class TenderIndexer:
    """招标文档索引器"""

    def __init__(self, qdrant_util, embedding_util):
        """
        初始化索引器

        Args:
            qdrant_util: QdrantUtil 实例
            embedding_util: EmbeddingUtil 实例
        """
        self.qdrant_util = qdrant_util
        self.embedding_util = embedding_util

    def index_document(self,
                       doc_id: str,
                       tables: List[Dict[str, Any]],
                       paragraphs: List[Dict[str, Any]],
                       metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        索引一个文档的所有内容到向量数据库

        Args:
            doc_id: 文档ID (如 "ORDOS-2025-0001")
            tables: 表格列表 (来自 extract_all_tables())
            paragraphs: 段落列表 (来自 extract_all_paragraphs())
            metadata: 额外元数据 (region, agency, published_at_ts等)

        Returns:
            成功插入的 chunk 数量
        """
        print(f"[索引器] 开始索引文档: {doc_id}")

        # 默认元数据
        default_metadata = {
            "region": metadata.get("region", "unknown") if metadata else "unknown",
            "agency": metadata.get("agency", "unknown") if metadata else "unknown",
            "published_at_ts": metadata.get("published_at_ts", 0) if metadata else 0,
        }

        # Step 1: 收集文本
        print(f"[索引器] [1/4] 收集文本...")
        texts, chunk_infos = self._collect_texts(doc_id, tables, paragraphs, default_metadata)
        print(f"[索引器] [1/4]   OK 收集了 {len(texts)} 个文本")

        # Step 2: 批量向量化
        print(f"[索引器] [2/4] 批量向量化...")
        vectors = self._vectorize_batch(texts)
        print(f"[索引器] [2/4]   OK 向量化完成")

        # 显示缓存统计
        stats = self.embedding_util.get_cache_stats()
        print(f"[索引器] [2/4]   缓存命中率: {stats['hit_rate']}")

        # Step 3: 组装 Points
        print(f"[索引器] [3/4] 组装 Points...")
        points = self._build_points(chunk_infos, vectors)
        print(f"[索引器] [3/4]   OK 组装了 {len(points)} 个 points")

        # Step 4: 批量插入
        print(f"[索引器] [4/4] 批量插入到 Qdrant...")
        if points:
            success = self.qdrant_util.insert_points_batch("tender_chunks", points)
            if success:
                print(f"[索引器] [4/4]   OK 插入成功: {len(points)} 个 chunks")
                return len(points)
            else:
                print(f"[索引器] [4/4]   FAILED 插入失败")
                return 0
        else:
            print(f"[索引器] [4/4]   ⚠️ 没有数据，跳过插入")
            return 0

    def _collect_texts(self,
                       doc_id: str,
                       tables: List[Dict[str, Any]],
                       paragraphs: List[Dict[str, Any]],
                       default_metadata: Dict[str, Any]) -> tuple:
        """
        收集需要向量化的文本和元信息

        Returns:
            (texts_to_embed, chunk_infos)
        """
        texts_to_embed = []
        chunk_infos = []

        # 1. 收集段落文本
        for idx, para in enumerate(paragraphs):
            content = para.get("content", "").strip()
            if not content:
                continue

            page = para.get("page", 1)
            chunk_id_str = self.qdrant_util._generate_chunk_id(doc_id, "paragraph", page, idx)
            chunk_id = self.qdrant_util._hash_to_int(chunk_id_str)

            payload = {
                "doc_id": doc_id,
                "chunk_type": "paragraph",
                "page": page,
                "content": content,
                "bbox": para.get("bbox"),
                "para_id": para.get("id"),
                **default_metadata
            }

            texts_to_embed.append(content)
            chunk_infos.append({
                "id": chunk_id,
                "payload": payload
            })

        paragraph_count = len(texts_to_embed)
        print(f"[索引器]   段落: {paragraph_count} 个")

        # 2. 收集表格行文本
        for table_idx, table in enumerate(tables):
            table_id = table.get("id", f"t{table_idx+1:03d}")
            page = table.get("page", 1)
            columns = table.get("columns", [])

            for row_idx, row in enumerate(table.get("rows", [])):
                cells = row.get("cells", [])

                # 格式化行内容: "col1: val1 | col2: val2 | ..."
                row_parts = []
                for cell in cells:
                    col_id = cell.get("col_id", "")
                    content = cell.get("content", "").strip()

                    # 找到对应的列名
                    col_name = "unknown"
                    for col in columns:
                        if col.get("id") == col_id:
                            col_name = col.get("name", col_id)
                            break

                    row_parts.append(f"{col_name}: {content}")

                row_content = " | ".join(row_parts)
                if not row_content.strip():
                    continue

                chunk_id_str = self.qdrant_util._generate_chunk_id(
                    doc_id, "table_row", page, table_idx * 1000 + row_idx
                )
                chunk_id = self.qdrant_util._hash_to_int(chunk_id_str)

                payload = {
                    "doc_id": doc_id,
                    "chunk_type": "table_row",
                    "page": page,
                    "content": row_content,
                    "table_id": table_id,
                    "row_id": row.get("id"),
                    "table_idx": table_idx,
                    "row_idx": row_idx,
                    **default_metadata
                }

                texts_to_embed.append(row_content)
                chunk_infos.append({
                    "id": chunk_id,
                    "payload": payload
                })

        table_row_count = len(texts_to_embed) - paragraph_count
        print(f"[索引器]   表格行: {table_row_count} 个")

        return texts_to_embed, chunk_infos

    def _vectorize_batch(self, texts: List[str]) -> list:
        """
        批量向量化文本

        Args:
            texts: 文本列表

        Returns:
            [(dense_vector, sparse_vector, content_hash), ...]
        """
        return self.embedding_util.encode_batch(texts, use_cache=True)

    def _build_points(self, chunk_infos: List[Dict], vectors: list) -> list:
        """
        组装 Qdrant Points

        Args:
            chunk_infos: chunk 元信息列表
            vectors: 向量列表

        Returns:
            points 列表
        """
        points = []
        for i, chunk_info in enumerate(chunk_infos):
            dense_vec, sparse_vec, content_hash = vectors[i]

            # 添加 content_hash 到 payload
            chunk_info["payload"]["content_hash"] = content_hash

            points.append({
                "id": chunk_info["id"],
                "vector": {
                    "dense": dense_vec,
                    "sparse": sparse_vec
                },
                "payload": chunk_info["payload"]
            })

        return points