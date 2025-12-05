/**
 * 要素节点构建器
 * 从 ontology 数据中提取 fields 并挂载到知识图谱
 */

export interface FieldNode {
  id: string
  label: string
  type: 'element'
}

export interface FieldEdge {
  id: string
  source: string
  target: string
  label: 'hasAttribute'
}

export interface OntologyItem {
  pid: string
  label: string
  fields?: Record<string, any>
  [key: string]: any
}

export interface ConceptNode {
  id: string
  label: string
  type: string
}

export interface FieldNodesResult {
  fieldNodes: FieldNode[]
  fieldEdges: FieldEdge[]
}

/**
 * 从 structuredData (ontology) 中提取 fields 并创建要素节点和边
 *
 * @param structuredData - ontology 数据数组
 * @param conceptNodes - 概念节点数组（用于查找匹配的概念节点）
 * @returns 要素节点和边的数组
 */
export function buildFieldNodes(
  structuredData: OntologyItem[],
  conceptNodes: ConceptNode[]
): FieldNodesResult {
  console.log('🎯 开始构建要素节点（fields）...')
  console.log('📋 structuredData 节点数:', structuredData?.length || 0)
  console.log('📋 conceptNodes 节点数:', conceptNodes?.length || 0)

  const fieldNodes: FieldNode[] = []
  const fieldEdges: FieldEdge[] = []

  if (!structuredData || !Array.isArray(structuredData)) {
    console.warn('⚠️ structuredData 为空或不是数组')
    return { fieldNodes, fieldEdges }
  }

  // 🔍 统计有 fields 的节点数
  const itemsWithFields = structuredData.filter(
    (item) => item.fields && Object.keys(item.fields).length > 0
  )
  console.log('📋 有 fields 的节点数:', itemsWithFields.length)

  let fieldNodeCounter = 0

  // 遍历 structuredData 中每个节点
  structuredData.forEach((item: OntologyItem) => {
    // 检查节点是否有 fields
    if (!item.fields || Object.keys(item.fields).length === 0) {
      return
    }

    // 解析 label path（如 "采购项目/采购包/商务要求"）
    const labelPath = item.label || ''
    if (!labelPath || !labelPath.includes('/')) {
      console.log(`  ⚠️ 跳过无效 label (pid: ${item.pid}):`, {
        label: labelPath,
        'label类型': typeof labelPath,
        'label包含/': labelPath?.includes('/'),
        fields: Object.keys(item.fields)
      })
      return
    }

    // 提取最后一级标签作为概念名称
    const parts = labelPath.split('/')
    const conceptLabel = parts[parts.length - 1]

    console.log(`\n📍 处理节点: ${item.pid}`)
    console.log(`  - label 路径: ${labelPath}`)
    console.log(`  - 概念标签: ${conceptLabel}`)

    // 查找对应的概念节点
    const conceptNode = conceptNodes.find((n: ConceptNode) => n.label === conceptLabel)
    if (!conceptNode) {
      console.log(`  ⚠️ 未找到概念节点: ${conceptLabel}`)
      console.log(`  📋 可用的概念节点:`, conceptNodes.map(n => n.label).slice(0, 10))
      return
    }

    console.log(`  ✓ 找到概念节点: ${conceptNode.id} - ${conceptNode.label}`)

    // 为每个 field 创建要素节点并连接到概念节点
    Object.entries(item.fields).forEach(([fieldKey, fieldValue]: [string, any]) => {
      // 跳过空值的 field
      if (fieldValue === null || fieldValue === '') {
        console.log(`  ⊘ 跳过空值 field: ${fieldKey}`)
        return
      }

      fieldNodeCounter++
      const fieldNodeId = `field_${item.pid}_${fieldKey}`

      // 添加要素节点，继承父节点的 location、pid 等信息
      fieldNodes.push({
        id: fieldNodeId,
        label: fieldKey, // 默认使用 key
        type: 'element',
        pid: item.pid, // 继承父节点 pid 用于跳转定位
        location: item.location, // 继承父节点 location
        fieldKey: fieldKey, // 保存字段 key（配置页面显示）
        fieldValue: fieldValue // 保存字段值（审查页面显示）
      })

      // 添加 hasAttribute 边（概念 -> 要素）
      fieldEdges.push({
        id: `edge_field_${fieldNodeCounter}`,
        source: conceptNode.id,
        target: fieldNodeId,
        label: 'hasAttribute'
      })

      console.log(`  ✓ 添加要素: ${conceptLabel} -> ${fieldKey} (值: ${fieldValue})`)
    })
  })

  console.log(`\n📊 要素节点构建完成:`)
  console.log(`  - 要素节点数: ${fieldNodes.length}`)
  console.log(`  - 要素边数: ${fieldEdges.length}`)

  // 🔍 检查前3个要素节点是否包含 location
  if (fieldNodes.length > 0) {
    console.log(`\n🔍 前3个要素节点的完整信息:`)
    fieldNodes.slice(0, 3).forEach((node, index) => {
      console.log(`  节点 ${index + 1}:`, {
        id: node.id,
        label: node.label,
        type: node.type,
        pid: node.pid,
        hasLocation: !!node.location,
        location: node.location
      })
    })
  }

  return { fieldNodes, fieldEdges }
}

/**
 * 创建模拟数据用于测试
 */
export function createMockStructuredData(): OntologyItem[] {
  return [
    {
      pid: 'texts-15',
      label: '采购项目/采购包/符合性要求/符合性审查项',
      fields: {
        '是否一票否决': null,
        '证明材料': '资格证明资料',
        '符合性要求内容': '符合招标公告中的投标人资格要求'
      }
    },
    {
      pid: 'texts-16',
      label: '采购项目/采购包/符合性要求/符合性审查项',
      fields: {
        '是否一票否决': '',
        '证明材料': '',
        '符合性要求内容': ''
      }
    },
    {
      pid: 'texts-18',
      label: '采购项目/采购包/评标信息/评标方法',
      fields: {
        '评标方法描述': '综合评分法说明',
        '评标方法名称': '综合评分法'
      }
    }
  ]
}

/**
 * 打印 label 路径分析（调试用）
 */
export function printLabelPathAnalysis(structuredData: OntologyItem[]): void {
  console.log('📊 Label 路径分析:')

  structuredData.forEach((item, index) => {
    if (!item.fields || Object.keys(item.fields).length === 0) {
      return
    }

    console.log(`\n📍 节点 ${index + 1}:`)
    console.log(`  - pid: ${item.pid}`)
    console.log(`  - label: ${item.label}`)
    console.log(`  - label 路径解析:`)

    const parts = item.label.split('/')
    parts.forEach((part, i) => {
      console.log(`    ${i + 1}. ${part}`)
    })

    console.log(`  - 最后一级标签: ${parts[parts.length - 1]}`)
    console.log(`  - fields:`, item.fields)
    console.log(`  - fields 键值对:`)

    Object.entries(item.fields).forEach(([key, value]) => {
      console.log(`    • ${key}: ${value}`)
    })
  })
}
