"""
测试pdfplumber的cells格式
"""
import pdfplumber

pdf_path = r"E:\programFile\AIProgram\docxServer\pdf\task\1979102567573037058\1979102567573037058.pdf"

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[2]  # 第3页
    tables = page.find_tables()

    if tables:
        table = tables[0]
        print(f"表格找到，cells类型: {type(table.cells)}")
        print(f"cells总数: {len(table.cells)}")
        print(f"\n前5个cells:")
        for i, cell in enumerate(table.cells[:5]):
            print(f"Cell {i}: {cell}")
            print(f"  类型: {type(cell)}, 长度: {len(cell)}")