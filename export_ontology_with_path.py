"""
知识图谱本体层导出工具 - 扁平化节点 + 路径字段

采用行业标准做法:
1. 底层: 扁平化节点 + 父子关系(adjacency list)
2. 加速: materialized path 字段用于快速查询和展示
3. 分层: 本体层(Ontology) + 实例层(Instance) + 标签层

运行方式:
    python export_ontology_with_path.py

输出:
    1. ontology_nodes.json - 本体节点(扁平化 + path)
    2. ontology_edges.json - 本体关系
    3. ontology_schema.sql - 数据库表结构
    4. ontology_data.sql - 数据库插入语句
"""

import json
from typing import List, Dict, Any, Set
from collections import defaultdict


class OntologyExporter:
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

        # 构建父子关系映射(只处理层级关系: hasPart, hasMember, attachedTo)
        self.parent_map = {}
        self.children_map = defaultdict(list)

        for edge in self.edges:
            if edge['label'] in ['hasPart', 'hasMember', 'attachedTo']:
                # source -> target 表示 source 是 target 的父节点
                self.parent_map[edge['target']] = {
                    'parent_id': edge['source'],
                    'edge_type': edge['label']
                }
                self.children_map[edge['source']].append(edge['target'])

    def calculate_path(self, node_id: str, visited: Set[str] = None) -> str:
        """
        计算节点的完整路径(materialized path)

        Args:
            node_id: 节点ID
            visited: 已访问节点集合(防止循环引用)

        Returns:
            路径字符串, 如: /招标文件/采购项目/采购包/商务要求/商务要求表/商务要求项
        """
        if visited is None:
            visited = set()

        if node_id in visited:
            return f"/[循环:{node_id}]"

        visited.add(node_id)

        # 获取父节点
        parent_info = self.parent_map.get(node_id)

        if parent_info:
            parent_path = self.calculate_path(parent_info['parent_id'], visited)
            return f"{parent_path}/{node_id}"
        else:
            # 根节点
            return f"/{node_id}"

    def calculate_depth(self, path: str) -> int:
        """计算节点深度(根节点深度为0)"""
        return path.count('/') - 1

    def export_flat_with_path(self, output_file: str = 'ontology_nodes.json'):
        """
        导出扁平化节点 + 路径字段

        这是推荐的主要导出格式:
        - 每个节点是独立的记录
        - parent_id: 父节点ID
        - edge_type: 关系类型(hasPart/hasMember/attachedTo)
        - path: 物化路径(用于快速查询和展示)
        - depth: 节点深度(根节点为0)

        Args:
            output_file: 输出文件路径
        """
        flat_nodes = []

        for node in self.nodes:
            node_id = node['id']
            parent_info = self.parent_map.get(node_id)
            path = self.calculate_path(node_id)

            flat_node = {
                'id': node_id,
                'label': node['label'],
                'type': node['type'],
                'level': node.get('level'),
                'parent_id': parent_info['parent_id'] if parent_info else None,
                'edge_type': parent_info['edge_type'] if parent_info else None,
                'path': path,
                'depth': self.calculate_depth(path),
                'is_leaf': node_id not in self.children_map,  # 是否叶子节点
                'children_count': len(self.children_map.get(node_id, []))  # 子节点数量
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
                'edge_type': None,
                'path': '/招标文件',
                'depth': 0,
                'is_leaf': False,
                'children_count': len(self.children_map.get('招标文件', []))
            })

        # 按路径排序(方便查看层级结构)
        flat_nodes.sort(key=lambda x: x['path'])

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(flat_nodes, f, ensure_ascii=False, indent=2)

        print(f'✅ 扁平化节点(含路径)已导出到: {output_file}')
        print(f'   共 {len(flat_nodes)} 个本体节点')
        return flat_nodes

    def export_edges(self, output_file: str = 'ontology_edges.json'):
        """
        导出本体关系边

        包含所有类型的关系:
        - hasPart: 部分关系
        - hasMember: 成员关系
        - attachedTo: 附属关系
        - sameAs: 等价关系
        - instanceOf: 实例关系
        - referTo: 引用关系

        Args:
            output_file: 输出文件路径
        """
        edges_data = []

        for edge in self.edges:
            edge_record = {
                'id': edge['id'],
                'from_node': edge['source'],
                'to_node': edge['target'],
                'edge_type': edge['label'],
                'is_hierarchical': edge['label'] in ['hasPart', 'hasMember', 'attachedTo']
            }
            edges_data.append(edge_record)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(edges_data, f, ensure_ascii=False, indent=2)

        print(f'✅ 本体关系已导出到: {output_file}')
        print(f'   共 {len(edges_data)} 条关系')
        return edges_data

    def generate_sql_schema(self, output_file: str = 'ontology_schema.sql'):
        """
        生成数据库表结构SQL

        包括三张表:
        1. ontology_nodes: 本体节点表
        2. ontology_edges: 本体关系表
        3. document_instances: 文档实例表(示例)

        Args:
            output_file: 输出文件路径
        """
        sql = """-- ============================================
-- 知识图谱本体层数据库表结构
-- ============================================

-- 1. 本体节点表(扁平化 + 路径字段)
CREATE TABLE IF NOT EXISTS ontology_nodes (
    id VARCHAR(100) PRIMARY KEY COMMENT '节点ID',
    label VARCHAR(200) NOT NULL COMMENT '节点标签',
    type VARCHAR(50) NOT NULL DEFAULT 'normal' COMMENT '节点类型: normal/doc/supplement',
    level INT COMMENT '层级(1或2)',
    parent_id VARCHAR(100) COMMENT '父节点ID',
    edge_type VARCHAR(50) COMMENT '与父节点的关系类型: hasPart/hasMember/attachedTo',
    path VARCHAR(500) NOT NULL COMMENT '物化路径: /招标文件/采购项目/...',
    depth INT NOT NULL DEFAULT 0 COMMENT '节点深度(根节点为0)',
    is_leaf BOOLEAN DEFAULT FALSE COMMENT '是否叶子节点',
    children_count INT DEFAULT 0 COMMENT '子节点数量',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_parent_id (parent_id),
    INDEX idx_path (path),
    INDEX idx_depth (depth),
    INDEX idx_type (type),
    INDEX idx_is_leaf (is_leaf),
    FOREIGN KEY (parent_id) REFERENCES ontology_nodes(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='本体节点表';

-- 2. 本体关系表
CREATE TABLE IF NOT EXISTS ontology_edges (
    id VARCHAR(50) PRIMARY KEY COMMENT '边ID',
    from_node VARCHAR(100) NOT NULL COMMENT '源节点ID',
    to_node VARCHAR(100) NOT NULL COMMENT '目标节点ID',
    edge_type VARCHAR(50) NOT NULL COMMENT '关系类型: hasPart/hasMember/attachedTo/sameAs/instanceOf/referTo',
    is_hierarchical BOOLEAN DEFAULT FALSE COMMENT '是否层级关系',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_from_node (from_node),
    INDEX idx_to_node (to_node),
    INDEX idx_edge_type (edge_type),
    INDEX idx_hierarchical (is_hierarchical),
    FOREIGN KEY (from_node) REFERENCES ontology_nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (to_node) REFERENCES ontology_nodes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='本体关系表';

-- 3. 文档实例表(示例 - 存储实际文档中的片段)
CREATE TABLE IF NOT EXISTS document_instances (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '实例ID',
    document_id VARCHAR(100) NOT NULL COMMENT '文档ID',
    section_id VARCHAR(200) COMMENT '章节ID',
    content TEXT COMMENT '文本内容',
    ontology_node_id VARCHAR(100) NOT NULL COMMENT '本体节点ID(打的标签)',
    ontology_path VARCHAR(500) COMMENT '本体路径(冗余,方便查询)',
    page_number INT COMMENT '页码',
    position_info JSON COMMENT '位置信息(bbox等)',
    confidence FLOAT COMMENT '标签置信度',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_document_id (document_id),
    INDEX idx_ontology_node_id (ontology_node_id),
    INDEX idx_ontology_path (ontology_path),
    FULLTEXT INDEX idx_content (content),
    FOREIGN KEY (ontology_node_id) REFERENCES ontology_nodes(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档实例表';

-- ============================================
-- 常用查询示例
-- ============================================

-- 查询1: 查找某个节点的所有子孙节点(使用路径前缀)
-- SELECT * FROM ontology_nodes
-- WHERE path LIKE '/招标文件/采购项目/采购包/商务要求/%';

-- 查询2: 查找某个节点的所有祖先节点(使用路径拆分)
-- 方法1: 递归CTE (MySQL 8.0+)
-- WITH RECURSIVE ancestors AS (
--     SELECT * FROM ontology_nodes WHERE id = '商务要求项'
--     UNION ALL
--     SELECT n.* FROM ontology_nodes n
--     INNER JOIN ancestors a ON n.id = a.parent_id
-- )
-- SELECT * FROM ancestors;

-- 查询3: 查找所有叶子节点
-- SELECT * FROM ontology_nodes WHERE is_leaf = TRUE;

-- 查询4: 按深度分组统计
-- SELECT depth, COUNT(*) as node_count
-- FROM ontology_nodes
-- GROUP BY depth
-- ORDER BY depth;

-- 查询5: 查找某个文档中所有"商务要求"相关的片段
-- SELECT d.*, n.path
-- FROM document_instances d
-- INNER JOIN ontology_nodes n ON d.ontology_node_id = n.id
-- WHERE d.document_id = 'DOC123'
--   AND n.path LIKE '%/商务要求/%'
-- ORDER BY d.page_number, d.section_id;

-- 查询6: 统计每个本体节点的实例数量
-- SELECT
--     n.id,
--     n.label,
--     n.path,
--     COUNT(d.id) as instance_count
-- FROM ontology_nodes n
-- LEFT JOIN document_instances d ON n.id = d.ontology_node_id
-- GROUP BY n.id, n.label, n.path
-- ORDER BY instance_count DESC;
"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(sql)

        print(f'✅ 数据库表结构已导出到: {output_file}')
        return sql

    def generate_sql_data(self, output_file: str = 'ontology_data.sql'):
        """
        生成数据插入SQL语句

        Args:
            output_file: 输出文件路径
        """
        # 先导出节点和边数据
        nodes = self.export_flat_with_path('temp_nodes.json')
        edges = self.export_edges('temp_edges.json')

        sql_lines = [
            "-- ============================================",
            "-- 知识图谱本体层数据插入",
            "-- ============================================\n",
            "-- 插入本体节点",
            "INSERT INTO ontology_nodes (id, label, type, level, parent_id, edge_type, path, depth, is_leaf, children_count) VALUES"
        ]

        # 生成节点插入语句
        node_values = []
        for node in nodes:
            parent_id = f"'{node['parent_id']}'" if node['parent_id'] else "NULL"
            edge_type = f"'{node['edge_type']}'" if node['edge_type'] else "NULL"
            level = node['level'] if node['level'] else "NULL"

            value = f"('{node['id']}', '{node['label']}', '{node['type']}', {level}, {parent_id}, {edge_type}, '{node['path']}', {node['depth']}, {str(node['is_leaf']).lower()}, {node['children_count']})"
            node_values.append(value)

        sql_lines.append(',\n'.join(node_values) + ';\n')

        # 生成边插入语句
        sql_lines.append("\n-- 插入本体关系")
        sql_lines.append("INSERT INTO ontology_edges (id, from_node, to_node, edge_type, is_hierarchical) VALUES")

        edge_values = []
        for edge in edges:
            value = f"('{edge['id']}', '{edge['from_node']}', '{edge['to_node']}', '{edge['edge_type']}', {str(edge['is_hierarchical']).lower()})"
            edge_values.append(value)

        sql_lines.append(',\n'.join(edge_values) + ';\n')

        sql = '\n'.join(sql_lines)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(sql)

        print(f'✅ 数据插入SQL已导出到: {output_file}')

        # 删除临时文件
        import os
        os.remove('temp_nodes.json')
        os.remove('temp_edges.json')

        return sql

    def print_usage_guide(self):
        """打印使用指南"""
        guide = """
