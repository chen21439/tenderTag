"""
测试 TableExtractor 第一轮提取结果
检查序号列是否在最原始的提取中就已经丢失
"""
import sys
from pathlib import Path

# 添加项目根目录到sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.utils.unTaggedPDF.table_extractor import TableExtractor

def test_raw_extraction():
    """
    测试第一轮原始提取（不进行任何后处理）
    """
    pdf_path = r"E:\programFile\AIProgram\docxServer\pdf\task\鄂尔多斯市政府网站群集约化平台升级改造项目\鄂尔多斯市政府网站群集约化平台升级改造项目.pdf"

    print(f"测试 PDF: {pdf_path}\n")

    # 创建提取器
    extractor = TableExtractor(pdf_path)

    # 第一轮提取（detect_header=False，延迟表头识别）
    tables = extractor.extract_tables(detect_header=False)

    print(f"\n提取到 {len(tables)} 个表格\n")

    # 只检查第4页的表格
    page_4_tables = [t for t in tables if t.get('page') == 4]

    if not page_4_tables:
        print("[ERROR] 第4页没有提取到表格！")
        return

    table = page_4_tables[0]
    table_id = table.get('id', 'N/A')
    print(f"第4页表格 {table_id}:")
    print(f"  页码: {table['page']}")
    print(f"  列数: {len(table.get('columns', []))}")
    print(f"  行数: {len(table.get('rows', []))}")
    print(f"  表格 bbox: {table.get('bbox')}")
    print()

    # 检查列定义
    print("列定义:")
    for col in table.get('columns', []):
        print(f"  {col['id']}: name=\"{col.get('name', '')}\"")
    print()

    # 检查前3行的所有单元格内容
    print("前3行数据:")
    for row_idx, row in enumerate(table.get('rows', [])[:3]):
        print(f"\n  行 {row_idx + 1} ({row['id']}):")
        for cell in row.get('cells', []):
            col_id = cell.get('col_id')
            content = cell.get('content', '')
            bbox = cell.get('bbox')

            # 显示前50个字符
            content_preview = content[:50] if content else "(空)"

            print(f"    {col_id}: content=\"{content_preview}\"")
            if bbox:
                print(f"         bbox={[f'{x:.1f}' for x in bbox]}")
            else:
                print(f"         bbox=None")

if __name__ == '__main__':
    test_raw_extraction()