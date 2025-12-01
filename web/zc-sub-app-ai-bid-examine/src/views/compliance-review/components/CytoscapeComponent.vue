<template>
  <div class="cytoscape-wrapper">
    <div class="cytoscape-container" ref="cytoscapeRef"></div>

    <div v-if="selectedNodeId" class="legend-panel">
      <div class="legend-title">图例</div>
      <div class="legend-item">
        <span class="legend-box legend-parent"></span>
        <span class="legend-text">父节点</span>
      </div>
      <div class="legend-item">
        <span class="legend-box legend-child"></span>
        <span class="legend-text">子节点</span>
      </div>
    </div>

    <!-- Tooltip for node hover -->
    <div
      v-if="tooltipVisible"
      class="node-tooltip"
      :style="{ left: tooltipX + 'px', top: tooltipY + 'px' }"
    >
      <div class="tooltip-label">{{ tooltipContent.label }}</div>
      <div v-if="tooltipContent.fieldValue" class="tooltip-value">{{ tooltipContent.fieldValue }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import cytoscape, { type Core, type ElementDefinition } from 'cytoscape'
import { getGraphData, getConceptNodes, getConceptEdges } from '@/components/knowledge-graph/graphData'
import { getGraphStyles } from '@/components/knowledge-graph/graphStyles'

defineOptions({
  name: 'CytoscapeComponent'
})

interface Props {
  nodes?: Array<{ id: string; label?: string; type?: string }>
  edges?: Array<{ id: string; source: string; target: string; label?: string }>
  layout?: string
  useSampleData?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  nodes: () => [],
  edges: () => [],
  layout: 'cose',
  useSampleData: true
})

const emit = defineEmits(['node-click', 'edge-click', 'node-hover'])

const cytoscapeRef = ref<HTMLElement | null>(null)
let cy: Core | null = null
const selectedNodeId = ref<string | null>(null) // Currently selected node

// Tooltip state
const tooltipVisible = ref(false)
const tooltipX = ref(0)
const tooltipY = ref(0)
const tooltipContent = ref<{ label: string; fieldValue?: string }>({ label: '' })

// Load concept data from ontology.json (with inferred edges from sameAs)
const conceptDataCache = ref<{ nodes: any[]; edges: any[] } | null>(null)

const loadConceptData = async () => {
  if (!conceptDataCache.value) {
    conceptDataCache.value = await getGraphData()
  }
  return conceptDataCache.value
}

// Generate sample instance nodes (dynamic - for testing)
const getSampleInstanceNodes = () => {
  return [
    { id: '文本片段1', label: '文本片段1', type: 'doc' },
    { id: '文本片段2', label: '文本片段2', type: 'doc' },
    { id: '文本片段3', label: '文本片段3', type: 'doc' },
    { id: '文本片段4', label: '文本片段4', type: 'doc' },
    { id: '文本片段5', label: '文本片段5', type: 'doc' },
    { id: '文本片段6', label: '文本片段6', type: 'doc' },
    { id: '文本片段7', label: '文本片段7', type: 'doc' },
    { id: '文本片段8', label: '文本片段8', type: 'doc' },
    { id: '文本片段9', label: '文本片段9', type: 'doc' },
    { id: '文本片段10', label: '文本片段10', type: 'doc' },
    { id: '文本片段11', label: '文本片段11', type: 'doc' },
    { id: '文本片段12', label: '文本片段12', type: 'doc' },
    { id: '文本片段13', label: '文本片段13', type: 'doc' },
    { id: '文本片段14', label: '文本片段14', type: 'doc' },
    { id: '文本片段15', label: '文本片段15', type: 'doc' },
    { id: '文本片段16', label: '文本片段16', type: 'doc' },
    { id: '文本片段17', label: '文本片段17', type: 'doc' },
    { id: '文本片段18', label: '文本片段18', type: 'doc' },
    { id: '文本片段19', label: '文本片段19', type: 'doc' },
    { id: '补充说明1', label: '补充说明1', type: 'supplement' },
    { id: '补充说明2', label: '补充说明2', type: 'supplement' },
    { id: '补充说明3', label: '补充说明3', type: 'supplement' }
  ]
}

