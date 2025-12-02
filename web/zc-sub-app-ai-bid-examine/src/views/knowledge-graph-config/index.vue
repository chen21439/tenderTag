<template>
  <div class="knowledge-graph-config-page">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <a-button type="text" class="nav-btn back-btn" @click="goHome">
          <template #icon>
            <CornerUpLeft class="icon" :size="16" />
          </template>
          返回首页
        </a-button>
        <h2>知识图谱配置</h2>
      </div>
      <div class="toolbar-right">
        <GraphToolbar
          show-nav-button
          :nav-collapsed="isNavCollapsed"
          @reset="resetLayout"
          @fit="fitView"
          @zoomIn="zoomIn"
          @zoomOut="zoomOut"
          @toggleNav="toggleNavPanel"
        />
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧操作面板 -->
      <div class="left-panel">
        <div class="panel-section">
          <h3>节点类型过滤</h3>
          <a-checkbox-group v-model:value="visibleNodeTypes" @change="handleNodeTypeFilterChange">
            <a-checkbox value="normal">标签节点</a-checkbox>
            <a-checkbox value="element">要素节点</a-checkbox>
          </a-checkbox-group>
        </div>

        <div class="panel-section">
          <a-button @click="handleSave" type="primary" block class="save-btn">
            <Save :size="16" />
            <span>保存配置</span>
          </a-button>
          <a-button @click="handleResetToDefault" block class="reset-btn" style="margin-top: 8px;">
            <span>恢复默认配置</span>
          </a-button>
        </div>

        <div class="panel-section">
          <h3>操作模式</h3>
          <div class="mode-buttons">
            <a-button
              :type="currentMode === 'add' ? 'primary' : 'default'"
              @click="handleAddNode"
              class="mode-btn"
            >添加节点</a-button>
            <a-button
              :type="currentMode === 'select' ? 'primary' : 'default'"
              @click="handleModeChange('select')"
              class="mode-btn"
            >选择</a-button>
            <a-button
              :type="currentMode === 'connect' ? 'primary' : 'default'"
              @click="handleModeChange('connect')"
              class="mode-btn"
            >连接</a-button>
            <a-button
              :type="currentMode === 'delete' ? 'primary' : 'default'"
              @click="handleModeChange('delete')"
              class="mode-btn"
            >删除</a-button>
          </div>
        </div>

        <div class="panel-section" v-if="currentMode === 'add'">
          <h3>节点类型</h3>
          <div class="add-node-buttons">
            <a-button
              :type="addNodeType === 'normal' ? 'primary' : 'default'"
              @click="addNodeType = 'normal'"
              size="small"
            >标签节点</a-button>
            <a-button
              :type="addNodeType === 'element' ? 'primary' : 'default'"
              @click="addNodeType = 'element'"
              size="small"
            >要素节点</a-button>
          </div>
        </div>

        <div class="panel-section" v-if="currentMode === 'select'">
          <a-radio-group v-model:value="highlightMode" style="display: flex; flex-direction: column; gap: 8px;">
            <a-radio value="none">展示所有节点</a-radio>
            <a-radio value="recursive">高亮关联节点</a-radio>
            <a-radio value="direct">高亮父子节点（仅一层）</a-radio>
          </a-radio-group>
        </div>

        <div class="panel-section" v-if="currentMode === 'connect'">
          <h3>连接类型</h3>
          <div class="edge-type-buttons">
            <a-button
              v-for="type in edgeTypes"
              :key="type.value"
              :type="connectEdgeType === type.value ? 'primary' : 'default'"
              @click="connectEdgeType = type.value"
              class="edge-type-btn"
            >
              {{ type.label }}
            </a-button>
          </div>
        </div>

        <div class="panel-section" v-if="selectedNode">
          <h3>节点属性</h3>
          <div class="form-item">
            <label>节点名称:</label>
            <a-input v-model:value="selectedNode.label" @change="updateNodeLabel" />
          </div>
          <div class="form-item">
            <label>节点类型:</label>
            <div class="type-buttons">
              <a-button
                :type="selectedNode.type === 'normal' ? 'primary' : 'default'"
                @click="selectedNode.type = 'normal'; updateNodeType()"
                size="small"
              >标签节点</a-button>
              <a-button
                :type="selectedNode.type === 'element' ? 'primary' : 'default'"
                @click="selectedNode.type = 'element'; updateNodeType()"
                size="small"
              >要素节点</a-button>
            </div>
          </div>
        </div>

        <div class="panel-section" v-if="selectedNode">
          <h3>相关要素</h3>
          <div class="elements-list">
            <div
              v-for="element in getRelatedElements(selectedNode.id)"
              :key="element.id"
              class="element-item"
            >
              <div class="element-name">{{ element.label }}</div>
              <div class="element-type">{{ element.type }}</div>
            </div>
            <div v-if="getRelatedElements(selectedNode.id).length === 0" class="no-elements">
              暂无相关要素
            </div>
          </div>
        </div>

        <div class="panel-section" v-if="selectedEdge">
          <h3>边属性</h3>
          <div class="form-item">
            <label>边ID:</label>
            <a-input v-model:value="selectedEdge.id" disabled />
          </div>
          <div class="form-item">
            <label>起始节点:</label>
            <a-input v-model:value="selectedEdge.source" disabled />
          </div>
          <div class="form-item">
            <label>目标节点:</label>
            <a-input v-model:value="selectedEdge.target" disabled />
          </div>
          <div class="form-item">
            <label>关系类型:</label>
            <a-select v-model:value="selectedEdge.label" @change="updateEdgeLabel" style="width: 100%">
              <a-select-option value="hasPart">hasPart</a-select-option>
              <a-select-option value="hasMember">hasMember</a-select-option>
              <a-select-option value="instanceOf">instanceOf</a-select-option>
              <a-select-option value="hasField">hasField</a-select-option>
              <a-select-option value="sameAs">sameAs</a-select-option>
            </a-select>
          </div>
        </div>
      </div>

      <!-- 右侧图谱画布 -->
      <div class="graph-canvas-wrapper">
        <!-- 使用共享的图谱导航面板组件（浮动布局） -->
        <GraphNavigationPanel
          :tree-data="graphTreeData"
          :selected-node-id="selectedGraphNodeId"
          :collapsed="isNavCollapsed"
          layout="floating"
          @node-select="handleNavNodeSelect"
        >
          <template #graph>
            <div ref="cytoscapeContainer" class="cytoscape-container"></div>
            <div class="canvas-tips" v-if="currentMode === 'connect'">
              点击第一个节点，然后点击第二个节点创建连接
            </div>
            <div class="canvas-tips" v-if="currentMode === 'add'">
              左键点击画布创建节点，右键取消
            </div>

            <!-- 图例 - 固定在右下角 -->
            <div class="legend-wrapper">
              <GraphLegend />
            </div>

            <!-- Tooltip for element nodes -->
            <div
              v-if="tooltipState.visible"
              class="node-tooltip"
              :style="{ left: tooltipState.x + 'px', top: tooltipState.y + 'px' }"
            >
              <div class="tooltip-label">{{ tooltipState.content.label }}</div>
              <div v-if="tooltipState.content.fieldValue" class="tooltip-value">
                {{ tooltipState.content.fieldValue }}
              </div>
            </div>
          </template>
        </GraphNavigationPanel>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import cytoscape, { Core, ElementDefinition } from 'cytoscape'
