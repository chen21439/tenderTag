"""
清空 Milvus pdf collection 的数据

使用方法:
    python clear_milvus_collection.py
"""

from pymilvus import connections, utility, Collection


def clear_pdf_collection():
    """清空 pdf collection 的所有数据"""

    # 连接到 Milvus
    print("[清空Collection] 正在连接到 Milvus...")
    connections.connect(
        alias="default",
        host="localhost",
        port="19530"
    )
    print("[清空Collection] ✓ 已连接")

    collection_name = "pdf"

    # 检查集合是否存在
    if not utility.has_collection(collection_name):
        print(f"[清空Collection] 集合 '{collection_name}' 不存在，无需清空")
        connections.disconnect("default")
        return

    print(f"[清空Collection] 集合 '{collection_name}' 存在")

    # 获取集合
    collection = Collection(collection_name)

    # 加载集合
    collection.load()

    # 查询当前数据量
    count_before = collection.num_entities
    print(f"[清空Collection] 清空前数据量: {count_before} 条")

    if count_before == 0:
        print("[清空Collection] 集合已经是空的，无需清空")
        connections.disconnect("default")
        return

    # 方案1: 删除并重建集合 (推荐，最快)
    print(f"[清空Collection] 正在删除集合 '{collection_name}'...")
    utility.drop_collection(collection_name)
    print(f"[清空Collection] ✓ 集合已删除")

    print(f"[清空Collection] 提示: 集合将在下次上传PDF时自动重建")

    # 关闭连接
    connections.disconnect("default")
    print("[清空Collection] ✓ 完成")


if __name__ == "__main__":
    try:
        clear_pdf_collection()
    except Exception as e:
        print(f"[清空Collection] ✗ 错误: {e}")
        import traceback
        traceback.print_exc()