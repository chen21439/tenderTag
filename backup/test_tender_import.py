"""
测试招标文件导入到 Qdrant

使用示例：
python test_tender_import.py
"""
from pathlib import Path
from app.utils.db.qdrant import QdrantUtil


def main():
    # 1. 初始化 Qdrant 工具
    util = QdrantUtil(url="http://localhost:6333")

    # 2. 初始化 tender_chunks 集合（只需执行一次）
    print("\n=== 初始化 tender_chunks 集合 ===")
    util.init_tender_collection(vector_size=768)

    # 3. 导入招标文件数据
    print("\n=== 导入招标文件数据 ===")

    # 设置文件路径（请根据实际情况修改）
    base_dir = Path(r"E:\programFile\AIProgram\docxServer\pdf\task\1978018096320905217")
    table_json = base_dir / "1978018096320905217_table_20250130_234126.json"
    paragraph_json = base_dir / "1978018096320905217_paragraph_20250130_234126.json"

    # 检查文件是否存在
    if not table_json.exists():
        print(f"错误: table.json 不存在: {table_json}")
        return
    if not paragraph_json.exists():
        print(f"错误: paragraph.json 不存在: {paragraph_json}")
        return

    # 导入数据（暂时不使用向量化，使用占位向量）
    doc_id = "ORDOS-2025-0001"
    metadata = {
        "region": "内蒙古-鄂尔多斯",
        "agency": "鄂尔多斯市政府",
        "published_at_ts": 1706601600  # 2024-01-30 00:00:00
    }

    chunk_count = util.insert_tender_chunks_from_json(
        doc_id=doc_id,
        table_json_path=str(table_json),
        paragraph_json_path=str(paragraph_json),
        embedding_fn=None,  # 暂时不使用向量化
        metadata=metadata
    )

    print(f"\n成功导入 {chunk_count} 个 chunks!")

    # 4. 测试搜索（使用占位向量）
    print("\n=== 测试搜索（限定文档ID） ===")
    query_vector = [0.0] * 768  # 占位向量
    results = util.search_tender_chunks(
        query_vector=query_vector,
        doc_id=doc_id,
        limit=5
    )

    for i, result in enumerate(results, 1):
        payload = result['payload']
        print(f"\n结果 {i}:")
        print(f"  类型: {payload['chunk_type']}")
        print(f"  页码: {payload['page']}")
        print(f"  内容: {payload['content'][:100]}...")

    # 5. 测试搜索（只搜段落）
    print("\n=== 测试搜索（只搜段落） ===")
    results = util.search_tender_chunks(
        query_vector=query_vector,
        doc_id=doc_id,
        chunk_types=["paragraph"],
        limit=3
    )

    for i, result in enumerate(results, 1):
        payload = result['payload']
        print(f"\n段落 {i}:")
        print(f"  页码: {payload['page']}")
        print(f"  内容: {payload['content'][:100]}...")


if __name__ == '__main__':
    main()