"""
使用 Ollama API 的向量化工具类
适用于已经通过 Ollama 下载的模型
"""
import hashlib
import requests
from typing import Dict, Tuple, Optional, List
from qdrant_client.models import SparseVector


class OllamaEmbeddingUtil:
    """
    基于 Ollama API 的向量化工具

    注意：Ollama 的 bge-m3 只提供稠密向量，没有稀疏向量
    """

    def __init__(self, model_name: str = 'bge-m3', ollama_url: str = 'http://localhost:11434'):
        """
        初始化

        Args:
            model_name: Ollama 中的模型名称
            ollama_url: Ollama 服务地址
        """
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.embed_url = f"{ollama_url}/api/embeddings"

        print(f"[Embedding] 使用 Ollama API")
        print(f"[Embedding]   模型: {model_name}")
        print(f"[Embedding]   地址: {ollama_url}")

        # 测试连接
        try:
            response = requests.post(
                self.embed_url,
                json={"model": model_name, "prompt": "test"},
                timeout=5
            )
            if response.status_code == 200:
                vec_dim = len(response.json()['embedding'])
                print(f"[Embedding] OK 连接成功，向量维度: {vec_dim}")
            else:
                print(f"[Embedding] FAILED 连接失败: {response.status_code}")
        except Exception as e:
            print(f"[Embedding] FAILED 连接失败: {e}")

        # 缓存
        self._cache = {}
        self.cache_hits = 0
        self.cache_misses = 0

    def _compute_hash(self, text: str) -> str:
        """计算文本 hash"""
        normalized = text.strip()
        return hashlib.sha1(normalized.encode('utf-8')).hexdigest()

    def _call_ollama_embed(self, text: str) -> list:
        """调用 Ollama API 获取向量"""
        response = requests.post(
            self.embed_url,
            json={
                "model": self.model_name,
                "prompt": text
            },
            timeout=30
        )

        if response.status_code == 200:
            return response.json()['embedding']
        else:
            raise Exception(f"Ollama API 失败: {response.status_code} {response.text}")

    def encode_document(self, text: str, use_cache: bool = True) -> Tuple[list, None, str]:
        """
        向量化文档（只返回稠密向量）

        Returns:
            (dense_vector, None, content_hash)
            注意：Ollama 不提供稀疏向量，返回 None
        """
        content_hash = self._compute_hash(text)

        # 检查缓存
        if use_cache and content_hash in self._cache:
            self.cache_hits += 1
            dense = self._cache[content_hash]
            return dense, None, content_hash

        # 调用 Ollama
        self.cache_misses += 1
        dense_vector = self._call_ollama_embed(text)

        # 缓存
        if use_cache:
            self._cache[content_hash] = dense_vector

        return dense_vector, None, content_hash

    def encode_query(self, query: str) -> Tuple[list, None]:
        """
        向量化查询

        Returns:
            (dense_vector, None)
        """
        dense_vector = self._call_ollama_embed(query)
        return dense_vector, None

    def encode_batch(self, texts: List[str], use_cache: bool = True) -> List[Tuple[list, None, str]]:
        """
        批量向量化（Ollama 暂不支持批量，逐个调用）

        Returns:
            [(dense_vector, None, content_hash), ...]
        """
        results = []
        for text in texts:
            dense, _, hash_val = self.encode_document(text, use_cache)
            results.append((dense, None, hash_val))
        return results

    def get_cache_stats(self) -> Dict:
        """获取缓存统计"""
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


# 单例
_ollama_embedding_util_instance: Optional[OllamaEmbeddingUtil] = None


def get_ollama_embedding_util(model_name: str = 'bge-m3',
                               ollama_url: str = 'http://localhost:11434') -> OllamaEmbeddingUtil:
    """获取 Ollama 向量化工具单例"""
    global _ollama_embedding_util_instance

    if _ollama_embedding_util_instance is None:
        _ollama_embedding_util_instance = OllamaEmbeddingUtil(
            model_name=model_name,
            ollama_url=ollama_url
        )

    return _ollama_embedding_util_instance
