-- ============================================
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