import { PlusCircle, Save, CornerUpLeft } from 'lucide-vue-next'
import { message } from 'ant-design-vue'
import {
  getGraphData,
  edgeTypes as graphEdgeTypes,
  highlightDirectParentChild,
  highlightAllAncestorsDescendants,
  clearHighlights,
  getGraphStyles,
  registerHtmlLabelPlugin,
  applyHtmlLabels,
  toggleFieldNodes,
  hideAllFieldNodes,
  bindTooltipEvents,
  unbindTooltipEvents,
  GraphLegend,
  GraphToolbar,
  GraphNavigationPanel
} from '@/components/knowledge-graph'

// 注册 HTML 标签插件
registerHtmlLabelPlugin(cytoscape)
import type { GraphNode, GraphEdge, TooltipState } from '@/components/knowledge-graph'

const router = useRouter()

// Cytoscape 实例
let cy: Core | null = null
const cytoscapeContainer = ref<HTMLElement | null>(null)

// 当前操作模式
const currentMode = ref<'select' | 'connect' | 'delete' | 'add'>('select')

// 添加节点时选择的类型
const addNodeType = ref<'normal' | 'element'>('normal')

// 可见的节点类型（默认仅选中标签节点）
const visibleNodeTypes = ref<string[]>(['normal'])

