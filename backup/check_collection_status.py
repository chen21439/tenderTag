"""
检查 tender_chunks 集合状态
"""
from app.utils.db.qdrant import QdrantUtil

util = QdrantUtil(url="http://localhost:6333")

print("=" * 80)
print("检查集合状态")
print("=" * 80)

# 1. 检查集合是否存在
collections = util.list_collections()
print(f"\n[1] 现有集合: {collections}")

if "tender_chunks" in collections:
    print("\n[2] tender_chunks 集合存在")

    # 2. 获取集合信息
    collection_info = util.client.get_collection("tender_chunks")

    print(f"\n[3] 向量配置:")
    print(f"    {collection_info.config.params.vectors}")

    print(f"\n[4] Points 数量:")
    print(f"    {collection_info.points_count}")

    print(f"\n[5] 索引配置:")
    if collection_info.payload_schema:
        for field, schema in collection_info.payload_schema.items():
            print(f"    {field}: {schema}")
    else:
        print("    无 payload 索引")
else:
    print("\n[2] tender_chunks 集合不存在")

print("\n" + "=" * 80)
