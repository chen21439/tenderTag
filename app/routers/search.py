"""
搜索路由 - 支持关键字向量搜索
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
import os

router = APIRouter(tags=["search"])


# ============================================================
# 请求/响应模型
# ============================================================

class SearchRequest(BaseModel):
    """搜索请求"""
    keywords: List[str] = Field(..., description="关键字数组", min_items=1, example=["项目", "预算", "网站"])
    top_k: int = Field(default=5, description="返回结果数量", ge=1, le=100)
    collection_name: Optional[str] = Field(default="pdf", description="集合名称")


class SearchResultItem(BaseModel):
    """搜索结果项"""
    id: int = Field(..., description="记录ID")
    distance: float = Field(..., description="相似度距离（越小越相似）")
    doc_id: str = Field(..., description="文档ID")
    chunk_type: str = Field(..., description="内容类型")
    content: str = Field(..., description="内容文本")
    page: int = Field(..., description="页码")
    insert_time: int = Field(..., description="插入时间戳(毫秒)")


class SearchResponse(BaseModel):
    """搜索响应"""
    success: bool = Field(..., description="是否成功")
    query: str = Field(..., description="查询文本（关键字拼接）")
    total: int = Field(..., description="返回结果数量")
    results: List[SearchResultItem] = Field(..., description="搜索结果列表")


# ============================================================
# 全局状态（单例模式）
# ============================================================

_milvus_instance = None


def get_milvus_client():
    """获取 Milvus 客户端（单例）"""
    global _milvus_instance

    if _milvus_instance is None:
        from app.utils.db.milvus.MilvusUtil import MilvusUtil

        # 从环境变量读取配置
        host = os.getenv("MILVUS_HOST", "localhost")
        port = os.getenv("MILVUS_PORT", "19530")

        _milvus_instance = MilvusUtil(host=host, port=port)

    return _milvus_instance


# ============================================================
# API 路由
# ============================================================

@router.post("/search", response_model=SearchResponse, summary="关键字向量搜索")
async def search_by_keywords(request: SearchRequest):
    """
    根据关键字数组进行向量搜索

    ## 功能说明
    - 接收关键字数组，自动进行向量化
    - 在 Milvus 中进行相似度搜索
    - 返回 Top-K 最相关的结果

    ## 参数说明
    - **keywords**: 关键字列表（至少1个）
    - **top_k**: 返回结果数量（1-100，默认5）
    - **collection_name**: 集合名称（默认 "pdf"）

    ## 示例
    ```json
    {
        "keywords": ["项目", "预算", "网站"],
        "top_k": 10,
        "collection_name": "pdf"
    }
    ```

    ## 返回
    - 相似度最高的 Top-K 条记录
    - 按相似度排序（distance 越小越相似）
    """
    try:
        # 1. 获取 Milvus 客户端
        milvus = get_milvus_client()

        # 2. 选择集合
        if not milvus.collection or milvus.collection.name != request.collection_name:
            # 加载指定集合
            from pymilvus import Collection
            milvus.collection = Collection(request.collection_name)
            print(f"[Search API] 切换到集合: {request.collection_name}")

        # 3. 获取向量化工具（使用全局单例，避免重复加载模型）
        from app.utils.db.qdrant import get_embedding_util
        embedding_util = get_embedding_util()

        # 4. 执行搜索
        results = milvus.search_by_keywords(
            keywords=request.keywords,
            top_k=request.top_k,
            embedding_util=embedding_util
        )

        # 5. 构造响应
        query_text = " ".join(request.keywords)
        search_results = [
            SearchResultItem(
                id=r["id"],
                distance=r["distance"],
                doc_id=r["doc_id"],
                chunk_type=r["chunk_type"],
                content=r["content"],
                page=r["page"],
                insert_time=r["insert_time"]
            )
            for r in results
        ]

        return SearchResponse(
            success=True,
            query=query_text,
            total=len(search_results),
            results=search_results
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"搜索失败: {str(e)}"
        )


@router.get("/search", response_model=SearchResponse, summary="关键字向量搜索 (GET)")
async def search_by_keywords_get(
    keywords: List[str] = Query(..., description="关键字列表", min_items=1),
    top_k: int = Query(default=5, description="返回结果数量", ge=1, le=100),
    collection_name: str = Query(default="pdf", description="集合名称")
):
    """
    根据关键字数组进行向量搜索（GET 方法）

    ## 使用方式
    ```
    GET /api/search?keywords=项目&keywords=预算&keywords=网站&top_k=10
    ```

    ## 参数说明
    - **keywords**: 关键字（可多次传递）
    - **top_k**: 返回结果数量（默认5）
    - **collection_name**: 集合名称（默认 "pdf"）
    """
    # 复用 POST 方法的逻辑
    request = SearchRequest(
        keywords=keywords,
        top_k=top_k,
        collection_name=collection_name
    )
    return await search_by_keywords(request)


@router.get("/stats", summary="获取集合统计信息")
async def get_collection_stats(collection_name: str = Query(default="pdf", description="集合名称")):
    """
    获取 Milvus 集合的统计信息

    ## 返回信息
    - 集合名称
    - 数据条数
    - 加载状态
    """
    try:
        milvus = get_milvus_client()

        # 切换集合
        if not milvus.collection or milvus.collection.name != collection_name:
            from pymilvus import Collection
            milvus.collection = Collection(collection_name)

        stats = milvus.get_stats()

        return {
            "success": True,
            "collection_name": collection_name,
            "stats": stats
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取统计信息失败: {str(e)}"
        )