"""
持久化模块

提供向量数据库（Milvus）的数据导入功能
"""

from .milvus_persistence import MilvusPersistence

__all__ = ["MilvusPersistence"]