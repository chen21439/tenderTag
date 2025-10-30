"""
Qdrant 向量数据库工具类

## MySQL vs Qdrant 概念对应关系

| MySQL | Qdrant | 说明 |
|-------|--------|------|
| Database | - | Qdrant 单实例管理所有集合 |
| Table | Collection | 集合对应表 |
| Row | Point | 点对应行 |
| Column | Payload | 负载对应列 |
| Primary Key | Point ID | 点ID对应主键 |
| Index | Vector Index | 向量索引 |

## 使用示例

```python
from app.utils.db.qdrant import QdrantUtil

# 初始化
util = QdrantUtil(url="http://localhost:6333")

# 创建集合（相当于创建表）
util.create_collection("my_collection", vector_size=128)

# 插入数据（相当于INSERT）
util.insert_point(
    collection_name="my_collection",
    point_id=1,
    vector=[0.1] * 128,
    payload={"name": "张三", "age": 25}
)

# 读取数据（相当于SELECT）
point = util.get_point("my_collection", point_id=1)
print(point)
```
"""
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue
)


class QdrantUtil:
    """Qdrant 向量数据库工具类"""

    def __init__(self, url: str = "http://localhost:6333", api_key: Optional[str] = None):
        """
        初始化 Qdrant 客户端

        Args:
            url: Qdrant 服务地址（默认 http://localhost:6333）
            api_key: API 密钥（可选，用于云服务）
        """
        self.client = QdrantClient(url=url, api_key=api_key)
        print(f"[Qdrant] 已连接到: {url}")

    def create_collection(self,
                          collection_name: str,
                          vector_size: int,
                          distance: Distance = Distance.COSINE) -> bool:
        """
        创建集合（相当于 MySQL 的 CREATE TABLE）

        Args:
            collection_name: 集合名称（相当于表名）
            vector_size: 向量维度
            distance: 距离度量方式
                - Distance.COSINE: 余弦相似度（默认，适合文本）
                - Distance.DOT: 点积（适合归一化向量）
                - Distance.EUCLID: 欧几里得距离

        Returns:
            是否创建成功
        """
        try:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=distance),
            )
            print(f"[Qdrant] 集合 '{collection_name}' 创建成功 (向量维度: {vector_size})")
            return True
        except Exception as e:
            print(f"[Qdrant] 创建集合失败: {e}")
            return False

    def insert_point(self,
                     collection_name: str,
                     point_id: int,
                     vector: List[float],
                     payload: Optional[Dict[str, Any]] = None) -> bool:
        """
        插入单条数据（相当于 MySQL 的 INSERT）

        Args:
            collection_name: 集合名称
            point_id: 点ID（相当于主键）
            vector: 向量数据
            payload: 附加数据（相当于其他列）

        Returns:
            是否插入成功

        示例:
            util.insert_point(
                collection_name="users",
                point_id=1,
                vector=[0.1, 0.2, 0.3, 0.4],
                payload={"name": "张三", "age": 25, "city": "北京"}
            )
        """
        try:
            point = PointStruct(
                id=point_id,
                vector=vector,
                payload=payload or {}
            )
            self.client.upsert(
                collection_name=collection_name,
                points=[point]
            )
            print(f"[Qdrant] 插入数据成功: ID={point_id}, Payload={payload}")
            return True
        except Exception as e:
            print(f"[Qdrant] 插入数据失败: {e}")
            return False

    def insert_points_batch(self,
                            collection_name: str,
                            points: List[Dict[str, Any]]) -> bool:
        """
        批量插入数据（相当于 MySQL 的 INSERT ... VALUES (...), (...), ...）

        Args:
            collection_name: 集合名称
            points: 点列表，格式：[
                {"id": 1, "vector": [...], "payload": {...}},
                {"id": 2, "vector": [...], "payload": {...}}
            ]

        Returns:
            是否插入成功
        """
        try:
            point_structs = [
                PointStruct(
                    id=p["id"],
                    vector=p["vector"],
                    payload=p.get("payload", {})
                )
                for p in points
            ]
            self.client.upsert(
                collection_name=collection_name,
                points=point_structs
            )
            print(f"[Qdrant] 批量插入 {len(points)} 条数据成功")
            return True
        except Exception as e:
            print(f"[Qdrant] 批量插入失败: {e}")
            return False

    def get_point(self, collection_name: str, point_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID读取数据（相当于 MySQL 的 SELECT * FROM table WHERE id = ?）

        Args:
            collection_name: 集合名称
            point_id: 点ID

        Returns:
            点数据（包含 id, vector, payload），如果不存在返回 None
        """
        try:
            points = self.client.retrieve(
                collection_name=collection_name,
                ids=[point_id]
            )
            if points:
                point = points[0]
                result = {
                    "id": point.id,
                    "vector": point.vector,
                    "payload": point.payload
                }
                print(f"[Qdrant] 读取数据成功: {result}")
                return result
            else:
                print(f"[Qdrant] 未找到 ID={point_id} 的数据")
                return None
        except Exception as e:
            print(f"[Qdrant] 读取数据失败: {e}")
            return None

    def search_similar(self,
                       collection_name: str,
                       query_vector: List[float],
                       limit: int = 10) -> List[Dict[str, Any]]:
        """
        向量相似度搜索（Qdrant 的核心功能，MySQL 无直接对应）

        Args:
            collection_name: 集合名称
            query_vector: 查询向量
            limit: 返回结果数量

        Returns:
            相似的点列表，按相似度降序排列
        """
        try:
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit
            )
            output = []
            for result in results:
                output.append({
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload
                })
            print(f"[Qdrant] 相似度搜索完成，返回 {len(output)} 条结果")
            return output
        except Exception as e:
            print(f"[Qdrant] 相似度搜索失败: {e}")
            return []

    def delete_point(self, collection_name: str, point_id: int) -> bool:
        """
        删除数据（相当于 MySQL 的 DELETE FROM table WHERE id = ?）

        Args:
            collection_name: 集合名称
            point_id: 点ID

        Returns:
            是否删除成功
        """
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=[point_id]
            )
            print(f"[Qdrant] 删除数据成功: ID={point_id}")
            return True
        except Exception as e:
            print(f"[Qdrant] 删除数据失败: {e}")
            return False

    def list_collections(self) -> List[str]:
        """
        列出所有集合（相当于 MySQL 的 SHOW TABLES）

        Returns:
            集合名称列表
        """
        try:
            collections = self.client.get_collections()
            names = [col.name for col in collections.collections]
            print(f"[Qdrant] 共有 {len(names)} 个集合: {names}")
            return names
        except Exception as e:
            print(f"[Qdrant] 列出集合失败: {e}")
            return []

    def delete_collection(self, collection_name: str) -> bool:
        """
        删除集合（相当于 MySQL 的 DROP TABLE）

        Args:
            collection_name: 集合名称

        Returns:
            是否删除成功
        """
        try:
            self.client.delete_collection(collection_name=collection_name)
            print(f"[Qdrant] 集合 '{collection_name}' 删除成功")
            return True
        except Exception as e:
            print(f"[Qdrant] 删除集合失败: {e}")
            return False


# 测试代码
if __name__ == '__main__':
    # 1. 初始化（连接数据库）
    util = QdrantUtil(url="http://localhost:6333")

    # 2. 创建集合（相当于创建表）
    collection_name = "test_collection"
    util.create_collection(
        collection_name=collection_name,
        vector_size=4,  # 向量维度
        distance=Distance.DOT
    )

    # 3. 插入一条数据（相当于 INSERT）
    print("\n=== 插入数据 ===")
    util.insert_point(
        collection_name=collection_name,
        point_id=1,
        vector=[0.1, 0.2, 0.3, 0.4],
        payload={
            "name": "张三",
            "age": 25,
            "city": "北京"
        }
    )

    # 4. 读取数据（相当于 SELECT）
    print("\n=== 读取数据 ===")
    point = util.get_point(collection_name, point_id=1)
    if point:
        print(f"ID: {point['id']}")
        print(f"向量: {point['vector']}")
        print(f"负载: {point['payload']}")

    # 5. 批量插入（可选）
    print("\n=== 批量插入 ===")
    util.insert_points_batch(
        collection_name=collection_name,
        points=[
            {
                "id": 2,
                "vector": [0.5, 0.6, 0.7, 0.8],
                "payload": {"name": "李四", "age": 30, "city": "上海"}
            },
            {
                "id": 3,
                "vector": [0.9, 1.0, 1.1, 1.2],
                "payload": {"name": "王五", "age": 28, "city": "深圳"}
            }
        ]
    )

    # 6. 向量相似度搜索
    print("\n=== 向量搜索 ===")
    results = util.search_similar(
        collection_name=collection_name,
        query_vector=[0.1, 0.2, 0.3, 0.4],
        limit=3
    )
    for i, result in enumerate(results, 1):
        print(f"排名 {i}: ID={result['id']}, 得分={result['score']:.4f}, {result['payload']}")

    # 7. 列出所有集合
    print("\n=== 列出集合 ===")
    util.list_collections()

    # 8. 清理（可选）
    # util.delete_collection(collection_name)