// Generate sample instance edges (dynamic - for testing)
const getSampleInstanceEdges = () => {
  return [
    // supplement nodes attach to tables
    { id: 'e27', source: '补充说明1', target: '商务要求表', label: 'attachedTo' },
    { id: 'e28', source: '补充说明2', target: '技术要求表', label: 'attachedTo' },
    { id: 'e29', source: '补充说明3', target: '评标信息表', label: 'attachedTo' },
    // doc nodes are instances of concepts
    { id: 'e30', source: '文本片段1', target: '项目基本信息', label: 'instanceOf' },
    { id: 'e31', source: '文本片段2', target: '投标人须知', label: 'instanceOf' },
    { id: 'e32', source: '文本片段3', target: '商务要求', label: 'instanceOf' },
    { id: 'e33', source: '文本片段4', target: '技术要求', label: 'instanceOf' },
    { id: 'e34', source: '文本片段5', target: '资格要求', label: 'instanceOf' },
    { id: 'e35', source: '文本片段6', target: '符合性要求', label: 'instanceOf' },
    { id: 'e36', source: '文本片段7', target: '评标信息', label: 'instanceOf' },
    { id: 'e37', source: '文本片段8', target: '评标信息表', label: 'instanceOf' },
    { id: 'e38', source: '文本片段9', target: '商务要求表', label: 'instanceOf' },
    { id: 'e39', source: '文本片段10', target: '技术要求表', label: 'instanceOf' },
    { id: 'e40', source: '文本片段11', target: '资格性审查表', label: 'instanceOf' },
    { id: 'e41', source: '文本片段12', target: '符合性审查表', label: 'instanceOf' },
    { id: 'e42', source: '文本片段13', target: '评标方法', label: 'instanceOf' },
    { id: 'e43', source: '文本片段14', target: '商务要求项', label: 'instanceOf' },
    { id: 'e44', source: '文本片段15', target: '技术要求项', label: 'instanceOf' },
    { id: 'e45', source: '文本片段16', target: '资格性审查项', label: 'instanceOf' },
    { id: 'e46', source: '文本片段17', target: '符合性审查项', label: 'instanceOf' },
    { id: 'e47', source: '文本片段18', target: '评标信息项', label: 'instanceOf' },
    { id: 'e48', source: '文本片段19', target: '补充说明', label: 'instanceOf' },
    { id: 'e49', source: '文本片段1', target: '文本片段2', label: 'referTo' }
  ]
}

// Sample graph data with concept nodes loaded from ontology.json
const sampleGraphData = ref<{ nodes: any[]; edges: any[] }>({ nodes: [], edges: [] })

const loadSampleGraphData = async () => {
  const conceptData = await loadConceptData()

  // 创建 label -> id 的映射
  const labelToId = new Map<string, string>()
  conceptData.nodes.forEach(node => {
    if (node.label) {
      labelToId.set(node.label, node.id)
    }
  })

  // 获取测试实例节点和边
  const instanceNodes = getSampleInstanceNodes()
  const instanceEdges = getSampleInstanceEdges()

  // 修正边的引用：将 label 转换为真实 ID
  const fixedEdges = instanceEdges.map(edge => {
    return {
      ...edge,
      source: labelToId.get(edge.source) || edge.source,
      target: labelToId.get(edge.target) || edge.target
    }
  })

  sampleGraphData.value = {
    nodes: [...conceptData.nodes, ...instanceNodes],
    edges: [...conceptData.edges, ...fixedEdges]
  }
}

// Computed graph data
const graphData = computed(() => {
  if (props.useSampleData) {
    return sampleGraphData.value
  }
  return {
    nodes: props.nodes,
    edges: props.edges
  }
})

