"""
向量化工具类 - 基于 bge-m3 模型
支持稠密+稀疏混合向量化，并提供内容去重缓存机制
"""
import hashlib
from typing import Dict, Tuple, Optional
from qdrant_client.models import SparseVector


class EmbeddingUtil:
    """
    向量化工具类

    功能：
    1. 使用 bge-m3 模型生成稠密+稀疏向量
    2. 内容去重：相同内容只计算一次向量
    3. 支持文档和查询两种模式
    """

    def __init__(self, model_name: str = 'BAAI/bge-m3', use_fp16: bool = True, device: str = 'cpu'):
        """
        初始化向量化工具

        Args:
            model_name: 模型名称（默认 bge-m3）
            use_fp16: 是否使用 fp16（节省显存，默认 True）
            device: 设备（'cpu' 或 'cuda'）
        """
        try:
            from FlagEmbedding import BGEM3FlagModel

            print(f"[Embedding] 正在加载模型 {model_name}...")
            print(f"[Embedding]   设备: {device}")
            print(f"[Embedding]   FP16: {use_fp16}")

            self.model = BGEM3FlagModel(
                model_name,
                use_fp16=use_fp16,
                device=device
            )

            print(f"[Embedding] OK 模型加载成功")

            # 内容缓存：hash -> (dense_vector, sparse_vector)
            self._cache = {}
            self.cache_hits = 0
            self.cache_misses = 0

        except ImportError as e:
            print(f"[Embedding] FAILED 模型加载失败: {e}")
            print(f"[Embedding] 提示: 请先安装依赖")
            print(f"[Embedding]   pip install FlagEmbedding")
            raise

    def _compute_hash(self, text: str) -> str:
        """
        计算文本的 hash（用于去重）

        Args:
            text: 输入文本

        Returns:
            SHA1 hash 字符串
        """
        normalized = text.strip()
        return hashlib.sha1(normalized.encode('utf-8')).hexdigest()

    def _safe_convert_sparse(self, sparse_data: dict) -> Tuple[list, list]:
        """
        安全地将稀疏向量数据转换为列表

        Args:
            sparse_data: 稀疏向量数据字典，包含 'indices' 和 'values'

        Returns:
            (indices_list, values_list) - 两个列表，如果数据无效则返回空列表
        """
        indices = []
        values = []

        if sparse_data and isinstance(sparse_data, dict):
            idx_data = sparse_data.get('indices')
            val_data = sparse_data.get('values')

            # 处理 indices
            if idx_data is not None:
                # 如果是 numpy 数组或 tensor，转换为列表
                if hasattr(idx_data, 'tolist'):
                    indices = idx_data.tolist()
                # 如果是列表或元组，直接转换
                elif isinstance(idx_data, (list, tuple)):
                    indices = list(idx_data)
                # 如果是整数（错误情况），返回空列表
                # (不尝试迭代，避免 TypeError)

            # 处理 values
            if val_data is not None:
                if hasattr(val_data, 'tolist'):
                    values = val_data.tolist()
                elif isinstance(val_data, (list, tuple)):
                    values = list(val_data)

        return indices, values

    def encode_document(self, text: str, use_cache: bool = True) -> Tuple[list, SparseVector, str]:
        """
        向量化文档内容（用于入库）

        Args:
            text: 文档文本
            use_cache: 是否使用缓存（默认 True）

        Returns:
            (dense_vector, sparse_vector, content_hash)
            - dense_vector: 稠密向量（1024维，list）
            - sparse_vector: 稀疏向量（SparseVector 对象）
            - content_hash: 内容 hash（用于去重）
        """
        content_hash = self._compute_hash(text)

        # 检查缓存
        if use_cache and content_hash in self._cache:
            self.cache_hits += 1
            dense, sparse = self._cache[content_hash]
            return dense, sparse, content_hash

        # 计算向量
        self.cache_misses += 1
        result = self.model.encode(
            [text],  # batch 输入
            batch_size=1,
            max_length=512,  # 最大长度（bge-m3 支持 8192，但 512 够用且快）
            return_dense=True,
            return_sparse=True,
            return_colbert_vecs=False  # 不需要 ColBERT 向量
        )

        # 提取稠密向量（1024维）
        dense_vector = result['dense_vecs'][0].tolist()

        # 提取稀疏向量（使用安全转换）
        sparse_data = result['lexical_weights'][0]  # bge-m3 的稀疏向量字段
        indices, values = self._safe_convert_sparse(sparse_data)

        sparse_vector = SparseVector(
            indices=indices,
            values=values
        )

        # 缓存结果
        if use_cache:
            self._cache[content_hash] = (dense_vector, sparse_vector)

        return dense_vector, sparse_vector, content_hash

    def encode_query(self, query: str) -> Tuple[list, SparseVector]:
        """
        向量化查询内容（用于搜索）

        Args:
            query: 查询文本

        Returns:
            (dense_vector, sparse_vector)
        """
        result = self.model.encode_queries(
            [query],
            batch_size=1,
            max_length=256,  # 查询通常较短
            return_dense=True,
            return_sparse=True
        )

        dense_vector = result['dense_vecs'][0].tolist()
        sparse_data = result['lexical_weights'][0]

        # 提取稀疏向量（使用安全转换）
        indices, values = self._safe_convert_sparse(sparse_data)

        sparse_vector = SparseVector(
            indices=indices,
            values=values
        )

        return dense_vector, sparse_vector

    def encode_batch(self, texts: list, use_cache: bool = True) -> list:
        """
        批量向量化文档（更高效）

        Args:
            texts: 文本列表
            use_cache: 是否使用缓存

        Returns:
            [(dense_vector, sparse_vector, content_hash), ...]
        """
        results = []
        texts_to_encode = []
        text_indices = []

        # 第一遍：检查缓存
        for i, text in enumerate(texts):
            content_hash = self._compute_hash(text)

            if use_cache and content_hash in self._cache:
                self.cache_hits += 1
                dense, sparse = self._cache[content_hash]
                results.append((dense, sparse, content_hash))
            else:
                # 需要计算
                texts_to_encode.append(text)
                text_indices.append(i)
                results.append(None)  # 占位

        # 第二遍：批量计算未缓存的
        if texts_to_encode:
            self.cache_misses += len(texts_to_encode)

            batch_result = self.model.encode(
                texts_to_encode,
                batch_size=32,  # 批量大小
                max_length=512,
                return_dense=True,
                return_sparse=True,
                return_colbert_vecs=False
            )

            # 填充结果
            for idx, original_idx in enumerate(text_indices):
                text = texts_to_encode[idx]
                content_hash = self._compute_hash(text)

                dense_vector = batch_result['dense_vecs'][idx].tolist()
                sparse_data = batch_result['lexical_weights'][idx]

                # 提取稀疏向量（使用安全转换）
                indices, values = self._safe_convert_sparse(sparse_data)

                sparse_vector = SparseVector(
                    indices=indices,
                    values=values
                )

                # 缓存
                if use_cache:
                    self._cache[content_hash] = (dense_vector, sparse_vector)

                results[original_idx] = (dense_vector, sparse_vector, content_hash)

        return results

    def get_cache_stats(self) -> Dict:
        """
        获取缓存统计信息

        Returns:
            缓存统计字典
        """
        total = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total if total > 0 else 0

        return {
            "cache_size": len(self._cache),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "total_queries": total,
            "hit_rate": f"{hit_rate:.2%}"
        }

    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0
        print(f"[Embedding] 缓存已清空")


# 单例模式（可选）
_embedding_util_instance: Optional[EmbeddingUtil] = None


def get_embedding_util(model_name: str = 'BAAI/bge-m3',
                       use_fp16: bool = True,
                       device: str = 'cpu') -> EmbeddingUtil:
    """
    获取全局向量化工具实例（单例）

    Args:
        model_name: 模型名称
        use_fp16: 是否使用 fp16
        device: 设备

    Returns:
        EmbeddingUtil 实例
    """
    global _embedding_util_instance

    if _embedding_util_instance is None:
        _embedding_util_instance = EmbeddingUtil(
            model_name=model_name,
            use_fp16=use_fp16,
            device=device
        )

    return _embedding_util_instance
