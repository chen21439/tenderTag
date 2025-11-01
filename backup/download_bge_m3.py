"""
下载 bge-m3 模型（PyTorch 格式）
"""
from FlagEmbedding import BGEM3FlagModel

print("开始下载 bge-m3 模型...")
print("目标路径: E:\\models\\bge-m3")

# 下载到指定路径
model = BGEM3FlagModel(
    'BAAI/bge-m3',
    cache_folder=r'E:\models',  # 下载到这里
    use_fp16=True
)

print("✓ 下载完成!")
print(f"模型路径: E:\\models\\bge-m3")

# 测试
text = "这是一个测试"
result = model.encode([text], return_dense=True, return_sparse=True)
print(f"\n测试成功:")
print(f"  稠密向量维度: {len(result['dense_vecs'][0])}")
print(f"  稀疏向量维度: {len(result['lexical_weights'][0]['indices'])}")