// 高亮模式：'none' | 'direct' | 'recursive'
// none: 展示所有节点（无高亮）
// direct: 高亮父子节点（仅一层）
// recursive: 高亮关联节点（递归）
const highlightMode = ref<'none' | 'direct' | 'recursive'>('none')

// 边类型列表（从共享模块导入）
const edgeTypes = graphEdgeTypes

// 当前选中的连接类型
const connectEdgeType = ref('attachedTo')

// 选中的节点和边
const selectedNode = ref<any>(null)
const selectedEdge = ref<any>(null)

// Tooltip 状态
const tooltipState = ref<TooltipState>({
  visible: false,
  x: 0,
  y: 0,
  content: {
    label: '',
    fieldValue: ''
  }
})

// 连接模式的临时变量
let connectSourceNode: any = null
let tempEdge: any = null // 临时预览边

// 添加模式的临时变量
let tempPreviewNode: any = null // 临时预览节点

// 节点计数器（用于生成唯一ID）
let nodeCounter = 0

// 初始化图谱数据（从 API 加载，包含概念节点和要素节点）
const graphData = ref<{ nodes: any[]; edges: any[] }>({ nodes: [], edges: [] })

// 导航面板相关
const isNavCollapsed = ref(false) // 默认展开
const graphTreeData = ref<any[]>([])
const selectedGraphNodeId = ref<string | null>(null)

// localStorage 存储键名
const STORAGE_KEY_GRAPH = 'knowledge_graph_data'
const STORAGE_KEY_FLAG = 'knowledge_graph_saved'

// 从 localStorage 加载配置
const loadFromStorage = (): { nodes: any[]; edges: any[] } | null => {
  try {
    const savedFlag = localStorage.getItem(STORAGE_KEY_FLAG)
    if (savedFlag === 'true') {
      const savedData = localStorage.getItem(STORAGE_KEY_GRAPH)
      if (savedData) {
        const data = JSON.parse(savedData)
        console.log('从本地存储加载配置:', data)
        return data
      }
    }
  } catch (error) {
    console.error('加载本地存储配置失败:', error)
  }
  return null
}

const initGraphData = async () => {
  // 优先从 localStorage 加载
  const storedData = loadFromStorage()
  if (storedData) {
    graphData.value = storedData
    console.log('从本地存储加载图谱数据，节点数:', storedData.nodes.length, '边数:', storedData.edges.length)
    return
  }

  // 如果没有本地存储，从 API 加载
  console.log('从 API 加载图谱数据（包含概念节点、要素节点和关系）')
  graphData.value = await getGraphData()

  console.log(`✅ API 数据加载完成: ${graphData.value.nodes.length} 个节点, ${graphData.value.edges.length} 条边`)

  // 构建树形导航数据
  buildGraphTreeData()
}

// 初始化 Cytoscape
const initCytoscape = () => {
  if (!cytoscapeContainer.value) return

  const elements: ElementDefinition[] = [
    ...graphData.value.nodes.map(node => ({
      data: {
        id: node.id,
        label: node.label,
        type: node.type,
        level: node.level,
        fieldCount: (node as any).fieldCount || 0  // 添加要素节点数量
      }
    })),
    ...graphData.value.edges.map(edge => ({
      data: {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        label: edge.label
      }
    }))
  ]

  cy = cytoscape({
    container: cytoscapeContainer.value,
    elements,
    userPanningEnabled: true,
    userZoomingEnabled: true,
    boxSelectionEnabled: false,
    style: getGraphStyles(),
    layout: {
      name: 'cose',
      animate: true,
      animationDuration: 500
    }
  })

  // 应用 HTML 标签（显示要素节点数量徽章）
  applyHtmlLabels(cy)

  // 默认隐藏所有要素节点（使用共享函数）
  hideAllFieldNodes(cy)

  // 绑定事件
  bindEvents()

  // 初始化节点可拖拽状态
  updateNodeGrabbable()

  // 应用节点类型过滤
  handleNodeTypeFilterChange()

  // 居中显示图谱
  cy.fit(undefined, 50)
}