const initCytoscape = () => {
  if (!cytoscapeRef.value) return

  const data = graphData.value

  console.log('🎨 Cytoscape 初始化数据:')
  console.log('  - 节点数:', data.nodes.length)
  console.log('  - 边数:', data.edges.length)
  console.log('  - 前3个节点:', data.nodes.slice(0, 3).map(n => ({ id: n.id, label: n.label, type: n.type })))
  console.log('  - 前3条边 (原始):', data.edges.slice(0, 3))
  console.log('  - 前3条边 (映射后):', data.edges.slice(0, 3).map(e => ({ id: e.id, source: e.source, target: e.target, label: e.label })))

  const elements: ElementDefinition[] = [
    ...data.nodes.map(node => ({
      data: {
        ...node, // 保留所有原始字段（包括 location, pid 等）
        label: node.label || node.id,
        type: node.type || 'default'
      }
    })),
    ...data.edges.map(edge => ({
      data: {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        label: edge.label || ''
      }
    }))
  ]

  console.log('  - Elements 总数:', elements.length)
  console.log('  - 节点 Elements:', elements.filter(e => !e.data.source).length)
  console.log('  - 边 Elements:', elements.filter(e => e.data.source).length)

  // 检查边 elements 的完整信息
  const edgeElements = elements.filter(e => e.data.source)
  if (edgeElements.length > 0) {
    console.log('  - 前3个边 Elements:', edgeElements.slice(0, 3).map(e => e.data))
  }

  cy = cytoscape({
    container: cytoscapeRef.value,
    elements,
    style: getGraphStyles(),
    layout: {
      name: props.layout,
      animate: true,
      animationDuration: 500,
      animationEasing: 'ease-out',
      nodeRepulsion: 8000,
      idealEdgeLength: 100,
      edgeElasticity: 100,
      nestingFactor: 5,
      gravity: 80,
      numIter: 1000,
      initialTemp: 200,
      coolingFactor: 0.95,
      minTemp: 1.0
    },
    minZoom: 0.3,
    maxZoom: 3,
    wheelSensitivity: 0.2
  })

  bindEvents()
}

const bindEvents = () => {
  if (!cy) return

  // 左键点击节点：高亮
  cy.on('tap', 'node', event => {
    const node = event.target
    const nodeId = node.data('id')

    // Highlight children of clicked node
    highlightNodeChildren(nodeId)

    // 传递完整的节点数据（包括 location、pid 等自定义字段）
    emit('node-click', node.data())
  })

  // 右键点击节点：切换要素节点展开/折叠
  cy.on('cxttap', 'node', event => {
    event.preventDefault()
    const node = event.target
    const nodeId = node.data('id')

    // 切换要素节点显示状态
    toggleFieldNodes(nodeId)
  })

  // Click on background to clear highlights
  cy.on('tap', event => {
    if (event.target === cy) {
      clearHighlights()
    }
  })

  cy.on('tap', 'edge', event => {
    const edge = event.target
    emit('edge-click', {
      id: edge.data('id'),
      source: edge.data('source'),
      target: edge.data('target'),
      label: edge.data('label')
    })
  })

  cy.on('mouseover', 'node', event => {
    const node = event.target
    const nodeData = node.data()

    emit('node-hover', {
      id: nodeData.id,
      label: nodeData.label,
      type: nodeData.type
    })

    // Show tooltip for element nodes (要素节点)
    if (nodeData.type === 'element') {
      const renderedPosition = node.renderedPosition()
      tooltipX.value = renderedPosition.x + 10
      tooltipY.value = renderedPosition.y - 10

      tooltipContent.value = {
        label: nodeData.label || nodeData.id,
        fieldValue: nodeData.fieldValue
      }

      tooltipVisible.value = true
    }
  })

  cy.on('mouseout', 'node', event => {
    tooltipVisible.value = false
  })
}