================================================================================
📖 知识图谱本体层使用指南
================================================================================

一、数据结构说明

1. ontology_nodes.json (本体节点 - 扁平化 + 路径)
   ├─ 每个节点是独立记录
   ├─ parent_id: 指向父节点(adjacency list模式)
   ├─ path: 物化路径(materialized path)用于快速查询
   ├─ depth: 节点深度(根节点为0)
   ├─ is_leaf: 是否叶子节点
   └─ children_count: 子节点数量

2. ontology_edges.json (本体关系)
   ├─ 存储所有节点间的关系
   ├─ is_hierarchical: 标记是否为层级关系
   └─ 支持多种关系类型(hasPart/sameAs等)

二、推荐使用方式

✅ 方案: 扁平化 + 路径字段 + 关系型数据库

适用场景: 大多数业务场景
数据库: MySQL 8.0+ / PostgreSQL
存储结构:
  - ontology_nodes表: 存储扁平节点 + path字段
  - ontology_edges表: 存储关系(可选,用于复杂查询)
  - document_instances表: 存储文档实例,通过ontology_node_id关联

查询优势:
  ✓ 查单个节点: O(1) 通过ID直接查
  ✓ 查子树: WHERE path LIKE '/招标文件/采购项目/%'
  ✓ 查祖先: 递归CTE或拆分path
  ✓ 查叶子节点: WHERE is_leaf = TRUE
  ✓ 统计实例: LEFT JOIN document_instances

