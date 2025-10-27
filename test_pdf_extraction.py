"""
测试pdfplumber不同参数配置的效果
"""
import pdfplumber

pdf_path = r"E:\programFile\AIProgram\docxServer\pdf\task\1979102567573037058\1979102567573037058.pdf"

with pdfplumber.open(pdf_path) as pdf:
    # 测试第4页（问题出现的页面）
    page = pdf.pages[3]  # 第4页，索引3

    print("=" * 60)
    print("测试1: 默认extract_tables()")
    print("=" * 60)
    tables = page.extract_tables()
    if tables:
        print(f"找到 {len(tables)} 个表格")
        print("第一个单元格内容:")
        print(tables[0][0][0] if tables[0] else "无")

    print("\n" + "=" * 60)
    print("测试2: extract_text() 查看原始文本")
    print("=" * 60)
    text = page.extract_text()
    print(text[:500])  # 打印前500字符

    print("\n" + "=" * 60)
    print("测试3: extract_tables() with keep_blank_chars=True")
    print("=" * 60)
    table_settings = {
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        "intersection_tolerance": 5,
    }
    tables2 = page.extract_tables(table_settings=table_settings)
    if tables2:
        print(f"找到 {len(tables2)} 个表格")
        print("第一个单元格内容:")
        print(tables2[0][0][0] if tables2[0] else "无")