// 绑定事件
const bindEvents = () => {
  if (!cy) return

  // 绑定 tooltip 事件（使用共享函数）
  bindTooltipEvents(cy, tooltipState.value)

  // 节点点击事件
  cy.on('tap', 'node', (evt) => {
    // 添加模式下不处理节点点击，让画布点击事件处理
    if (currentMode.value === 'add') {
      return
    }
    const node = evt.target
    handleNodeClick(node)
  })

  // 边点击事件
  cy.on('tap', 'edge', (evt) => {
    const edge = evt.target
    handleEdgeClick(edge)
  })

  // 右键点击节点：切换要素节点展开/折叠
  cy.on('cxttap', 'node', (evt) => {
    evt.preventDefault()
    const node = evt.target
    const nodeId = node.data('id')

    // 使用共享的 toggleFieldNodes 函数
    toggleFieldNodes(cy, nodeId, graphData.value.edges)
  })

  // 画布点击事件（取消选择或添加节点）
  cy.on('tap', (evt) => {
    // 添加节点模式：点击任何地方（包括预览节点）创建节点
    if (currentMode.value === 'add') {
      const pos = evt.position
      createNodeAtPosition(pos.x, pos.y)
      return
    }

    if (evt.target === cy) {
      selectedNode.value = null
      selectedEdge.value = null

      // 如果在连接模式且有临时边，取消连接
      if (currentMode.value === 'connect' && connectSourceNode) {
        removeTempEdge()
        connectSourceNode = null
        message.info('已取消连接')
      }
    }
  })

  // 鼠标移动事件（连接模式或添加模式下）
  cy.on('mousemove', (evt) => {
    if (currentMode.value === 'connect' && connectSourceNode) {
      updateTempEdge(evt)
    } else if (currentMode.value === 'add') {
      updateTempPreviewNode(evt)
    }
  })

  // 右键点击事件（取消添加节点）
  cy.on('cxttap', (evt) => {
    if (currentMode.value === 'add') {
      removeTempPreviewNode()
      currentMode.value = 'select'
      updateNodeGrabbable()
      message.info('已取消添加节点')
    }
  })
}

// 创建临时预览边
const createTempEdge = (sourceNode: any) => {
  if (!cy) return

  const sourcePos = sourceNode.position()
  tempEdge = cy.add({
    group: 'edges',
    data: {
      id: 'temp-edge',
      source: sourceNode.id(),
      target: sourceNode.id()
    },
    classes: 'temp-edge'
  })
}

// 更新临时边的位置
const updateTempEdge = (evt: any) => {
  if (!cy || !tempEdge || !connectSourceNode) return

  // 获取鼠标位置
  const mousePos = evt.position || evt.renderedPosition

  // 检查鼠标下是否有节点
  const nodeUnderMouse = cy.elements('node').filter((ele: any) => {
    const bb = ele.boundingBox()
    return mousePos.x >= bb.x1 && mousePos.x <= bb.x2 &&
           mousePos.y >= bb.y1 && mousePos.y <= bb.y2
  })

  if (nodeUnderMouse.length > 0 && nodeUnderMouse[0].id() !== connectSourceNode.id()) {
    // 鼠标在某个节点上，连接到该节点
    tempEdge.move({ target: nodeUnderMouse[0].id() })
  } else {
    // 鼠标在空白处，创建一个虚拟目标点
    if (!cy.$id('temp-target').length) {
      cy.add({
        group: 'nodes',
        data: { id: 'temp-target' },
        position: mousePos,
        classes: 'temp-node'
      })
      tempEdge.move({ target: 'temp-target' })
    } else {
      cy.$id('temp-target').position(mousePos)
    }
  }
}

// 移除临时边
const removeTempEdge = () => {
  if (!cy) return

  if (tempEdge) {
    cy.remove(tempEdge)
    tempEdge = null
  }

  const tempNode = cy.$id('temp-target')
  if (tempNode.length) {
    cy.remove(tempNode)
  }
}

// 创建或更新临时预览节点
const updateTempPreviewNode = (evt: any) => {
  if (!cy) return

  const mousePos = evt.position

  if (!tempPreviewNode) {
    // 创建临时预览节点
    tempPreviewNode = cy.add({
      group: 'nodes',
      data: {
        id: 'temp-preview-node',
        label: '',
        type: 'normal'
      },
      position: mousePos,
      classes: 'temp-preview-node'
    })
  } else {
    // 更新位置
    tempPreviewNode.position(mousePos)
  }
}

// 移除临时预览节点
const removeTempPreviewNode = () => {
  if (!cy) return

  if (tempPreviewNode) {
    cy.remove(tempPreviewNode)
    tempPreviewNode = null
  }
}

