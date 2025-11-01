# Milvus Cells Integration - Implementation Summary

## Overview

Successfully integrated cell-level table data storage into Milvus vector database. The integration happens automatically when extracting tables from PDFs.

## Architecture

```
PDF → Table Extraction → Cell Conversion → Vectorization → Milvus Storage
```

### Components

1. **TableToCellsConverter** (`app/utils/unTaggedPDF/table_to_cells.py`)
   - Converts table rows into cell-level records
   - Extracts numeric values and units
   - Normalizes column names with alias mapping
   - Generates row context for better search

2. **MilvusUtil** (`app/utils/db/milvus/MilvusUtil.py`)
   - Quick validation utility for Milvus operations
   - Create collection, insert data, search, get stats
   - Uses COSINE similarity with IVF_FLAT index

3. **Integration in PDFContentExtractor** (`pdf_content_extractor.py`)
   - Automatic cell conversion in `save_to_json()` method
   - Vectorizes cells using bge-m3 (1024-dim)
   - Writes to Milvus before/after JSON file

## Cell Data Structure

Each cell becomes a record with:

```python
{
    "doc_id": "task_id",
    "table_id": "doc001",
    "row_id": "r001",
    "col_id": "c001",
    "page": 1,
    "header_name": "Project Name",
    "canonical_header": "Project Name",
    "cell_value_raw": "Website Platform Upgrade",
    "cell_value_norm": "Project Name: Website Platform Upgrade",
    "cell_value_with_context": "Project Name: Website Platform Upgrade | Row context: Seq:1 | Project:... | Amount:...",
    "row_context": "Seq:1 | Project:Website Platform Upgrade | Amount:1000000",
    "num_value": 1000000.0,  # If numeric
    "unit": "CNY"  # If has unit
}
```

## Milvus Collection Schema

```python
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=200),
    FieldSchema(name="chunk_type", dtype=DataType.VARCHAR, max_length=50),
    FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=5000),
    FieldSchema(name="page", dtype=DataType.INT64),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1024)
]

index_params = {
    "metric_type": "COSINE",
    "index_type": "IVF_FLAT",
    "params": {"nlist": 128}
}
```

## Usage

### Automatic Integration (Default)

```python
from app.utils.unTaggedPDF import PDFContentExtractor

extractor = PDFContentExtractor("document.pdf")

# This will:
# 1. Extract tables
# 2. Convert to cells
# 3. Save cells JSON
# 4. Vectorize cells
# 5. Write to Milvus
output_paths = extractor.save_to_json(
    task_id="PROJECT_001",
    save_cells=True  # Default: True
)
```

### Manual Control

```python
from app.utils.unTaggedPDF.table_to_cells import TableToCellsConverter
from app.utils.db.milvus import MilvusUtil
from app.utils.db.qdrant import get_embedding_util

# 1. Convert tables to cells
converter = TableToCellsConverter()
cells = converter.convert_tables_to_cells(tables, "doc_id")

# 2. Initialize Milvus
milvus = MilvusUtil(host="localhost", port="19530")
milvus.create_collection("collection_name", dim=1024, drop_old=True)

# 3. Vectorize
embedding_util = get_embedding_util(model_name='BAAI/bge-m3')
texts = [cell["cell_value_with_context"] for cell in cells]
vectors = embedding_util.encode_batch(texts)
embeddings = [dense_vec for dense_vec, _, _ in vectors]

# 4. Prepare chunks
chunks = [{
    "chunk_type": "table_cell",
    "content": cell["cell_value_with_context"],
    "page": cell["page"]
} for cell in cells]

# 5. Insert
count = milvus.insert_data("doc_id", chunks, embeddings)
milvus.close()
```

## Test Results

**Test File**: `test_milvus_direct.py`

- Mock table: 2 rows × 3 columns
- Cells generated: 6 cells
- Vectorization: bge-m3 (1024-dim)
- Milvus insertion: 6/6 successful ✅
- Collection: `cells_test_doc_001`

## Configuration

### Milvus Connection

Default:
- Host: `localhost`
- Port: `19530`

### Vector Model

Default:
- Model: `BAAI/bge-m3`
- Dimension: 1024
- Device: Auto-detect (CUDA/CPU)

### Collection Naming

Pattern: `cells_{doc_id}` (lowercase, `-` → `_`)

Example: `cells_project_001`

## Files Modified/Created

### Created
- `app/utils/unTaggedPDF/table_to_cells.py` - Cell converter
- `app/utils/db/milvus/MilvusUtil.py` - Milvus utility
- `app/utils/db/milvus/__init__.py` - Module exports
- `test_milvus_direct.py` - Integration test
- `test_cells_to_milvus.py` - Full pipeline test
- `MILVUS_CELLS_INTEGRATION.md` - This document

### Modified
- `app/utils/unTaggedPDF/pdf_content_extractor.py` - Added Milvus writing
- `app/utils/unTaggedPDF/__init__.py` - Exported PDFContentExtractor
- `app/utils/db/qdrant/EmbeddingUtil.py` - Fixed Unicode for Windows console
- `app/utils/db/qdrant/TenderIndexer.py` - Fixed Unicode
- `app/utils/db/qdrant/TenderSearcher.py` - Fixed Unicode
- `app/utils/db/qdrant/OllamaEmbeddingUtil.py` - Fixed Unicode

## Column Normalization

The converter includes column alias mapping:

```python
header_alias_map = {
    "序号": "序号",
    "编号": "序号",
    "No.": "序号",
    "项目名称": "项目名称",
    "名称": "项目名称",
    "金额": "金额",
    "标的金额": "金额",
    "预算金额": "金额",
    "单价": "单价",
    "数量": "数量",
    "规格": "规格",
    "型号": "规格",
    "备注": "备注",
    "说明": "备注"
}
```

## Number/Unit Extraction

Automatically detects:

- Numbers: Integers and decimals (with comma separators)
- Units: 元, 万元, 亿元, kg, km, m, cm, mm, 平方米, 立方米, 吨, 件, 个, 台, 套
- Inferred units from column names (e.g., "金额" → "元")

## Benefits

1. **Granular Search**: Search at cell level instead of whole table
2. **Context Preservation**: Each cell includes row context
3. **Structured Data**: Normalized columns and extracted numbers
4. **Flexible Queries**: Search by content, column name, or numeric value
5. **Scalable**: Milvus handles millions of vectors efficiently

## Future Improvements

1. **Hybrid Search**: Combine dense + sparse vectors (Milvus 2.4+)
2. **Metadata Filtering**: Filter by page, table_id, column name
3. **Aggregation Queries**: Sum/avg numeric cells matching criteria
4. **Multi-language**: Extend column aliases for other languages
5. **Custom Vectorization**: Allow user-provided embedding models

## Dependencies

```
pymilvus>=2.3.0
torch>=1.13.0
transformers>=4.30.0
FlagEmbedding>=1.2.0
```

## Known Issues

1. **Windows Console Encoding**: GBK encoding can't display emojis
   - Fixed: Replaced ✓/✗ with OK/FAILED in all output
2. **Large PDFs**: Vectorization can be slow on CPU
   - Solution: Use GPU (CUDA) for faster encoding
3. **Memory Usage**: Loading bge-m3 requires ~2GB RAM
   - Solution: Use FP16 precision (already enabled)

## Contact

For questions or issues, refer to:
- Project CLAUDE.md: `E:\programFile\AIProgram\docxServer\python\table\CLAUDE.md`
- Qdrant implementation: `QDRANT_IMPLEMENTATION.md`
- Embedding usage: `EMBEDDING_USAGE.md`