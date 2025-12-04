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
import {
  highlightAllAncestorsDescendants,
  clearHighlights as clearGraphHighlights,
  toggleFieldNodes as toggleFieldNodesShared,
  hideAllFieldNodes
} from '@/components/knowledge-graph/graphHighlight'
import {
  registerHtmlLabelPlugin,
  applyHtmlLabels,
  getHtmlLabelStyles
} from '@/components/knowledge-graph/graphHtmlLabel'

// 注册 HTML 标签插件
registerHtmlLabelPlugin(cytoscape)

defineOptions({
  name: 'CytoscapeComponent'
})

interface Props {
  nodes?: Array<{ id: string; label?: string; type?: string }>
  edges?: Array<{ id: string; source: string; target: string; label?: string }>
  layout?: string
  useSampleData?: boolean
  elementLabelMode?: 'key' | 'value' // 要素节点标签模式：key=字段名, value=字段值
}

const props = withDefaults(defineProps<Props>(), {
  nodes: () => [],
  edges: () => [],
  layout: 'cose',
  useSampleData: true,
  elementLabelMode: 'key' // 默认显示字段名
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
    ...data.nodes.map(node => {
      // 根据 elementLabelMode 决定要素节点显示的 label
      let displayLabel = node.label || node.id
      if (node.type === 'element' && props.elementLabelMode === 'value') {
        displayLabel = node.fieldValue || node.label || node.id
      }

      return {
        data: {
          ...node, // 保留所有原始字段（包括 location, pid, fieldKey, fieldValue 等）
          label: displayLabel,
          type: node.type || 'default'
        }
      }
    }),
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

    // 切换要素节点显示状态，传递布局参数
    toggleFieldNodesShared(cy, nodeId, graphData.value.edges, props.layout)
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

      // tooltip 显示：key（显示名称），value（详细信息）
      tooltipContent.value = {
        label: nodeData.fieldKey || nodeData.label || nodeData.id,
        fieldValue: nodeData.fieldValue
      }

      tooltipVisible.value = true
    }
  })

  cy.on('mouseout', 'node', event => {
    tooltipVisible.value = false
  })
}

// Highlight all related nodes (高亮所有关联节点)
const highlightNodeChildren = (nodeId: string) => {
  if (!cy) return

  selectedNodeId.value = nodeId

  // 使用共享的高亮方法（递归高亮所有祖先和后代）
  highlightAllAncestorsDescendants(cy, nodeId, graphData.value.edges)
}

// Clear all highlights
const clearHighlights = () => {
  if (!cy) return

  selectedNodeId.value = null

  // 使用共享的清除高亮方法
  clearGraphHighlights(cy)
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
  console.log('  - elementLabelMode:', props.elementLabelMode)

  const elements: ElementDefinition[] = [
    ...data.nodes.map(node => {
      // 根据 elementLabelMode 决定要素节点显示的 label
      let displayLabel = node.label || node.id
      if (node.type === 'element' && props.elementLabelMode === 'value') {
        displayLabel = node.fieldValue || node.label || node.id
      }

      return {
        data: {
          ...node, // 保留所有原始字段（包括 location, pid, fieldKey, fieldValue 等）
          label: displayLabel,
          type: node.type || 'default'
        }
      }
    }),
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

  // 默认隐藏所有要素节点（使用共享函数）
  hideAllFieldNodes(cy)

  // 应用 HTML 标签（显示要素节点数量徽章）
  applyHtmlLabels(cy)

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

  // HTML 标签样式（要素节点数量徽章）
  :deep(.node-html-label) {
    pointer-events: none;
  }

  :deep(.node-badge-container) {
    position: relative;
    width: 0;
    height: 0;
  }

  :deep(.node-badge) {
    position: absolute;
    top: -35px;
    right: -35px;
    min-width: 20px;
    height: 20px;
    padding: 0 6px;
    background: #ff4d4f;
    color: #fff;
    border-radius: 10px;
    font-size: 12px;
    font-weight: bold;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    border: 2px solid #fff;
  }
}
</style>
