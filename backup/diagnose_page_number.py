"""
诊断页码被提取到表格的问题
"""
import json
import sys

def diagnose_page_number_issue(json_file):
    """分析table_raw.json中是否包含页码"""

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"PDF文件: {data['pdf_file']}")
    print(f"总表格数: {data['total_tables']}")
    print()

    found_issues = []

    for table_idx, table in enumerate(data['tables']):
        page_num = table['page']
        table_bbox = table['bbox']
        table_id = table.get('id', f'table_{table_idx}')

        # 获取页面高度
        page_height = 842.0  # A4纸默认高度
        for page_meta in data.get('page_metadata', []):
            if page_meta['page'] == page_num:
                page_height = page_meta['height']
                break

        print(f"[表格 {table_id}] 页码{page_num}, bbox: {table_bbox}")

        # 检查表格bbox是否异常
        if table_bbox[3] > page_height * 2:
            print(f"  ⚠️ 表格bbox异常！y1={table_bbox[3]:.2f} 超过2倍页面高度({page_height})")

        # 检查每个单元格
        for row in table['rows']:
            for cell in row['cells']:
                content = cell.get('content', '')
                cell_bbox = cell.get('bbox')

                # 检测页码特征
                if '第' in content and '页' in content and '-' in content:
                    issue = {
                        'table_id': table_id,
                        'page': page_num,
                        'table_bbox': table_bbox,
                        'row_id': cell['row_id'],
                        'col_id': cell['col_id'],
                        'cell_bbox': cell_bbox,
                        'content_tail': content[-150:],
                        'page_height': page_height
                    }
                    found_issues.append(issue)

                    print(f"  ❌ 发现页码: row={cell['row_id']}, col={cell['col_id']}")
                    print(f"     单元格bbox: {cell_bbox}")
                    if cell_bbox:
                        print(f"     y0={cell_bbox[1]:.2f}, y1={cell_bbox[3]:.2f}")
                        print(f"     单元格高度: {cell_bbox[3] - cell_bbox[1]:.2f}")
                        print(f"     距离页面底部: {page_height - cell_bbox[3]:.2f}")

                        # 分析问题
                        if cell_bbox[3] > page_height:
                            print(f"     ⚠️ 问题: cell bbox的y1超过页面高度！")
                            print(f"     原因: pdfplumber检测的单元格bbox异常，包含了页面底部区域")

                    print(f"     内容末尾: ...{content[-100:]}")
                    print()

    print("\n" + "="*80)
    print(f"总共发现 {len(found_issues)} 个页码问题")

    if found_issues:
        print("\n建议的解决方案:")
        print("1. 在 extract_cell_text() 中裁剪 cell bbox 到页面范围内")
        print("2. 添加页码区域过滤（检测页面底部30pt范围内的文本）")
        print("3. 修正 pdfplumber 检测到的异常bbox（y1 > page_height）")

    return found_issues

if __name__ == '__main__':
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    else:
        # 默认文件
        json_file = r"E:\programFile\AIProgram\docxServer\pdf\task\鄂尔多斯市政府网站群集约化平台升级改造项目\鄂尔多斯市政府网站群集约化平台升级改造项目_table_raw_20251029_233153.json"

    diagnose_page_number_issue(json_file)