// 切换要素节点展开/折叠（右键点击）
const toggleFieldNodes = (nodeId: string) => {
  if (!cy) return

  const data = graphData.value

  // 查找所有 hasAttribute 边，source 是当前节点
  const fieldEdges = data.edges.filter((e: any) => e.source === nodeId && e.label === 'hasAttribute')

  if (fieldEdges.length === 0) return

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
  fieldEdges.forEach((edge: any) => {
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
}

// Highlight parent and child nodes of selected node
const highlightNodeChildren = (nodeId: string) => {
  if (!cy) return

  // Clear previous highlights
  clearHighlights()

  selectedNodeId.value = nodeId
  const data = graphData.value

  const parentNodeIds = new Set<string>()
  const childNodeIds = new Set<string>()
  const relatedEdges: string[] = []

  // Process all edges to find parents and children
  // Direction depends on edge type:
  // - instanceOf: source (instance) -> target (concept), so source is child, target is parent
  // - hasField: source (paragraph) -> target (field), so source is parent, target is child
  // - hasPart/hasMember: source (whole) -> target (part), so source is parent, target is child
  data.edges.forEach(edge => {
    const isInstanceOf = edge.label === 'instanceOf'

    if (edge.source === nodeId) {
      // This node is source
      if (isInstanceOf) {
        // For instanceOf: source is child (instance), target is parent (concept)
        parentNodeIds.add(edge.target)
      } else {
        // For hasPart/hasMember/hasField/etc: source is parent, target is child
        childNodeIds.add(edge.target)
      }
      relatedEdges.push(edge.id)
    } else if (edge.target === nodeId) {
      // This node is target
      if (isInstanceOf) {
        // For instanceOf: target is parent (concept), source is child (instance)
        childNodeIds.add(edge.source)
      } else {
        // For hasPart/hasMember/hasField/etc: target is child, source is parent
        parentNodeIds.add(edge.source)
      }
      relatedEdges.push(edge.id)
    }
  })

  console.log(`🎯 Selected node: ${nodeId}`)
  console.log(`   ⬆️  ${parentNodeIds.size} parent(s):`, Array.from(parentNodeIds))
  console.log(`   ⬇️  ${childNodeIds.size} child(ren):`, Array.from(childNodeIds))

  // Dim all nodes and edges
  cy.nodes().addClass('dimmed')
  cy.edges().addClass('dimmed')

  // Highlight selected node (remove dimming)
  const selectedNode = cy.getElementById(nodeId)
  selectedNode.removeClass('dimmed')

  // Highlight parent nodes (different style from children)
  parentNodeIds.forEach(parentId => {
    const parentNode = cy.getElementById(parentId)
    if (parentNode.length > 0) {
      parentNode.removeClass('dimmed')
      parentNode.addClass('highlighted-parent')
    }
  })

  // Highlight child nodes
  childNodeIds.forEach(childId => {
    const childNode = cy.getElementById(childId)
    if (childNode.length > 0) {
      childNode.removeClass('dimmed')
      childNode.addClass('highlighted-child')
    }
  })

  // Highlight related edges
  relatedEdges.forEach(edgeId => {
    const edgeElement = cy.getElementById(edgeId)
    if (edgeElement.length > 0) {
      edgeElement.removeClass('dimmed')
      edgeElement.addClass('highlighted')
    }
  })
}

// Clear all highlights
const clearHighlights = () => {
  if (!cy) return

  selectedNodeId.value = null

  // Remove all highlight classes
  cy.nodes().removeClass('dimmed highlighted-parent highlighted-child')
  cy.edges().removeClass('dimmed highlighted')

  console.log('✨ Cleared all highlights')
}

const resetLayout = () => {
  if (!cy) return

  const layout = cy.layout({
    name: props.layout,
    animate: true,
    animationDuration: 500,
    animationEasing: 'ease-out',
    nodeRepulsion: 8000,
    idealEdgeLength: 100,
    edgeElasticity: 100,
    nestingFactor: 5,
    gravity: 80,
    numIter: 1000,
    initialTemp: 200,
    coolingFactor: 0.95,
    minTemp: 1.0
  })

  layout.run()
}

const fitView = () => {
  if (!cy) return
  cy.fit(undefined, 50)
}

const zoomIn = () => {
  if (!cy) return
  cy.zoom({
    level: cy.zoom() * 1.2,
    renderedPosition: {
      x: cy.width() / 2,
      y: cy.height() / 2
    }
  })
}

const zoomOut = () => {
  if (!cy) return
  cy.zoom({
    level: cy.zoom() * 0.8,
    renderedPosition: {
      x: cy.width() / 2,
      y: cy.height() / 2
    }
  })
}

const updateGraph = () => {
  if (!cy) return

  cy.elements().remove()

  const data = graphData.value
  console.log('📊 CytoscapeComponent updateGraph:')
  console.log('  - nodes:', data.nodes.length)
  console.log('  - edges:', data.edges.length)
  console.log('  - useSampleData:', props.useSampleData)

  const elements: ElementDefinition[] = [
    ...data.nodes.map(node => ({
      data: {
        ...node, // 保留所有原始字段（包括 location, pid 等）
        label: node.label || node.id,
        type: node.type || 'default'
      }
    })),
    ...data.edges.map(edge => ({
      data: {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        label: edge.label || ''
      }
    }))
  ]

  console.log('  - elements 数量:', elements.length)
  cy.add(elements)

  // 默认隐藏所有要素节点
  cy.nodes().forEach(node => {
    if (node.data('type') === 'element') {
      node.hide()
    }
  })

  // 隐藏 hasAttribute 边
  cy.edges().forEach(edge => {
    if (edge.data('label') === 'hasAttribute') {
      edge.hide()
    }
  })

  resetLayout()
}

watch(
  () => [props.nodes, props.edges],
  () => {
    updateGraph()
  },
  { deep: true }
)

onMounted(async () => {
  // Load sample data if needed
  if (props.useSampleData) {
    await loadSampleGraphData()
  }
  initCytoscape()
})

onUnmounted(() => {
  if (cy) {
    cy.destroy()
    cy = null
  }
})

defineExpose({
  resetLayout,
  fitView,
  zoomIn,
  zoomOut,
  getCytoscape: () => cy,
  getConceptNodes,
  getConceptEdges,
  highlightNode: highlightNodeChildren,
  centerNode: (nodeId: string) => {
    if (!cy) return
    const node = cy.getElementById(nodeId)
    if (node.length > 0) {
      cy.animate({
        zoom: 1.0,
        center: { eles: node }
      }, {
        duration: 300
      })
    }
  }
})
</script>

<style lang="scss" scoped>
.cytoscape-wrapper {
  width: 100%;
  height: 100%;
  position: relative;
  background: #fafafa;
  border-radius: 8px;
  overflow: hidden;

  .cytoscape-container {
    width: 100%;
    height: 100%;
  }

  .legend-panel {
    position: absolute;
    bottom: 16px;
    left: 16px;
    background: #fff;
    border-radius: 8px;
    padding: 12px 16px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    z-index: 10;

    .legend-title {
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 8px;
      color: #262626;
    }

    .legend-item {
      display: flex;
      align-items: center;
      margin-bottom: 6px;

      &:last-child {
        margin-bottom: 0;
      }

      .legend-box {
        width: 20px;
        height: 20px;
        border-radius: 4px;
        border: 3px solid;
        margin-right: 8px;
        background: #f5f5f5;
      }

      .legend-parent {
        border-color: #fa8c16;
      }

      .legend-child {
        border-color: #52c41a;
      }

      .legend-text {
        font-size: 12px;
        color: #595959;
      }
    }
  }

  .node-tooltip {
    position: absolute;
    background: rgba(0, 0, 0, 0.85);
    color: #fff;
    padding: 8px 12px;
    border-radius: 4px;
    font-size: 12px;
    z-index: 1000;
    pointer-events: none;
    white-space: nowrap;
    max-width: 300px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);

    .tooltip-label {
      font-weight: 600;
      margin-bottom: 4px;
      white-space: normal;
      word-break: break-all;
    }

    .tooltip-value {
      font-size: 11px;
      color: #d4d4d4;
      white-space: normal;
      word-break: break-all;
    }
  }
}
</style>
