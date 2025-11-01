# Qdrant 向量库导入实现总结

## 实现概述

实现了从 PDF 提取内容并**直接从内存**导入到 Qdrant 向量数据库的功能，无需中间文件。

## 核心设计

### 1. 存储架构

**Collection**: `tender_chunks` （单个集合统一存储段落和表格）

**Point ID 格式**: `{doc_id}#{chunk_type}#p{page}#{local_idx}` → MD5 → 整数ID

**Chunk 类型**:
- `paragraph`: 段落块（直接存储段落内容）
- `table_row`: 表格行（格式：`列名1: 值1 | 列名2: 值2 | ...`）

### 2. Payload 结构

```json
{
  "doc_id": "ORDOS-2025-0001",           // 文档ID（索引字段）
  "chunk_type": "paragraph|table_row",   // 块类型（索引字段）
  "page": 12,                            // 页码
  "content": "...",                      // 文本内容
  "bbox": [x0, y0, x1, y1],             // 位置信息

  // 元数据（索引字段）
  "region": "内蒙古-鄂尔多斯",           // 地区（索引）
  "agency": "鄂尔多斯市政府",            // 机构（索引）
  "published_at_ts": 1706601600,        // 发布时间戳（索引）

  // 段落特有字段
  "para_id": "doc001",                   // 段落ID

  // 表格行特有字段
  "table_id": "doc001",                  // 表格ID
  "row_id": "r001",                      // 行ID
  "table_idx": 0,                        // 表格索引
  "row_idx": 5                           // 行索引
}
```

### 3. 索引字段

为以下字段创建了 Payload 索引（加速过滤查询）：
- `doc_id` (KEYWORD)
- `chunk_type` (KEYWORD)
- `region` (KEYWORD)
- `agency` (KEYWORD)
- `published_at_ts` (INTEGER)

## 实现文件

### 文件1: `app/utils/db/qdrant/QdrantUtil.py`

**新增方法**:

#### `init_tender_collection(vector_size=768)`
初始化招标文件集合（只需执行一次）
- 创建 `tender_chunks` 集合
- 创建 5 个 payload 索引

#### `insert_tender_chunks_from_memory(doc_id, tables, paragraphs, embedding_fn, metadata)`
**核心方法** - 从内存导入数据（无文件I/O）
- 输入：内存中的表格列表和段落列表
- 处理：转换为 chunks 格式
- 输出：批量插入到 Qdrant

#### `insert_tender_chunks_from_json(doc_id, table_json_path, paragraph_json_path, ...)`
从 JSON 文件导入（保留用于兼容）

#### `search_tender_chunks(query_vector, doc_id, chunk_types, region, limit)`
搜索招标文件 chunks（支持过滤）

#### `_generate_chunk_id(doc_id, chunk_type, page, local_idx)`
生成 chunk 唯一ID

#### `_hash_to_int(text)`
将字符串ID转换为整数ID（MD5哈希）

### 文件2: `app/utils/unTaggedPDF/pdf_content_extractor.py`

**新增导入块** (lines 23-35):
```python
# Qdrant 导入
try:
    import sys
    from pathlib import Path as ImportPath
    project_root = ImportPath(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from app.utils.db.qdrant import QdrantUtil
    QDRANT_AVAILABLE = True
except ImportError as e:
    print(f"[警告] Qdrant 不可用: {e}")
    QDRANT_AVAILABLE = False
```

**新增方法**: `save_to_qdrant(doc_id, qdrant_url, metadata, embedding_fn)`
- 提取表格（内存）
- 提取段落（内存）
- 直接导入到 Qdrant（内存操作）

### 文件3: 包初始化文件
- `app/utils/db/__init__.py`
- `app/utils/db/qdrant/__init__.py`

## 使用方式

### 方式1: 通过 PDFContentExtractor（推荐）

```python
from pathlib import Path
from app.utils.unTaggedPDF.pdf_content_extractor import PDFContentExtractor

# 初始化提取器
pdf_path = Path("your_file.pdf")
extractor = PDFContentExtractor(
    str(pdf_path),
    enable_cross_page_merge=True
)

# 直接从内存导入到 Qdrant
chunk_count = extractor.save_to_qdrant(
    doc_id="ORDOS-2025-0001",
    qdrant_url="http://localhost:6333",
    metadata={
        "region": "内蒙古-鄂尔多斯",
        "agency": "鄂尔多斯市政府",
        "published_at_ts": 1706601600
    },
    embedding_fn=None  # 暂时使用占位向量
)

print(f"成功导入 {chunk_count} 个 chunks")
```

