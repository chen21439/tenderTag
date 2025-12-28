"""
导出知识图谱数据到前端public目录

运行: python export_to_public.py
"""

import json
import os
import shutil
from typing import List, Dict, Any
from collections import defaultdict


class KnowledgeGraphExporter:
    def __init__(self):
        # 节点数据
        self.nodes = [
            # 一级标签
            {'id': '招标文件', 'label': '招标文件', 'type': 'normal', 'level': 1},
            {'id': '项目基本信息', 'label': '项目基本信息', 'type': 'normal', 'level': 1},
            {'id': '投标人须知', 'label': '投标人须知', 'type': 'normal', 'level': 1},
            {'id': '商务要求', 'label': '商务要求', 'type': 'normal', 'level': 1},
            {'id': '技术要求', 'label': '技术要求', 'type': 'normal', 'level': 1},
            {'id': '资格要求', 'label': '资格要求', 'type': 'normal', 'level': 1},
            {'id': '符合性要求', 'label': '符合性要求', 'type': 'normal', 'level': 1},
            {'id': '评标信息', 'label': '评标信息', 'type': 'normal', 'level': 1},
            {'id': '评标方法', 'label': '评标方法', 'type': 'normal', 'level': 1},
            {'id': '采购标的', 'label': '采购标的', 'type': 'normal', 'level': 1},
            {'id': '采购包', 'label': '采购包', 'type': 'normal', 'level': 1},
            {'id': '采购项目', 'label': '采购项目', 'type': 'normal', 'level': 1},
            # 二级标签
            {'id': '其他关键信息', 'label': '其他关键信息', 'type': 'normal', 'level': 2},
            {'id': '对通用条款的补充内容', 'label': '对通用条款的补充内容', 'type': 'normal', 'level': 2},
            {'id': '商务要求偏离表', 'label': '商务要求偏离表', 'type': 'normal', 'level': 2},
            {'id': '商务要求表', 'label': '商务要求表', 'type': 'normal', 'level': 2},
            {'id': '商务要求说明', 'label': '商务要求说明', 'type': 'normal', 'level': 2},
            {'id': '商务要求项', 'label': '商务要求项', 'type': 'normal', 'level': 2},
            {'id': '技术要求偏离表', 'label': '技术要求偏离表', 'type': 'normal', 'level': 2},
            {'id': '技术要求表', 'label': '技术要求表', 'type': 'normal', 'level': 2},
            {'id': '技术要求说明', 'label': '技术要求说明', 'type': 'normal', 'level': 2},
            {'id': '技术要求项', 'label': '技术要求项', 'type': 'normal', 'level': 2},
            {'id': '符合性审查表', 'label': '符合性审查表', 'type': 'normal', 'level': 2},
            {'id': '符合性审查项', 'label': '符合性审查项', 'type': 'normal', 'level': 2},
            {'id': '补充说明', 'label': '补充说明(概念)', 'type': 'normal', 'level': 2},
            {'id': '评标信息表', 'label': '评标信息表', 'type': 'normal', 'level': 2},
            {'id': '评标信息项', 'label': '评标信息项', 'type': 'normal', 'level': 2},
            {'id': '资格性审查表', 'label': '资格性审查表', 'type': 'normal', 'level': 2},
            {'id': '资格性审查项', 'label': '资格性审查项', 'type': 'normal', 'level': 2}
        ]

        # 边数据
        self.edges = [
            {'id': 'e1', 'source': '招标文件', 'target': '采购项目', 'label': 'attachedTo'},
            {'id': 'e3', 'source': '采购项目', 'target': '项目基本信息', 'label': 'hasPart'},
            {'id': 'e4', 'source': '采购项目', 'target': '投标人须知', 'label': 'hasPart'},
            {'id': 'e5', 'source': '采购项目', 'target': '采购包', 'label': 'hasPart'},
            {'id': 'e6', 'source': '采购包', 'target': '商务要求', 'label': 'hasPart'},
            {'id': 'e7', 'source': '采购包', 'target': '技术要求', 'label': 'hasPart'},
            {'id': 'e8', 'source': '采购包', 'target': '资格要求', 'label': 'hasPart'},
            {'id': 'e9', 'source': '采购包', 'target': '符合性要求', 'label': 'hasPart'},
            {'id': 'e10', 'source': '采购包', 'target': '评标信息', 'label': 'hasPart'},
            {'id': 'e11', 'source': '采购包', 'target': '采购标的', 'label': 'hasPart'},
            {'id': 'e12', 'source': '评标信息', 'target': '评标信息表', 'label': 'hasPart'},
            {'id': 'e13', 'source': '评标信息', 'target': '评标方法', 'label': 'hasPart'},
            {'id': 'e14', 'source': '商务要求', 'target': '商务要求表', 'label': 'hasPart'},
            {'id': 'e14b', 'source': '商务要求', 'target': '商务要求说明', 'label': 'hasPart'},
            {'id': 'e15', 'source': '技术要求', 'target': '技术要求表', 'label': 'hasPart'},
            {'id': 'e15b', 'source': '技术要求', 'target': '技术要求说明', 'label': 'hasPart'},
            {'id': 'e16', 'source': '资格要求', 'target': '资格性审查表', 'label': 'hasPart'},
            {'id': 'e17', 'source': '符合性要求', 'target': '符合性审查表', 'label': 'hasPart'},
            {'id': 'e18', 'source': '商务要求表', 'target': '商务要求项', 'label': 'hasMember'},
            {'id': 'e19', 'source': '技术要求表', 'target': '技术要求项', 'label': 'hasMember'},
            {'id': 'e20', 'source': '资格性审查表', 'target': '资格性审查项', 'label': 'hasMember'},
            {'id': 'e21', 'source': '符合性审查表', 'target': '符合性审查项', 'label': 'hasMember'},
            {'id': 'e22', 'source': '评标信息表', 'target': '评标信息项', 'label': 'hasMember'},
            {'id': 'e23', 'source': '投标人须知', 'target': '对通用条款的补充内容', 'label': 'sameAs'},
            {'id': 'e24', 'source': '投标人须知', 'target': '其他关键信息', 'label': 'sameAs'},
            {'id': 'e25', 'source': '商务要求表', 'target': '商务要求偏离表', 'label': 'sameAs'},
            {'id': 'e26', 'source': '技术要求表', 'target': '技术要求偏离表', 'label': 'sameAs'}
        ]

        # 构建父子关系映射
        self.parent_map = {}
        self.children_map = defaultdict(list)

        for edge in self.edges:
            # 处理层级关系: hasPart, hasMember, attachedTo
            if edge['label'] in ['hasPart', 'hasMember', 'attachedTo']:
                self.parent_map[edge['target']] = {
                    'parent_id': edge['source'],
                    'edge_type': edge['label']
                }
                self.children_map[edge['source']].append(edge['target'])
            # 处理sameAs等价关系: target继承source的父节点
            elif edge['label'] == 'sameAs':
                # sameAs表示两个节点等价,target应该和source在同一层级
                # 所以target的父节点应该是source的父节点
                self.parent_map[edge['target']] = {
                    'parent_id': edge['source'],
                    'edge_type': edge['label']
                }
                self.children_map[edge['source']].append(edge['target'])

    def calculate_path(self, node_id: str, visited: set = None) -> str:
        """计算节点的完整路径"""
        if visited is None:
            visited = set()

        if node_id in visited:
            return f"/[循环:{node_id}]"

        visited.add(node_id)

        parent_info = self.parent_map.get(node_id)

        if parent_info:
            parent_path = self.calculate_path(parent_info['parent_id'], visited)
            return f"{parent_path}/{node_id}"
        else:
            return f"/{node_id}"

    def export_ontology_data(self):
        """导出扁平化+路径的知识图谱数据"""
        flat_nodes = []

        for node in self.nodes:
            node_id = node['id']
            parent_info = self.parent_map.get(node_id)
            path = self.calculate_path(node_id)
            depth = path.count('/') - 1

            flat_node = {
                'id': node_id,
                'label': node['label'],
                'type': node['type'],
                'level': node.get('level'),
                'parent_id': parent_info['parent_id'] if parent_info else None,
                'edge_type': parent_info['edge_type'] if parent_info else None,
                'path': path,
                'depth': depth,
                'is_leaf': node_id not in self.children_map,
                'children_count': len(self.children_map.get(node_id, []))
            }
            flat_nodes.append(flat_node)

        # 添加招标文件根节点
        if not any(n['id'] == '招标文件' for n in flat_nodes):
            flat_nodes.insert(0, {
                'id': '招标文件',
                'label': '招标文件',
                'type': 'normal',
                'level': 1,
                'parent_id': None,
                'edge_type': None,
                'path': '/招标文件',
                'depth': 0,
                'is_leaf': False,
                'children_count': len(self.children_map.get('招标文件', []))
            })

        # 按路径排序
        flat_nodes.sort(key=lambda x: x['path'])

        # 导出边数据
        edges_data = []
        for edge in self.edges:
            edges_data.append({
                'id': edge['id'],
                'from_node': edge['source'],
                'to_node': edge['target'],
                'edge_type': edge['label'],
                'is_hierarchical': edge['label'] in ['hasPart', 'hasMember', 'attachedTo']
            })

        return {
            'nodes': flat_nodes,
            'edges': edges_data,
            'metadata': {
                'total_nodes': len(flat_nodes),
                'total_edges': len(edges_data),
                'max_depth': max(n['depth'] for n in flat_nodes),
                'leaf_nodes': len([n for n in flat_nodes if n['is_leaf']]),
                'description': '招标文件知识图谱本体层 - 扁平化+路径方案'
            }
        }


def main():
    """主函数"""
    import sys
    import io

    # 设置UTF-8编码
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    exporter = KnowledgeGraphExporter()

    # 导出数据
    data = exporter.export_ontology_data()

    # 目标目录
    output_dir = 'web/zc-sub-app-ai-bid-examine/public/knowledge-graph'
    os.makedirs(output_dir, exist_ok=True)

    # 保存文件
    output_file = os.path.join(output_dir, 'ontology.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f'✅ 知识图谱数据已导出到: {output_file}')
    print(f'\n📊 数据统计:')
    print(f'   - 节点数量: {data["metadata"]["total_nodes"]}')
    print(f'   - 关系数量: {data["metadata"]["total_edges"]}')
    print(f'   - 最大深度: {data["metadata"]["max_depth"]}')
    print(f'   - 叶子节点: {data["metadata"]["leaf_nodes"]}')


if __name__ == '__main__':
    main()
