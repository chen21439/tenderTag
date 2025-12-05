/**
 * sameAs 关系处理逻辑
 * 处理 sameAs 等价关系的查找和高亮
 */

import type { GraphEdge } from './graphData'

/**
 * 查找节点的所有 sameAs 等价节点（双向查找）
 * @param nodeId - 当前节点 ID
 * @param edges - 所有边
 * @returns sameAs 等价节点 ID 集合和相关边 ID 集合
 */
export const findSameAsRelatives = (
  nodeId: string,
  edges: GraphEdge[]
): { relatives: Set<string>; relatedEdges: Set<string> } => {
  const relatives = new Set<string>()
  const relatedEdges = new Set<string>()
  const visited = new Set<string>([nodeId])

  // BFS 查找所有通过 sameAs 连接的节点
  const queue = [nodeId]

  while (queue.length > 0) {
    const currentId = queue.shift()!

    edges.forEach(edge => {
      if (edge.label !== 'sameAs') return

      let relativeId: string | null = null

      if (edge.source === currentId) {
        relativeId = edge.target
      } else if (edge.target === currentId) {
        relativeId = edge.source
      }

      if (relativeId && !visited.has(relativeId)) {
        visited.add(relativeId)
        relatives.add(relativeId)
        relatedEdges.add(edge.id)
        queue.push(relativeId)
      } else if (relativeId && visited.has(relativeId)) {
        // 已访问的节点，但仍需记录边
        relatedEdges.add(edge.id)
      }
    })
  }

  return { relatives, relatedEdges }
}

/**
 * 扩展节点集合，包含所有 sameAs 等价节点
 * @param nodeIds - 原始节点 ID 集合
 * @param edges - 所有边
 * @returns 扩展后的节点 ID 集合和 sameAs 边集合
 */
export const expandWithSameAsRelatives = (
  nodeIds: Set<string>,
  edges: GraphEdge[]
): { expandedNodes: Set<string>; sameAsEdges: Set<string> } => {
  const expandedNodes = new Set<string>(nodeIds)
  const sameAsEdges = new Set<string>()

  nodeIds.forEach(nodeId => {
    const { relatives, relatedEdges } = findSameAsRelatives(nodeId, edges)
    relatives.forEach(relativeId => expandedNodes.add(relativeId))
    relatedEdges.forEach(edgeId => sameAsEdges.add(edgeId))
  })

  return { expandedNodes, sameAsEdges }
}