### 方式2: 直接使用 QdrantUtil

```python
from app.utils.db.qdrant import QdrantUtil

# 初始化
util = QdrantUtil(url="http://localhost:6333")

# 初始化集合（只需执行一次）
util.init_tender_collection(vector_size=768)

# 从内存导入（需要先准备好 tables 和 paragraphs 列表）
chunk_count = util.insert_tender_chunks_from_memory(
    doc_id="ORDOS-2025-0001",
    tables=tables_list,           # 表格列表
    paragraphs=paragraphs_list,   # 段落列表
    embedding_fn=None,
    metadata={...}
)
```

### 搜索示例

```python
from app.utils.db.qdrant import QdrantUtil

util = QdrantUtil(url="http://localhost:6333")

# 搜索指定文档的内容
query_vector = [0.0] * 768  # 占位向量
results = util.search_tender_chunks(
    query_vector=query_vector,
    doc_id="ORDOS-2025-0001",
    chunk_types=["paragraph"],  # 只搜段落
    limit=10
)

for result in results:
    print(result['payload']['content'])
```

## 数据流程

```
┌─────────┐
│  PDF    │
└────┬────┘
     │
     ├──> extract_all_tables() ──┐
     │    (内存)                  │
     │                           ▼
     │                      ┌─────────────────┐
     │                      │  tables[] (内存) │
     │                      └────────┬─────────┘
     │                               │
     └──> extract_all_paragraphs() ─┤
          (内存)                     │
                                     ▼
                          ┌──────────────────────┐
                          │ paragraphs[] (内存)   │
                          └──────────┬────────────┘
                                     │
                                     ▼
                    insert_tender_chunks_from_memory()
                                     │
                                     ▼
                          ┌──────────────────────┐
                          │  Qdrant: tender_chunks│
                          │  - 段落 chunks         │
                          │  - 表格行 chunks       │
                          └──────────────────────┘

【关键】全程无文件I/O，直接从内存到Qdrant
```

## 测试脚本

运行 `test_memory_qdrant.py` 测试完整流程：

```bash
python test_memory_qdrant.py
```

测试内容：
1. 初始化 `tender_chunks` 集合
2. 从 PDF 提取并导入（内存操作）
3. 验证导入结果
4. 统计信息

## 关键特性

✅ **内存直连**: PDF → 内存 → Qdrant（无中间文件）
✅ **统一存储**: 段落和表格存储在同一个 collection
✅ **索引优化**: 5 个 payload 索引加速过滤查询
✅ **灵活向量**: 支持自定义 embedding 函数或占位向量
✅ **结构化内容**: 表格行格式化为 "列名: 值" 格式便于搜索
✅ **元数据丰富**: 包含地区、机构、时间戳等元数据
✅ **批量插入**: 使用 batch insert 提高效率

## 后续优化方向

1. **向量化**: 集成真实的 embedding 模型（如 BERT、sentence-transformers）
2. **增量更新**: 支持更新已存在的文档
3. **删除功能**: 支持删除指定文档的所有 chunks
4. **混合搜索**: 结合关键词搜索和向量搜索
5. **分页查询**: 支持大结果集的分页返回

## 依赖

- `qdrant-client`: Qdrant Python 客户端
- PDFBox 相关依赖（已存在）

安装 Qdrant 客户端：
```bash
poetry add qdrant-client
```

## 注意事项

1. **Qdrant 服务**: 确保 Qdrant 服务运行在 `http://localhost:6333`
2. **集合初始化**: 首次使用需要调用 `init_tender_collection()`
3. **向量维度**: 默认 768 维，如使用其他模型需修改
4. **占位向量**: 当前使用 `[0.0] * 768`，实际使用需替换为真实向量
5. **Point ID**: 使用 MD5 哈希，理论上有碰撞风险（但概率极低）

## 验证方法

1. **导入验证**: 检查返回的 chunk_count
2. **搜索验证**: 使用 `search_tender_chunks()` 查询
3. **Qdrant UI**: 访问 `http://localhost:6333/dashboard` 查看集合
4. **API验证**: 使用 Qdrant REST API 直接查询