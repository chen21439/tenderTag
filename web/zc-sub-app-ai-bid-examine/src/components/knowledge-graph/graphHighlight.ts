/**
 * 知识图谱高亮逻辑
 * 处理节点选中后的父子节点高亮
 */

import type { Core } from 'cytoscape'
import type { GraphEdge } from './graphData'
import { findSameAsRelatives } from './sameAsHandler'

/**
 * 递归查找所有祖先节点（向上单条路径）
 * @param nodeId - 当前节点 ID
 * @param edges - 所有边
 * @param ancestors - 已找到的祖先节点集合
 * @param visitedEdges - 已访问的边集合
 */
const findAncestors = (
  nodeId: string,
  edges: GraphEdge[],
  ancestors: Set<string>,
  visitedEdges: Set<string>
) => {
  edges.forEach(edge => {
    const isInstanceOf = edge.label === 'instanceOf'
    let parentId: string | null = null

    // 确定父节点
    if (edge.source === nodeId && isInstanceOf) {
      // instanceOf: source -> target，target 是父节点
      parentId = edge.target
    } else if (edge.target === nodeId && !isInstanceOf) {
      // hasPart/hasMember 等: source -> target，source 是父节点
      parentId = edge.source
    }

    if (parentId && !ancestors.has(parentId)) {
      ancestors.add(parentId)
      visitedEdges.add(edge.id)
      // 递归查找父节点的父节点
      findAncestors(parentId, edges, ancestors, visitedEdges)
    }
  })
}

/**
 * 递归查找所有后代节点（向下完全展开）
 * @param nodeId - 当前节点 ID
 * @param edges - 所有边
 * @param descendants - 已找到的后代节点集合
 * @param visitedEdges - 已访问的边集合
 */
const findDescendants = (
  nodeId: string,
  edges: GraphEdge[],
  descendants: Set<string>,
  visitedEdges: Set<string>
) => {
  edges.forEach(edge => {
    const isInstanceOf = edge.label === 'instanceOf'
    let childId: string | null = null

    // 确定子节点
    if (edge.source === nodeId && !isInstanceOf) {
      // hasPart/hasMember 等: source -> target，target 是子节点
      childId = edge.target
    } else if (edge.target === nodeId && isInstanceOf) {
      // instanceOf: source -> target，source 是子节点
      childId = edge.source
    }

    if (childId && !descendants.has(childId)) {
      descendants.add(childId)
      visitedEdges.add(edge.id)
      // 递归查找子节点的子节点
      findDescendants(childId, edges, descendants, visitedEdges)
    }
  })
}

/**
 * 高亮选中节点的直接父子节点（仅一层）
 * @param cy - Cytoscape 实例
 * @param nodeId - 选中的节点 ID
 * @param edges - 图谱中的所有边
 */
