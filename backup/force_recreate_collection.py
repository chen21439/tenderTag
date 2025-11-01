"""
强制删除并重新创建 tender_chunks 集合（混合向量版本）
"""
from app.utils.db.qdrant import QdrantUtil

util = QdrantUtil(url="http://localhost:6333")

print("=" * 80)
print("强制重新创建集合")
print("=" * 80)

# 1. 强制删除
print("\n[1/3] 强制删除 tender_chunks 集合...")
try:
    util.client.delete_collection("tender_chunks")
    print("  ✓ 集合已删除")
except Exception as e:
    print(f"  ! 删除失败或集合不存在: {e}")

# 2. 验证删除
print("\n[2/3] 验证集合已删除...")
collections = util.list_collections()
if "tender_chunks" in collections:
    print("  ✗ 集合仍然存在！")
    exit(1)
else:
    print("  ✓ 集合已不存在")

# 3. 创建新集合（混合向量）
print("\n[3/3] 创建新集合（混合向量：稠密1024维+稀疏）...")
success = util.init_tender_collection(use_hybrid=True)

if success:
    print("  ✓ 集合创建成功")

    # 验证配置
    print("\n[验证] 集合配置:")
    collection_info = util.client.get_collection("tender_chunks")
    print(f"  向量配置: {collection_info.config.params.vectors}")
    print(f"  Points 数量: {collection_info.points_count}")
else:
    print("  ✗ 集合创建失败")

print("\n" + "=" * 80)
print("完成！")
print("=" * 80)
