import { ref, Ref } from 'vue'

export type TreeBuildStrategy = 'parentId' | 'path' | 'label'

/**
 * 通用树构建逻辑
 * 支持多种数据源和构建策略
 */
export function useTreeBuilder() {
  /**
   * 策略1: 通过 parent_id 构建树结构
   * 适用于扁平化数据，每个节点有 parent_id 字段
   *
   * @param flatData - 扁平化的节点数组
   * @param idField - ID字段名，默认 'line_id'
   * @param parentIdField - 父ID字段名，默认 'parent_id'
   */
  const buildTreeByParentId = (
    flatData: any[],
    idField: string = 'line_id',
    parentIdField: string = 'parent_id',
    relationField: string = 'relation'
  ): any[] => {
    console.log('🏗️ 通过 parent_id 和 relation 构建树结构')
    console.log('  - 数据节点数:', flatData.length)
    console.log('  - ID字段:', idField)
    console.log('  - 父ID字段:', parentIdField)
    console.log('  - 关系字段:', relationField)

    if (!flatData || flatData.length === 0) {
      console.warn('⚠️ 数据为空，无法构建树')
      return []
    }

    const idMap = new Map<string, any>()
    const roots: any[] = []

    // 第一遍：建立ID映射，初始化关系数组
    flatData.forEach(item => {
      const node = {
        ...item,
        children: [],      // contain 关系的子节点
        siblings: [],      // equality 关系的平级节点
        connectedNodes: [] // connect 关系的连接节点
      }
      // 统一转换为字符串类型作为 Map 的 key
      const nodeId = String(item[idField])
      idMap.set(nodeId, node)
    })

    console.log('  - ID映射表大小:', idMap.size)

    // 第二遍：根据 relation 建立不同类型的关系
    let rootCount = 0
    let containCount = 0
    let equalityCount = 0
    let connectCount = 0

    flatData.forEach(item => {
      const nodeId = String(item[idField])
      const node = idMap.get(nodeId)
      const rawParentId = item[parentIdField]
      // 明确判断 null/undefined/空字符串，数字 0 是有效值
      let parentId = (rawParentId !== null && rawParentId !== undefined && rawParentId !== '')
        ? String(rawParentId)
        : null
      const relation = item[relationField]

      console.log(`  🔍 处理节点 ${nodeId}: parent_id原始值=${JSON.stringify(rawParentId)}, 转换后=${parentId}, relation=${relation}`)

      // 跳过文档根节点本身（它应该是真正的根节点）
      if (nodeId === '-1') {
        roots.push(node)
        rootCount++
        console.log(`  📄 文档根节点 (id=-1) 作为根节点`)
        return
      }

      // 如果 parent_id 为空字符串/null/undefined（但不包括数字0）且存在文档根节点(id=-1)，则将其挂到文档根节点
      if (parentId === null && idMap.has('-1')) {
        parentId = '-1'
        // 记录实际父节点ID，供后续 equality/connect 关系查找使用
        node._actualParentId = '-1'
        console.log(`  📄 将根节点元素 ${nodeId} (原parent_id为空) 挂载到文档根节点`)
      }

      if (parentId && idMap.has(parentId)) {
        const relatedNode = idMap.get(parentId)

        // 根据 relation 类型建立不同的关系
        if (relation === 'contain') {
          // contain: 包含关系 - 作为子节点
          relatedNode.children.push(node)
          containCount++
          console.log(`  📦 Contain: ${nodeId} → ${parentId}`)
        } else if (relation === 'equality') {
          // equality: 平级关系 - 找到 relatedNode 的父节点，添加到同一层级
          // parent_id 指向的是平级节点，需要找到那个节点的父节点
          // 优先使用 _actualParentId (处理多层 equality 时记录的真实父节点)
          const relatedNodeParentId = relatedNode._actualParentId !== undefined
            ? relatedNode._actualParentId
            : (relatedNode[parentIdField] ? String(relatedNode[parentIdField]) : null)

          if (relatedNodeParentId && idMap.has(relatedNodeParentId)) {
            // 找到共同的父节点，添加到其 children
            const grandParent = idMap.get(relatedNodeParentId)
            grandParent.children.push(node)
            // 使用内部字段记录真实父节点，不修改原始 parent_id
            node._actualParentId = relatedNodeParentId
            console.log(`  ⚖️ Equality: ${nodeId} ↔ ${parentId}，添加到共同父节点 ${relatedNodeParentId}`)
          } else {
            // relatedNode 是根节点，那当前节点也应该是根节点
            roots.push(node)
            rootCount++
            // 使用内部字段标记为根节点，不修改原始 parent_id
            node._actualParentId = null
            console.log(`  ⚖️ Equality: ${nodeId} ↔ ${parentId}，都作为根节点`)
          }
          equalityCount++
        } else if (relation === 'connect') {
          // connect: 连接关系 - 段落内的行连接（fstline, para_line, para_line2...）
          // parent_id 指向前一行，需要找到共同的父节点（section），添加到同一层级
          // 优先使用 _actualParentId (处理多层 connect 时记录的真实父节点)
          const relatedNodeParentId = relatedNode._actualParentId !== undefined
            ? relatedNode._actualParentId
            : (relatedNode[parentIdField] ? String(relatedNode[parentIdField]) : null)

          if (relatedNodeParentId && idMap.has(relatedNodeParentId)) {
            // 找到共同的父节点（section），添加到其 children
            const grandParent = idMap.get(relatedNodeParentId)
            grandParent.children.push(node)
            // 使用内部字段记录真实父节点，不修改原始 parent_id
            node._actualParentId = relatedNodeParentId
            console.log(`  🔗 Connect: ${nodeId} → ${parentId}，添加到共同父节点 ${relatedNodeParentId}`)
          } else {
            // relatedNode 是根节点，那当前节点也应该是根节点
            roots.push(node)
            rootCount++
            // 使用内部字段标记为根节点，不修改原始 parent_id
            node._actualParentId = null
            console.log(`  🔗 Connect: ${nodeId} → ${parentId}，都作为根节点`)
          }
          connectCount++
        } else {
          // 没有 relation 或未知关系类型，默认作为子节点（向后兼容）
          relatedNode.children.push(node)
          console.log(`  ❓ Unknown/Empty relation: ${nodeId} → ${parentId}`)
        }
      } else {
        // 无父节点或父节点不存在，作为根节点
        roots.push(node)
        rootCount++
      }
    })

    console.log('✅ 树构建完成')
    console.log('  - 根节点数量:', rootCount)
    console.log('  - Contain 关系:', containCount)
    console.log('  - Equality 关系:', equalityCount)
    console.log('  - Connect 关系:', connectCount)

    // 检查树结构
    const checkTree = (node: any, depth: number = 0) => {
      const prefix = '  '.repeat(depth)
      console.log(`${prefix}├─ id=${node[idField]}, class=${node.class}, children=${node.children?.length || 0}`)
      if (node.children && node.children.length > 0 && depth < 3) {
        node.children.slice(0, 5).forEach((child: any) => checkTree(child, depth + 1))
        if (node.children.length > 5) {
          console.log(`${prefix}   ... 还有 ${node.children.length - 5} 个子节点`)
        }
      }
    }
    console.log('🌳 树结构预览:')
    roots.slice(0, 3).forEach(root => checkTree(root))

    return roots
  }

  /**
   * 策略2: 通过路径字段构建树结构
   * 适用于有 directory_path 等路径字段的数据
   *
   * @param nodes - 节点数组
   * @param pathField - 路径字段名，默认 'directory_path'
   */
  const buildTreeByPath = (
    nodes: any[],
    pathField: string = 'directory_path'
  ): any[] => {
    console.log('🏗️ 通过路径字段构建树结构')
    console.log('  - 数据节点数:', nodes.length)
    console.log('  - 路径字段:', pathField)

    if (!nodes || nodes.length === 0) {
      console.warn('⚠️ 数据为空，无法构建树')
      return []
    }

    const pathMap = new Map<string, any>()
    const roots: any[] = []
    let virtualNodeId = -1 // 虚拟节点的ID从-1开始递减

    // 按路径构建树形结构
    nodes.forEach(node => {
      const path = node[pathField]
      if (!path || typeof path !== 'string') {
        // 没有路径的节点作为根节点
        roots.push({ ...node, children: [] })
        return
      }

      const pathParts = path.split('/').filter(part => part.trim())
      let currentPath = ''
      let parentNode: any = null

      // 逐级创建或查找路径节点
      pathParts.forEach((part, index) => {
        currentPath = currentPath ? `${currentPath}/${part}` : part

        if (!pathMap.has(currentPath)) {
          // 创建虚拟路径节点
          const pathNode = {
            line_id: virtualNodeId--,
            text: part,
            class: 'path-node',
            isVirtual: true,
            path: currentPath,
            children: []
          }

          pathMap.set(currentPath, pathNode)

          // 挂载到父节点或根节点
          if (parentNode) {
            parentNode.children.push(pathNode)
          } else {
            roots.push(pathNode)
          }
        }

        parentNode = pathMap.get(currentPath)
      })

      // 将数据节点挂载到最后一级路径节点
      if (parentNode) {
        parentNode.children.push({ ...node, children: [] })
      } else {
        roots.push({ ...node, children: [] })
      }
    })

    console.log('✅ 树构建完成')
    console.log('  - 根节点数量:', roots.length)
    console.log('  - 路径节点数量:', pathMap.size)

    return roots
  }

  /**
   * 策略3: 通过标签字段构建本体树
   * 适用于有 label 字段的数据，按标签层级组织
   *
   * @param nodes - 节点数组
   * @param labelField - 标签字段名，默认 'label'
   */
  const buildTreeByLabel = (
    nodes: any[],
    labelField: string = 'label'
  ): any[] => {
    console.log('🏗️ 通过标签字段构建本体树')
    console.log('  - 数据节点数:', nodes.length)
    console.log('  - 标签字段:', labelField)

    if (!nodes || nodes.length === 0) {
      console.warn('⚠️ 数据为空，无法构建树')
      return []
    }

    const labelTree = new Map<string, any>()
    const allLabelPaths = new Set<string>()
    let virtualNodeId = -1000 // 标签节点从-1000开始

    // 收集所有标签路径
    nodes.forEach(node => {
      const labelValue = node[labelField] || node.class
      if (labelValue && typeof labelValue === 'string' && labelValue.trim()) {
        allLabelPaths.add(labelValue)
      }
    })

    console.log('  - 唯一标签数:', allLabelPaths.size)

    if (allLabelPaths.size === 0) {
      console.warn('⚠️ 数据中没有标签字段，无法构建标签树')
      return []
    }

    // 构建纯标签树结构
    allLabelPaths.forEach(fullPath => {
      const pathParts = fullPath.split('/').filter(part => part.trim())
      let currentLevel = labelTree

      pathParts.forEach((labelName, index) => {
        if (!currentLevel.has(labelName)) {
          currentLevel.set(labelName, {
            fullPath: pathParts.slice(0, index + 1).join('/'),
            children: new Map(),
            items: []
          })
        }
        currentLevel = currentLevel.get(labelName).children
      })
    })

    // 将数据节点挂载到标签树
    nodes.forEach(node => {
      const labelValue = node[labelField] || node.class
      if (!labelValue) return

      const pathParts = labelValue.split('/').filter(part => part.trim())
      let currentLevel = labelTree

      pathParts.forEach((labelName, index) => {
        const labelNode = currentLevel.get(labelName)
        if (labelNode && index === pathParts.length - 1) {
          // 挂载到最后一级标签
          labelNode.items.push(node)
        }
        if (labelNode) {
          currentLevel = labelNode.children
        }
      })
    })

    // 转换为UI节点树
    const convertLabelTreeToNodes = (
      labelMap: Map<string, any>,
      labelPath: string[] = []
    ): any[] => {
      const result: any[] = []

      labelMap.forEach((node, labelName) => {
        const currentPath = [...labelPath, labelName]
        const fullPath = currentPath.join('/')
        const depth = currentPath.length

        // 创建标签节点
        const labelNode: any = {
          line_id: virtualNodeId--,
          text: labelName,
          class: depth === 1 ? 'label-group' : 'label-group-2',
          label: fullPath,
          labelDepth: depth,
          children: [],
          isVirtual: true
        }

        // 递归处理子标签
        if (node.children && node.children.size > 0) {
          const childLabelNodes = convertLabelTreeToNodes(node.children, currentPath)
          labelNode.children.push(...childLabelNodes)
        }

        // 添加挂载的数据节点
        if (node.items && node.items.length > 0) {
          labelNode.children.push(...node.items.map((item: any) => ({
            ...item,
            children: item.children || []
          })))
        }

        result.push(labelNode)
      })

      return result
    }

    const result = convertLabelTreeToNodes(labelTree)

    console.log('✅ 本体树构建完成')
    console.log('  - 根节点数量:', result.length)

    return result
  }

  /**
   * 通用构建方法 - 根据策略选择构建方式
   */
  const buildTree = (
    data: any[],
    strategy: TreeBuildStrategy,
    options?: {
      idField?: string
      parentIdField?: string
      pathField?: string
      labelField?: string
    }
  ): any[] => {
    switch (strategy) {
      case 'parentId':
        return buildTreeByParentId(
          data,
          options?.idField,
          options?.parentIdField
        )
      case 'path':
        return buildTreeByPath(data, options?.pathField)
      case 'label':
        return buildTreeByLabel(data, options?.labelField)
      default:
        console.error('❌ 未知的构建策略:', strategy)
        return []
    }
  }

  return {
    buildTree,
    buildTreeByParentId,
    buildTreeByPath,
    buildTreeByLabel
  }
}