// 处理节点点击
const handleNodeClick = (node: any) => {
  if (currentMode.value === 'select') {
    selectedNode.value = {
      id: node.data('id'),
      label: node.data('label'),
      type: node.data('type') || 'normal',
      level: node.data('level') || 1
    }
    selectedEdge.value = null

    // 根据高亮模式决定高亮方式
    if (highlightMode.value === 'recursive') {
      // 高亮关联节点（递归）
      highlightAllAncestorsDescendants(cy, node.data('id'), graphData.value.edges)
    } else if (highlightMode.value === 'direct') {
      // 高亮父子节点（仅一层）
      highlightDirectParentChild(cy, node.data('id'), graphData.value.edges)
    } else {
      // none: 展示所有节点，不做高亮和变暗
      clearHighlights(cy)
      if (cy) {
        node.addClass('selected')
      }
    }
  } else if (currentMode.value === 'connect') {
    if (!connectSourceNode) {
      // 第一次点击，选择起始节点
      connectSourceNode = node
      createTempEdge(node)
      message.info(`已选择起始节点: ${node.data('label')}，请选择目标节点`)
    } else {
      // 第二次点击，创建真正的连接
      if (node.id() !== connectSourceNode.id()) {
        createEdge(connectSourceNode, node)
      } else {
        message.warning('不能连接到自己')
      }
      removeTempEdge()
      connectSourceNode = null
    }
  } else if (currentMode.value === 'delete') {
    deleteNode(node)
  }
}

// 处理边点击
const handleEdgeClick = (edge: any) => {
  if (currentMode.value === 'select') {
    selectedEdge.value = {
      id: edge.data('id'),
      source: edge.data('source'),
      target: edge.data('target'),
      label: edge.data('label')
    }
    selectedNode.value = null

    // 高亮选中的边
    if (cy) {
      cy.elements().removeClass('selected')
      edge.addClass('selected')
    }
  } else if (currentMode.value === 'delete') {
    deleteEdge(edge)
  }
}

// 更新节点可拖拽状态
const updateNodeGrabbable = () => {
  if (!cy) return

  // 只在选择模式下允许拖拽节点
  const isGrabbable = currentMode.value === 'select'
  cy.nodes().forEach((node: any) => {
    node.grabify()
    if (!isGrabbable) {
      node.ungrabify()
    }
  })

  // 添加模式下修改鼠标样式
  if (currentMode.value === 'add') {
    cy.container()?.style.setProperty('cursor', 'crosshair')
  } else {
    cy.container()?.style.setProperty('cursor', 'default')
  }
}

// 模式切换
const handleModeChange = (mode: string) => {
  currentMode.value = mode
  selectedNode.value = null
  selectedEdge.value = null
  removeTempEdge()
  removeTempPreviewNode()
  connectSourceNode = null
  updateNodeGrabbable()

  // 使用共享的清除高亮逻辑
  clearHighlights(cy)

  message.info(`已切换到${mode === 'select' ? '选择' : mode === 'connect' ? '连接' : '删除'}模式`)
}

// 获取节点相关的要素（从图谱数据中提取）
const getRelatedElements = (nodeId: string) => {
  // 找到所有从该节点出发的 hasAttribute 边
  const relatedEdges = graphData.value.edges.filter(
    (edge: any) => edge.source === nodeId && edge.label === 'hasAttribute'
  )

  // 根据边找到目标要素节点
  const elementNodeIds = new Set(relatedEdges.map((edge: any) => edge.target))

  return graphData.value.nodes.filter((node: any) =>
    elementNodeIds.has(node.id) && node.type === 'element'
  )
}

// 切换导航面板
const toggleNavPanel = () => {
  isNavCollapsed.value = !isNavCollapsed.value
}

// 处理导航节点选择
const handleNavNodeSelect = (nodeId: string) => {
  selectedGraphNodeId.value = nodeId

  // 在 Cytoscape 中高亮选中的节点
  if (cy && nodeId) {
    const node = cy.getElementById(nodeId)
    if (node.length > 0) {
      // 更新选中节点状态
      selectedNode.value = {
        id: node.data('id'),
        label: node.data('label'),
        type: node.data('type') || 'normal',
        level: node.data('level') || 1
      }
      selectedEdge.value = null

      // 导航点击时始终递归高亮所有关联节点（不受左侧模式影响）
      highlightAllAncestorsDescendants(cy, nodeId, graphData.value.edges)

      // 居中显示节点
      cy.animate({
        center: { eles: node },
        zoom: 1.5
      }, {
        duration: 500
      })
    }
  }
}

