"""
Milvus 持久化类

负责将单元格数据向量化并存入 Milvus 数据库
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import sys


class MilvusPersistence:
    """
    Milvus 持久化处理器

    功能：
    1. 将单元格数据 (cells) 转换为 chunks
    2. 使用 bge-m3 模型进行向量化
    3. 批量写入 Milvus 数据库
    """

    def __init__(self,
                 host: str = "localhost",
                 port: str = "19530",
                 collection_name: str = "pdf",
                 embedding_model: str = "BAAI/bge-m3",
                 vector_dim: int = 1024,
                 device: str = "auto"):
        """
        初始化 Milvus 持久化器

        Args:
            host: Milvus 服务器地址 (默认 localhost)
            port: Milvus 端口 (默认 19530)
            collection_name: 集合名称 (默认 "pdf")
            embedding_model: 向量化模型名称 (默认 BAAI/bge-m3)
            vector_dim: 向量维度 (默认 1024)
            device: 计算设备 ('auto', 'cuda', 'cpu')
        """
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.vector_dim = vector_dim
        self.device = device

        self.milvus = None
        self.embedding_util = None

    def _init_milvus(self):
        """初始化 Milvus 连接"""
        if self.milvus is not None:
            return

        try:
            # 动态导入（支持包导入和脚本直接运行）
            try:
                from ...db.milvus import MilvusUtil
            except ImportError:
                # 添加项目根目录到 sys.path
                project_root = Path(__file__).resolve().parent.parent.parent.parent
                if str(project_root) not in sys.path:
                    sys.path.insert(0, str(project_root))
                from app.utils.db.milvus import MilvusUtil

            self.milvus = MilvusUtil(host=self.host, port=self.port)
            print(f"[向量库] ✓ 已连接到 Milvus ({self.host}:{self.port})")

        except Exception as e:
            print(f"[向量库] ✗ Milvus 连接失败: {e}")
            raise

    def _init_embedding(self):
        """初始化向量化模型"""
        if self.embedding_util is not None:
            return

        try:
            # 动态导入
            try:
                from ...db.qdrant import get_embedding_util
            except ImportError:
                project_root = Path(__file__).resolve().parent.parent.parent.parent
                if str(project_root) not in sys.path:
                    sys.path.insert(0, str(project_root))
                from app.utils.db.qdrant import get_embedding_util

            import torch

            # 自动选择设备
            if self.device == "auto":
                self.device = "cuda" if torch.cuda.is_available() else "cpu"

            print(f"[向量库] 正在加载模型: {self.embedding_model} ({self.device})...")
            self.embedding_util = get_embedding_util(
                model_name=self.embedding_model,
                use_fp16=True,
                device=self.device
            )
            print(f"[向量库] ✓ 模型加载完成")

        except Exception as e:
            print(f"[向量库] ✗ 模型加载失败: {e}")
            raise

    def _ensure_collection(self, drop_old: bool = False):
        """
        确保集合存在

        Args:
            drop_old: 是否删除旧集合并重新创建 (默认 False，追加数据)
        """
        success = self.milvus.create_collection(
            collection_name=self.collection_name,
            dim=self.vector_dim,
            drop_old=drop_old
        )

        if not success:
            raise RuntimeError(f"创建集合 {self.collection_name} 失败")

        print(f"[向量库] ✓ 集合 '{self.collection_name}' 已就绪")

    def _cells_to_chunks(self, cells: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        将单元格数据转换为 chunks 格式

        Args:
            cells: 单元格列表

        Returns:
            chunks 列表
        """
        chunks = []
        for cell in cells:
            # 优先使用 cell_value_with_context (包含上下文信息)
            content = cell.get("cell_value_with_context",
                             cell.get("cell_value_norm", ""))

            if not content or not content.strip():
                continue

            chunks.append({
                "chunk_type": "table_cell",
                "content": content,
                "page": cell.get("page", 1)
            })

        return chunks

    def save_cells(self,
                   doc_id: str,
                   cells: List[Dict[str, Any]],
                   drop_old: bool = False) -> int:
        """
        将单元格数据保存到 Milvus

        Args:
            doc_id: 文档ID (如 task_id)
            cells: 单元格数据列表
            drop_old: 是否删除旧集合并重新创建 (默认 False，追加数据)

        Returns:
            成功写入的数据条数
        """
        if not cells:
            print("[向量库] ✗ 没有单元格数据需要保存")
            return 0

        try:
            print(f"\n[向量库] 准备写入 Milvus...")
            print(f"[向量库]   文档ID: {doc_id}")
            print(f"[向量库]   单元格数: {len(cells)}")

            # 1. 初始化 Milvus
            self._init_milvus()

            # 2. 确保集合存在
            self._ensure_collection(drop_old=drop_old)

            # 3. 初始化向量化模型
            self._init_embedding()

            # 4. 转换为 chunks
            chunks = self._cells_to_chunks(cells)
            if not chunks:
                print("[向量库] ✗ 没有有效内容需要向量化")
                return 0

            print(f"[向量库]   有效 chunks: {len(chunks)}")

            # 5. 向量化
            print(f"[向量库] 正在向量化...")
            texts = [chunk["content"] for chunk in chunks]
            vectors = self.embedding_util.encode_batch(texts, use_cache=False)
            embeddings = [dense_vec for dense_vec, _, _ in vectors]

            # 6. 写入 Milvus
            print(f"[向量库] 正在写入数据...")
            count = self.milvus.insert_data(
                doc_id=doc_id,
                chunks=chunks,
                embeddings=embeddings
            )

            if count > 0:
                print(f"[向量库] ✓ 成功写入 {count} 条数据")

                # 查询统计
                stats = self.milvus.get_stats()
                print(f"[向量库] 集合统计: {stats.get('num_entities', 0)} 条记录")
            else:
                print("[向量库] ✗ 写入失败")

            return count

        except Exception as e:
            print(f"[向量库] ✗ 保存失败: {e}")
            import traceback
            traceback.print_exc()
            return 0

    def close(self):
        """关闭 Milvus 连接"""
        if self.milvus:
            self.milvus.close()
            self.milvus = None
            print("[向量库] ✓ 连接已关闭")

    def __enter__(self):
        """支持 with 语句"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持 with 语句"""
        self.close()