# 向量化功能使用指南

## 📋 概述

已将向量化功能完全集成到 `PDFContentExtractor` 中,并创建了独立的索引器和搜索器类。

## 📁 新增文件

```
app/utils/db/qdrant/
├── TenderIndexer.py      # 招标文档索引器(写入)
├── TenderSearcher.py     # 招标文档搜索器(搜索)
└── __init__.py           # 更新导出

app/utils/unTaggedPDF/
└── pdf_content_extractor.py  # 集成向量化功能
```

---

## 🚀 使用方法

### 1️⃣ **基础使用 - 提取并索引**

```python
from app.utils.unTaggedPDF.pdf_content_extractor import PDFContentExtractor

# 初始化提取器(启用向量化)
extractor = PDFContentExtractor(
    pdf_path="test.pdf",
    enable_vectorization=True,      # 启用向量化
    qdrant_url="http://localhost:6333",
    embedding_model="BAAI/bge-m3",
    device="auto"                    # 自动检测 GPU
)

# 一键提取并索引
result = extractor.extract_and_index(
    doc_id="ORDOS-2025-0001",
    metadata={
        "region": "内蒙古-鄂尔多斯",
        "agency": "鄂尔多斯市政府",
        "published_at_ts": 1706601600
    },
    save_json=True  # 同时保存JSON文件
)

print(f"✓ 索引了 {result['chunks_count']} 个 chunks")
```

### 2️⃣ **独立使用索引器**

```python
from app.utils.db.qdrant import QdrantUtil, get_embedding_util, TenderIndexer

# 1. 初始化组件
qdrant_util = QdrantUtil(url="http://localhost:6333")
embedding_util = get_embedding_util(
    model_name='BAAI/bge-m3',
    use_fp16=True,
    device='cuda'
)

# 2. 创建索引器
indexer = TenderIndexer(qdrant_util, embedding_util)

# 3. 索引文档
chunk_count = indexer.index_document(
    doc_id="ORDOS-2025-0001",
    tables=tables,      # 从 extract_all_tables() 获取
    paragraphs=paragraphs,  # 从 extract_all_paragraphs() 获取
    metadata={
        "region": "内蒙古",
        "agency": "鄂尔多斯市政府"
    }
)
```

### 3️⃣ **使用搜索器**

```python
from app.utils.db.qdrant import QdrantUtil, get_embedding_util, TenderSearcher

# 1. 初始化搜索器
qdrant_util = QdrantUtil(url="http://localhost:6333")
embedding_util = get_embedding_util(model_name='BAAI/bge-m3')
searcher = TenderSearcher(qdrant_util, embedding_util)

# 2. 语义搜索
results = searcher.search(
    query="网站集约化平台",
    doc_id="ORDOS-2025-0001",  # 可选:限定文档
    chunk_types=["paragraph"],  # 可选:限定类型
    limit=10
)

for result in results:
    print(f"[{result['score']:.3f}] {result['content'][:80]}")

# 3. 关键词搜索
results = searcher.search_by_keyword(
    keyword="投标人",
    doc_id="ORDOS-2025-0001",
    chunk_types=["table_row"],
    limit=10
)

# 4. 混合搜索(语义+关键词)
results = searcher.hybrid_search(
    query="网站建设",
    keyword_filter="平台",
    limit=10
)

# 5. 获取文档所有 chunks
chunks = searcher.get_document_chunks(
    doc_id="ORDOS-2025-0001",
    chunk_types=["paragraph"]
)
```

---

## 🔧 核心类说明

### `TenderIndexer` - 索引器

**职责**: 将 tables + paragraphs 转换为向量并写入 Qdrant

**核心方法**:
```python
def index_document(doc_id, tables, paragraphs, metadata) -> int:
    """索引一个文档,返回成功索引的chunk数量"""
```

**内部流程**:
1. 收集文本 (`_collect_texts`)
2. 批量向量化 (`_vectorize_batch`)
3. 组装 Points (`_build_points`)
4. 批量插入 Qdrant

---

### `TenderSearcher` - 搜索器

**职责**: 在向量库中搜索内容

**核心方法**:

| 方法 | 说明 | 搜索方式 |
|------|------|---------|
| `search()` | 语义搜索 | 稠密向量相似度 |
| `search_by_keyword()` | 关键词搜索 | 文本匹配 |
| `hybrid_search()` | 混合搜索 | 语义+关键词过滤 |
| `get_document_chunks()` | 获取文档所有chunks | 过滤查询 |

---

## 📊 数据流

```
PDF文件
  ↓
PDFContentExtractor.extract_and_index()
  ↓
├─ extract_all_tables()      → tables
├─ extract_all_paragraphs()  → paragraphs
├─ save_to_json()            → JSON文件(可选)
  ↓
TenderIndexer.index_document()
  ↓
├─ 收集文本 (段落content + 表格行 "col1:val1|col2:val2")
├─ 批量向量化 (bge-m3: dense 1024维 + sparse)
├─ 组装 Points (id, vector, payload)
  ↓
Qdrant.insert_points_batch()
  ↓
向量数据库 (tender_chunks 集合)
```