修改优势:
  ✓ 添加节点: 插入一条记录 + 计算path
  ✓ 删除节点: 删除记录 + 更新子节点
  ✓ 移动节点: 更新parent_id + 重算path
  ✓ 批量操作: 支持事务保证一致性

三、核心概念

1. 本体层(Ontology Layer)
   - 定义概念和关系(如: 商务要求、资格要求)
   - 相对稳定,不频繁变动
   - 本脚本导出的就是本体层

2. 实例层(Instance Layer)
   - 实际文档中的片段(如: 文档123的第5页的商务要求段落)
   - 通过 instanceOf 关系连接到本体节点
   - 存储在 document_instances 表

3. 标签层(Label Layer)
   - 模型输出的标签(只需要叶子节点ID)
   - 显示时通过path字段补全层级信息
   - 例: 只存"商务要求项",展示时显示"招标文件/采购项目/.../商务要求项"

四、数据库部署步骤

1. 创建数据库:
   CREATE DATABASE tender_kg DEFAULT CHARSET=utf8mb4;
   USE tender_kg;

2. 导入表结构:
   source ontology_schema.sql;

3. 导入数据:
   source ontology_data.sql;

4. 验证数据:
   SELECT COUNT(*) FROM ontology_nodes;  -- 应该有27个节点
   SELECT COUNT(*) FROM ontology_edges;  -- 应该有26条关系