// 构建图谱树形导航数据
const buildGraphTreeData = () => {
  console.log('🌲 开始构建图谱树形导航数据')

  const nodes = graphData.value.nodes
  const edges = graphData.value.edges

  if (nodes.length === 0) {
    console.log('⚠️ 没有节点数据')
    graphTreeData.value = []
    return
  }

  // 创建节点映射
  const nodeMap = new Map()
  nodes.forEach(node => {
    nodeMap.set(node.id, {
      id: node.id,
      label: node.label,
      nodeType: node.type,
      children: []
    })
  })

  // 找到所有父子关系
  const childToParentMap = new Map()
  edges.forEach(edge => {
    // 使用 hasPart, hasMember, hasAttribute 等关系构建树
    if (['hasPart', 'hasMember', 'hasAttribute'].includes(edge.label)) {
      const childId = edge.target
      const parentId = edge.source

      if (!childToParentMap.has(childId)) {
        childToParentMap.set(childId, [])
      }
      childToParentMap.get(childId).push(parentId)
    }
  })

  // 构建树结构
  const rootNodes: any[] = []
  const addedNodes = new Set()

  nodeMap.forEach((treeNode, nodeId) => {
    const parents = childToParentMap.get(nodeId)

    if (!parents || parents.length === 0) {
      // 没有父节点，是根节点
      if (!addedNodes.has(nodeId)) {
        rootNodes.push(treeNode)
        addedNodes.add(nodeId)
      }
    } else {
      // 有父节点，添加到父节点的 children
      parents.forEach(parentId => {
        const parentNode = nodeMap.get(parentId)
        if (parentNode && !addedNodes.has(nodeId)) {
          parentNode.children.push(treeNode)
          addedNodes.add(nodeId)
        }
      })
    }
  })

  graphTreeData.value = rootNodes
  console.log(`✅ 树形数据构建完成，根节点数: ${rootNodes.length}`)
}

// 返回首页
const goHome = () => {
  try {
    sessionStorage.setItem('clearHomeUpload', '1')
  } catch {}
  router.push({ name: 'HomeIndex' })
}

// 添加节点：切换到添加模式
const handleAddNode = () => {
  currentMode.value = 'add'
  updateNodeGrabbable()
  selectedNode.value = null
  selectedEdge.value = null

  // 使用共享的清除高亮逻辑
  clearHighlights(cy)

  message.info('请在画布上左键点击以创建节点，右键取消')
}

// 添加指定类型的节点
const handleAddNodeWithType = (type: 'normal' | 'element' | 'doc') => {
  addNodeType.value = type
  handleAddNode()

  const typeLabels = {
    normal: '标签节点',
    element: '要素节点',
    doc: '文档节点'
  }
  message.info(`请在画布上左键点击以创建${typeLabels[type]}，右键取消`)
}

// 在指定位置创建节点
const createNodeAtPosition = (x: number, y: number) => {
  if (!cy) return

  // 生成唯一ID和默认标签
  nodeCounter++
  const nodeId = `node_${Date.now()}_${nodeCounter}`

  // 根据节点类型生成标签
  const typeLabels = {
    normal: '标签节点',
    element: '要素节点',
    doc: '文档节点'
  }
  const nodeLabel = `${typeLabels[addNodeType.value]}${nodeCounter}`

  // 创建新节点数据，使用选择的类型
  const newNodeData = {
    id: nodeId,
    label: nodeLabel,
    type: addNodeType.value,
    level: 1
  }

  // 添加到数据中
  graphData.value.nodes.push(newNodeData)

  // 在画布上创建节点
  cy.add({
    data: newNodeData,
    position: { x, y }
  })

  // 保持在添加模式，继续创建节点
  message.success('节点已创建，可继续点击创建或右键退出')
}

// 创建边
const createEdge = (sourceNode: any, targetNode: any) => {
  const edgeId = `e${Date.now()}`
  const newEdge = {
    id: edgeId,
    source: sourceNode.data('id'),
    target: targetNode.data('id'),
    label: connectEdgeType.value
  }

  graphData.value.edges.push(newEdge)

  cy?.add({
    data: newEdge
  })

  message.success(`已创建连接: ${sourceNode.data('label')} --[${connectEdgeType.value}]--> ${targetNode.data('label')}`)
}

