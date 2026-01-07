import { ref, Ref } from 'vue'

export type TreeBuildStrategy = 'parentId' | 'path' | 'label'

/**
 * 树节点类（参考 tree_utils.py 的 Node 类）
 */
class TreeNode {
  name: string
  info: any
  children: TreeNode[] = []
  parent: TreeNode | null = null
  refChildren: TreeNode[] = []
  refParent: TreeNode | null = null
  refParentRelation: string | null = null
  depth: number = 0

  // 保存原始数据
  data: any

  constructor(name: string, info: any = null, data: any = null) {
    this.name = name
    this.info = info
    this.data = data
  }

  addChild(node: TreeNode): void {
    this.children.push(node)
    node.parent = this
  }

  addRefChild(node: TreeNode, relation: string): void {
    this.refChildren.push(node)
    node.refParent = this
    node.refParentRelation = relation
  }

  setDepth(curDepth: number): void {
    this.depth = curDepth
    for (const child of this.children) {
      child.setDepth(curDepth + 1)
    }
  }
}

/**
 * 通用树构建逻辑（参考 tree_utils.py）
 */
export function useTreeBuilderV2() {
  /**
   * 通过 parent_id 和 relation 构建树结构
   *
   * 参考: tree_utils.py 的 _build_tree_relations 函数
   *
   * @param flatData - 扁平化的节点数组
   * @param idField - ID字段名，默认 'id'
   * @param parentIdField - 父ID字段名，默认 'parent_id'
   * @param relationField - 关系字段名，默认 'relation'
   */
  const buildTreeByParentId = (
    flatData: any[],
    idField: string = 'id',
    parentIdField: string = 'parent_id',
    relationField: string = 'relation'
  ): any[] => {
    console.log('🏗️ [V2] 通过 parent_id 和 relation 构建树结构')
    console.log('  - 数据节点数:', flatData.length)
    console.log('  - ID字段:', idField)
    console.log('  - 父ID字段:', parentIdField)
    console.log('  - 关系字段:', relationField)

    if (!flatData || flatData.length === 0) {
      console.warn('⚠️ 数据为空，无法构建树')
      return []
    }

    const n = flatData.length

    // 创建 ROOT 节点
    const root = new TreeNode('ROOT', { index: -1 })

    // 创建所有节点（TreeNode 对象）
    const nodes: TreeNode[] = flatData.map((item, i) =>
      new TreeNode(item.text || `node_${i}`, { index: i }, item)
    )

    // 创建 ID 到节点的映射（用于快速查找）
    const nodeMap = new Map<number, TreeNode>()
    nodes.forEach((node, i) => {
      const id = flatData[i][idField]
      nodeMap.set(id, node)
    })
    nodeMap.set(-1, root)

    console.log('  - 创建了', nodes.length, '个节点')

    // 建立树关系（参考 tree_utils.py 的 _build_tree_relations）
    let containCount = 0
    let equalityCount = 0
    let connectCount = 0

    for (let i = 0; i < n; i++) {
      const item = flatData[i]
      const node = nodes[i]
      const refParentId = item[parentIdField]
      const relation = item[relationField] || 'contain'

      // 获取 refParent
      let refParent: TreeNode | null = null
      if (refParentId === -1 || refParentId === '-1') {
        refParent = root
      } else if (nodeMap.has(refParentId)) {
        refParent = nodeMap.get(refParentId)!
      } else {
        console.warn(`⚠️ 节点 ${i} 的 parent_id=${refParentId} 不存在，跳过`)
        continue
      }

      // 建立引用关系
      refParent.addRefChild(node, relation)

      // 建立层级关系（核心逻辑，完全参考 Python）
      if (relation === 'contain') {
        // contain: 直接成为 refParent 的子节点
        refParent.addChild(node)
        containCount++
        console.log(`  📦 Contain: id=${item[idField]} → parent_id=${refParentId}`)
      } else if (relation === 'connect') {
        // connect: 阅读顺序延续，与 refParent 是兄弟
        if (refParent.parent) {
          refParent.parent.addChild(node)
          console.log(`  🔗 Connect: id=${item[idField]} → parent_id=${refParentId}，添加到共同父节点`)
        } else {
          // refParent 是 root 下的顶层节点
          root.addChild(node)
          console.log(`  🔗 Connect: id=${item[idField]} → parent_id=${refParentId}，添加到 ROOT`)
        }
        connectCount++
      } else if (relation === 'equality') {
        // equality: 沿着 refParent 链回溯找到最老的兄弟
        let oldestBro = node.refParent!
        while (oldestBro.refParentRelation === 'equality') {
          oldestBro = oldestBro.refParent!
        }
        if (oldestBro.parent) {
          oldestBro.parent.addChild(node)
          console.log(`  ⚖️ Equality: id=${item[idField]} ↔ ${refParentId}，添加到共同父节点`)
        } else {
          // oldestBro 是根节点
          root.addChild(node)
          console.log(`  ⚖️ Equality: id=${item[idField]} ↔ ${refParentId}，添加到 ROOT`)
        }
        equalityCount++
      }
    }

    // 设置深度
    root.setDepth(0)

    console.log('✅ [V2] 树构建完成')
    console.log('  - 根节点数量:', root.children.length)
    console.log('  - Contain 关系:', containCount)
    console.log('  - Connect 关系:', connectCount)
    console.log('  - Equality 关系:', equalityCount)

    // 转换为前端需要的格式
    const convertToUINode = (treeNode: TreeNode): any => {
      return {
        ...treeNode.data,
        children: treeNode.children.map(child => convertToUINode(child))
      }
    }

    const result = root.children.map(child => convertToUINode(child))

    // 打印树结构预览
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
    console.log('🌳 [V2] 树结构预览:')
    result.slice(0, 3).forEach(root => checkTree(root))

    return result
  }

  /**
   * 通用构建方法
   */
  const buildTree = (
    data: any[],
    strategy: TreeBuildStrategy,
    options?: {
      idField?: string
      parentIdField?: string
      relationField?: string
    }
  ): any[] => {
    if (strategy === 'parentId') {
      return buildTreeByParentId(
        data,
        options?.idField,
        options?.parentIdField,
        options?.relationField
      )
    } else {
      console.error('❌ [V2] 暂时只支持 parentId 策略')
      return []
    }
  }

  return {
    buildTree,
    buildTreeByParentId
  }
}
