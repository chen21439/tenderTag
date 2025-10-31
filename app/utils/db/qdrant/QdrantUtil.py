"""
Qdrant 向量数据库工具类

## MySQL vs Qdrant 概念对应关系

| MySQL | Qdrant | 说明 |
|-------|--------|------|
| Database | - | Qdrant 单实例管理所有集合 |
| Table | Collection | 集合对应表 |
| Row | Point | 点对应行 |
| Column | Payload | 负载对应列 |
| Primary Key | Point ID | 点ID对应主键 |
| Index | Vector Index | 向量索引 |

## 使用示例

```python
from app.utils.db.qdrant import QdrantUtil

# 初始化
util = QdrantUtil(url="http://localhost:6333")

# 创建集合（相当于创建表）
util.create_collection("my_collection", vector_size=128)

# 插入数据（相当于INSERT）
util.insert_point(
    collection_name="my_collection",
    point_id=1,
    vector=[0.1] * 128,
    payload={"name": "张三", "age": 25}
)

# 读取数据（相当于SELECT）
point = util.get_point("my_collection", point_id=1)
print(point)
```
"""
from typing import List, Dict, Any, Optional
import hashlib
import json
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    PayloadSchemaType,
    SparseVectorParams,
    SparseIndexParams
)


class QdrantUtil:
    """Qdrant 向量数据库工具类"""

    def __init__(self, url: str = "http://localhost:6333", api_key: Optional[str] = None):
        """
        初始化 Qdrant 客户端

        Args:
            url: Qdrant 服务地址（默认 http://localhost:6333）
            api_key: API 密钥（可选，用于云服务）
        """
        self.client = QdrantClient(url=url, api_key=api_key)
        print(f"[Qdrant] 已连接到: {url}")

    def create_collection(self,
                          collection_name: str,
                          vector_size: int,
                          distance: Distance = Distance.COSINE) -> bool:
        """
        创建集合（相当于 MySQL 的 CREATE TABLE）

        Args:
            collection_name: 集合名称（相当于表名）
            vector_size: 向量维度
            distance: 距离度量方式
                - Distance.COSINE: 余弦相似度（默认，适合文本）
                - Distance.DOT: 点积（适合归一化向量）
                - Distance.EUCLID: 欧几里得距离

        Returns:
            是否创建成功
        """
        try:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=distance),
            )
            print(f"[Qdrant] 集合 '{collection_name}' 创建成功 (向量维度: {vector_size})")
            return True
        except Exception as e:
            print(f"[Qdrant] 创建集合失败: {e}")
            return False

    def insert_point(self,
                     collection_name: str,
                     point_id: int,
                     vector: List[float],
                     payload: Optional[Dict[str, Any]] = None) -> bool:
        """
        插入单条数据（相当于 MySQL 的 INSERT）

        Args:
            collection_name: 集合名称
            point_id: 点ID（相当于主键）
            vector: 向量数据
            payload: 附加数据（相当于其他列）

        Returns:
            是否插入成功

        示例:
            util.insert_point(
                collection_name="users",
                point_id=1,
                vector=[0.1, 0.2, 0.3, 0.4],
                payload={"name": "张三", "age": 25, "city": "北京"}
            )
        """
        try:
            point = PointStruct(
                id=point_id,
                vector=vector,
                payload=payload or {}
            )
            self.client.upsert(
                collection_name=collection_name,
                points=[point]
            )
            print(f"[Qdrant] 插入数据成功: ID={point_id}, Payload={payload}")
            return True
        except Exception as e:
            print(f"[Qdrant] 插入数据失败: {e}")
            return False

    def insert_points_batch(self,
                            collection_name: str,
                            points: List[Dict[str, Any]]) -> bool:
        """
        批量插入数据（相当于 MySQL 的 INSERT ... VALUES (...), (...), ...）

        Args:
            collection_name: 集合名称
            points: 点列表，格式：[
                {"id": 1, "vector": [...], "payload": {...}},
                {"id": 2, "vector": [...], "payload": {...}}
            ]

        Returns:
            是否插入成功
        """
        try:
            print(f"      [批量插入] 正在转换 {len(points)} 个 chunks 为 PointStruct...")
            point_structs = [
                PointStruct(
                    id=p["id"],
                    vector=p["vector"],
                    payload=p.get("payload", {})
                )
                for p in points
            ]
            print(f"      [批量插入] 正在调用 Qdrant upsert() 方法...")
            self.client.upsert(
                collection_name=collection_name,
                points=point_structs
            )
            print(f"      [批量插入] ✅ 批量插入 {len(points)} 条数据成功到 {collection_name}")
            return True
        except Exception as e:
            print(f"      [批量插入] ❌ 批量插入失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_point(self, collection_name: str, point_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID读取数据（相当于 MySQL 的 SELECT * FROM table WHERE id = ?）

        Args:
            collection_name: 集合名称
            point_id: 点ID

        Returns:
            点数据（包含 id, vector, payload），如果不存在返回 None
        """
        try:
            points = self.client.retrieve(
                collection_name=collection_name,
                ids=[point_id]
            )
            if points:
                point = points[0]
                result = {
                    "id": point.id,
                    "vector": point.vector,
                    "payload": point.payload
                }
                print(f"[Qdrant] 读取数据成功: {result}")
                return result
            else:
                print(f"[Qdrant] 未找到 ID={point_id} 的数据")
                return None
        except Exception as e:
            print(f"[Qdrant] 读取数据失败: {e}")
            return None

    def search_similar(self,
                       collection_name: str,
                       query_vector: List[float],
                       limit: int = 10) -> List[Dict[str, Any]]:
        """
        向量相似度搜索（Qdrant 的核心功能，MySQL 无直接对应）

        Args:
            collection_name: 集合名称
            query_vector: 查询向量
            limit: 返回结果数量

        Returns:
            相似的点列表，按相似度降序排列
        """
        try:
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit
            )
            output = []
            for result in results:
                output.append({
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload
                })
            print(f"[Qdrant] 相似度搜索完成，返回 {len(output)} 条结果")
            return output
        except Exception as e:
            print(f"[Qdrant] 相似度搜索失败: {e}")
            return []

    def delete_point(self, collection_name: str, point_id: int) -> bool:
        """
        删除数据（相当于 MySQL 的 DELETE FROM table WHERE id = ?）

        Args:
            collection_name: 集合名称
            point_id: 点ID

        Returns:
            是否删除成功
        """
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=[point_id]
            )
            print(f"[Qdrant] 删除数据成功: ID={point_id}")
            return True
        except Exception as e:
            print(f"[Qdrant] 删除数据失败: {e}")
            return False

    def list_collections(self) -> List[str]:
        """
        列出所有集合（相当于 MySQL 的 SHOW TABLES）

        Returns:
            集合名称列表
        """
        try:
            collections = self.client.get_collections()
            names = [col.name for col in collections.collections]
            print(f"[Qdrant] 共有 {len(names)} 个集合: {names}")
            return names
        except Exception as e:
            print(f"[Qdrant] 列出集合失败: {e}")
            return []

    def delete_collection(self, collection_name: str) -> bool:
        """
        删除集合（相当于 MySQL 的 DROP TABLE）

        Args:
            collection_name: 集合名称

        Returns:
            是否删除成功
        """
        try:
            self.client.delete_collection(collection_name=collection_name)
            print(f"[Qdrant] 集合 '{collection_name}' 删除成功")
            return True
        except Exception as e:
            print(f"[Qdrant] 删除集合失败: {e}")
            return False

    # ==================== 招标文件专用方法 ====================

    def init_tender_collection(self, use_hybrid: bool = True) -> bool:
        """
        初始化招标文件集合（tender_chunks）

        Args:
            use_hybrid: 是否使用混合向量（稠密+稀疏，默认True，适配 bge-m3）
                       False 则只使用稠密向量（适配 bge-base-zh 等）

        Returns:
            是否初始化成功
        """
        collection_name = "tender_chunks"

        try:
            if use_hybrid:
                # 混合向量配置（稠密 1024维 + 稀疏）
                print(f"[Qdrant] 创建混合向量集合（稠密 1024维 + 稀疏）...")
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config={
                        "dense": VectorParams(size=1024, distance=Distance.COSINE)
                    },
                    sparse_vectors_config={
                        "sparse": SparseVectorParams(
                            index=SparseIndexParams()
                        )
                    }
                )
            else:
                # 只使用稠密向量
                print(f"[Qdrant] 创建稠密向量集合（768维）...")
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=768, distance=Distance.COSINE)
                )

            print(f"[Qdrant] 集合 '{collection_name}' 创建成功")

        except Exception as e:
            print(f"[Qdrant] 创建集合失败: {e}")
            return False

        # 2. 创建payload索引（加速过滤查询）
        try:
            index_fields = [
                ("doc_id", PayloadSchemaType.KEYWORD),
                ("chunk_type", PayloadSchemaType.KEYWORD),
                ("region", PayloadSchemaType.KEYWORD),
                ("agency", PayloadSchemaType.KEYWORD),
                ("published_at_ts", PayloadSchemaType.INTEGER),
            ]

            for field_name, schema_type in index_fields:
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name=field_name,
                    field_schema=schema_type
                )
                print(f"[Qdrant] 创建索引成功: {field_name} ({schema_type})")

            return True
        except Exception as e:
            print(f"[Qdrant] 创建索引失败: {e}")
            return False

    def _generate_chunk_id(self, doc_id: str, chunk_type: str, page: int, local_idx: int = 0) -> str:
        """
        生成chunk的唯一ID

        格式: {doc_id}#{chunk_type}#p{page}#{local_idx}
        例如: ORDOS-2025-0001#para#p12#0

        Args:
            doc_id: 文档ID
            chunk_type: 块类型（paragraph/table_row/table_cell）
            page: 页码
            local_idx: 页内索引

        Returns:
            唯一ID字符串
        """
        return f"{doc_id}#{chunk_type}#p{page}#{local_idx}"

    def _hash_to_int(self, text: str) -> int:
        """
        将字符串ID转换为整数ID（Qdrant需要）

        Args:
            text: 字符串ID

        Returns:
            整数ID
        """
        return int(hashlib.md5(text.encode()).hexdigest()[:16], 16)

    def insert_tender_chunks_from_memory(self,
                                        doc_id: str,
                                        tables: List[Dict[str, Any]],
                                        paragraphs: List[Dict[str, Any]],
                                        embedding_util=None,
                                        metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        从内存中的表格和段落数据导入到 tender_chunks（不读文件）

        Args:
            doc_id: 文档ID（如 "ORDOS-2025-0001"）
            tables: 表格列表（来自 extract_all_tables()）
            paragraphs: 段落列表（来自 extract_all_paragraphs()）
            embedding_util: 向量化工具（EmbeddingUtil实例）
                           如果为None，使用占位向量（全0）
            metadata: 额外元数据（region, agency, published_at_ts等）

        Returns:
            成功插入的chunk数量
        """
        chunks = []

        # 默认元数据
        default_metadata = {
            "region": metadata.get("region", "unknown") if metadata else "unknown",
            "agency": metadata.get("agency", "unknown") if metadata else "unknown",
            "published_at_ts": metadata.get("published_at_ts", 0) if metadata else 0,
        }

        # 收集所有需要向量化的文本
        texts_to_embed = []
        chunk_metadata_list = []

        print(f"    [内存→Chunks] 开始收集 {len(paragraphs)} 个段落...")
        # 1. 收集段落文本
        for idx, para in enumerate(paragraphs):
            content = para.get("content", "").strip()
            if not content:
                continue

            page = para.get("page", 1)
            chunk_id_str = self._generate_chunk_id(doc_id, "paragraph", page, idx)
            chunk_id = self._hash_to_int(chunk_id_str)

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
            chunk_metadata_list.append({
                "id": chunk_id,
                "payload": payload
            })

        print(f"    [内存→Chunks] 段落收集完成: {len(texts_to_embed)} 个有效段落")

        # 2. 处理表格（按行粒度存储）
        paragraph_count = len(chunks)  # 记录段落数量

        print(f"    [内存→Chunks] 开始处理 {len(tables)} 个表格...")
        for table_idx, table in enumerate(tables):
            table_id = table.get("id", f"t{table_idx+1:03d}")
            page = table.get("page", 1)
            columns = table.get("columns", [])

            for row_idx, row in enumerate(table.get("rows", [])):
                cells = row.get("cells", [])

                # 方案1: 每行一个chunk，内容为 "col1: val1 | col2: val2 | ..."
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

                chunk_id_str = self._generate_chunk_id(doc_id, "table_row", page,
                                                       table_idx * 1000 + row_idx)
                chunk_id = self._hash_to_int(chunk_id_str)

                # 生成向量
                vector = embedding_fn(row_content) if embedding_fn else [0.0] * 768

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

                chunks.append({
                    "id": chunk_id,
                    "vector": vector,
                    "payload": payload
                })

        table_row_count = len(chunks) - paragraph_count
        print(f"    [内存→Chunks] 表格处理完成: {table_row_count} 个表格行")
        print(f"    [Chunks→Qdrant] 总计生成 {len(chunks)} 个chunks ({paragraph_count}段落 + {table_row_count}表格行)")

        # 3. 批量插入
        if chunks:
            print(f"    [Chunks→Qdrant] 开始批量插入到 tender_chunks 集合...")
            print(f"    [Chunks→Qdrant]   Collection: tender_chunks")
            print(f"    [Chunks→Qdrant]   Chunks 数量: {len(chunks)}")
            print(f"    [Chunks→Qdrant]   向量维度: {len(chunks[0]['vector']) if chunks else 0}")

            success = self.insert_points_batch("tender_chunks", chunks)

            if success:
                print(f"    [Chunks→Qdrant] ✅ 批量插入成功!")
                return len(chunks)
            else:
                print(f"    [Chunks→Qdrant] ❌ 批量插入失败!")
                return 0
        else:
            print(f"    [Chunks→Qdrant] ⚠️  没有生成任何 chunks，跳过插入")
            return 0

    def insert_tender_chunks_from_json(self,
                                       doc_id: str,
                                       table_json_path: str,
                                       paragraph_json_path: str,
                                       embedding_fn=None,
                                       metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        从 table.json 和 paragraph.json 导入招标文件数据到 tender_chunks

        Args:
            doc_id: 文档ID（如 "ORDOS-2025-0001"）
            table_json_path: table.json 文件路径
            paragraph_json_path: paragraph.json 文件路径
            embedding_fn: 向量化函数（输入文本，返回向量）如果为None，使用占位向量
            metadata: 额外元数据（region, agency, published_at_ts等）

        Returns:
            成功插入的chunk数量
        """
        chunks = []

        # 默认元数据
        default_metadata = {
            "region": metadata.get("region", "unknown") if metadata else "unknown",
            "agency": metadata.get("agency", "unknown") if metadata else "unknown",
            "published_at_ts": metadata.get("published_at_ts", 0) if metadata else 0,
        }

        # 1. 处理 paragraph.json
        try:
            with open(paragraph_json_path, 'r', encoding='utf-8') as f:
                para_data = json.load(f)

            for idx, para in enumerate(para_data.get("paragraphs", [])):
                content = para.get("content", "").strip()
                if not content:
                    continue

                page = para.get("page", 1)
                chunk_id_str = self._generate_chunk_id(doc_id, "paragraph", page, idx)
                chunk_id = self._hash_to_int(chunk_id_str)

                # 生成向量
                vector = embedding_fn(content) if embedding_fn else [0.0] * 768

                payload = {
                    "doc_id": doc_id,
                    "chunk_type": "paragraph",
                    "page": page,
                    "content": content,
                    "bbox": para.get("bbox"),
                    "para_id": para.get("id"),
                    **default_metadata
                }

                chunks.append({
                    "id": chunk_id,
                    "vector": vector,
                    "payload": payload
                })

            print(f"[Qdrant] 处理段落完成: {len(chunks)} 个段落")

        except Exception as e:
            print(f"[Qdrant] 处理段落失败: {e}")

        # 2. 处理 table.json（按行粒度存储）
        try:
            with open(table_json_path, 'r', encoding='utf-8') as f:
                table_data = json.load(f)

            for table_idx, table in enumerate(table_data.get("tables", [])):
                table_id = table.get("id", f"t{table_idx+1:03d}")
                page = table.get("page", 1)
                columns = table.get("columns", [])
                col_names = [col.get("name", f"col{i}") for i, col in enumerate(columns)]

                for row_idx, row in enumerate(table.get("rows", [])):
                    cells = row.get("cells", [])

                    # 方案1: 每行一个chunk，内容为 "col1: val1 | col2: val2 | ..."
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

                    chunk_id_str = self._generate_chunk_id(doc_id, "table_row", page,
                                                           table_idx * 1000 + row_idx)
                    chunk_id = self._hash_to_int(chunk_id_str)

                    # 生成向量
                    vector = embedding_fn(row_content) if embedding_fn else [0.0] * 768

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

                    chunks.append({
                        "id": chunk_id,
                        "vector": vector,
                        "payload": payload
                    })

            print(f"[Qdrant] 处理表格完成: 共 {len(chunks)} 个chunks（包含段落和表格行）")

        except Exception as e:
            print(f"[Qdrant] 处理表格失败: {e}")

        # 3. 批量插入
        if chunks:
            success = self.insert_points_batch("tender_chunks", chunks)
            if success:
                print(f"[Qdrant] 成功导入 {len(chunks)} 个chunks到 tender_chunks")
                return len(chunks)

        return 0

    def search_tender_chunks(self,
                            query_vector: List[float],
                            doc_id: Optional[str] = None,
                            chunk_types: Optional[List[str]] = None,
                            region: Optional[str] = None,
                            limit: int = 10) -> List[Dict[str, Any]]:
        """
        搜索招标文件chunks（支持过滤）

        Args:
            query_vector: 查询向量
            doc_id: 限定文档ID（可选）
            chunk_types: 限定chunk类型（如 ["paragraph"] 或 ["table_row"]）
            region: 限定地区（可选）
            limit: 返回结果数量

        Returns:
            搜索结果列表
        """
        # 构建过滤条件
        must_conditions = []

        if doc_id:
            must_conditions.append(
                FieldCondition(key="doc_id", match=MatchValue(value=doc_id))
            )

        if chunk_types:
            for chunk_type in chunk_types:
                must_conditions.append(
                    FieldCondition(key="chunk_type", match=MatchValue(value=chunk_type))
                )

        if region:
            must_conditions.append(
                FieldCondition(key="region", match=MatchValue(value=region))
            )

        # 构建Filter
        query_filter = Filter(must=must_conditions) if must_conditions else None

        # 搜索
        try:
            results = self.client.search(
                collection_name="tender_chunks",
                query_vector=query_vector,
                query_filter=query_filter,
                limit=limit
            )

            output = []
            for result in results:
                output.append({
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload
                })

            print(f"[Qdrant] 搜索完成: 返回 {len(output)} 条结果")
            return output
        except Exception as e:
            print(f"[Qdrant] 搜索失败: {e}")
            return []

    def search_by_keyword(self,
                         keyword: str,
                         doc_id: Optional[str] = None,
                         chunk_types: Optional[List[str]] = None,
                         region: Optional[str] = None,
                         limit: int = 10) -> List[Dict[str, Any]]:
        """
        根据关键词搜索招标文件chunks（文本匹配）

        Args:
            keyword: 搜索关键词
            doc_id: 限定文档ID（可选）
            chunk_types: 限定chunk类型（如 ["paragraph"] 或 ["table_row"]）
            region: 限定地区（可选）
            limit: 返回结果数量

        Returns:
            搜索结果列表，按相关性排序

        示例:
            # 搜索包含"项目预算"的所有段落
            results = util.search_by_keyword(
                keyword="项目预算",
                chunk_types=["paragraph"],
                limit=5
            )

            # 搜索指定文档中包含"投标人"的表格行
            results = util.search_by_keyword(
                keyword="投标人",
                doc_id="ORDOS-2025-0001",
                chunk_types=["table_row"],
                limit=10
            )
        """
        from qdrant_client.models import FieldCondition, MatchValue, MatchText, Filter

        # 构建过滤条件
        must_conditions = []

        # 关键词匹配（content字段）
        must_conditions.append(
            FieldCondition(key="content", match=MatchText(text=keyword))
        )

        if doc_id:
            must_conditions.append(
                FieldCondition(key="doc_id", match=MatchValue(value=doc_id))
            )

        if chunk_types:
            # 如果有多个chunk_type，使用should条件（OR关系）
            if len(chunk_types) == 1:
                must_conditions.append(
                    FieldCondition(key="chunk_type", match=MatchValue(value=chunk_types[0]))
                )
            else:
                from qdrant_client.models import Filter as QFilter
                should_conditions = [
                    FieldCondition(key="chunk_type", match=MatchValue(value=ct))
                    for ct in chunk_types
                ]
                # 注意：这里需要特殊处理，Qdrant的should需要放在Filter中
                # 暂时简化为使用第一个类型
                must_conditions.append(
                    FieldCondition(key="chunk_type", match=MatchValue(value=chunk_types[0]))
                )

        if region:
            must_conditions.append(
                FieldCondition(key="region", match=MatchValue(value=region))
            )

        # 构建Filter
        query_filter = Filter(must=must_conditions)

        # 使用 scroll 方法进行过滤搜索（不需要向量）
        try:
            results, _ = self.client.scroll(
                collection_name="tender_chunks",
                scroll_filter=query_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )

            output = []
            for result in results:
                output.append({
                    "id": result.id,
                    "payload": result.payload,
                    "content": result.payload.get("content", "")
                })

            print(f"[Qdrant] 关键词搜索完成: 关键词='{keyword}', 返回 {len(output)} 条结果")
            return output

        except Exception as e:
            print(f"[Qdrant] 搜索失败: {e}")
            return []


# 测试代码
if __name__ == '__main__':
    # 1. 初始化（连接数据库）
    util = QdrantUtil(url="http://localhost:6333")

    # 2. 创建集合（相当于创建表）
    collection_name = "test_collection"
    util.create_collection(
        collection_name=collection_name,
        vector_size=4,  # 向量维度
        distance=Distance.DOT
    )

    # 3. 插入一条数据（相当于 INSERT）
    print("\n=== 插入数据 ===")
    util.insert_point(
        collection_name=collection_name,
        point_id=1,
        vector=[0.1, 0.2, 0.3, 0.4],
        payload={
            "name": "张三",
            "age": 25,
            "city": "北京"
        }
    )

    # 4. 读取数据（相当于 SELECT）
    print("\n=== 读取数据 ===")
    point = util.get_point(collection_name, point_id=1)
    if point:
        print(f"ID: {point['id']}")
        print(f"向量: {point['vector']}")
        print(f"负载: {point['payload']}")

    # 5. 批量插入（可选）
    print("\n=== 批量插入 ===")
    util.insert_points_batch(
        collection_name=collection_name,
        points=[
            {
                "id": 2,
                "vector": [0.5, 0.6, 0.7, 0.8],
                "payload": {"name": "李四", "age": 30, "city": "上海"}
            },
            {
                "id": 3,
                "vector": [0.9, 1.0, 1.1, 1.2],
                "payload": {"name": "王五", "age": 28, "city": "深圳"}
            }
        ]
    )

    # 6. 向量相似度搜索
    print("\n=== 向量搜索 ===")
    results = util.search_similar(
        collection_name=collection_name,
        query_vector=[0.1, 0.2, 0.3, 0.4],
        limit=3
    )
    for i, result in enumerate(results, 1):
        print(f"排名 {i}: ID={result['id']}, 得分={result['score']:.4f}, {result['payload']}")

    # 7. 列出所有集合
    print("\n=== 列出集合 ===")
    util.list_collections()

    # 8. 清理（可选）
    # util.delete_collection(collection_name)