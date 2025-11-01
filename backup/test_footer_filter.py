"""
测试页脚过滤器效果
"""
import sys
import json
from pathlib import Path

# 添加项目根目录到sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.utils.unTaggedPDF.table_extractor import TableExtractor

def test_footer_filter():
    """
    测试页脚过滤器是否能够过滤掉页码

    只测试前5页的表格
    """
    # 使用鄂尔多斯PDF（已知包含页码问题）
    pdf_path = r"E:\programFile\AIProgram\docxServer\pdf\task\鄂尔多斯市政府网站群集约化平台升级改造项目\鄂尔多斯市政府网站群集约化平台升级改造项目.pdf"

    print(f"测试PDF: {pdf_path}\n")
    print("注意：只测试前5页的表格以加快速度\n")

    # 提取表格
    extractor = TableExtractor(pdf_path)
    tables = extractor.extract_tables()

    print(f"\n提取到 {len(tables)} 个表格")

    # 只检查前5页的表格
    tables_to_check = [t for t in tables if t.get('page', 999) <= 5]
    print(f"前5页有 {len(tables_to_check)} 个表格\n")

    # 检查是否还有页码
    page_number_found = False
    for table_idx, table in enumerate(tables_to_check):
        page_num = table.get('page', -1)
        table_id = table.get('id', f'table_{table_idx}')

        print(f"[表格 {table_id}] 页码 {page_num}")

        for row in table.get('rows', []):
            for cell in row.get('cells', []):
                content = cell.get('content', '')

                # 检测页码模式
                if '第' in content and '页' in content:
                    page_number_found = True
                    print(f"  [FAIL] 发现页码模式: row={cell.get('row_id')}, col={cell.get('col_id')}")
                    print(f"     content末尾: ...{content[-150:]}")

    print("\n" + "="*80)
    if page_number_found:
        print("[FAIL] 测试失败：仍然提取到了页码")
        print("\n可能的原因：")
        print("1. cell bbox 异常巨大（跨页），超出了页脚安全区")
        print("2. 页码不在底部30pt范围内")
        print("3. 正则过滤没有生效")
        return False
    else:
        print("[PASS] 测试成功：未发现页码被提取到表格中")
        return True

if __name__ == '__main__':
    success = test_footer_filter()
    sys.exit(0 if success else 1)