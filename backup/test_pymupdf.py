"""
测试PyMuPDF提取效果对比
"""
import fitz  # PyMuPDF

pdf_path = r"E:\programFile\AIProgram\docxServer\pdf\task\1979102567573037058\1979102567573037058.pdf"

doc = fitz.open(pdf_path)
page = doc[3]  # 第4页

print("=" * 60)
print("PyMuPDF - get_text() 默认模式")
print("=" * 60)
text1 = page.get_text()
print(text1[:500])

print("\n" + "=" * 60)
print("PyMuPDF - get_text('text') 纯文本模式")
print("=" * 60)
text2 = page.get_text("text")
print(text2[:500])

print("\n" + "=" * 60)
print("PyMuPDF - get_text('blocks') 块模式")
print("=" * 60)
blocks = page.get_text("blocks")
for i, block in enumerate(blocks[:3]):
    print(f"Block {i}: {block[4][:100]}")

doc.close()