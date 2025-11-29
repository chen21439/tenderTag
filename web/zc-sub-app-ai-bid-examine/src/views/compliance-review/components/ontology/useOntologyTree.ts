import { ref, Ref } from 'vue'

/**
 * 本体树构建逻辑
 * 用于处理多级标签路径的树形结构构建
 */
export function useOntologyTree() {
  // 全局field节点ID计数器，确保每个field节点都有唯一的line_id
  let globalFieldNodeId = -10000

  /**
   * 递归扁平化所有节点（包括嵌套子节点），清除原始 children
   */
  const flattenAllNodes = (nodes: any[]): any[] => {
    const flattened: any[] = []

    const traverse = (nodeList: any[]) => {
      nodeList.forEach(node => {
        // 先保存原始 children 用于递归
        const originalChildren = node.children

        // 创建节点副本，清除原始 children 和 content
        const cleanedNode = {
          ...node,
          children: [], // 清空 children
          content: undefined // 清除 content
        }

        // 添加到扁平化列表
        flattened.push(cleanedNode)

        // 递归处理原始 children
        if (originalChildren && Array.isArray(originalChildren) && originalChildren.length > 0) {
          traverse(originalChildren)
        }
      })
    }

    traverse(nodes)
    return flattened
  }

  /**
   * 从扁平化的节点中筛选出有 label 的节点，并提取 label paths
   */
  const extractLabeledNodes = (nodes: any[]): { labeledNodes: any[], allLabelPaths: Set<string> } => {
    const labeledNodes: any[] = []
    const allLabelPaths = new Set<string>()

    nodes.forEach(node => {
      // 检查标签字段：优先使用 label，如果没有则使用 class
      const labelValue = node.label || node.class

      // 如果有标签（包含"/"分隔符或者单个标签名），添加到集合
      if (labelValue && typeof labelValue === 'string' && labelValue.trim()) {
        // 所有标签都添加到路径集合（单个标签作为一级标签，多级标签按层级）
        allLabelPaths.add(labelValue)

        // 如果节点没有 label 字段，将 class 值复制到 label
        if (!node.label) {
          node.label = labelValue
        }

        labeledNodes.push(node)
      }
    })

    return { labeledNodes, allLabelPaths }
  }

  /**
   * 构建纯标签树结构（多级嵌套Map）
   */
  const buildLabelTree = (labelPaths: Set<string>): Map<string, any> => {
    const labelTree = new Map<string, any>()

    labelPaths.forEach(fullPath => {
      const pathParts = fullPath.split('/').filter((part: string) => part.trim())

      let currentLevel = labelTree
      for (let i = 0; i < pathParts.length; i++) {
        const labelName = pathParts[i]

        if (!currentLevel.has(labelName)) {
          currentLevel.set(labelName, {
            fullPath: pathParts.slice(0, i + 1).join('/'),
            children: new Map(),
            items: []
          })
        }

        currentLevel = currentLevel.get(labelName).children
      }
    })

    return labelTree
  }

  /**
   * 将 fields 对象转换为子节点数组
   * @param fields - 字段对象
   * @param parentNode - 父节点（用于继承location信息）
   */
  const convertFieldsToChildren = (fields: any, parentNode?: any): any[] => {
    if (!fields || typeof fields !== 'object' || Object.keys(fields).length === 0) {
      return []
    }

    // 使用全局计数器，不再每次从-10000开始
    const fieldChildren: any[] = []

    // 从父节点继承location和page信息
    // 注意：这里继承的是父节点（数据节点）的location，通常指向标题位置
    // 如果需要精确定位到字段值在content中的位置，需要额外的文本搜索和位置计算
    const inheritedProps: any = {}
    if (parentNode) {
      // 深拷贝location，避免引用同一个对象
      if (parentNode.location) {
        inheritedProps.location = JSON.parse(JSON.stringify(parentNode.location))
      }
      if (parentNode.page !== undefined) inheritedProps.page = parentNode.page
      // 深拷贝boxes，避免引用同一个对象
      if (parentNode.boxes) {
        inheritedProps.boxes = JSON.parse(JSON.stringify(parentNode.boxes))
      }

      // 调试日志：查看继承的位置信息
      if (parentNode.location && parentNode.location[0]) {
        const loc = parentNode.location[0]
        console.log(`📍 Field继承父节点位置: page=${loc.page}, title=${parentNode.title?.substring(0, 30)}`)
      }
    }

    Object.entries(fields).forEach(([key, value]) => {
      let displayValue = ''

      if (value === null || value === undefined || value === '') {
        return // 跳过空值
      }

      if (Array.isArray(value)) {
        // 数组类型：每个元素作为独立子节点
        value.forEach((item, index) => {
          if (item !== null && item !== undefined && item !== '') {
            fieldChildren.push({
              line_id: globalFieldNodeId--,
              text: `${key}[${index}]: ${String(item)}`,
              class: 'field-item',
              isVirtual: true,
              children: [],
              ...inheritedProps
            })
          }
        })
      } else if (typeof value === 'object') {
        // 对象类型：递归展开
        const subFields = convertFieldsToChildren(value, parentNode)
        if (subFields.length > 0) {
          fieldChildren.push({
            line_id: globalFieldNodeId--,
            text: key,
            class: 'field-group',
            isVirtual: true,
            children: subFields,
            ...inheritedProps
          })
        }
      } else {
        // 基本类型：直接显示
        displayValue = String(value)
        fieldChildren.push({
          line_id: globalFieldNodeId--,
          text: `${key}: ${displayValue}`,
          class: 'field-item',
          isVirtual: true,
          children: [],
          ...inheritedProps
        })
      }
    })

    return fieldChildren
  }

  /**
   * 将数据节点挂载到标签树（只挂载 fields 子节点，不显示数据节点本身）
   */
  const mountDataToLabelTree = (labelTree: Map<string, any>, labeledNodes: any[]) => {
    labeledNodes.forEach(node => {
      if (!node.label) return

      const pathParts = node.label.split('/').filter((part: string) => part.trim())
      let currentLevel = labelTree

      for (let i = 0; i < pathParts.length; i++) {
        const labelName = pathParts[i]
        const labelNode = currentLevel.get(labelName)

        if (labelNode) {
          // 到达最后一级标签，挂载数据节点的 fields
          if (i === pathParts.length - 1) {
            // 将 fields 转换为子节点，传入父节点以继承location等信息
            const fieldsChildren = convertFieldsToChildren(node.fields, node)

            // 直接将 fields 子节点添加到标签的 items 中，不包装数据节点本身
            labelNode.items.push(...fieldsChildren)
          }
          currentLevel = labelNode.children
        }
      }
    })
  }

  /**
   * 将标签Map树转换为UI节点树
   */
  const convertLabelTreeToNodes = (labelMap: Map<string, any>, labelPath: string[] = []): any[] => {
    const nodes: any[] = []
    // 使用全局计数器确保label节点也有唯一ID
    // label节点使用 -1000 ~ -9999 范围，field节点使用 -10000 及以下

    labelMap.forEach((node, labelName) => {
      const currentPath = [...labelPath, labelName]
      const fullPath = currentPath.join('/')
      const depth = currentPath.length

      // 使用路径的hash值作为ID的一部分，确保唯一性
      const pathHash = fullPath.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
      const uniqueId = -1000 - pathHash

      const labelNode: any = {
        line_id: uniqueId,
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

      // 处理挂载的 fields 子节点
      if (node.items && node.items.length > 0) {
        // items 中直接是 fields 子节点，保留其原始结构
        const fieldNodes = node.items.map((item: any) => ({
          ...item,
          children: item.children || []
        }))

        // 全量展示所有fields子节点，不限制数量
        const allChildren = [...labelNode.children, ...fieldNodes]
        labelNode._fullChildren = allChildren
        labelNode.children = allChildren
      }

      nodes.push(labelNode)
    })

    return nodes
  }

  /**
   * 主函数：构建本体标签树
   */
  const buildOntologyTree = (rawTreeData: any[]): any[] => {
    console.log('🏷️ 开始构建按标签分组的树形结构')

    if (!rawTreeData || rawTreeData.length === 0) {
      console.warn('⚠️ 原始数据为空，无法构建树')
      return []
    }

    // Step 1: 扁平化所有节点，清除原始 children 和 content
    const flattenedNodes = flattenAllNodes(rawTreeData)

    console.log('📊 Step 1 - 扁平化所有节点:')
    console.log('  - 扁平化节点数:', flattenedNodes.length)

    // Step 2: 筛选出有 label 的节点
    const { labeledNodes, allLabelPaths } = extractLabeledNodes(flattenedNodes)

    console.log('📊 Step 2 - 筛选有标签的节点:')
    console.log('  - 有标签的节点数:', labeledNodes.length)
    console.log('  - 唯一标签数:', allLabelPaths.size)
    console.log('  - 所有标签:', Array.from(allLabelPaths))

    // 检查是否有标签
    if (allLabelPaths.size === 0) {
      console.warn('⚠️ 数据中没有标签字段，无法构建标签树')
      return []
    }

    // Step 3: 构建纯标签树结构
    const labelTree = buildLabelTree(allLabelPaths)

    console.log('📊 Step 3 - 构建纯标签树结构:')
    console.log('  - 一级标签数:', labelTree.size)

    // Step 4: 将数据节点挂载到标签树（并添加 fields 子节点）
    mountDataToLabelTree(labelTree, labeledNodes)

    console.log('📊 Step 4 - 数据节点挂载完成')

    // Step 5: 转换为UI节点树
    const resultNodes = convertLabelTreeToNodes(labelTree)

    console.log('📊 Step 5 - 转换为UI节点树:')
    console.log('  - 根节点数:', resultNodes.length)
    console.log('✅ 本体标签树构建完成')

    return resultNodes
  }

  /**
   * 展开"查看更多"节点
   */
  const expandMoreNode = (moreNode: any): boolean => {
    if (!moreNode._parentNode || !moreNode._parentNode._fullChildren) {
      return false
    }

    const parentNode = moreNode._parentNode
    parentNode.children = parentNode._fullChildren
    delete parentNode._fullChildren

    return true
  }

  return {
    buildOntologyTree,
    expandMoreNode,
    flattenAllNodes,
    extractLabeledNodes,
    buildLabelTree,
    mountDataToLabelTree,
    convertLabelTreeToNodes,
    convertFieldsToChildren
  }
}
