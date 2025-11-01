"""
测试两种向量化方案

方案1: 使用 FlagEmbedding（需要重新下载模型）
方案2: 使用 Ollama API（使用现有模型）
"""

print("=" * 80)
print("向量化方案选择")
print("=" * 80)
print("\n【方案1】使用 FlagEmbedding + PyTorch 模型")
print("  优点: 速度快、支持批量、支持稠密+稀疏混合向量")
print("  缺点: 需要重新下载模型（约 2GB）")
print("  适用: 生产环境、大批量数据")

print("\n【方案2】使用 Ollama API")
print("  优点: 使用现有模型、无需重新下载")
print("  缺点: 速度较慢、不支持批量、只有稠密向量")
print("  适用: 快速测试、小批量数据")

print("\n" + "=" * 80)
choice = input("请选择方案 (1/2): ").strip()

if choice == "1":
    print("\n>>> 你选择了方案1: FlagEmbedding")
    print("\n步骤1: 安装依赖")
    print("  pip install FlagEmbedding")

    print("\n步骤2: 下载模型")
    print("  python download_bge_m3.py")
    print("  （会下载到 E:\\models\\bge-m3）")

    print("\n步骤3: 使用模型")
    print("  示例代码:")
    print("""
    from app.utils.db.qdrant.EmbeddingUtil import get_embedding_util

    embedding_util = get_embedding_util(
        model_name='BAAI/bge-m3',  # 会自动从缓存加载
        use_fp16=True,
        device='cpu'
    )

    # 向量化
    dense, sparse, hash_val = embedding_util.encode_document("你的文本")
    print(f"稠密维度: {len(dense)}, 稀疏维度: {len(sparse.indices)}")
    """)

elif choice == "2":
    print("\n>>> 你选择了方案2: Ollama API")
    print("\n步骤1: 确保 Ollama 服务运行中")
    print("  检查: http://localhost:11434")

    print("\n步骤2: 测试连接")
    print("  运行以下代码:")

    try:
        from app.utils.db.qdrant.OllamaEmbeddingUtil import get_ollama_embedding_util

        print("\n>>> 正在测试 Ollama 连接...")
        embedding_util = get_ollama_embedding_util(
            model_name='bge-m3',
            ollama_url='http://localhost:11434'
        )

        print("\n>>> 测试向量化...")
        text = "这是一个测试文本"
        dense, sparse, hash_val = embedding_util.encode_document(text)

        print(f"\n✓ 测试成功!")
        print(f"  文本: {text}")
        print(f"  向量维度: {len(dense)}")
        print(f"  Content Hash: {hash_val[:16]}...")

        print("\n步骤3: 在你的代码中使用")
        print("""
from app.utils.db.qdrant.OllamaEmbeddingUtil import get_ollama_embedding_util

embedding_util = get_ollama_embedding_util(
    model_name='bge-m3',
    ollama_url='http://localhost:11434'
)

# 向量化
dense, sparse, hash_val = embedding_util.encode_document("你的文本")
print(f"维度: {len(dense)}")
        """)

        print("\n注意: Ollama 方案只支持稠密向量，创建集合时需要:")
        print("  util.init_tender_collection(use_hybrid=False)  # 关闭混合向量")

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        print("\n可能的原因:")
        print("  1. Ollama 服务未启动")
        print("  2. 模型 'bge-m3' 未安装")
        print("  3. 端口 11434 被占用")

else:
    print("\n无效选择，请输入 1 或 2")
