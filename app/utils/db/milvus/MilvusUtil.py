"""
Milvus 快速验证工具类
用于快速测试存储和搜索功能
"""
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
from typing import List, Dict, Any


class MilvusUtil:
    """Milvus 工具类 - 快速验证版本"""

    def __init__(self, host: str = "localhost", port: str = "19530"):
        """
        初始化 Milvus 连接

        Args:
            host: Milvus 服务器地址
            port: Milvus 端口
        """
        self.host = host
        self.port = port
        self.collection = None

        # 连接到 Milvus
        print(f"[Milvus] 连接到 {host}:{port}...")
        connections.connect(host=host, port=port)
        print(f"[Milvus] OK 连接成功")

    def create_collection(self,
                         collection_name: str = "tender_test",
                         dim: int = 1024,
                         drop_old: bool = True) -> bool:
        """
        创建集合

        Args:
            collection_name: 集合名称
            dim: 向量维度 (bge-m3: 1024维)
            drop_old: 是否删除旧集合

        Returns:
            是否成功
        """
        try:
            # 删除旧集合
            if drop_old and utility.has_collection(collection_name):
                print(f"[Milvus] 删除旧集合: {collection_name}")
                utility.drop_collection(collection_name)

            # 定义字段
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=200),
                FieldSchema(name="chunk_type", dtype=DataType.VARCHAR, max_length=50),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=5000),
                FieldSchema(name="page", dtype=DataType.INT64),
                FieldSchema(name="insert_time", dtype=DataType.INT64),  # 插入时间戳 (epoch ms)
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim)
            ]

            # 创建 schema
            schema = CollectionSchema(fields=fields, description="招标文档测试集合")

            # 创建集合
            print(f"[Milvus] 创建集合: {collection_name} (dim={dim})")
            collection = Collection(name=collection_name, schema=schema)

            # 创建索引
            print(f"[Milvus] 创建索引...")
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
            collection.create_index(field_name="embedding", index_params=index_params)

            self.collection = collection
            print(f"[Milvus] OK 集合创建成功")
            return True

        except Exception as e:
            print(f"[Milvus] FAILED 创建集合失败: {e}")
            return False

    def insert_data(self,
                   doc_id: str,
                   chunks: List[Dict[str, Any]],
                   embeddings: List[List[float]]) -> int:
        """
        插入数据

        Args:
            doc_id: 文档ID
            chunks: chunk 列表 [{"chunk_type": "paragraph", "content": "...", "page": 1}, ...]
            embeddings: 向量列表 [[...], [...], ...]

        Returns:
            插入的条数
        """
        if not self.collection:
            print("[Milvus] FAILED 集合未初始化")
            return 0

        if len(chunks) != len(embeddings):
            print(f"[Milvus] FAILED chunks数量({len(chunks)}) 与 embeddings数量({len(embeddings)}) 不匹配")
            return 0

        try:
            # 获取当前时间戳 (毫秒)
            import time
            current_time_ms = int(time.time() * 1000)

            # 准备数据
            entities = [
                [doc_id] * len(chunks),  # doc_id
                [chunk["chunk_type"] for chunk in chunks],  # chunk_type
                [chunk["content"][:5000] for chunk in chunks],  # content (截断到5000字符)
                [chunk["page"] for chunk in chunks],  # page
                [current_time_ms] * len(chunks),  # insert_time (所有数据使用同一个时间戳)
                embeddings  # embedding
            ]

            # 插入数据
            print(f"[Milvus] 插入 {len(chunks)} 条数据...")
            insert_result = self.collection.insert(entities)

            # 刷新
            self.collection.flush()

            print(f"[Milvus] OK 插入成功: {len(insert_result.primary_keys)} 条")
            return len(insert_result.primary_keys)

        except Exception as e:
            print(f"[Milvus] FAILED 插入失败: {e}")
            import traceback
            traceback.print_exc()
            return 0

    def search(self,
              query_embedding: List[float],
              top_k: int = 5) -> List[Dict[str, Any]]:
        """
        向量搜索

        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量

        Returns:
            搜索结果列表
        """
        if not self.collection:
            print("[Milvus] FAILED 集合未初始化")
            return []

        try:
            # 加载集合到内存
            self.collection.load()

            # 搜索参数
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10}
            }

            # 执行搜索
            print(f"[Milvus] 搜索 Top-{top_k}...")
            results = self.collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["doc_id", "chunk_type", "content", "page", "insert_time"]
            )

            # 格式化结果
            formatted_results = []
            for hits in results:
                for hit in hits:
                    formatted_results.append({
                        "id": hit.id,
                        "distance": hit.distance,
                        "doc_id": hit.entity.get("doc_id"),
                        "chunk_type": hit.entity.get("chunk_type"),
                        "content": hit.entity.get("content"),
                        "page": hit.entity.get("page"),
                        "insert_time": hit.entity.get("insert_time")
                    })

            print(f"[Milvus] OK 找到 {len(formatted_results)} 条结果")
            return formatted_results

        except Exception as e:
            print(f"[Milvus] FAILED 搜索失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def search_by_keywords(self,
                          keywords: List[str],
                          top_k: int = 5,
                          embedding_util=None) -> List[Dict[str, Any]]:
        """
        根据关键字进行向量搜索

        Args:
            keywords: 关键字列表
            top_k: 返回结果数量
            embedding_util: 向量化工具实例

        Returns:
            搜索结果列表
        """
        if not embedding_util:
            print("[Milvus] FAILED embedding_util 未提供")
            return []

        try:
            # 1. 将关键字拼接成查询文本
            query_text = " ".join(keywords)
            print(f"[Milvus] 搜索关键字: {query_text}")

            # 2. 向量化查询文本
            vectors = embedding_util.encode_batch([query_text])
            query_embedding, _, _ = vectors[0]  # 只使用稠密向量

            # 3. 执行搜索
            return self.search(query_embedding=query_embedding, top_k=top_k)

        except Exception as e:
            print(f"[Milvus] FAILED 关键字搜索失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_stats(self) -> Dict[str, Any]:
        """
        获取集合统计信息

        Returns:
            统计信息字典
        """
        if not self.collection:
            return {"error": "集合未初始化"}

        try:
            self.collection.load()
            num_entities = self.collection.num_entities

            return {
                "collection_name": self.collection.name,
                "num_entities": num_entities,
                "status": "loaded"
            }
        except Exception as e:
            return {"error": str(e)}

    def close(self):
        """关闭连接"""
        print("[Milvus] 关闭连接")
        connections.disconnect("default")


# 快速测试
def quick_test():
    """快速测试 Milvus 存储和搜索"""
    print("="*80)
    print("Milvus 快速测试")
    print("="*80)

    # 1. 初始化
    milvus = MilvusUtil(host="localhost", port="19530")

    # 2. 创建集合
    milvus.create_collection(collection_name="tender_test", dim=1024)

    # 3. 准备测试数据
    chunks = [
        {"chunk_type": "paragraph", "content": "鄂尔多斯市政府网站群集约化平台升级改造项目", "page": 1},
        {"chunk_type": "paragraph", "content": "项目预算总金额为100万元", "page": 2},
        {"chunk_type": "table_row", "content": "序号: 1 | 项目名称: 网站建设", "page": 3}
    ]

    # 生成随机向量 (模拟 bge-m3 输出)
    import random
    embeddings = [[random.random() for _ in range(1024)] for _ in chunks]

    # 4. 插入数据
    count = milvus.insert_data(
        doc_id="ORDOS-TEST-001",
        chunks=chunks,
        embeddings=embeddings
    )

    # 5. 查询数据
    print(f"\n{'='*80}")
    print("测试搜索")
    print("="*80)

    query_embedding = [random.random() for _ in range(1024)]
    results = milvus.search(query_embedding, top_k=3)

    for i, result in enumerate(results, 1):
        print(f"\n[{i}] 距离: {result['distance']:.4f}")
        print(f"    类型: {result['chunk_type']}, 页码: {result['page']}")
        print(f"    内容: {result['content'][:80]}...")

    # 6. 统计信息
    print(f"\n{'='*80}")
    print("统计信息")
    print("="*80)
    stats = milvus.get_stats()
    print(f"集合名称: {stats['collection_name']}")
    print(f"数据条数: {stats['num_entities']}")

    # 7. 关闭连接
    milvus.close()

    print(f"\n{'='*80}")
    print("测试完成!")
    print("="*80)


if __name__ == "__main__":
    quick_test()