// 删除节点
const deleteNode = (node: any) => {
  const nodeId = node.data('id')

  graphData.value.nodes = graphData.value.nodes.filter(n => n.id !== nodeId)
  graphData.value.edges = graphData.value.edges.filter(e => e.source !== nodeId && e.target !== nodeId)

  cy?.remove(node)

  message.success('节点已删除')
  selectedNode.value = null
}

// 删除边
const deleteEdge = (edge: any) => {
  const edgeId = edge.data('id')

  graphData.value.edges = graphData.value.edges.filter(e => e.id !== edgeId)

  cy?.remove(edge)

  message.success('边已删除')
  selectedEdge.value = null
}

// 更新节点标签
const updateNodeLabel = () => {
  if (!selectedNode.value || !cy) return

  const node = cy.$id(selectedNode.value.id)
  node.data('label', selectedNode.value.label)

  const nodeData = graphData.value.nodes.find(n => n.id === selectedNode.value.id)
  if (nodeData) nodeData.label = selectedNode.value.label

  message.success('节点标签已更新')
}

// 更新节点类型
const updateNodeType = () => {
  if (!selectedNode.value || !cy) return

  const node = cy.$id(selectedNode.value.id)
  node.data('type', selectedNode.value.type)

  const nodeData = graphData.value.nodes.find(n => n.id === selectedNode.value.id)
  if (nodeData) nodeData.type = selectedNode.value.type

  message.success('节点类型已更新')
}

// 更新节点层级
const updateNodeLevel = () => {
  if (!selectedNode.value || !cy) return

  const node = cy.$id(selectedNode.value.id)
  node.data('level', selectedNode.value.level)

  const nodeData = graphData.value.nodes.find(n => n.id === selectedNode.value.id)
  if (nodeData) nodeData.level = selectedNode.value.level

  message.success('节点层级已更新')
}

// 更新边标签
const updateEdgeLabel = () => {
  if (!selectedEdge.value || !cy) return

  const edge = cy.$id(selectedEdge.value.id)
  edge.data('label', selectedEdge.value.label)

  const edgeData = graphData.value.edges.find(e => e.id === selectedEdge.value.id)
  if (edgeData) edgeData.label = selectedEdge.value.label

  message.success('边类型已更新')
}

// 保存配置到 localStorage
const handleSave = () => {
  try {
    // 过滤掉临时节点和边（连接模式下的预览元素）
    const cleanData = {
      nodes: graphData.value.nodes.filter(node =>
        !node.id?.includes('temp') && node.id !== 'temp-target'
      ),
      edges: graphData.value.edges.filter(edge =>
        !edge.id?.includes('temp') &&
        edge.source !== 'temp-target' &&
        edge.target !== 'temp-target'
      )
    }

    // 保存图谱数据
    localStorage.setItem(STORAGE_KEY_GRAPH, JSON.stringify(cleanData))
    // 设置已保存标识
    localStorage.setItem(STORAGE_KEY_FLAG, 'true')

    console.log('保存配置:', cleanData)
    message.success('配置已保存到本地存储')
  } catch (error) {
    console.error('保存配置失败:', error)
    message.error('保存配置失败')
  }
}

// 清除本地存储的配置（可选功能）
const clearStoredConfig = () => {
  localStorage.removeItem(STORAGE_KEY_GRAPH)
  localStorage.removeItem(STORAGE_KEY_FLAG)
  message.success('已清除本地存储的配置')
}

// 处理节点类型过滤
const handleNodeTypeFilterChange = () => {
  if (!cy) return

  // 获取所有节点
  const allNodes = cy.nodes()

  allNodes.forEach((node: any) => {
    const nodeType = node.data('type')

    // 如果节点类型在可见列表中，显示节点；否则隐藏
    if (visibleNodeTypes.value.includes(nodeType)) {
      node.show()
    } else {
      node.hide()
    }
  })

  // 处理连接的边：只显示两端节点都可见的边
  const allEdges = cy.edges()
  allEdges.forEach((edge: any) => {
    const sourceNode = edge.source()
    const targetNode = edge.target()

    // 如果源节点和目标节点都可见，则显示边
    if (sourceNode.visible() && targetNode.visible()) {
      edge.show()
    } else {
      edge.hide()
    }
  })

  message.info(`已更新节点过滤：显示 ${visibleNodeTypes.value.length} 种类型`)
}

