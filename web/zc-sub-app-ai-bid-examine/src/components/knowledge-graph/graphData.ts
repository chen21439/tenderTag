/**
 * 知识图谱数据定义
 * 从 ontology.json 加载数据
 */

export interface GraphNode {
  id: string
  label: string
  type: 'normal' | 'doc' | 'supplement'
  level?: number
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  label: string
}

// API 返回的节点结构
interface ApiNode {
  id: number
  labels: string[]
  properties: {
    name: string
    description?: string
    [key: string]: any
  }
}

// API 返回的边结构
interface ApiEdge {
  id: number
  source: number
  target: number
  type: string
  properties: Record<string, any>
}

// API 响应结构
interface ApiResponse {
  nodes: ApiNode[]
  edges: ApiEdge[]
}

interface OntologyNode {
  id: string
  label: string
  type: string
  level?: number
}

interface OntologyEdge {
  id: string
  from_node: string
  to_node: string
  edge_type: string
}

interface Ontology {
  nodes: OntologyNode[]
  edges: OntologyEdge[]
}

let cachedOntology: Ontology | null = null

/**
 * 从 API 加载知识图谱数据
 * GET /python/api/knowledge/graph
 */
async function loadOntology(): Promise<Ontology> {
  if (cachedOntology) {
    return cachedOntology
  }

  console.log('📡 开始调用知识图谱 API: /python/api/knowledge/graph')

  const response = await fetch('/python/api/knowledge/graph')

  console.log('📡 API 响应状态:', response.status, response.statusText)

  if (!response.ok) {
    throw new Error(`Failed to load ontology: ${response.statusText}`)
  }

  const apiData = await response.json()
  console.log('📡 API 返回数据:', apiData)

  // 提取 data 字段
  const { nodes: apiNodes, edges: apiEdges } = apiData.data as ApiResponse

  console.log(`📡 解析数据: ${apiNodes.length} 个节点, ${apiEdges.length} 条边`)

  // 转换节点格式
  const nodes: OntologyNode[] = apiNodes.map(node => {
    // 根据 properties.类别 判断节点类型
    const category = node.properties['类别'] || node.properties.category || ''
    const nodeType = category === '要素' ? 'element' : 'normal'

    return {
      id: String(node.id),
      label: node.properties.name || (node.labels[0] || 'Unknown'),
      type: nodeType,
      level: 1
    }
  })

  // 转换边格式
  const edges: OntologyEdge[] = apiEdges.map(edge => ({
    id: String(edge.id),
    from_node: String(edge.source),
    to_node: String(edge.target),
    edge_type: edge.type
  }))

  cachedOntology = { nodes, edges }

  console.log('📡 数据转换完成:', cachedOntology)

  return cachedOntology!
}

/**
 * 获取概念节点
 * 这些是知识图谱的固定骨架节点
 */
export const getConceptNodes = async (): Promise<GraphNode[]> => {
  const ontology = await loadOntology()
  return ontology.nodes.map(node => ({
    id: node.id,
    label: node.label,
    type: node.type as 'normal' | 'doc' | 'supplement',
    level: node.level
  }))
}

/**
 * 获取概念边
 * 这些是知识图谱的固定骨架关系
 */
export const getConceptEdges = async (): Promise<GraphEdge[]> => {
  const ontology = await loadOntology()
  return ontology.edges.map(edge => ({
    id: edge.id,
    source: edge.from_node,
    target: edge.to_node,
    label: edge.edge_type
  }))
}

/**
 * 边类型定义
 *
 * 从 API 返回的边类型：
 * - attachedTo: 附属关系
 * - explainTo: 解释关系 (新增)
 * - hasAttribute: 具有属性 (用于段落→字段)
 * - hasMember: 包含成员
 * - hasPart: 包含部分
 * - referTo: 引用关系
 * - sameAs: 等同关系
 * - sectionOf: 章节关系 (新增)
 * - instanceOf: 实例关系 (用于段落→概念，由前端生成)
 */
export const edgeTypes = [
  { value: 'attachedTo', label: 'attachedTo' },
  { value: 'explainTo', label: 'explainTo' },
  { value: 'hasAttribute', label: 'hasAttribute' },
  { value: 'hasMember', label: 'hasMember' },
  { value: 'hasPart', label: 'hasPart' },
  { value: 'referTo', label: 'referTo' },
  { value: 'sameAs', label: 'sameAs' },
  { value: 'sectionOf', label: 'sectionOf' },
  { value: 'instanceOf', label: 'instanceOf' }
]

/**
 * 从 sameAs 关系推理出隐含的层级关系
 *
 * 推理规则：
 * 1. A hasPart B + B sameAs C → A hasPart C (父节点关系传递)
 * 2. B hasPart D + B sameAs C → C hasPart D (子节点关系传递)
 * 3. 适用于所有层级关系：hasPart, hasMember, attachedTo
 *
 * @param edges 原始边列表
 * @returns 原始边 + 推理出的边
 */
