"""
表格转单元格结构
将表格按行拆分为单元格级别的结构化数据,适合向量化存储
"""
import re
from typing import List, Dict, Any, Optional


class TableToCellsConverter:
    """表格转单元格转换器"""

    def __init__(self):
        """初始化转换器"""
        # 列名别名映射(用于归一化列名)
        self.header_alias_map = {
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

    def convert_tables_to_cells(self,
                                tables: List[Dict[str, Any]],
                                doc_id: str) -> List[Dict[str, Any]]:
        """
        将表格列表转换为单元格级别的结构化数据

        Args:
            tables: 表格列表 (来自 extract_all_tables())
            doc_id: 文档ID

        Returns:
            单元格记录列表
        """
        all_cells = []

        for table_idx, table in enumerate(tables):
            table_id = table.get("id", f"t{table_idx+1:03d}")
            page = table.get("page", 1)
            columns = table.get("columns", [])

            # 构建列名映射
            col_headers = {}
            for col in columns:
                col_id = col.get("id", "")
                col_name = col.get("name", col_id)
                col_headers[col_id] = col_name

            # 处理每一行
            rows = table.get("rows", [])
            for row_idx, row in enumerate(rows):
                row_id = row.get("id", f"r{row_idx+1:03d}")
                cells = row.get("cells", [])

                # 构建行上下文 (所有单元格内容拼接)
                row_context_parts = []
                for cell in cells:
                    col_id = cell.get("col_id", "")
                    content = cell.get("content", "").strip()
                    if content:
                        header = col_headers.get(col_id, col_id)
                        row_context_parts.append(f"{header}:{content}")

                row_context = " | ".join(row_context_parts)

                # 为每个单元格创建一条记录
                for col_idx, cell in enumerate(cells):
                    col_id = cell.get("col_id", "")
                    content = cell.get("content", "").strip()

                    if not content:
                        continue  # 跳过空单元格

                    header_name = col_headers.get(col_id, col_id)
                    canonical_header = self.header_alias_map.get(header_name, header_name)

                    # 创建单元格记录
                    cell_record = {
                        # 基础信息
                        "doc_id": doc_id,
                        "table_id": table_id,
                        "row_id": row_id,
                        "col_id": col_id,
                        "page": page,

                        # 列信息
                        "header_name": header_name,
                        "canonical_header": canonical_header,
                        "col_index": col_idx,

                        # 单元格内容
                        "cell_value_raw": content,

                        # 行上下文 (整行内容)
                        "row_context": row_context,

                        # 归一化文本 (用于向量化)
                        "cell_value_norm": f"{header_name}：{content}",
                        "cell_value_with_context": f"{header_name}：{content} | 行上下文：{row_context}",

                        # 位置信息
                        "row_index": row_idx,
                        "table_index": table_idx
                    }

                    # 数值检测
                    num_info = self._extract_number(content, header_name)
                    if num_info:
                        cell_record.update(num_info)

                    all_cells.append(cell_record)

        return all_cells

    def _extract_number(self, text: str, header: str) -> Optional[Dict[str, Any]]:
        """
        提取数值信息

        Args:
            text: 单元格文本
            header: 列名

        Returns:
            数值信息字典 (如果是数值)
        """
        # 移除千分位逗号
        cleaned = text.replace(",", "").replace("，", "")

        # 匹配数值 (整数或小数)
        match = re.search(r"(\d+(?:\.\d+)?)", cleaned)
        if not match:
            return None

        num_value = float(match.group(1))

        # 检测单位
        unit = self._detect_unit(text, header)

        return {
            "num_value": num_value,
            "unit": unit,
            "has_number": True
        }

    def _detect_unit(self, text: str, header: str) -> str:
        """
        检测单位

        Args:
            text: 单元格文本
            header: 列名

        Returns:
            单位字符串
        """
        # 常见单位列表
        units = ["元", "万元", "亿元", "kg", "km", "m", "cm", "mm", "平方米", "立方米", "吨", "件", "个", "台", "套"]

        # 从文本中查找单位
        for unit in units:
            if unit in text:
                return unit

        # 从列名中推断单位
        if "金额" in header or "价格" in header:
            return "元"
        elif "数量" in header:
            return "个"
        elif "面积" in header:
            return "平方米"

        return ""

    def group_by_table(self, cells: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        按表格分组单元格

        Args:
            cells: 单元格列表

        Returns:
            {table_id: [cell1, cell2, ...]}
        """
        grouped = {}
        for cell in cells:
            table_id = cell["table_id"]
            if table_id not in grouped:
                grouped[table_id] = []
            grouped[table_id].append(cell)

        return grouped

    def create_milvus_payload(self, cells: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        创建 Milvus 导入格式的数据

        Args:
            cells: 单元格列表

        Returns:
            Milvus payload 格式
        """
        return {
            "collection": "tabular_cells",
            "data": cells,
            "schema": {
                "fields": [
                    {"name": "doc_id", "type": "varchar"},
                    {"name": "table_id", "type": "varchar"},
                    {"name": "row_id", "type": "varchar"},
                    {"name": "col_id", "type": "varchar"},
                    {"name": "page", "type": "int64"},
                    {"name": "header_name", "type": "varchar"},
                    {"name": "canonical_header", "type": "varchar"},
                    {"name": "cell_value_raw", "type": "varchar"},
                    {"name": "cell_value_norm", "type": "varchar"},
                    {"name": "row_context", "type": "varchar"},
                    {"name": "num_value", "type": "float", "nullable": True},
                    {"name": "unit", "type": "varchar", "nullable": True},
                    {"name": "embedding", "type": "float_vector", "dim": 1024}
                ]
            }
        }


# 便捷函数
def convert_tables_to_cells(tables: List[Dict[str, Any]], doc_id: str) -> List[Dict[str, Any]]:
    """
    快捷转换函数

    Args:
        tables: 表格列表
        doc_id: 文档ID

    Returns:
        单元格列表
    """
    converter = TableToCellsConverter()
    return converter.convert_tables_to_cells(tables, doc_id)


# 测试示例
def test_convert():
    """测试转换"""
    # 模拟表格数据
    test_tables = [
        {
            "id": "t001",
            "page": 1,
            "columns": [
                {"id": "c001", "name": "序号"},
                {"id": "c002", "name": "项目名称"},
                {"id": "c003", "name": "金额(元)"}
            ],
            "rows": [
                {
                    "id": "r001",
                    "cells": [
                        {"col_id": "c001", "content": "1"},
                        {"col_id": "c002", "content": "网站建设"},
                        {"col_id": "c003", "content": "1,000,000"}
                    ]
                },
                {
                    "id": "r002",
                    "cells": [
                        {"col_id": "c001", "content": "2"},
                        {"col_id": "c002", "content": "平台升级"},
                        {"col_id": "c003", "content": "500,000"}
                    ]
                }
            ]
        }
    ]

    converter = TableToCellsConverter()
    cells = converter.convert_tables_to_cells(test_tables, "TEST-DOC-001")

    print(f"转换结果: {len(cells)} 个单元格")
    for i, cell in enumerate(cells, 1):
        print(f"\n[{i}] {cell['table_id']}-{cell['row_id']}-{cell['col_id']}")
        print(f"    列名: {cell['header_name']} → {cell['canonical_header']}")
        print(f"    原始值: {cell['cell_value_raw']}")
        print(f"    归一化: {cell['cell_value_norm']}")
        if cell.get('has_number'):
            print(f"    数值: {cell['num_value']} {cell['unit']}")


if __name__ == "__main__":
    test_convert()