"""
知识图谱标签树结构导出工具

功能:
1. 读取知识图谱的节点和边数据
2. 构建树形结构(使用children数组嵌套)
3. 导出为JSON格式
4. 提供多种行业标准的深层嵌套数据存储方案建议
"""

import json
from typing import List, Dict, Any, Set
from collections import defaultdict


class LabelTreeExporter:
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

        # 边数据(父子关系)
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

        # 构建节点映射
        self.node_map = {node['id']: node for node in self.nodes}

        # 构建父子关系映射(只处理hasPart和hasMember关系)
        self.children_map = defaultdict(list)
        for edge in self.edges:
            if edge['label'] in ['hasPart', 'hasMember', 'attachedTo']:
                self.children_map[edge['source']].append(edge['target'])

    def build_tree_node(self, node_id: str, visited: Set[str]) -> Dict[str, Any]:
        """
        递归构建树节点

        Args:
            node_id: 节点ID
            visited: 已访问的节点集合(防止循环引用)

        Returns:
            树节点字典
        """
        if node_id in visited:
            return None

        visited.add(node_id)

        node = self.node_map.get(node_id)
        if not node:
            return None

        tree_node = {
            'id': node['id'],
            'label': node['label'],
            'type': node['type'],
            'level': node.get('level'),
            'children': []
        }

        # 递归添加子节点
        for child_id in self.children_map.get(node_id, []):
            child_node = self.build_tree_node(child_id, visited.copy())
            if child_node:
                tree_node['children'].append(child_node)

        return tree_node

    def export_nested_tree(self, output_file: str = 'label_tree_nested.json'):
        """
        导出嵌套树结构(children数组方式)

        Args:
            output_file: 输出文件路径
        """
        # 找到根节点(招标文件)
        root_node = self.build_tree_node('招标文件', set())

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(root_node, f, ensure_ascii=False, indent=2)

        print(f'✅ 嵌套树结构已导出到: {output_file}')
        return root_node

    def export_flat_tree(self, output_file: str = 'label_tree_flat.json'):
        """
        导出扁平化树结构(parent_id方式)

        这是行业常用的方式之一,避免深层嵌套

        Args:
            output_file: 输出文件路径
        """
        flat_nodes = []

        # 为每个节点添加parent_id字段
        parent_map = {}
        for edge in self.edges:
            if edge['label'] in ['hasPart', 'hasMember', 'attachedTo']:
                parent_map[edge['target']] = edge['source']

        for node in self.nodes:
            flat_node = {
                'id': node['id'],
                'label': node['label'],
                'type': node['type'],
                'level': node.get('level'),
                'parent_id': parent_map.get(node['id'], None),
                'relation': next(
                    (e['label'] for e in self.edges if e['target'] == node['id'] and e['label'] in ['hasPart', 'hasMember', 'attachedTo']),
                    None
                )
            }
            flat_nodes.append(flat_node)

        # 添加招标文件节点(根节点)
        if not any(n['id'] == '招标文件' for n in flat_nodes):
            flat_nodes.insert(0, {
                'id': '招标文件',
                'label': '招标文件',
                'type': 'normal',
                'level': 1,
                'parent_id': None,
                'relation': None
            })

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(flat_nodes, f, ensure_ascii=False, indent=2)

        print(f'✅ 扁平化树结构已导出到: {output_file}')
        return flat_nodes

    def export_path_enumeration(self, output_file: str = 'label_tree_path.json'):
        """
        导出路径枚举方式(存储完整路径)

        这种方式在查询祖先节点时非常高效

        Args:
            output_file: 输出文件路径
        """
        def get_path(node_id: str) -> str:
            """获取节点的完整路径"""
            path_parts = [node_id]
            current_id = node_id

            while True:
                parent = next((e['source'] for e in self.edges
                             if e['target'] == current_id and e['label'] in ['hasPart', 'hasMember', 'attachedTo']),
                            None)
                if not parent:
                    break
                path_parts.insert(0, parent)
                current_id = parent

            return '/' + '/'.join(path_parts)

        path_nodes = []
        for node in self.nodes:
            path_node = {
                'id': node['id'],
                'label': node['label'],
                'type': node['type'],
                'level': node.get('level'),
                'path': get_path(node['id']),
                'depth': get_path(node['id']).count('/') - 1
            }
            path_nodes.append(path_node)

        # 添加招标文件
        if not any(n['id'] == '招标文件' for n in path_nodes):
            path_nodes.insert(0, {
                'id': '招标文件',
                'label': '招标文件',
                'type': 'normal',
                'level': 1,
                'path': '/招标文件',
                'depth': 0
            })

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(path_nodes, f, ensure_ascii=False, indent=2)

        print(f'✅ 路径枚举结构已导出到: {output_file}')
        return path_nodes

    def export_adjacency_list(self, output_file: str = 'label_tree_adjacency.json'):
        """
        导出邻接表方式

        这种方式在图数据库中常用,查询效率高

        Args:
            output_file: 输出文件路径
        """
        adjacency_data = {
            'nodes': self.nodes,
            'edges': [
                {
                    'from': e['source'],
                    'to': e['target'],
                    'type': e['label']
                }
                for e in self.edges
            ]
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(adjacency_data, f, ensure_ascii=False, indent=2)

        print(f'✅ 邻接表结构已导出到: {output_file}')
        return adjacency_data

    def print_storage_methods_comparison(self):
        """打印各种存储方式的对比说明"""
        print('\n' + '='*80)
        print('📊 深层嵌套数据存储方法对比')
        print('='*80 + '\n')

        comparison = """
1️⃣  嵌套树结构 (Nested Tree / Children Array)
   文件: label_tree_nested.json
   优点:
   - 结构直观,符合人类思维
   - 前端渲染树组件时无需额外处理
   - 适合数据量小、层级不深的场景
   缺点:
   - 深层嵌套时JSON文件体积大
   - 查询特定节点需要递归遍历,效率低
   - 修改节点位置需要重构整个树
   - 不适合频繁更新的场景
   适用场景: 前端展示、配置文件、静态数据

2️⃣  扁平化树结构 (Flat Tree / Parent ID)
   文件: label_tree_flat.json
   优点:
   - 数据扁平,查询单个节点效率高 O(1)
   - 易于存储在关系型数据库(如MySQL)
   - 修改节点位置只需更新parent_id
   - 支持快速添加/删除节点
   缺点:
   - 查询整棵树或子树需要多次查询
   - 前端需要额外处理才能渲染树组件
   适用场景: 关系型数据库、需要频繁增删改的场景、大数据量

3️⃣  路径枚举 (Path Enumeration)
   文件: label_tree_path.json
   优点:
   - 查询祖先节点极快(通过路径前缀匹配)
   - 查询子树也很快(通过路径前缀)
   - 适合读多写少的场景
   缺点:
   - 移动节点时需要更新所有子孙节点的路径
   - 路径字符串占用存储空间较大
   - 节点名称包含特殊字符时需要转义
   适用场景: 文件系统、目录结构、权限系统

4️⃣  邻接表 (Adjacency List)
   文件: label_tree_adjacency.json
   优点:
   - 最灵活,支持复杂图结构(不仅是树)
   - 图数据库(Neo4j, ArangoDB)的标准格式
   - 支持多种关系类型(hasPart, sameAs等)
   - 查询性能优秀(通过索引)
   缺点:
   - 需要图数据库或专门的查询算法
   - 实现复杂度较高
   适用场景: 知识图谱、社交网络、推荐系统、复杂关系网络

5️⃣  闭包表 (Closure Table) - 未实现,仅说明
   需要两张表: nodes表 + tree_paths表
   tree_paths表存储所有祖先-后代关系对:
   | ancestor | descendant | depth |
   |----------|------------|-------|
   | 招标文件  | 招标文件    | 0     |
   | 招标文件  | 采购项目    | 1     |
   | 招标文件  | 项目基本信息| 2     |
   | ...      | ...        | ...   |

   优点:
   - 查询子树/祖先树只需简单JOIN,性能极佳
   - 支持快速计算节点深度
   - 适合复杂树查询(如查找所有叶子节点)
   缺点:
   - 存储冗余大(O(n²)空间复杂度)
   - 插入/删除节点需要更新多条记录
   适用场景: 大型组织架构、复杂分类系统

6️⃣  Nested Set Model (嵌套集合模型) - 未实现,仅说明
   每个节点有left和right值,表示在先序遍历中的位置:
   | id       | label      | lft | rgt |
   |----------|------------|-----|-----|
   | 招标文件  | 招标文件    | 1   | 54  |
   | 采购项目  | 采购项目    | 2   | 53  |
   | ...      | ...        | ... | ... |

   优点:
   - 查询子树非常快: WHERE lft > X AND rgt < Y
   - 无需递归即可获取整棵子树
   缺点:
   - 插入/删除节点时需要更新大量节点的lft/rgt值
   - 不适合频繁修改的场景
   适用场景: 读多写少的分类系统、论坛主题树

🎯 推荐方案:

对于您的招标文件知识图谱场景,推荐使用:

方案A (简单场景): 扁平化树结构 (Flat Tree)
- 如果主要是CRUD操作,不频繁查询整棵树
- 使用MySQL/PostgreSQL等关系型数据库
- 前端渲染时用递归函数构建树

方案B (复杂场景): 邻接表 + 图数据库
- 如果有复杂的关系查询需求(如sameAs, referTo等)
- 使用Neo4j或ArangoDB图数据库
- 支持复杂的图遍历查询(祖先、后代、最短路径等)

方案C (混合方案): 扁平化 + 缓存
- 数据库用扁平化存储(便于修改)
- Redis缓存构建好的嵌套树(便于前端读取)
- 数据更新时清除缓存,按需重建

"""
        print(comparison)


def main():
    """主函数"""
    import sys
    import io

    # 设置stdout为UTF-8编码
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    exporter = LabelTreeExporter()

    print('🚀 开始导出知识图谱标签树结构...\n')

    # 导出各种格式
    exporter.export_nested_tree()
    exporter.export_flat_tree()
    exporter.export_path_enumeration()
    exporter.export_adjacency_list()

    # 打印对比说明
    exporter.print_storage_methods_comparison()

    print('\n✨ 所有格式导出完成!')


if __name__ == '__main__':
    main()
