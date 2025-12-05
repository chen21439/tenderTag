/**
 * 知识图谱数据构建模块
 * 从 ontology 数据构建图谱节点和边
 */

export interface GraphNode {
  id: string
  label: string
  type: string
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  label: string
}

export interface OntologyNode {
  id?: string
  label: string
  type?: string
  parent_id?: string
  edge_type?: string
  [key: string]: any
}

/**
 * 从 ontology 数据构建图谱
 * @param ontologyData ontology 扁平化数据
 * @returns { nodes, edges }
 */
export function buildGraphFromOntology(ontologyData: OntologyNode[]): {
  nodes: GraphNode[]
  edges: GraphEdge[]
} {
  console.log('🔧 开始从 ontology 数据构建图谱')
  console.log('📊 ontology 数据节点数:', ontologyData.length)

  const nodes: GraphNode[] = []
  const edges: GraphEdge[] = []
  const nodeIdSet = new Set<string>() // 用于检测重复ID

  // 添加所有节点（过滤掉无效节点和重复ID）
  ontologyData.forEach((node: OntologyNode) => {
    const nodeId = node.id || node.label

    // 跳过没有有效ID的节点
    if (!nodeId || nodeId.trim() === '') {
      console.warn('⚠️ 跳过无效节点（ID为空）:', node)
      return
    }

    // 跳过没有有效label的节点
    if (!node.label || node.label.trim() === '') {
      console.warn('⚠️ 跳过无效节点（label为空）:', node)
      return
    }

    // 跳过重复ID的节点
    if (nodeIdSet.has(nodeId)) {
      console.warn('⚠️ 跳过重复节点（ID已存在）:', nodeId, node)
      return
    }

    nodeIdSet.add(nodeId)
    nodes.push({
      id: nodeId,
      label: node.label,
      type: node.type || 'normal'
    })
  })

  // 从 parent_id 和 edge_type 构建边
  let edgeId = 0
  // nodeIdSet 已经在上面定义了，这里直接使用

  ontologyData.forEach((node: OntologyNode) => {
    if (node.parent_id && node.edge_type) {
      const targetId = node.id || node.label

      // 跳过无效的边（source或target不存在）
      if (!targetId || !nodeIdSet.has(node.parent_id) || !nodeIdSet.has(targetId)) {
        console.warn('⚠️ 跳过无效边:', {
          parent: node.parent_id,
          target: targetId,
          type: node.edge_type
        })
        return
      }

      edges.push({
        id: `edge_${edgeId++}`,
        source: node.parent_id,
        target: targetId,
        label: node.edge_type
      })
    }
  })

  console.log('📊 构建完成:')
  console.log('  - 节点数:', nodes.length)
  console.log('  - 边数:', edges.length)

  // 调试：显示前几个节点和边
  if (nodes.length > 0) {
    console.log('  - 前3个节点:', nodes.slice(0, 3))
  }
  if (edges.length > 0) {
    console.log('  - 前3条边:', edges.slice(0, 3))
  }

  // 检查边的匹配情况
  const unmatchedEdges = edges.filter(e => !nodeIdSet.has(e.source) || !nodeIdSet.has(e.target))
  if (unmatchedEdges.length > 0) {
    console.warn('⚠️ 有', unmatchedEdges.length, '条边无法匹配到节点')
    console.warn('  示例:', unmatchedEdges.slice(0, 3))
  }

  return { nodes, edges }
}

/**
 * 为边添加唯一前缀，避免与节点ID冲突
 * @param edges 边数组
 * @returns 处理后的边数组
 */
export function addEdgeIdPrefix(edges: GraphEdge[]): GraphEdge[] {
  return edges.map(edge => {
    const edgeId = edge.id || `edge_${edges.indexOf(edge)}`
    return {
      ...edge,
      id: edgeId.toString().startsWith('edge_') ? edgeId : `edge_${edgeId}`
    }
  })
}
