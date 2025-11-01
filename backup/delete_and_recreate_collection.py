"""
删除并重新创建 tender_chunks 集合
"""
from app.utils.db.qdrant import QdrantUtil

util = QdrantUtil(url="http://localhost:6333")

# 检查集合是否存在
collections = util.list_collections()

if "tender_chunks" in collections:
    print("[1/2] 正在删除现有的 tender_chunks 集合...")
    util.client.delete_collection("tender_chunks")
    print("  [OK] 集合已删除")
else:
    print("[1/2] tender_chunks 集合不存在")

print("\n[2/2] 正在创建新的 tender_chunks 集合（混合向量：稠密1024维+稀疏）...")
success = util.init_tender_collection(use_hybrid=True)
if success:
    print("  [OK] 集合创建成功")

    # 验证集合配置
    print("\n[验证] 检查集合配置...")
    collection_info = util.client.get_collection("tender_chunks")
    print(f"  向量配置: {collection_info.config.params.vectors}")
else:
    print("  [ERROR] 集合创建失败")