export const highlightDirectParentChild = (
  cy: Core | null,
  nodeId: string,
  edges: GraphEdge[]
) => {
  if (!cy) return

  // 清除之前的高亮
  clearHighlights(cy)

  const parentNodeIds = new Set<string>()
  const childNodeIds = new Set<string>()
  const relatedEdges: string[] = []

  // 处理所有边以找到直接父节点和直接子节点（仅一层）
  edges.forEach(edge => {
    const isInstanceOf = edge.label === 'instanceOf'

    if (edge.source === nodeId) {
      // 该节点是源节点
      if (isInstanceOf) {
        // 对于 instanceOf: source 是子节点（实例），target 是父节点（概念）
        parentNodeIds.add(edge.target)
      } else {
        // 对于 hasPart/hasMember/hasField 等: source 是父节点，target 是子节点
        childNodeIds.add(edge.target)
      }
      relatedEdges.push(edge.id)
    } else if (edge.target === nodeId) {
      // 该节点是目标节点
      if (isInstanceOf) {
        // 对于 instanceOf: target 是父节点（概念），source 是子节点（实例）
        childNodeIds.add(edge.source)
      } else {
        // 对于 hasPart/hasMember/hasField 等: target 是子节点，source 是父节点
        parentNodeIds.add(edge.source)
      }
      relatedEdges.push(edge.id)
    }
  })

  // 查找 sameAs 兄弟节点
  const { relatives: sameAsRelatives, relatedEdges: sameAsEdges } = findSameAsRelatives(nodeId, edges)

  console.log(`🎯 选中节点: ${nodeId}`)
  console.log(`   ⬆️  ${parentNodeIds.size} 个父节点:`, Array.from(parentNodeIds))
  console.log(`   ⬇️  ${childNodeIds.size} 个子节点:`, Array.from(childNodeIds))
  console.log(`   🔗 ${sameAsRelatives.size} 个 sameAs 兄弟:`, Array.from(sameAsRelatives))

  // 将所有节点和边变暗
  cy.nodes().addClass('dimmed')
  cy.edges().addClass('dimmed')

  // 高亮选中的节点（移除变暗效果）
  const selectedNode = cy.getElementById(nodeId)
  selectedNode.removeClass('dimmed')

  // 高亮 sameAs 兄弟节点（与选中节点相同的样式）
  sameAsRelatives.forEach(relativeId => {
    const relativeNode = cy.getElementById(relativeId)
    if (relativeNode.length > 0) {
      relativeNode.removeClass('dimmed')
    }
  })

  // 高亮父节点（橙色边框）
  parentNodeIds.forEach(parentId => {
    const parentNode = cy.getElementById(parentId)
    if (parentNode.length > 0) {
      parentNode.removeClass('dimmed')
      parentNode.addClass('highlighted-parent')
    }
  })

  // 高亮子节点（绿色边框）
  childNodeIds.forEach(childId => {
    const childNode = cy.getElementById(childId)
    if (childNode.length > 0) {
      childNode.removeClass('dimmed')
      childNode.addClass('highlighted-child')
    }
  })

  // 高亮相关的边
  relatedEdges.forEach(edgeId => {
    const edgeElement = cy.getElementById(edgeId)
    if (edgeElement.length > 0) {
      edgeElement.removeClass('dimmed')
      edgeElement.addClass('highlighted')
    }
  })

  // 高亮 sameAs 边
  sameAsEdges.forEach(edgeId => {
    const edgeElement = cy.getElementById(edgeId)
    if (edgeElement.length > 0) {
      edgeElement.removeClass('dimmed')
      edgeElement.addClass('highlighted')
    }
  })
}

/**
 * 高亮选中节点的所有祖先和后代节点（递归）
 * @param cy - Cytoscape 实例
 * @param nodeId - 选中的节点 ID
 * @param edges - 图谱中的所有边
 */
export const highlightAllAncestorsDescendants = (
  cy: Core | null,
  nodeId: string,
  edges: GraphEdge[]
) => {
  if (!cy) return

  // 清除之前的高亮
  clearHighlights(cy)

  const ancestors = new Set<string>()
  const descendants = new Set<string>()
  const relatedEdges = new Set<string>()

  // 向上查找所有祖先（单条路径）
  findAncestors(nodeId, edges, ancestors, relatedEdges)

  // 向下查找所有后代（完全展开）
  findDescendants(nodeId, edges, descendants, relatedEdges)

  // 查找 sameAs 兄弟节点
  const { relatives: sameAsRelatives, relatedEdges: sameAsEdges } = findSameAsRelatives(nodeId, edges)

  console.log(`🎯 选中节点: ${nodeId}`)
  console.log(`   ⬆️  ${ancestors.size} 个祖先节点:`, Array.from(ancestors))
  console.log(`   ⬇️  ${descendants.size} 个后代节点:`, Array.from(descendants))
  console.log(`   🔗 ${sameAsRelatives.size} 个 sameAs 兄弟:`, Array.from(sameAsRelatives))

  // 将所有节点和边变暗
  cy.nodes().addClass('dimmed')
  cy.edges().addClass('dimmed')

  // 高亮选中的节点（移除变暗效果，添加选中样式）
  const selectedNode = cy.getElementById(nodeId)
  selectedNode.removeClass('dimmed')
  selectedNode.addClass('selected')  // 添加蓝色边框

  // 高亮 sameAs 兄弟节点（与选中节点相同的样式）
  sameAsRelatives.forEach(relativeId => {
    const relativeNode = cy.getElementById(relativeId)
    if (relativeNode.length > 0) {
      relativeNode.removeClass('dimmed')
    }
  })

  // 高亮祖先节点（橙色边框）
  ancestors.forEach(ancestorId => {
    const ancestorNode = cy.getElementById(ancestorId)
    if (ancestorNode.length > 0) {
      ancestorNode.removeClass('dimmed')
      ancestorNode.addClass('highlighted-parent')
    }
  })

  // 高亮后代节点（绿色边框）
  descendants.forEach(descendantId => {
    const descendantNode = cy.getElementById(descendantId)
    if (descendantNode.length > 0) {
      descendantNode.removeClass('dimmed')
      descendantNode.addClass('highlighted-child')
    }
  })

  // 高亮相关的边
  relatedEdges.forEach(edgeId => {
    const edgeElement = cy.getElementById(edgeId)
    if (edgeElement.length > 0) {
      edgeElement.removeClass('dimmed')
      edgeElement.addClass('highlighted')
    }
  })

  // 高亮 sameAs 边
  sameAsEdges.forEach(edgeId => {
    const edgeElement = cy.getElementById(edgeId)
    if (edgeElement.length > 0) {
      edgeElement.removeClass('dimmed')
      edgeElement.addClass('highlighted')
    }
  })
}

