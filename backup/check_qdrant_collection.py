"""
检查 Qdrant 集合配置
"""
from app.utils.db.qdrant import QdrantUtil

util = QdrantUtil(url="http://localhost:6333")

# 列出所有集合
print("现有集合:")
collections = util.list_collections()
for coll in collections:
    print(f"  - {coll}")

# 检查 tender_chunks 集合的配置
if "tender_chunks" in collections:
    print("\n[tender_chunks 集合信息]")
    try:
        collection_info = util.client.get_collection("tender_chunks")
        print(f"  向量配置: {collection_info.config.params.vectors}")
    except Exception as e:
        print(f"  获取集合信息失败: {e}")

    # 尝试删除集合
    response = input("\n是否删除 tender_chunks 集合并重新创建? (y/n): ")
    if response.lower() == 'y':
        print("  正在删除集合...")
        util.client.delete_collection("tender_chunks")
        print("  ✅ 集合已删除")

        print("  正在重新创建集合...")
        success = util.init_tender_collection(vector_size=768)
        if success:
            print("  ✅ 集合重新创建成功")
        else:
            print("  ❌ 集合创建失败")
else:
    print("\n[tender_chunks 集合不存在]")
    print("正在创建集合...")
    success = util.init_tender_collection(vector_size=768)
    if success:
        print("✅ 集合创建成功")
    else:
        print("❌ 集合创建失败")
