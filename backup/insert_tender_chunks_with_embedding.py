"""
带向量化的 tender_chunks 插入方法（替换原有方法）
"""

def insert_tender_chunks_from_memory_v2(qdrant_util,
                                        doc_id: str,
                                        tables: list,
                                        paragraphs: list,
                                        embedding_util=None,
                                        metadata: dict = None) -> int:
    """
    从内存中的表格和段落数据导入到 tender_chunks（支持向量化）

    Args:
        qdrant_util: QdrantUtil 实例
        doc_id: 文档ID
        tables: 表格列表
        paragraphs: 段落列表
        embedding_util: EmbeddingUtil 实例（如果None，使用占位向量）
        metadata: 元数据

    Returns:
        成功插入的chunk数量
    """
    # 默认元数据
    default_metadata = {
        "region": metadata.get("region", "unknown") if metadata else "unknown",
        "agency": metadata.get("agency", "unknown") if metadata else "unknown",
        "published_at_ts": metadata.get("published_at_ts", 0) if metadata else 0,
    }

    # 第1步：收集所有文本
    texts_to_embed = []
    chunk_infos = []  # 存储 chunk 元信息

    print(f"    [步骤1/4] 收集文本...")
    # 1.1 收集段落
    for idx, para in enumerate(paragraphs):
        content = para.get("content", "").strip()
        if not content:
            continue

        page = para.get("page", 1)
        chunk_id_str = qdrant_util._generate_chunk_id(doc_id, "paragraph", page, idx)
        chunk_id = qdrant_util._hash_to_int(chunk_id_str)

        texts_to_embed.append(content)
        chunk_infos.append({
            "id": chunk_id,
            "payload": {
                "doc_id": doc_id,
                "chunk_type": "paragraph",
                "page": page,
                "content": content,
                "bbox": para.get("bbox"),
                "para_id": para.get("id"),
                **default_metadata
            }
        })

    paragraph_count = len(chunk_infos)
    print(f"    [步骤1/4]   收集了 {paragraph_count} 个段落")

    # 1.2 收集表格行
    for table_idx, table in enumerate(tables):
        table_id = table.get("id", f"t{table_idx+1:03d}")
        page = table.get("page", 1)
        columns = table.get("columns", [])

        for row_idx, row in enumerate(table.get("rows", [])):
            cells = row.get("cells", [])

            # 格式化行内容
            row_parts = []
            for cell in cells:
                col_id = cell.get("col_id", "")
                content = cell.get("content", "").strip()

                # 找列名
                col_name = "unknown"
                for col in columns:
                    if col.get("id") == col_id:
                        col_name = col.get("name", col_id)
                        break

                row_parts.append(f"{col_name}: {content}")

            row_content = " | ".join(row_parts)
            if not row_content.strip():
                continue

            chunk_id_str = qdrant_util._generate_chunk_id(doc_id, "table_row", page,
                                                           table_idx * 1000 + row_idx)
            chunk_id = qdrant_util._hash_to_int(chunk_id_str)

            texts_to_embed.append(row_content)
            chunk_infos.append({
                "id": chunk_id,
                "payload": {
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
            })

    table_row_count = len(chunk_infos) - paragraph_count
    print(f"    [步骤1/4]   收集了 {table_row_count} 个表格行")
    print(f"    [步骤1/4]   总计 {len(texts_to_embed)} 个文本待向量化")

    # 第2步：批量向量化
    print(f"\n    [步骤2/4] 批量向量化...")
    if embedding_util:
        # 使用真实向量化
        print(f"    [步骤2/4]   使用 bge-m3 模型...")
        vectors = embedding_util.encode_batch(texts_to_embed)

        # 显示缓存统计
        stats = embedding_util.get_cache_stats()
        print(f"    [步骤2/4]   缓存命中率: {stats['hit_rate']}")
        print(f"    [步骤2/4]   缓存大小: {stats['cache_size']}")
    else:
        # 使用占位向量
        print(f"    [步骤2/4]   使用占位向量（全0）...")
        vectors = [(None, None, None) for _ in texts_to_embed]

    # 第3步：组装 points
    print(f"\n    [步骤3/4] 组装 chunks...")
    points = []
    for i, chunk_info in enumerate(chunk_infos):
        if embedding_util:
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
        else:
            # 占位向量（旧集合兼容）
            points.append({
                "id": chunk_info["id"],
                "vector": [0.0] * 768,  # 占位
                "payload": chunk_info["payload"]
            })

    print(f"    [步骤3/4]   组装完成: {len(points)} 个 points")

    # 第4步：批量插入
    print(f"\n    [步骤4/4] 批量插入到 Qdrant...")
    if points:
        success = qdrant_util.insert_points_batch("tender_chunks", points)

        if success:
            print(f"    [步骤4/4]   ✓ 插入成功: {len(points)} 个 chunks")
            print(f"              ({paragraph_count} 段落 + {table_row_count} 表格行)")
            return len(points)
        else:
            print(f"    [步骤4/4]   ✗ 插入失败")
            return 0
    else:
        print(f"    [步骤4/4]   ⚠️  没有数据，跳过插入")
        return 0
