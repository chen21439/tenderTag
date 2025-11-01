"""
招标文档搜索器 - 负责在向量数据库中搜索内容

职责:
1. 语义向量搜索
2. 关键词搜索
3. 混合搜索 (语义+关键词)
4. 结果过滤和排序
"""
from typing import List, Dict, Any, Optional


class TenderSearcher:
    """招标文档搜索器"""

    def __init__(self, qdrant_util, embedding_util):
        """
        初始化搜索器

        Args:
            qdrant_util: QdrantUtil 实例
            embedding_util: EmbeddingUtil 实例
        """
        self.qdrant_util = qdrant_util
        self.embedding_util = embedding_util

    def search(self,
               query: str,
               doc_id: Optional[str] = None,
               chunk_types: Optional[List[str]] = None,
               region: Optional[str] = None,
               limit: int = 10) -> List[Dict[str, Any]]:
        """
        语义向量搜索 (使用稠密向量)

        Args:
            query: 搜索查询文本
            doc_id: 限定文档ID (可选)
            chunk_types: 限定chunk类型 (如 ["paragraph"] 或 ["table_row"])
            region: 限定地区 (可选)
            limit: 返回结果数量

        Returns:
            搜索结果列表，格式:
            [
                {
                    "id": chunk_id,
                    "score": 0.85,
                    "doc_id": "ORDOS-...",
                    "chunk_type": "paragraph",
                    "page": 2,
                    "content": "...",
                    ...
                },
                ...
            ]

        示例:
            # 基本搜索
            results = searcher.search("网站集约化平台", limit=5)

            # 在指定文档中搜索段落
            results = searcher.search(
                "网站集约化平台",
                doc_id="ORDOS-2025-0001",
                chunk_types=["paragraph"],
                limit=5
            )
        """
        print(f"[搜索器] 语义搜索: '{query}'")

        # 1. 向量化查询
        dense_vec, sparse_vec = self.embedding_util.encode_query(query)

        # 2. 构建过滤条件
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        must_conditions = []

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
                # 简化处理：只使用第一个类型（完整实现需要使用should）
                must_conditions.append(
                    FieldCondition(key="chunk_type", match=MatchValue(value=chunk_types[0]))
                )

        if region:
            must_conditions.append(
                FieldCondition(key="region", match=MatchValue(value=region))
            )

        query_filter = Filter(must=must_conditions) if must_conditions else None

        # 3. 执行搜索 (Qdrant 1.9.0 只支持 dense 向量搜索)
        try:
            results = self.qdrant_util.client.search(
                collection_name="tender_chunks",
                query_vector=("dense", dense_vec),
                query_filter=query_filter,
                limit=limit,
                with_payload=True
            )

            # 4. 格式化结果
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result.id,
                    "score": result.score,
                    **result.payload  # 展开所有 payload 字段
                })

            print(f"[搜索器]   OK 找到 {len(formatted_results)} 条结果")
            return formatted_results

        except Exception as e:
            print(f"[搜索器]   FAILED 搜索失败: {e}")
            return []

    def search_by_keyword(self,
                          keyword: str,
                          doc_id: Optional[str] = None,
                          chunk_types: Optional[List[str]] = None,
                          region: Optional[str] = None,
                          limit: int = 10) -> List[Dict[str, Any]]:
        """
        关键词搜索 (文本匹配)

        Args:
            keyword: 搜索关键词
            doc_id: 限定文档ID (可选)
            chunk_types: 限定chunk类型
            region: 限定地区
            limit: 返回结果数量

        Returns:
            搜索结果列表

        示例:
            # 搜索包含"项目预算"的所有段落
            results = searcher.search_by_keyword(
                keyword="项目预算",
                chunk_types=["paragraph"],
                limit=5
            )

            # 搜索指定文档中包含"投标人"的表格行
            results = searcher.search_by_keyword(
                keyword="投标人",
                doc_id="ORDOS-2025-0001",
                chunk_types=["table_row"],
                limit=10
            )
        """
        print(f"[搜索器] 关键词搜索: '{keyword}'")

        from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchText

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
            if len(chunk_types) == 1:
                must_conditions.append(
                    FieldCondition(key="chunk_type", match=MatchValue(value=chunk_types[0]))
                )
            else:
                # 简化处理
                must_conditions.append(
                    FieldCondition(key="chunk_type", match=MatchValue(value=chunk_types[0]))
                )

        if region:
            must_conditions.append(
                FieldCondition(key="region", match=MatchValue(value=region))
            )

        query_filter = Filter(must=must_conditions)

        # 使用 scroll 方法进行过滤搜索（不需要向量）
        try:
            results, _ = self.qdrant_util.client.scroll(
                collection_name="tender_chunks",
                scroll_filter=query_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )

            # 格式化结果
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result.id,
                    **result.payload
                })

            print(f"[搜索器]   OK 找到 {len(formatted_results)} 条结果")
            return formatted_results

        except Exception as e:
            print(f"[搜索器]   FAILED 搜索失败: {e}")
            return []

    def hybrid_search(self,
                      query: str,
                      keyword_filter: Optional[str] = None,
                      doc_id: Optional[str] = None,
                      chunk_types: Optional[List[str]] = None,
                      limit: int = 10) -> List[Dict[str, Any]]:
        """
        混合搜索: 语义搜索 + 关键词过滤

        Args:
            query: 语义搜索查询
            keyword_filter: 关键词过滤（可选）
            doc_id: 限定文档ID
            chunk_types: 限定chunk类型
            limit: 返回结果数量

        Returns:
            搜索结果列表

        示例:
            # 语义搜索"网站建设"，但只返回包含"平台"的结果
            results = searcher.hybrid_search(
                query="网站建设",
                keyword_filter="平台",
                limit=5
            )
        """
        print(f"[搜索器] 混合搜索: query='{query}', keyword='{keyword_filter}'")

        # 1. 先进行语义搜索
        semantic_results = self.search(
            query=query,
            doc_id=doc_id,
            chunk_types=chunk_types,
            limit=limit * 2  # 多取一些，因为后面要过滤
        )

        # 2. 如果有关键词过滤，进行二次过滤
        if keyword_filter:
            filtered_results = [
                r for r in semantic_results
                if keyword_filter.lower() in r.get("content", "").lower()
            ]
            print(f"[搜索器]   OK 关键词过滤后: {len(filtered_results)} 条结果")
            return filtered_results[:limit]
        else:
            return semantic_results[:limit]

    def get_document_chunks(self,
                            doc_id: str,
                            chunk_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        获取指定文档的所有 chunks

        Args:
            doc_id: 文档ID
            chunk_types: 限定chunk类型（可选）

        Returns:
            chunks 列表

        示例:
            # 获取文档的所有段落
            chunks = searcher.get_document_chunks(
                doc_id="ORDOS-2025-0001",
                chunk_types=["paragraph"]
            )
        """
        print(f"[搜索器] 获取文档所有chunks: {doc_id}")

        from qdrant_client.models import Filter, FieldCondition, MatchValue

        must_conditions = [
            FieldCondition(key="doc_id", match=MatchValue(value=doc_id))
        ]

        if chunk_types:
            if len(chunk_types) == 1:
                must_conditions.append(
                    FieldCondition(key="chunk_type", match=MatchValue(value=chunk_types[0]))
                )

        query_filter = Filter(must=must_conditions)

        try:
            # 使用 scroll 获取所有结果
            all_results = []
            offset = None

            while True:
                results, offset = self.qdrant_util.client.scroll(
                    collection_name="tender_chunks",
                    scroll_filter=query_filter,
                    limit=100,  # 每次取100条
                    offset=offset,
                    with_payload=True,
                    with_vectors=False
                )

                if not results:
                    break

                for result in results:
                    all_results.append({
                        "id": result.id,
                        **result.payload
                    })

                if offset is None:
                    break

            print(f"[搜索器]   OK 找到 {len(all_results)} 个 chunks")
            return all_results

        except Exception as e:
            print(f"[搜索器]   FAILED 获取失败: {e}")
            return []