---

## 🎯 Payload 结构

### 段落 chunk:
```json
{
  "doc_id": "ORDOS-2025-0001",
  "chunk_type": "paragraph",
  "page": 2,
  "content": "段落文本内容...",
  "bbox": [x0, y0, x1, y1],
  "para_id": "doc001",
  "content_hash": "abc123...",
  "region": "内蒙古-鄂尔多斯",
  "agency": "鄂尔多斯市政府",
  "published_at_ts": 1706601600
}
```

### 表格行 chunk:
```json
{
  "doc_id": "ORDOS-2025-0001",
  "chunk_type": "table_row",
  "page": 3,
  "content": "序号: 1 | 项目名称: 网站建设 | 金额: 100万",
  "table_id": "doc002",
  "row_id": "r001",
  "table_idx": 0,
  "row_idx": 0,
  "content_hash": "def456...",
  "region": "内蒙古-鄂尔多斯",
  "agency": "鄂尔多斯市政府",
  "published_at_ts": 1706601600
}
```

---

## ⚙️ 配置说明

### `PDFContentExtractor` 初始化参数:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `pdf_path` | str | 必填 | PDF文件路径 |
| `enable_vectorization` | bool | False | 是否启用向量化 |
| `qdrant_url` | str | "http://localhost:6333" | Qdrant服务地址 |
| `embedding_model` | str | "BAAI/bge-m3" | 向量化模型 |
| `device` | str | "auto" | 计算设备('auto', 'cuda', 'cpu') |

---

## 📝 注意事项

1. **Qdrant 版本**: 需要 qdrant-client >= 1.9.0
2. **模型下载**: 首次运行会自动下载 bge-m3 模型(~2GB)
3. **GPU 加速**: 设置 `device="cuda"` 或 `device="auto"` 自动检测
4. **集合创建**: 首次使用时会自动创建 `tender_chunks` 集合
5. **缓存**: 向量化结果会被缓存,相同文本不会重复计算

---

## 🔍 搜索过滤器

### 按文档ID过滤:
```python
results = searcher.search(query="...", doc_id="ORDOS-2025-0001")
```

### 按chunk类型过滤:
```python
results = searcher.search(query="...", chunk_types=["paragraph"])
results = searcher.search(query="...", chunk_types=["table_row"])
```

### 按地区过滤:
```python
results = searcher.search(query="...", region="内蒙古-鄂尔多斯")
```

---

## 🧪 完整示例

```python
from pathlib import Path
from app.utils.unTaggedPDF.pdf_content_extractor import PDFContentExtractor

# 配置
task_id = "鄂尔多斯市政府网站群集约化平台升级改造项目"
pdf_path = f"/path/to/{task_id}.pdf"

# 1. 提取并索引
extractor = PDFContentExtractor(
    pdf_path=str(pdf_path),
    enable_vectorization=True,
    device="auto"
)

result = extractor.extract_and_index(
    doc_id=f"ORDOS-{task_id[:10]}",
    metadata={
        "region": "内蒙古-鄂尔多斯",
        "agency": "鄂尔多斯市政府",
        "published_at_ts": 1706601600
    }
)

print(f"✓ 提取: {result['tables_count']} 个表格, {result['paragraphs_count']} 个段落")
print(f"✓ 索引: {result['chunks_count']} 个 chunks")

# 2. 搜索
if extractor.searcher:
    results = extractor.searcher.search(
        query="网站集约化平台",
        limit=5
    )

    print(f"\n搜索结果:")
    for i, r in enumerate(results, 1):
        print(f"  [{i}] 相似度: {r['score']:.3f}")
        print(f"      类型: {r['chunk_type']}, 页码: {r['page']}")
        print(f"      内容: {r['content'][:80]}...")
```

---

## 🆘 故障排查

### 1. GPU 未被使用
```python
import torch
print(torch.cuda.is_available())  # 应该返回 True
print(torch.cuda.get_device_name(0))  # 显示 GPU 型号
```

### 2. 模型加载失败
- 检查网络连接(首次需要下载模型)
- 手动下载模型到本地,修改 model_name 为本地路径

### 3. Qdrant 连接失败
- 确认 Qdrant 服务已启动
- 检查 qdrant_url 是否正确
- 使用 `docker ps` 检查 Qdrant 容器状态

### 4. 搜索结果为空
- 确认集合中有数据: `qdrant_util.list_collections()`
- 检查过滤条件是否过严
- 尝试不带过滤器的搜索

---

## 📚 相关文档

- [Qdrant 官方文档](https://qdrant.tech/documentation/)
- [bge-m3 模型](https://huggingface.co/BAAI/bge-m3)
- [test_embedding_integration.py](./test_embedding_integration.py) - 完整测试示例