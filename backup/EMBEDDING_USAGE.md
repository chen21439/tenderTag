# 向量化集成使用说明

## 1. 安装依赖

```bash
pip install FlagEmbedding
```

## 2. 快速开始

### 2.1 初始化向量化工具

```python
from app.utils.db.qdrant.EmbeddingUtil import get_embedding_util

# 初始化 bge-m3（单例模式）
embedding_util = get_embedding_util(
    model_name='BAAI/bge-m3',
    use_fp16=True,
    device='cpu'  # 如果有GPU: device='cuda'
)
```

### 2.2 初始化 Qdrant 集合（混合向量）

```python
from app.utils.db.qdrant import QdrantUtil

util = QdrantUtil(url="http://localhost:6333")

# 创建支持混合向量的集合
util.init_tender_collection(use_hybrid=True)
```

### 2.3 向量化并导入数据

```python
from insert_tender_chunks_with_embedding import insert_tender_chunks_from_memory_v2

# 提取 PDF 内容
extractor = PDFContentExtractor("your.pdf")
tables_result = extractor.extract_all_tables()
paragraphs_result = extractor.extract_all_paragraphs()

# 向量化并导入
chunk_count = insert_tender_chunks_from_memory_v2(
    qdrant_util=util,
    doc_id="ORDOS-2025-0001",
    tables=tables_result['tables'],
    paragraphs=paragraphs_result['paragraphs'],
    embedding_util=embedding_util,  # 使用真实向量化
    metadata={
        "region": "内蒙古-鄂尔多斯",
        "agency": "鄂尔多斯市政府",
        "published_at_ts": 1706601600
    }
)

print(f"成功导入 {chunk_count} 个 chunks")
```

### 2.4 混合搜索（语义 + 关键词）

```python
# 向量化查询
query = "网站集约化平台升级改造"
dense_vec, sparse_vec = embedding_util.encode_query(query)

# 混合搜索
results = util.client.search(
    collection_name="tender_chunks",
    query_vector=("dense", dense_vec),  # 稠密向量（语义）
    query_sparse_vector=sparse_vec,      # 稀疏向量（关键词）
    limit=10
)

for result in results:
    print(f"相似度: {result.score:.4f}")
    print(f"内容: {result.payload['content']}")
```

## 3. 向量化字段说明

**只对 `content` 字段向量化：**

- ✅ **段落**: `content` 字段（原文）
- ✅ **表格行**: `content` 字段（格式："列名1: 值1 | 列名2: 值2 | ..."）

**其他字段不向量化（存在 payload 中）：**

- `doc_id` - 文档ID（精确过滤）
- `chunk_type` - 块类型（paragraph / table_row）
- `region` - 地区
- `agency` - 机构
- `published_at_ts` - 发布时间戳
- `page` - 页码
- `bbox` - 位置信息
- `table_id`, `row_id` - 表格行信息

## 4. 重复内容去重机制

**自动去重**：`EmbeddingUtil` 内置缓存机制

- 相同内容只计算一次向量
- 使用 SHA1 hash 作为缓存键
- 进程内缓存（可扩展为 Redis/SQLite）

查看缓存统计：

```python
stats = embedding_util.get_cache_stats()
print(f"缓存大小: {stats['cache_size']}")
print(f"命中率: {stats['hit_rate']}")
```

## 5. 向量配置说明

### bge-m3（推荐）

- **稠密向量**: 1024 维（语义相似度）
- **稀疏向量**: 可变维度（关键词匹配，类似 BM25）
- **优势**: 混合检索，语义+关键词双保险
- **适用**: 中文招标文件检索

### bge-base-zh（备选）

- **稠密向量**: 768 维
- **优势**: 更轻量，速度快
- **适用**: 纯语义搜索

切换方法：

```python
# 使用 bge-base-zh
embedding_util = get_embedding_util(
    model_name='BAAI/bge-base-zh-v1.5',
    device='cpu'
)

# 创建只支持稠密向量的集合
util.init_tender_collection(use_hybrid=False)
```

## 6. 性能优化

### 6.1 批量向量化

```python
# 批量处理比逐个处理快 10 倍以上
texts = ["文本1", "文本2", ..., "文本100"]
vectors = embedding_util.encode_batch(texts)
```

### 6.2 GPU 加速

```python
# 有 GPU 时使用 CUDA
embedding_util = get_embedding_util(
    model_name='BAAI/bge-m3',
    use_fp16=True,
    device='cuda'  # GPU 加速
)
```

### 6.3 缓存复用

默认开启，相同内容不重复计算：

```python
# 第一次计算（约 10ms）
vec1 = embedding_util.encode_document("这是一段文本")

# 第二次直接从缓存读取（约 0.01ms）
vec2 = embedding_util.encode_document("这是一段文本")
```

## 7. 完整示例

运行测试脚本：

```bash
python test_embedding_integration.py
```

测试流程：
1. 加载 bge-m3 模型
2. 创建 Qdrant 集合
3. 提取 PDF 内容
4. 向量化并导入
5. 测试混合搜索

## 8. 常见问题

**Q1: 模型下载很慢怎么办？**

A: 使用镜像源
```bash
HF_ENDPOINT=https://hf-mirror.com python your_script.py
```

**Q2: 内存不够怎么办？**

A:
- 使用 `use_fp16=True`（减少一半内存）
- 使用 `bge-small-zh`（更小的模型）
- 减小 `batch_size`

**Q3: 如何持久化缓存？**

A: 修改 `EmbeddingUtil._cache` 使用 SQLite/Redis：

```python
import sqlite3

class EmbeddingUtil:
    def __init__(self, ...):
        self.cache_db = sqlite3.connect('embedding_cache.db')
        # ...
```

**Q4: 如何过滤搜索？**

A: 使用 `query_filter`：

```python
from qdrant_client.models import Filter, FieldCondition, MatchValue

results = util.client.search(
    collection_name="tender_chunks",
    query_vector=("dense", dense_vec),
    query_filter=Filter(
        must=[
            FieldCondition(key="doc_id", match=MatchValue(value="ORDOS-2025-0001")),
            FieldCondition(key="chunk_type", match=MatchValue(value="paragraph"))
        ]
    ),
    limit=10
)
```

## 9. 下一步

- [ ] 集成 bge-reranker 做重排（提高精度）
- [ ] 实现增量更新（避免重复导入）
- [ ] 添加删除功能（按 doc_id 删除）
- [ ] 实现混合检索权重调优
