"""
测试向量化集成（完整流程）

步骤：
1. 初始化 bge-m3 模型
2. 初始化 Qdrant 集合（混合向量）
3. 提取 PDF 内容
4. 向量化并导入到 Qdrant
5. 测试搜索
"""
from pathlib import Path
from app.utils.unTaggedPDF.pdf_content_extractor import PDFContentExtractor
from app.utils.db.qdrant import QdrantUtil
from app.utils.db.qdrant.EmbeddingUtil import get_embedding_util
from insert_tender_chunks_with_embedding import insert_tender_chunks_from_memory_v2


def main():
    # 配置
    task_id = "鄂尔多斯市政府网站群集约化平台升级改造项目"
    base_dir = Path(r"E:\programFile\AIProgram\docxServer\pdf\task\鄂尔多斯市政府网站群集约化平台升级改造项目")
    pdf_path = base_dir / f"{task_id}.pdf"

    if not pdf_path.exists():
        print(f"错误: PDF文件不存在: {pdf_path}")
        return

    print("=" * 80)
    print("步骤 1/5: 初始化 bge-m3 模型")
    print("=" * 80)

    # 自动检测并使用 GPU（如果可用）
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  检测到设备: {device}")
    if device == "cuda":
        print(f"  GPU: {torch.cuda.get_device_name(0)}")

    embedding_util = get_embedding_util(
        model_name='BAAI/bge-m3',
        use_fp16=True,
        device=device
    )

    print("\n" + "=" * 80)
    print("步骤 2/5: 初始化 Qdrant 集合")
    print("=" * 80)

    qdrant_util = QdrantUtil(url="http://localhost:6333")

    # 检查集合是否存在
    existing_collections = qdrant_util.list_collections()
    if "tender_chunks" in existing_collections:
        print("  集合已存在")
        response = input("  是否删除并重新创建? (y/n): ")
        if response.lower() == 'y':
            print("  正在删除...")
            qdrant_util.client.delete_collection("tender_chunks")
            print("  正在重新创建...")
            qdrant_util.init_tender_collection(use_hybrid=True)
    else:
        print("  正在创建集合...")
        qdrant_util.init_tender_collection(use_hybrid=True)

    print("\n" + "=" * 80)
    print("步骤 3/5: 提取 PDF 内容")
    print("=" * 80)

    extractor = PDFContentExtractor(
        str(pdf_path),
        enable_cross_page_merge=True,
        verbose=False
    )

    # 提取表格和段落（内存）
    print("  提取表格...")
    tables_result = extractor.extract_all_tables()
    tables_full = tables_result.get("tables", [])
    print(f"    ✓ 提取了 {len(tables_full)} 个表格")

    print("  提取段落...")
    paragraphs_result = extractor.extract_all_paragraphs()
    paragraphs_full = paragraphs_result.get("paragraphs", [])
    print(f"    ✓ 提取了 {len(paragraphs_full)} 个段落")

    # 🧪 测试模式：只取前几个段落和表格
    MAX_PARAGRAPHS = 10  # 只取前10个段落
    MAX_TABLE_ROWS = 5   # 每个表格只取前5行

    print(f"\n  [测试模式] 只向量化前 {MAX_PARAGRAPHS} 个段落和每个表格前 {MAX_TABLE_ROWS} 行")
    paragraphs = paragraphs_full[:MAX_PARAGRAPHS]

    # 限制表格行数
    tables = []
    for table in tables_full:
        limited_table = table.copy()
        rows = table.get("rows", [])
        limited_table["rows"] = rows[:MAX_TABLE_ROWS]
        tables.append(limited_table)

    print(f"    → 将向量化: {len(paragraphs)} 个段落")
    total_rows = sum(len(t.get("rows", [])) for t in tables)
    print(f"    → 将向量化: {total_rows} 个表格行（来自 {len(tables)} 个表格）")

    print("\n" + "=" * 80)
    print("步骤 4/5: 向量化并导入到 Qdrant")
    print("=" * 80)

    doc_id = f"ORDOS-{task_id[:10]}"
    metadata = {
        "region": "内蒙古-鄂尔多斯",
        "agency": "鄂尔多斯市政府",
        "published_at_ts": 1706601600
    }

    chunk_count = insert_tender_chunks_from_memory_v2(
        qdrant_util=qdrant_util,
        doc_id=doc_id,
        tables=tables,
        paragraphs=paragraphs,
        embedding_util=embedding_util,
        metadata=metadata
    )

    print(f"\n  ✓ 成功导入 {chunk_count} 个 chunks")

    # 显示最终缓存统计
    stats = embedding_util.get_cache_stats()
    print(f"\n  [缓存统计]")
    print(f"    缓存大小: {stats['cache_size']}")
    print(f"    缓存命中: {stats['cache_hits']}")
    print(f"    缓存未命中: {stats['cache_misses']}")
    print(f"    命中率: {stats['hit_rate']}")

    print("\n" + "=" * 80)
    print("步骤 5/5: 测试搜索")
    print("=" * 80)

    # 测试查询
    query = "网站集约化平台"
    print(f"\n  查询: '{query}'")

    dense_vec, sparse_vec = embedding_util.encode_query(query)

    # Qdrant 1.9.0: 仅使用稠密向量搜索 (1.9.0 不支持客户端 sparse 搜索)
    print(f"  [搜索] 使用稠密向量搜索...")
    results = qdrant_util.client.search(
        collection_name="tender_chunks",
        query_vector=("dense", dense_vec),
        limit=5,
        with_payload=True
    )

    print(f"\n  搜索结果（Top 5）:")
    for i, result in enumerate(results, 1):
        payload = result.payload
        content = payload['content'][:80]
        print(f"\n    [{i}] 相似度: {result.score:.4f}")
        print(f"        类型: {payload['chunk_type']}, 页码: {payload['page']}")
        print(f"        内容: {content}...")

    print("\n" + "=" * 80)
    print("测试完成!")
    print("=" * 80)


if __name__ == '__main__':
    main()
