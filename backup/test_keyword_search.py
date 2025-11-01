"""
测试关键词搜索功能
"""
from app.utils.db.qdrant import QdrantUtil

def main():
    # 初始化
    util = QdrantUtil(url="http://localhost:6333")

    print("=" * 60)
    print("测试1: 搜索包含'网站'的所有内容（前5条）")
    print("=" * 60)
    results = util.search_by_keyword(
        keyword="网站",
        limit=5
    )

    for i, result in enumerate(results, 1):
        payload = result['payload']
        content = result['content'][:100]  # 只显示前100个字符
        print(f"\n[{i}] {payload['chunk_type']} - 页{payload['page']}")
        print(f"    内容: {content}...")
        if payload['chunk_type'] == 'table_row':
            print(f"    表格: {payload.get('table_id', 'N/A')}, 行: {payload.get('row_id', 'N/A')}")

    print("\n" + "=" * 60)
    print("测试2: 搜索包含'项目'的段落（前3条）")
    print("=" * 60)
    results = util.search_by_keyword(
        keyword="项目",
        chunk_types=["paragraph"],
        limit=3
    )

    for i, result in enumerate(results, 1):
        payload = result['payload']
        content = result['content'][:100]
        print(f"\n[{i}] 页{payload['page']}")
        print(f"    内容: {content}...")

    print("\n" + "=" * 60)
    print("测试3: 搜索包含'技术'的表格行（前5条）")
    print("=" * 60)
    results = util.search_by_keyword(
        keyword="技术",
        chunk_types=["table_row"],
        limit=5
    )

    for i, result in enumerate(results, 1):
        payload = result['payload']
        content = result['content']
        print(f"\n[{i}] 表格 {payload.get('table_id', 'N/A')}, 行 {payload.get('row_id', 'N/A')}, 页{payload['page']}")
        print(f"    {content}")

    print("\n" + "=" * 60)
    print("测试4: 搜索指定文档中包含'系统'的内容")
    print("=" * 60)

    # 先获取所有文档ID
    all_results, _ = util.client.scroll(
        collection_name="tender_chunks",
        limit=1,
        with_payload=True
    )

    if all_results:
        doc_id = all_results[0].payload['doc_id']
        print(f"文档ID: {doc_id}\n")

        results = util.search_by_keyword(
            keyword="系统",
            doc_id=doc_id,
            limit=3
        )

        for i, result in enumerate(results, 1):
            payload = result['payload']
            content = result['content'][:80]
            print(f"\n[{i}] {payload['chunk_type']} - 页{payload['page']}")
            print(f"    {content}...")

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == '__main__':
    main()
