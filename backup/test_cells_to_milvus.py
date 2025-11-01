"""
测试单元格数据写入 Milvus 向量库
"""
import sys
from pathlib import Path

# 添加项目根目录到 sys.path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.utils.unTaggedPDF import PDFContentExtractor


def main():
    print("="*80)
    print("Test: Cells Data -> Milvus Vector DB")
    print("="*80)

    # 使用测试PDF
    task_id = "鄂尔多斯市政府网站群集约化平台升级改造项目"
    base_dir = Path(r"E:\programFile\AIProgram\docxServer\pdf\task\鄂尔多斯市政府网站群集约化平台升级改造项目")
    pdf_path = base_dir / f"{task_id}.pdf"

    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        return

    print(f"\nPDF file: {pdf_path}")
    print(f"Task ID: {task_id}")

    try:
        # 1. 创建提取器
        print(f"\n[1/3] Initializing PDFContentExtractor...")
        extractor = PDFContentExtractor(
            str(pdf_path),
            enable_cross_page_merge=True,
            verbose=False
        )
        print(f"[1/3] OK - Initialized")

        # 2. 提取并保存（会自动写入 Milvus）
        print(f"\n[2/3] Extracting tables and converting to cells...")
        output_paths = extractor.save_to_json(
            include_paragraphs=False,  # 只测试表格
            task_id=task_id,
            save_cells=True  # 启用单元格转换和向量化
        )
        print(f"[2/3] OK - Extraction completed")

        # 3. 显示结果
        print(f"\n[3/3] Output files:")
        for key, path in output_paths.items():
            print(f"  - {key}: {path}")

        print(f"\n{'='*80}")
        print(f"Test completed successfully!")
        print(f"{'='*80}")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()