/**
 * 清除所有高亮
 * @param cy - Cytoscape 实例
 */
export const clearHighlights = (cy: Core | null) => {
  if (!cy) return

  // 移除所有高亮类
  cy.nodes().removeClass('dimmed highlighted-parent highlighted-child selected')
  cy.edges().removeClass('dimmed highlighted selected')

  console.log('✨ 已清除所有高亮')
}

/**
 * 切换要素节点展开/折叠（右键点击）
 * @param cy - Cytoscape 实例
 * @param nodeId - 选中的节点 ID
 * @param edges - 图谱中的所有边
 * @param layout - 布局名称（可选，默认为 'cose'）
 */
export const toggleFieldNodes = (
  cy: Core | null,
  nodeId: string,
  edges: GraphEdge[],
  layout: string = 'cose'
) => {
  if (!cy) return

  // 查找所有 hasAttribute 边，source 是当前节点
  const fieldEdges = edges.filter((e: GraphEdge) => e.source === nodeId && e.label === 'hasAttribute')

  if (fieldEdges.length === 0) {
    console.log(`⚠️ 节点 ${nodeId} 没有要素节点`)
    return
  }

  // 检查第一个要素节点是否可见，以此判断当前状态
  const firstFieldNodeId = fieldEdges[0].target
  const firstFieldNode = cy.getElementById(firstFieldNodeId)
  const isExpanded = firstFieldNode.visible()

  if (isExpanded) {
    console.log(`🔒 折叠节点 ${nodeId} 的要素节点，共 ${fieldEdges.length} 个`)
  } else {
    console.log(`🔓 展开节点 ${nodeId} 的要素节点，共 ${fieldEdges.length} 个`)
  }

  // 切换显示/隐藏
  fieldEdges.forEach((edge: GraphEdge) => {
    const fieldNodeId = edge.target
    const fieldNode = cy.getElementById(fieldNodeId)
    const fieldEdge = cy.getElementById(edge.id)

    if (isExpanded) {
      // 当前已展开，执行折叠
      if (fieldNode.length > 0) {
        fieldNode.hide()
      }
      if (fieldEdge.length > 0) {
        fieldEdge.hide()
      }
    } else {
      // 当前已折叠，执行展开
      if (fieldNode.length > 0) {
        fieldNode.show()
      }
      if (fieldEdge.length > 0) {
        fieldEdge.show()
      }
    }
  })

  // 展开后调整要素节点位置
  if (!isExpanded) {
    // 获取父节点位置
    const parentNode = cy.getElementById(nodeId)
    if (parentNode.length === 0) return

    const parentPos = parentNode.position()
    const radius = 80 // 要素节点环绕半径
    const angleStep = (2 * Math.PI) / fieldEdges.length

    // 将要素节点环绕排列在父节点周围
    fieldEdges.forEach((edge: GraphEdge, index: number) => {
      const fieldNodeId = edge.target
      const fieldNode = cy.getElementById(fieldNodeId)

      if (fieldNode.length > 0) {
        const angle = angleStep * index
        const x = parentPos.x + radius * Math.cos(angle)
        const y = parentPos.y + radius * Math.sin(angle)

        // 使用动画移动到目标位置
        fieldNode.animate({
          position: { x, y }
        }, {
          duration: 800,
          easing: 'ease-out'
        })
      }
    })

    console.log(`📐 已将 ${fieldEdges.length} 个要素节点环绕排列在父节点周围`)
  }
}

/**
 * 初始化时隐藏所有要素节点
 * @param cy - Cytoscape 实例
 */
export const hideAllFieldNodes = (cy: Core | null) => {
  if (!cy) return

  // 隐藏所有要素节点
  cy.nodes().forEach(node => {
    if (node.data('type') === 'element') {
      node.hide()
    }
  })

  // 隐藏所有 hasAttribute 边
  cy.edges().forEach(edge => {
    if (edge.data('label') === 'hasAttribute') {
      edge.hide()
    }
  })

  console.log('👁️ 已隐藏所有要素节点')
}
