import { ref, Ref, computed } from 'vue'

export interface TreeEditorOptions {
  onNodeMove?: (nodeId: string, newParentId: string | null) => Promise<void>
  onLabelUpdate?: (nodeId: string, newLabel: string) => Promise<void>
  onNodeDelete?: (nodeId: string) => Promise<void>
}

/**
 * 树编辑逻辑封装
 * 提供节点移动、标签编辑、删除等功能
 */
export function useTreeEditor(
  treeData: Ref<any[]>,
  options: TreeEditorOptions = {}
) {
  // 编辑模式
  const editMode = ref(false)

  // 选中的节点ID列表（支持多选）
  const selectedNodeIds = ref<any[]>([])

  // 展开的节点集合
  const expandedNodes = ref(new Set<number>())

  /**
   * 在树中查找节点
   */
  const findNodeById = (nodes: any[], id: any): any => {
    for (const node of nodes) {
      if (node.line_id === id || node.id === id) {
        return node
      }
      if (node.children && node.children.length > 0) {
        const found = findNodeById(node.children, id)
        if (found) return found
      }
    }
    return null
  }

  /**
   * 查找节点的父节点
   */
  const findParentNode = (nodes: any[], targetId: any, parent: any = null): any => {
    for (const node of nodes) {
      if (node.line_id === targetId || node.id === targetId) {
        return parent
      }
      if (node.children && node.children.length > 0) {
        const found = findParentNode(node.children, targetId, node)
        if (found !== null) return found
      }
    }
    return null
  }

  /**
   * 从树中移除节点
   */
  const removeNodeFromTree = (nodes: any[], targetId: any): any | null => {
    for (let i = 0; i < nodes.length; i++) {
      const node = nodes[i]
      const nodeId = node.id || node.line_id
      console.log(`🔍 检查节点: ${nodeId}, 目标: ${targetId}, 匹配: ${nodeId == targetId}`)
      // 使用 == 进行宽松比较，允许字符串和数字匹配
      if (node.line_id == targetId || node.id == targetId) {
        // 找到目标节点，从数组中移除
        const [removed] = nodes.splice(i, 1)
        console.log(`✅ 找到并移除节点: ${nodeId}`)
        return removed
      }
      if (node.children && node.children.length > 0) {
        const removed = removeNodeFromTree(node.children, targetId)
        if (removed) return removed
      }
    }
    return null
  }

  /**
   * 移动节点到新的父节点下
   * @param nodeId - 要移动的节点ID
   * @param newParentId - 新父节点ID，null表示移动到根节点
   */
  const moveNode = async (nodeId: any, newParentId: any | null) => {
    console.log('🔄 移动节点:', { nodeId, newParentId })

    // 直接调用回调函数（API调用），让后端处理数据更新
    if (options.onNodeMove) {
      try {
        await options.onNodeMove(nodeId, newParentId)
        console.log('✅ 节点移动成功，等待数据重新加载')
        // 数据会由父组件重新加载，不需要手动操作树结构
      } catch (error) {
        console.error('❌ 节点移动失败:', error)
      }
    }
  }

  /**
   * 更新节点标签
   * @param nodeId - 节点ID
   * @param newLabel - 新标签值
   */
  const updateLabel = async (nodeId: any, newLabel: string) => {
    console.log('✏️ 更新节点标签:', { nodeId, newLabel })

    const node = findNodeById(treeData.value, nodeId)
    if (!node) {
      console.error('❌ 未找到节点:', nodeId)
      return
    }

    const oldLabel = node.label
    node.label = newLabel

    // 调用回调函数（可选，用于API调用）
    if (options.onLabelUpdate) {
      try {
        await options.onLabelUpdate(nodeId, newLabel)
        console.log('✅ 标签更新成功')
      } catch (error) {
        console.error('❌ 标签更新失败:', error)
        // 回滚
        node.label = oldLabel
      }
    }

    // 触发响应式更新
    treeData.value = [...treeData.value]
  }

  /**
   * 删除节点
   * @param nodeId - 要删除的节点ID
   */
  const deleteNode = async (nodeId: any) => {
    console.log('🗑️ 删除节点:', nodeId)

    const removedNode = removeNodeFromTree(treeData.value, nodeId)
    if (!removedNode) {
      console.error('❌ 未找到要删除的节点:', nodeId)
      return
    }

    // 调用回调函数（可选，用于API调用）
    if (options.onNodeDelete) {
      try {
        await options.onNodeDelete(nodeId)
        console.log('✅ 节点删除成功')
      } catch (error) {
        console.error('❌ 节点删除失败:', error)
        // 回滚：将节点添加回根节点
        treeData.value.push(removedNode)
      }
    }

    // 触发响应式更新
    treeData.value = [...treeData.value]
  }

  /**
   * 切换节点选中状态
   */
  const toggleNodeSelection = (nodeId: any) => {
    const index = selectedNodeIds.value.indexOf(nodeId)
    if (index > -1) {
      selectedNodeIds.value.splice(index, 1)
    } else {
      selectedNodeIds.value.push(nodeId)
    }
  }

  /**
   * 清空选中
   */
  const clearSelection = () => {
    selectedNodeIds.value = []
  }

  /**
   * 切换编辑模式
   */
  const toggleEditMode = () => {
    editMode.value = !editMode.value
    if (!editMode.value) {
      clearSelection()
    }
  }

  /**
   * 展开/折叠节点
   */
  const toggleNode = (nodeId: any) => {
    if (expandedNodes.value.has(nodeId)) {
      expandedNodes.value.delete(nodeId)
    } else {
      expandedNodes.value.add(nodeId)
    }
    expandedNodes.value = new Set(expandedNodes.value)
  }

  /**
   * 展开所有节点
   */
  const expandAll = () => {
    const collectIds = (nodes: any[]) => {
      const ids: any[] = []
      nodes.forEach(node => {
        ids.push(node.line_id || node.id)
        if (node.children && node.children.length > 0) {
          ids.push(...collectIds(node.children))
        }
      })
      return ids
    }
    expandedNodes.value = new Set(collectIds(treeData.value))
  }

  /**
   * 折叠所有节点
   */
  const collapseAll = () => {
    expandedNodes.value = new Set()
  }

  return {
    // 状态
    editMode,
    selectedNodeIds,
    expandedNodes,

    // 方法
    findNodeById,
    findParentNode,
    moveNode,
    updateLabel,
    deleteNode,
    toggleNodeSelection,
    clearSelection,
    toggleEditMode,
    toggleNode,
    expandAll,
    collapseAll
  }
}