五、常用查询示例

1. 查找"商务要求"下的所有子节点:
   SELECT * FROM ontology_nodes
   WHERE path LIKE '%/商务要求/%';

2. 查找所有叶子节点(可用于模型标签):
   SELECT id, label, path FROM ontology_nodes
   WHERE is_leaf = TRUE;

3. 查找某个文档中"资格要求"相关的所有片段:
   SELECT d.content, n.path
   FROM document_instances d
   JOIN ontology_nodes n ON d.ontology_node_id = n.id
   WHERE d.document_id = 'DOC123'
     AND n.path LIKE '%/资格要求/%';

4. 统计每个本体节点的实例数量:
   SELECT
       n.label,
       n.path,
       COUNT(d.id) as count
   FROM ontology_nodes n
   LEFT JOIN document_instances d ON n.id = d.ontology_node_id
   GROUP BY n.id
   ORDER BY count DESC;

六、与前端集成

1. 获取树结构(用于展示):
   - 方法A: 前端递归构建(从扁平数据)
   - 方法B: 后端接口返回已构建的树

2. Cytoscape.js可视化:
   - nodes: 从 ontology_nodes 读取
   - edges: 从 ontology_edges 读取
   - 高亮: 使用 path LIKE 查询相关节点

3. 标签选择器:
   - 只显示叶子节点(is_leaf = TRUE)
   - 辅助显示完整路径(path字段)

七、性能优化建议

1. 索引优化:
   ✓ path字段加索引(支持前缀查询)
   ✓ parent_id加索引(支持递归查询)
   ✓ depth加索引(支持按层查询)

2. 缓存策略:
   - 本体数据不常变化,可以全量缓存到Redis
   - key: ontology:nodes, ontology:edges
   - 数据更新时清除缓存

3. 查询优化:
   - 优先使用path字段查询(避免递归)
   - 复杂图遍历考虑使用图数据库(Neo4j)

================================================================================
"""
        print(guide)


def main():
    """主函数"""
    import sys
    import io

    # 设置stdout为UTF-8编码
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    exporter = OntologyExporter()

    print('🚀 开始导出知识图谱本体层(扁平化 + 路径)...\n')

    # 导出JSON格式
    exporter.export_flat_with_path()
    exporter.export_edges()

    # 导出SQL格式
    exporter.generate_sql_schema()
    exporter.generate_sql_data()

    print()

    # 打印使用指南
    exporter.print_usage_guide()

    print('\n✨ 所有文件导出完成!')
    print('\n📦 生成的文件:')
    print('   1. ontology_nodes.json - 本体节点(扁平化 + 路径)')
    print('   2. ontology_edges.json - 本体关系')
    print('   3. ontology_schema.sql - 数据库表结构')
    print('   4. ontology_data.sql - 数据插入SQL')


if __name__ == '__main__':
    main()
