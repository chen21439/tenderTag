"""
Direct test: Write cell data to Milvus
Tests the Milvus integration independently
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.utils.db.milvus import MilvusUtil
from app.utils.db.qdrant import get_embedding_util
from app.utils.unTaggedPDF.table_to_cells import TableToCellsConverter
import torch


def main():
    print("="*80)
    print("Direct Milvus Test: Cell Data -> Milvus")
    print("="*80)

    # 1. Create mock table data
    print("\n[1/5] Creating mock table data...")
    test_tables = [
        {
            "id": "doc001",
            "page": 1,
            "columns": [
                {"id": "c001", "name": "Sequence Number"},
                {"id": "c002", "name": "Project Name"},
                {"id": "c003", "name": "Amount (CNY)"}
            ],
            "rows": [
                {
                    "id": "r001",
                    "cells": [
                        {"col_id": "c001", "content": "1"},
                        {"col_id": "c002", "content": "Website Group Platform Upgrade"},
                        {"col_id": "c003", "content": "1,000,000"}
                    ]
                },
                {
                    "id": "r002",
                    "cells": [
                        {"col_id": "c001", "content": "2"},
                        {"col_id": "c002", "content": "Platform Maintenance Service"},
                        {"col_id": "c003", "content": "500,000"}
                    ]
                }
            ]
        }
    ]
    print(f"[1/5] OK - Created {len(test_tables)} table with 2 rows")

    # 2. Convert to cells
    print("\n[2/5] Converting tables to cells...")
    converter = TableToCellsConverter()
    doc_id = "TEST_DOC_001"
    cells = converter.convert_tables_to_cells(test_tables, doc_id)
    print(f"[2/5] OK - Converted to {len(cells)} cells")

    # 3. Initialize Milvus
    print("\n[3/5] Initializing Milvus...")
    try:
        milvus = MilvusUtil(host="localhost", port="19530")
        collection_name = f"cells_{doc_id}".replace("-", "_").lower()
        success = milvus.create_collection(
            collection_name=collection_name,
            dim=1024,
            drop_old=True
        )
        if not success:
            print("[3/5] FAILED - Could not create collection")
            return
        print(f"[3/5] OK - Created collection: {collection_name}")
    except Exception as e:
        print(f"[3/5] FAILED - Milvus error: {e}")
        print("Make sure Milvus is running on localhost:19530")
        return

    # 4. Vectorize cells
    print("\n[4/5] Vectorizing cells with bge-m3...")
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"  Using device: {device}")

        embedding_util = get_embedding_util(
            model_name='BAAI/bge-m3',
            use_fp16=True,
            device=device
        )

        # Prepare chunks
        chunks = []
        for cell in cells:
            chunks.append({
                "chunk_type": "table_cell",
                "content": cell.get("cell_value_with_context", cell.get("cell_value_norm", "")),
                "page": cell.get("page", 1)
            })

        # Vectorize
        texts = [chunk["content"] for chunk in chunks]
        vectors = embedding_util.encode_batch(texts, use_cache=False)
        embeddings = [dense_vec for dense_vec, _, _ in vectors]
        print(f"[4/5] OK - Vectorized {len(embeddings)} cells (dim={len(embeddings[0])})")
    except Exception as e:
        print(f"[4/5] FAILED - Vectorization error: {e}")
        milvus.close()
        return

    # 5. Insert to Milvus
    print("\n[5/5] Inserting to Milvus...")
    try:
        count = milvus.insert_data(
            doc_id=doc_id,
            chunks=chunks,
            embeddings=embeddings
        )

        if count > 0:
            print(f"[5/5] OK - Successfully inserted {count} records")

            # Get stats
            stats = milvus.get_stats()
            print(f"\nCollection stats:")
            print(f"  Name: {stats.get('collection_name')}")
            print(f"  Entities: {stats.get('num_entities')}")
        else:
            print("[5/5] FAILED - Insert returned 0 records")

        milvus.close()
    except Exception as e:
        print(f"[5/5] FAILED - Insert error: {e}")
        milvus.close()
        return

    print("\n" + "="*80)
    print("Test completed successfully!")
    print("="*80)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()