// 恢复默认配置
const handleResetToDefault = async () => {
  try {
    // 清空本地存储
    localStorage.removeItem(STORAGE_KEY_GRAPH)
    localStorage.removeItem(STORAGE_KEY_FLAG)

    // 重新加载数据（会自动从 API 加载）
    await initGraphData()

    // 重新初始化图谱
    if (cy) {
      cy.destroy()
    }
    initCytoscape()

    message.success('已恢复默认配置')
  } catch (error) {
    console.error('恢复默认配置失败:', error)
    message.error('恢复默认配置失败')
  }
}

// 监听高亮模式变化
watch(highlightMode, (newMode) => {
  if (!cy || !selectedNode.value || currentMode.value !== 'select') return

  // 根据新模式重新应用高亮
  if (newMode === 'recursive') {
    highlightAllAncestorsDescendants(cy, selectedNode.value.id, graphData.value.edges)
  } else if (newMode === 'direct') {
    highlightDirectParentChild(cy, selectedNode.value.id, graphData.value.edges)
  } else {
    // none: 清除高亮，只显示选中边框
    clearHighlights(cy)
    const node = cy.$id(selectedNode.value.id)
    if (node.length > 0) {
      node.addClass('selected')
    }
  }
})

// 图谱控制方法
const resetLayout = () => {
  if (!cy) return
  const layout = cy.layout({
    name: 'cose',
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

onMounted(async () => {
  await initGraphData()
  initCytoscape()
})

onUnmounted(() => {
  if (cy) {
    // 解绑 tooltip 事件
    unbindTooltipEvents(cy)
    cy.destroy()
  }
})
</script>

<style scoped>
.knowledge-graph-config-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    'Noto Sans', sans-serif, 'Microsoft YaHei', '微软雅黑', SimSun, '宋体';
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.toolbar-left h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.nav-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  color: #666;
  transition: all 0.2s;
}

.nav-btn:hover {
  color: #1890ff;
  background: #e6f7ff;
}

.nav-btn .icon {
  flex-shrink: 0;
}

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.left-panel {
  width: 300px;
  background: #fff;
  border-right: 1px solid #e8e8e8;
  overflow-y: auto;
  padding: 20px;
}

.legend-wrapper {
  position: absolute;
  left: 20px;
  bottom: 20px;
  z-index: 10;
}

.panel-section {
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid #f0f0f0;
}

.panel-section:last-child {
  border-bottom: none;
}

.panel-section h3 {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
}

.save-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.mode-buttons {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.mode-btn {
  flex: 1;
  font-size: 13px;
}

.form-item {
  margin-bottom: 16px;
}

.form-item label {
  display: block;
  font-size: 13px;
  color: #666;
  margin-bottom: 6px;
}

.type-buttons {
  display: flex;
  gap: 8px;
}

.type-buttons .ant-btn {
  flex: 1;
}

.add-node-buttons {
  display: flex;
  gap: 8px;
}

.add-node-buttons .ant-btn {
  flex: 1;
}

.edge-type-buttons {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.edge-type-btn {
  width: 100%;
  text-align: left;
  font-size: 12px;
}

.graph-canvas-wrapper {
  flex: 1;
  position: relative;
  background: #fff;
}

.cytoscape-container {
  width: 100%;
  height: 100%;
}

.canvas-tips {
  position: absolute;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(24, 144, 255, 0.9);
  color: #fff;
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 13px;
  z-index: 10;
}

.elements-list {
  max-height: 400px;
  overflow-y: auto;
}

.element-item {
  padding: 12px;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  margin-bottom: 8px;
  background: #fafafa;
}

.element-name {
  font-weight: 500;
  font-size: 14px;
  color: #1890ff;
  margin-bottom: 4px;
}

.element-type {
  font-size: 12px;
  color: #8c8c8c;
  margin-bottom: 4px;
}

.element-desc {
  font-size: 12px;
  color: #595959;
  line-height: 1.5;
}

.no-elements {
  padding: 20px;
  text-align: center;
  color: #8c8c8c;
  font-size: 13px;
}

/* HTML 标签样式（要素节点数量徽章） */
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

/* Tooltip 样式 */
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
}

.tooltip-label {
  font-weight: 500;
  margin-bottom: 4px;
}

.tooltip-value {
  font-size: 11px;
  color: #d4d4d4;
  white-space: normal;
  word-break: break-all;
}
</style>