export const inferEdgesFromSameAs = (edges: GraphEdge[]): GraphEdge[] => {
  const inferredEdges: Array<GraphEdge & { inferred?: boolean }> = []
  let inferredIdCounter = 0 // 全局计数器，避免 ID 重复

  // 层级关系类型（参与推理）
  const hierarchicalEdgeTypes = ['hasPart', 'hasMember', 'attachedTo']

  // 1. 按 target 分组：找到每个节点的父边（child -> [parents]）
  const parentEdgesByChild = new Map<string, Array<{ source: string; label: string }>>()

  // 2. 按 source 分组：找到每个节点的子边（parent -> [children]）
  const childEdgesByParent = new Map<string, Array<{ target: string; label: string }>>()

  edges.forEach(edge => {
    if (hierarchicalEdgeTypes.includes(edge.label)) {
      // 父边：A -> B (A 是 B 的父节点)
      const parents = parentEdgesByChild.get(edge.target) ?? []
      parents.push({ source: edge.source, label: edge.label })
      parentEdgesByChild.set(edge.target, parents)

      // 子边：A -> B (B 是 A 的子节点)
      const children = childEdgesByParent.get(edge.source) ?? []
      children.push({ target: edge.target, label: edge.label })
      childEdgesByParent.set(edge.source, children)
    }
  })

  // 3. 跟踪已有的边，避免重复
  const edgeKeySet = new Set<string>()
  edges.forEach(e => {
    edgeKeySet.add(`${e.source}|${e.target}|${e.label}`)
  })

  // 4. 处理 sameAs 边，进行双向推理
  edges.forEach(edge => {
    if (edge.label !== 'sameAs') return

    const b = edge.source // 例如：投标人须知
    const c = edge.target // 例如：对通用条款的补充内容

    // 规则 1: A hasPart B + B sameAs C → A hasPart C
    // 找到 B 的所有父节点，为 C 创建相同的父边
    const parentsOfB = parentEdgesByChild.get(b) ?? []
    parentsOfB.forEach(parent => {
      const key = `${parent.source}|${c}|${parent.label}`
      if (edgeKeySet.has(key)) return

      edgeKeySet.add(key)
      inferredEdges.push({
        id: `inf_${++inferredIdCounter}`,
        source: parent.source,
        target: c,
        label: parent.label,
        inferred: true
      })
    })

    // 对称：找到 C 的所有父节点，为 B 创建相同的父边
    const parentsOfC = parentEdgesByChild.get(c) ?? []
    parentsOfC.forEach(parent => {
      const key = `${parent.source}|${b}|${parent.label}`
      if (edgeKeySet.has(key)) return

      edgeKeySet.add(key)
      inferredEdges.push({
        id: `inf_${++inferredIdCounter}`,
        source: parent.source,
        target: b,
        label: parent.label,
        inferred: true
      })
    })

    // 规则 2: B hasPart D + B sameAs C → C hasPart D
    // 找到 B 的所有子节点，为 C 创建相同的子边
    const childrenOfB = childEdgesByParent.get(b) ?? []
    childrenOfB.forEach(child => {
      const key = `${c}|${child.target}|${child.label}`
      if (edgeKeySet.has(key)) return

      edgeKeySet.add(key)
      inferredEdges.push({
        id: `inf_${++inferredIdCounter}`,
        source: c,
        target: child.target,
        label: child.label,
        inferred: true
      })
    })

    // 对称：找到 C 的所有子节点，为 B 创建相同的子边
    const childrenOfC = childEdgesByParent.get(c) ?? []
    childrenOfC.forEach(child => {
      const key = `${b}|${child.target}|${child.label}`
      if (edgeKeySet.has(key)) return

      edgeKeySet.add(key)
      inferredEdges.push({
        id: `inf_${++inferredIdCounter}`,
        source: b,
        target: child.target,
        label: child.label,
        inferred: true
      })
    })
  })

  console.log(`🔍 sameAs 推理完成: 原始边 ${edges.length} 条，推理出 ${inferredEdges.length} 条新边`)

  return [...edges, ...inferredEdges]
}

/**
 * 获取要素数据
 */
export const getElementsData = async (): Promise<any> => {
  const response = await fetch(`${import.meta.env.BASE_URL}knowledge-graph/elements.json`)
  if (!response.ok) {
    throw new Error(`Failed to load elements: ${response.statusText}`)
  }
  return await response.json()
}

/**
 * 获取完整的图谱数据（包含推理后的边和要素节点数量统计）
 *
 * @returns { nodes, edges } 节点和边（包含推理边），节点包含 fieldCount 字段
 */
export const getGraphData = async (): Promise<{ nodes: GraphNode[]; edges: GraphEdge[] }> => {
  const nodes = await getConceptNodes()
  const edges = await getConceptEdges()
  const edgesWithInferred = inferEdgesFromSameAs(edges)

  // 重新生成唯一的边 ID，避免重复
  let edgeIdCounter = 1
  const edgesWithUniqueIds = edgesWithInferred.map(edge => ({
    ...edge,
    id: `edge_${edgeIdCounter++}`
  }))

  // 统计每个概念节点的要素节点数量
  const fieldCountMap = new Map<string, number>()

  edgesWithUniqueIds.forEach(edge => {
    if (edge.label === 'hasAttribute') {
      // 找到要素节点的父节点（source）
      const sourceNodeId = edge.source
      const currentCount = fieldCountMap.get(sourceNodeId) || 0
      fieldCountMap.set(sourceNodeId, currentCount + 1)
    }
  })

  // 为节点添加 fieldCount 字段
  const nodesWithFieldCount = nodes.map(node => ({
    ...node,
    fieldCount: fieldCountMap.get(node.id) || 0
  }))

  return {
    nodes: nodesWithFieldCount,
    edges: edgesWithUniqueIds
  }
}
