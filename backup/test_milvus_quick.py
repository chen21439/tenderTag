"""
Milvus 快速验证脚本
测试基本的存储和搜索功能
"""
import sys
from pathlib import Path

# 添加项目根目录到 sys.path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.utils.db.milvus import MilvusUtil
from app.utils.db.qdrant import get_embedding_util


def main():
    print("="*80)
    print("Milvus 功能验证测试")
    print("="*80)

    # 1. 初始化 Milvus
    print("\n[1/5] 初始化 Milvus...")
    milvus = MilvusUtil(host="localhost", port="19530")

    # 2. 创建集合
    print("\n[2/5] 创建测试集合...")
    success = milvus.create_collection(
        collection_name="tender_test",
        dim=1024,  # bge-m3 维度
        drop_old=True
    )

    if not success:
        print("创建集合失败,退出测试")
        return

    # 3. 初始化向量化模型
    print("\n[3/5] 初始化 bge-m3 模型...")
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  使用设备: {device}")

    embedding_util = get_embedding_util(
        model_name='BAAI/bge-m3',
        use_fp16=True,
        device=device
    )

    # 4. 准备测试数据并向量化
    print("\n[4/5] 准备测试数据...")
    test_chunks = [
        {
            "chunk_type": "paragraph",
            "content": "鄂尔多斯市政府网站群集约化平台升级改造项目招标公告",
            "page": 1
        },
        {
            "chunk_type": "paragraph",
            "content": "项目预算总金额为100万元人民币，采购内容包括平台开发和运维服务",
            "page": 2
        },
        {
            "chunk_type": "table_row",
            "content": "序号: 1 | 项目名称: 网站集约化平台 | 预算金额: 100万元",
            "page": 3
        },
        {
            "chunk_type": "paragraph",
            "content": "投标截止时间为2025年1月31日下午17:00",
            "page": 4
        }
    ]

    print(f"  测试数据: {len(test_chunks)} 条")

    # 向量化文本
    print(f"  正在向量化...")
    texts = [chunk["content"] for chunk in test_chunks]
    vectors = embedding_util.encode_batch(texts, use_cache=False)

    # 提取稠密向量
    embeddings = [dense_vec for dense_vec, _, _ in vectors]
    print(f"  ✓ 向量化完成 (维度: {len(embeddings[0])})")

    # 5. 插入数据
    print("\n[5/5] 插入数据到 Milvus...")
    count = milvus.insert_data(
        doc_id="ORDOS-TEST-001",
        chunks=test_chunks,
        embeddings=embeddings
    )

    if count == 0:
        print("插入失败,退出测试")
        milvus.close()
        return

    # 6. 查询统计
    print("\n" + "="*80)
    print("集合统计信息")
    print("="*80)
    stats = milvus.get_stats()
    print(f"集合名称: {stats.get('collection_name')}")
    print(f"数据条数: {stats.get('num_entities')}")

    # 7. 测试搜索
    print("\n" + "="*80)
    print("测试搜索功能")
    print("="*80)

    # 向量化查询
    query = "网站集约化平台预算"
    print(f"\n查询: '{query}'")
    print(f"正在向量化查询...")

    dense_vec, _ = embedding_util.encode_query(query)

    # 搜索
    results = milvus.search(query_embedding=dense_vec, top_k=3)

    print(f"\n搜索结果 (Top-{len(results)}):")
    for i, result in enumerate(results, 1):
        print(f"\n[{i}] 相似度: {result['distance']:.4f}")
        print(f"    文档ID: {result['doc_id']}")
        print(f"    类型: {result['chunk_type']}, 页码: {result['page']}")
        print(f"    内容: {result['content'][:100]}...")

    # 8. 关闭连接
    print("\n" + "="*80)
    milvus.close()
    print("测试完成!")
    print("="*80)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()