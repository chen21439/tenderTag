"""
测试从内存直接导入 Qdrant（完整流程）

演示：PDF → 内存 → Qdrant（无中间文件）
"""
from pathlib import Path
from app.utils.unTaggedPDF.pdf_content_extractor import PDFContentExtractor
from app.utils.db.qdrant import QdrantUtil


def main():
    # 配置参数
    task_id = "1978018096320905217"
    base_dir = Path(r"E:\programFile\AIProgram\docxServer\pdf\task\1978018096320905217")
    pdf_path = base_dir / f"{task_id}.pdf"

    # 检查PDF是否存在
    if not pdf_path.exists():
        print(f"错误: PDF文件不存在: {pdf_path}")
        return

    print(f"=== 测试从内存导入 Qdrant ===")
    print(f"PDF文件: {pdf_path}")

    # Step 1: 初始化 Qdrant（只需执行一次）
    print("\n[Step 1] 初始化 Qdrant 集合...")
    util = QdrantUtil(url="http://localhost:6333")

    # 检查集合是否已存在
    existing_collections = util.list_collections()
    if "tender_chunks" not in existing_collections:
        print("  创建 tender_chunks 集合...")
        success = util.init_tender_collection(vector_size=768)
        if not success:
            print("  ❌ 创建集合失败")
            return
        print("  ✅ 集合创建成功")
    else:
        print("  ✅ 集合已存在，跳过创建")

    # Step 2: 从 PDF 提取内容并直接导入到 Qdrant（内存中完成）
    print("\n[Step 2] 从 PDF 提取内容并导入到 Qdrant（内存操作）...")

    extractor = PDFContentExtractor(
        str(pdf_path),
        enable_cross_page_merge=True,
        enable_ai_row_classification=False,  # 关闭AI判断以加快测试
        verbose=False
    )

    # 文档元数据
    doc_id = "ORDOS-2025-0001"
    metadata = {
        "region": "内蒙古-鄂尔多斯",
        "agency": "鄂尔多斯市政府",
        "published_at_ts": 1706601600  # 2024-01-30 00:00:00
    }

    # 直接从内存导入（不写文件）
    print("  正在提取表格和段落...")
    chunk_count = extractor.save_to_qdrant(
        doc_id=doc_id,
        qdrant_url="http://localhost:6333",
        metadata=metadata,
        embedding_fn=None  # 使用占位向量
    )

    print(f"\n✅ 成功导入 {chunk_count} 个 chunks 到 Qdrant!")

    # Step 3: 验证导入结果
    print("\n[Step 3] 验证导入结果...")

    # 搜索所有该文档的chunks（使用占位向量）
    query_vector = [0.0] * 768
    results = util.search_tender_chunks(
        query_vector=query_vector,
        doc_id=doc_id,
        limit=5
    )

    print(f"\n查询结果（前5个）:")
    for i, result in enumerate(results, 1):
        payload = result['payload']
        content_preview = payload['content'][:80]
        print(f"\n  [{i}] 类型: {payload['chunk_type']}, 页码: {payload['page']}")
        print(f"      内容: {content_preview}...")
        if payload['chunk_type'] == 'table_row':
            print(f"      表格: {payload.get('table_id', 'N/A')}, 行: {payload.get('row_id', 'N/A')}")

    # 统计信息
    print("\n[统计信息]")
    all_results = util.search_tender_chunks(
        query_vector=query_vector,
        doc_id=doc_id,
        limit=10000  # 获取所有
    )

    paragraph_count = sum(1 for r in all_results if r['payload']['chunk_type'] == 'paragraph')
    table_row_count = sum(1 for r in all_results if r['payload']['chunk_type'] == 'table_row')

    print(f"  文档ID: {doc_id}")
    print(f"  总chunks: {len(all_results)}")
    print(f"  段落: {paragraph_count}")
    print(f"  表格行: {table_row_count}")
    print(f"  地区: {metadata['region']}")
    print(f"  机构: {metadata['agency']}")

    print("\n=== 测试完成 ===")


if __name__ == '__main__':
    main()