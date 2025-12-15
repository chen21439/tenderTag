<template>
  <div class="knowledge-graph-step-ppt">
    <PptSlideBase>
      <div class="ppt-content">
        <!-- 顶部标题居中 -->
        <div class="header">
          <h1 class="title">业务本体与项目知识图谱平台</h1>
        </div>

        <!-- 内容区域 -->
        <div class="content-area">
          <!-- 上方文字说明 -->
          <div class="text-section">
            <div class="step-desc">
              <h3>{{ stepConfig.title }}</h3>
              <p>{{ stepConfig.description }}</p>
            </div>
          </div>

          <!-- 下方图谱容器 -->
          <div class="graph-section">
            <div class="graph-container-wrapper">
              <div class="graph-full-container" ref="graphContainer"></div>
            </div>
          </div>
        </div>
      </div>
    </PptSlideBase>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import cytoscape from 'cytoscape'
import PptSlideBase from './PptSlideBase.vue'
import { documents, cytoscapeStyles } from './mockGraphData'

defineOptions({
  name: 'KnowledgeGraphStepPpt'
})

interface Props {
  step: number // 0: 信息孤岛, 1: 按项目聚合, 2: 按年份聚合
  graphWidth?: string // 图谱容器宽度，如 '70%', '600px'
  graphHeight?: string // 图谱容器高度，如 '420px', '500px'
}

const props = withDefaults(defineProps<Props>(), {
  step: 0,
  graphWidth: '70%',
  graphHeight: '420px'
})

const graphContainer = ref<HTMLElement | null>(null)
let cy: any = null

// 步骤配置
const stepConfig = computed(() => {
  const configs = [
    {
      title: '信息孤岛',
      description: '传统模式下，招标文件、评标报告、合同文本、验收报告等文档分散存储在不同位置，彼此孤立，难以关联。'
    },
    {
      title: '按项目聚合',
      description: '通过AI提取和语义分析，将同一项目下的所有文档自动聚合到项目节点下，形成项目级的文档集合。'
    },
    {
      title: '按年份聚合',
      description: '根据项目年份进行归类，建立项目与年份的关联关系，便于跨年度的项目追溯和统计分析。'
    }
  ]
  return configs[props.step] || configs[0]
})

onMounted(() => {
  if (!graphContainer.value) return

  // 初始化图谱元素
  const elements = [
    // 文档节点
    ...documents.map(doc => ({
      data: {
        id: doc.id,
        label: doc.label,
        type: 'doc',
        project: doc.project,
        supplier: doc.supplier,
      },
      classes: 'visible'
    })),

    // 占位节点（用于信息孤岛阶段的网格布局）- 5×5 需要 16 个白色占位格子
    { data: { id: 'placeholder_1', label: '', type: 'placeholder' }, classes: props.step === 0 ? 'visible' : 'hidden' },
    { data: { id: 'placeholder_2', label: '', type: 'placeholder' }, classes: props.step === 0 ? 'visible' : 'hidden' },
    { data: { id: 'placeholder_3', label: '', type: 'placeholder' }, classes: props.step === 0 ? 'visible' : 'hidden' },
    { data: { id: 'placeholder_4', label: '', type: 'placeholder' }, classes: props.step === 0 ? 'visible' : 'hidden' },
    { data: { id: 'placeholder_5', label: '', type: 'placeholder' }, classes: props.step === 0 ? 'visible' : 'hidden' },
    { data: { id: 'placeholder_6', label: '', type: 'placeholder' }, classes: props.step === 0 ? 'visible' : 'hidden' },
    { data: { id: 'placeholder_7', label: '', type: 'placeholder' }, classes: props.step === 0 ? 'visible' : 'hidden' },
    { data: { id: 'placeholder_8', label: '', type: 'placeholder' }, classes: props.step === 0 ? 'visible' : 'hidden' },
    { data: { id: 'placeholder_9', label: '', type: 'placeholder' }, classes: props.step === 0 ? 'visible' : 'hidden' },
    { data: { id: 'placeholder_10', label: '', type: 'placeholder' }, classes: props.step === 0 ? 'visible' : 'hidden' },
    { data: { id: 'placeholder_11', label: '', type: 'placeholder' }, classes: props.step === 0 ? 'visible' : 'hidden' },
    { data: { id: 'placeholder_12', label: '', type: 'placeholder' }, classes: props.step === 0 ? 'visible' : 'hidden' },
    { data: { id: 'placeholder_13', label: '', type: 'placeholder' }, classes: props.step === 0 ? 'visible' : 'hidden' },
    { data: { id: 'placeholder_14', label: '', type: 'placeholder' }, classes: props.step === 0 ? 'visible' : 'hidden' },
    { data: { id: 'placeholder_15', label: '', type: 'placeholder' }, classes: props.step === 0 ? 'visible' : 'hidden' },
    { data: { id: 'placeholder_16', label: '', type: 'placeholder' }, classes: props.step === 0 ? 'visible' : 'hidden' },

    // 4×9 底层文档方块（在step>=1时显示）- 21个橙色 + 15个白色
    // 第1行：橙 橙 白 橙 橙 白 橙 白 橙 (9列)
    { data: { id: 'grid_orange_1', label: '', type: 'grid_orange' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'grid_orange_2', label: '', type: 'grid_orange' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'grid_white_1', label: '', type: 'grid_white' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'grid_orange_3', label: '', type: 'grid_orange' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'grid_orange_4', label: '', type: 'grid_orange' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'grid_white_2', label: '', type: 'grid_white' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'grid_orange_5', label: '', type: 'grid_orange' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'grid_white_3', label: '', type: 'grid_white' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'grid_orange_6', label: '', type: 'grid_orange' }, classes: props.step >= 1 ? 'visible' : 'hidden' },

    // 第2行：橙 白 橙 橙 白 橙 白 橙 橙
    { data: { id: 'grid_orange_7', label: '', type: 'grid_orange' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'grid_white_4', label: '', type: 'grid_white' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'grid_orange_8', label: '', type: 'grid_orange' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'grid_orange_9', label: '', type: 'grid_orange' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'grid_white_5', label: '', type: 'grid_white' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'grid_orange_10', label: '', type: 'grid_orange' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'grid_white_6', label: '', type: 'grid_white' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'grid_orange_11', label: '', type: 'grid_orange' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'grid_orange_12', label: '', type: 'grid_orange' }, classes: props.step >= 1 ? 'visible' : 'hidden' },

    // 第3行：白 橙 白 白 橙 白 橙 橙 白
    { data: { id: 'grid_white_7', label: '', type: 'grid_white' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'grid_orange_13', label: '', type: 'grid_orange' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'grid_white_8', label: '', type: 'grid_white' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'grid_white_9', label: '', type: 'grid_white' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'grid_orange_14', label: '', type: 'grid_orange' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'grid_white_10', label: '', type: 'grid_white' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'grid_orange_15', label: '', type: 'grid_orange' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'grid_orange_16', label: '', type: 'grid_orange' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'grid_white_11', label: '', type: 'grid_white' }, classes: props.step >= 1 ? 'visible' : 'hidden' },

    // 第4行：橙 橙 白 橙 白 白 橙 白 橙
    { data: { id: 'grid_orange_17', label: '', type: 'grid_orange' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'grid_orange_18', label: '', type: 'grid_orange' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'grid_white_12', label: '', type: 'grid_white' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'grid_orange_19', label: '', type: 'grid_orange' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'grid_white_13', label: '', type: 'grid_white' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'grid_white_14', label: '', type: 'grid_white' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'grid_orange_20', label: '', type: 'grid_orange' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'grid_white_15', label: '', type: 'grid_white' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'grid_orange_21', label: '', type: 'grid_orange' }, classes: props.step >= 1 ? 'visible' : 'hidden' },

    // 项目节点
    { data: { id: 'proj_led_screen', label: 'LED显示屏', type: 'project', projectType: '框架协议采购项目', year: '2024-2025年度' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'proj_scanner', label: '扫描仪', type: 'project', projectType: '框架协议采购项目', year: '2025-2026年度' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'proj_air_conditioner', label: '空调机', type: 'project', projectType: '框架协议采购项目', year: '2025年' }, classes: props.step >= 1 ? 'visible' : 'hidden' },

    // 年份节点
    { data: { id: 'year_2024', label: '2024年', type: 'year' }, classes: props.step === 2 ? 'visible' : 'hidden' },
    { data: { id: 'year_2025', label: '2025年', type: 'year' }, classes: props.step === 2 ? 'visible' : 'hidden' },
  ]

  // 添加4×9方块到项目的连接边（step>=1时）
  if (props.step >= 1) {
    // 橙色方块连接到项目（21个橙色方块，每个项目7个）
    elements.push(
      // LED显示屏项目 (前7个橙色)
      { data: { source: 'grid_orange_1', target: 'proj_led_screen' }, classes: 'grid-edge' },
      { data: { source: 'grid_orange_2', target: 'proj_led_screen' }, classes: 'grid-edge' },
      { data: { source: 'grid_orange_3', target: 'proj_led_screen' }, classes: 'grid-edge' },
      { data: { source: 'grid_orange_4', target: 'proj_led_screen' }, classes: 'grid-edge' },
      { data: { source: 'grid_orange_5', target: 'proj_led_screen' }, classes: 'grid-edge' },
      { data: { source: 'grid_orange_6', target: 'proj_led_screen' }, classes: 'grid-edge' },
      { data: { source: 'grid_orange_7', target: 'proj_led_screen' }, classes: 'grid-edge' },

      // 扫描仪项目 (中间7个橙色)
      { data: { source: 'grid_orange_8', target: 'proj_scanner' }, classes: 'grid-edge' },
      { data: { source: 'grid_orange_9', target: 'proj_scanner' }, classes: 'grid-edge' },
      { data: { source: 'grid_orange_10', target: 'proj_scanner' }, classes: 'grid-edge' },
      { data: { source: 'grid_orange_11', target: 'proj_scanner' }, classes: 'grid-edge' },
      { data: { source: 'grid_orange_12', target: 'proj_scanner' }, classes: 'grid-edge' },
      { data: { source: 'grid_orange_13', target: 'proj_scanner' }, classes: 'grid-edge' },
      { data: { source: 'grid_orange_14', target: 'proj_scanner' }, classes: 'grid-edge' },

      // 空调机项目 (最后7个橙色)
      { data: { source: 'grid_orange_15', target: 'proj_air_conditioner' }, classes: 'grid-edge' },
      { data: { source: 'grid_orange_16', target: 'proj_air_conditioner' }, classes: 'grid-edge' },
      { data: { source: 'grid_orange_17', target: 'proj_air_conditioner' }, classes: 'grid-edge' },
      { data: { source: 'grid_orange_18', target: 'proj_air_conditioner' }, classes: 'grid-edge' },
      { data: { source: 'grid_orange_19', target: 'proj_air_conditioner' }, classes: 'grid-edge' },
      { data: { source: 'grid_orange_20', target: 'proj_air_conditioner' }, classes: 'grid-edge' },
      { data: { source: 'grid_orange_21', target: 'proj_air_conditioner' }, classes: 'grid-edge' }
    )
  }

  cy = cytoscape({
    container: graphContainer.value,
    elements: elements,
    style: cytoscapeStyles,
    layout: {
      name: 'random',
      fit: true,
      padding: 50,
    }
  })

  // 根据步骤显示对应的布局
  if (props.step === 0) {
    showStep0()
  } else if (props.step === 1) {
    showStep1()
  } else if (props.step === 2) {
    showStep2()
  }
})

onUnmounted(() => {
  if (cy) {
    cy.destroy()
  }
})

// 步骤0：信息孤岛 - 5×5 网格布局
const showStep0 = () => {
  if (!cy) return

  const gridSize = 70
  const startX = 100
  const startY = 80

  // 5×5 网格，9个橙色文档节点 + 16个白色占位节点（交错分布以体现孤岛效果）
  const positions: any = {
    // 第1行 - 橙白橙白白
    'doc_p1_tender': { x: startX, y: startY },
    'placeholder_1': { x: startX + gridSize, y: startY },
    'doc_p2_tender': { x: startX + gridSize * 2, y: startY },
    'placeholder_2': { x: startX + gridSize * 3, y: startY },
    'placeholder_3': { x: startX + gridSize * 4, y: startY },

    // 第2行 - 白橙白橙白
    'placeholder_4': { x: startX, y: startY + gridSize },
    'doc_p1_bid': { x: startX + gridSize, y: startY + gridSize },
    'placeholder_5': { x: startX + gridSize * 2, y: startY + gridSize },
    'doc_p3_tender': { x: startX + gridSize * 3, y: startY + gridSize },
    'placeholder_6': { x: startX + gridSize * 4, y: startY + gridSize },

    // 第3行 - 橙白白白橙
    'doc_p1_contract': { x: startX, y: startY + gridSize * 2 },
    'placeholder_7': { x: startX + gridSize, y: startY + gridSize * 2 },
    'placeholder_8': { x: startX + gridSize * 2, y: startY + gridSize * 2 },
    'placeholder_9': { x: startX + gridSize * 3, y: startY + gridSize * 2 },
    'doc_p2_bid': { x: startX + gridSize * 4, y: startY + gridSize * 2 },

    // 第4行 - 白白橙白橙
    'placeholder_10': { x: startX, y: startY + gridSize * 3 },
    'placeholder_11': { x: startX + gridSize, y: startY + gridSize * 3 },
    'doc_p2_contract': { x: startX + gridSize * 2, y: startY + gridSize * 3 },
    'placeholder_12': { x: startX + gridSize * 3, y: startY + gridSize * 3 },
    'doc_p3_bid': { x: startX + gridSize * 4, y: startY + gridSize * 3 },

    // 第5行 - 白橙白橙白
    'placeholder_13': { x: startX, y: startY + gridSize * 4 },
    'doc_p3_contract': { x: startX + gridSize, y: startY + gridSize * 4 },
    'placeholder_14': { x: startX + gridSize * 2, y: startY + gridSize * 4 },
    'placeholder_15': { x: startX + gridSize * 3, y: startY + gridSize * 4 },
    'placeholder_16': { x: startX + gridSize * 4, y: startY + gridSize * 4 },
  }

  cy.layout({
    name: 'preset',
    positions: (node: any) => positions[node.id()] || { x: 0, y: 0 },
    fit: true,
    padding: 50,
    animate: true,
    animationDuration: 800,
  }).run()
}

// 步骤1：按项目聚合
const showStep1 = () => {
  if (!cy) return

  // 将文档节点移入对应的项目容器
  documents.forEach(doc => {
    cy.nodes(`#${doc.id}`).move({ parent: doc.project })
  })

  // 添加同项目内文档的流程连接
  const projectGroups = {
    'proj_led_screen': ['doc_p1_tender', 'doc_p1_bid', 'doc_p1_contract'],
    'proj_scanner': ['doc_p2_tender', 'doc_p2_bid', 'doc_p2_contract'],
    'proj_air_conditioner': ['doc_p3_tender', 'doc_p3_bid', 'doc_p3_contract']
  }

  Object.values(projectGroups).forEach(docIds => {
    for (let i = 0; i < docIds.length - 1; i++) {
      const edgeId = `edge_flow_${docIds[i]}_${docIds[i + 1]}`
      if (cy.$id(edgeId).length === 0) {
        cy.add({
          group: 'edges',
          data: {
            id: edgeId,
            source: docIds[i],
            target: docIds[i + 1],
          },
          classes: 'doc-flow'
        })
      }
    }
  })

  const centerY = 100  // 项目Y坐标向上移动
  const spacing = 240
  const startX = 80
  const docSpacing = 95

  // 4×9 底层网格位置（与上方项目宽度一致）
  const gridStartY = 320  // 底层网格向上移动
  const gridStartX = startX
  const gridSpacing = 65

  const positions: any = {
    // 项目节点
    'proj_led_screen': { x: startX, y: centerY },
    'proj_scanner': { x: startX + spacing, y: centerY },
    'proj_air_conditioner': { x: startX + spacing * 2, y: centerY },

    // 文档节点
    'doc_p1_tender': { x: startX, y: centerY - docSpacing },
    'doc_p1_bid': { x: startX, y: centerY },
    'doc_p1_contract': { x: startX, y: centerY + docSpacing },

    'doc_p2_tender': { x: startX + spacing, y: centerY - docSpacing },
    'doc_p2_bid': { x: startX + spacing, y: centerY },
    'doc_p2_contract': { x: startX + spacing, y: centerY + docSpacing },

    'doc_p3_tender': { x: startX + spacing * 2, y: centerY - docSpacing },
    'doc_p3_bid': { x: startX + spacing * 2, y: centerY },
    'doc_p3_contract': { x: startX + spacing * 2, y: centerY + docSpacing },

    // 4×9 底层网格布局
    // 第1行：橙 橙 白 橙 橙 白 橙 白 橙
    'grid_orange_1': { x: gridStartX, y: gridStartY },
    'grid_orange_2': { x: gridStartX + gridSpacing, y: gridStartY },
    'grid_white_1': { x: gridStartX + gridSpacing * 2, y: gridStartY },
    'grid_orange_3': { x: gridStartX + gridSpacing * 3, y: gridStartY },
    'grid_orange_4': { x: gridStartX + gridSpacing * 4, y: gridStartY },
    'grid_white_2': { x: gridStartX + gridSpacing * 5, y: gridStartY },
    'grid_orange_5': { x: gridStartX + gridSpacing * 6, y: gridStartY },
    'grid_white_3': { x: gridStartX + gridSpacing * 7, y: gridStartY },
    'grid_orange_6': { x: gridStartX + gridSpacing * 8, y: gridStartY },

    // 第2行：橙 白 橙 橙 白 橙 白 橙 橙
    'grid_orange_7': { x: gridStartX, y: gridStartY + gridSpacing },
    'grid_white_4': { x: gridStartX + gridSpacing, y: gridStartY + gridSpacing },
    'grid_orange_8': { x: gridStartX + gridSpacing * 2, y: gridStartY + gridSpacing },
    'grid_orange_9': { x: gridStartX + gridSpacing * 3, y: gridStartY + gridSpacing },
    'grid_white_5': { x: gridStartX + gridSpacing * 4, y: gridStartY + gridSpacing },
    'grid_orange_10': { x: gridStartX + gridSpacing * 5, y: gridStartY + gridSpacing },
    'grid_white_6': { x: gridStartX + gridSpacing * 6, y: gridStartY + gridSpacing },
    'grid_orange_11': { x: gridStartX + gridSpacing * 7, y: gridStartY + gridSpacing },
    'grid_orange_12': { x: gridStartX + gridSpacing * 8, y: gridStartY + gridSpacing },

    // 第3行：白 橙 白 白 橙 白 橙 橙 白
    'grid_white_7': { x: gridStartX, y: gridStartY + gridSpacing * 2 },
    'grid_orange_13': { x: gridStartX + gridSpacing, y: gridStartY + gridSpacing * 2 },
    'grid_white_8': { x: gridStartX + gridSpacing * 2, y: gridStartY + gridSpacing * 2 },
    'grid_white_9': { x: gridStartX + gridSpacing * 3, y: gridStartY + gridSpacing * 2 },
    'grid_orange_14': { x: gridStartX + gridSpacing * 4, y: gridStartY + gridSpacing * 2 },
    'grid_white_10': { x: gridStartX + gridSpacing * 5, y: gridStartY + gridSpacing * 2 },
    'grid_orange_15': { x: gridStartX + gridSpacing * 6, y: gridStartY + gridSpacing * 2 },
    'grid_orange_16': { x: gridStartX + gridSpacing * 7, y: gridStartY + gridSpacing * 2 },
    'grid_white_11': { x: gridStartX + gridSpacing * 8, y: gridStartY + gridSpacing * 2 },

    // 第4行：橙 橙 白 橙 白 白 橙 白 橙
    'grid_orange_17': { x: gridStartX, y: gridStartY + gridSpacing * 3 },
    'grid_orange_18': { x: gridStartX + gridSpacing, y: gridStartY + gridSpacing * 3 },
    'grid_white_12': { x: gridStartX + gridSpacing * 2, y: gridStartY + gridSpacing * 3 },
    'grid_orange_19': { x: gridStartX + gridSpacing * 3, y: gridStartY + gridSpacing * 3 },
    'grid_white_13': { x: gridStartX + gridSpacing * 4, y: gridStartY + gridSpacing * 3 },
    'grid_white_14': { x: gridStartX + gridSpacing * 5, y: gridStartY + gridSpacing * 3 },
    'grid_orange_20': { x: gridStartX + gridSpacing * 6, y: gridStartY + gridSpacing * 3 },
    'grid_white_15': { x: gridStartX + gridSpacing * 7, y: gridStartY + gridSpacing * 3 },
    'grid_orange_21': { x: gridStartX + gridSpacing * 8, y: gridStartY + gridSpacing * 3 },
  }

  cy.layout({
    name: 'preset',
    positions: (node: any) => positions[node.id()] || { x: 400, y: 300 },
    fit: true,
    padding: 20,
    animate: true,
    animationDuration: 1000,
  }).run()
}

// 步骤2：按年份聚合
const showStep2 = () => {
  if (!cy) return

  // 将文档节点移入对应的项目容器
  documents.forEach(doc => {
    cy.nodes(`#${doc.id}`).move({ parent: doc.project })
  })

  // 添加同项目内文档的流程连接
  const projectGroups = {
    'proj_led_screen': ['doc_p1_tender', 'doc_p1_bid', 'doc_p1_contract'],
    'proj_scanner': ['doc_p2_tender', 'doc_p2_bid', 'doc_p2_contract'],
    'proj_air_conditioner': ['doc_p3_tender', 'doc_p3_bid', 'doc_p3_contract']
  }

  Object.values(projectGroups).forEach(docIds => {
    for (let i = 0; i < docIds.length - 1; i++) {
      const edgeId = `edge_flow_${docIds[i]}_${docIds[i + 1]}`
      if (cy.$id(edgeId).length === 0) {
        cy.add({
          group: 'edges',
          data: {
            id: edgeId,
            source: docIds[i],
            target: docIds[i + 1],
          },
          classes: 'doc-flow'
        })
      }
    }
  })

  // 添加项目到年份的边
  const yearEdges = [
    { id: 'edge_year_led', source: 'proj_led_screen', target: 'year_2025' },
    { id: 'edge_year_scanner', source: 'proj_scanner', target: 'year_2025' },
    { id: 'edge_year_air', source: 'proj_air_conditioner', target: 'year_2024' },
  ]

  yearEdges.forEach(edge => {
    if (cy.$id(edge.id).length === 0) {
      cy.add({
        group: 'edges',
        data: edge,
        classes: 'year-edge'
      })
    }
  })

  const yearY = 30  // 年份在最顶层，向上移动
  const projectY = 160  // 项目在中层，向上移动
  const spacing = 240
  const startX = 80
  const docSpacing = 95

  // 4×9 底层网格位置（与上方项目宽度一致）
  const gridStartY = 360  // 底层网格向上移动
  const gridStartX = startX
  const gridSpacing = 65

  const positions: any = {
    // 年份节点在最顶层
    'year_2025': { x: startX + spacing * 0.5, y: yearY },
    'year_2024': { x: startX + spacing * 2, y: yearY },

    // 项目节点在中层
    'proj_led_screen': { x: startX, y: projectY },
    'proj_scanner': { x: startX + spacing, y: projectY },
    'proj_air_conditioner': { x: startX + spacing * 2, y: projectY },

    'doc_p1_tender': { x: startX, y: projectY - docSpacing },
    'doc_p1_bid': { x: startX, y: projectY },
    'doc_p1_contract': { x: startX, y: projectY + docSpacing },

    'doc_p2_tender': { x: startX + spacing, y: projectY - docSpacing },
    'doc_p2_bid': { x: startX + spacing, y: projectY },
    'doc_p2_contract': { x: startX + spacing, y: projectY + docSpacing },

    'doc_p3_tender': { x: startX + spacing * 2, y: projectY - docSpacing },
    'doc_p3_bid': { x: startX + spacing * 2, y: projectY },
    'doc_p3_contract': { x: startX + spacing * 2, y: projectY + docSpacing },

    // 4×9 底层网格布局
    // 第1行：橙 橙 白 橙 橙 白 橙 白 橙
    'grid_orange_1': { x: gridStartX, y: gridStartY },
    'grid_orange_2': { x: gridStartX + gridSpacing, y: gridStartY },
    'grid_white_1': { x: gridStartX + gridSpacing * 2, y: gridStartY },
    'grid_orange_3': { x: gridStartX + gridSpacing * 3, y: gridStartY },
    'grid_orange_4': { x: gridStartX + gridSpacing * 4, y: gridStartY },
    'grid_white_2': { x: gridStartX + gridSpacing * 5, y: gridStartY },
    'grid_orange_5': { x: gridStartX + gridSpacing * 6, y: gridStartY },
    'grid_white_3': { x: gridStartX + gridSpacing * 7, y: gridStartY },
    'grid_orange_6': { x: gridStartX + gridSpacing * 8, y: gridStartY },

    // 第2行：橙 白 橙 橙 白 橙 白 橙 橙
    'grid_orange_7': { x: gridStartX, y: gridStartY + gridSpacing },
    'grid_white_4': { x: gridStartX + gridSpacing, y: gridStartY + gridSpacing },
    'grid_orange_8': { x: gridStartX + gridSpacing * 2, y: gridStartY + gridSpacing },
    'grid_orange_9': { x: gridStartX + gridSpacing * 3, y: gridStartY + gridSpacing },
    'grid_white_5': { x: gridStartX + gridSpacing * 4, y: gridStartY + gridSpacing },
    'grid_orange_10': { x: gridStartX + gridSpacing * 5, y: gridStartY + gridSpacing },
    'grid_white_6': { x: gridStartX + gridSpacing * 6, y: gridStartY + gridSpacing },
    'grid_orange_11': { x: gridStartX + gridSpacing * 7, y: gridStartY + gridSpacing },
    'grid_orange_12': { x: gridStartX + gridSpacing * 8, y: gridStartY + gridSpacing },

    // 第3行：白 橙 白 白 橙 白 橙 橙 白
    'grid_white_7': { x: gridStartX, y: gridStartY + gridSpacing * 2 },
    'grid_orange_13': { x: gridStartX + gridSpacing, y: gridStartY + gridSpacing * 2 },
    'grid_white_8': { x: gridStartX + gridSpacing * 2, y: gridStartY + gridSpacing * 2 },
    'grid_white_9': { x: gridStartX + gridSpacing * 3, y: gridStartY + gridSpacing * 2 },
    'grid_orange_14': { x: gridStartX + gridSpacing * 4, y: gridStartY + gridSpacing * 2 },
    'grid_white_10': { x: gridStartX + gridSpacing * 5, y: gridStartY + gridSpacing * 2 },
    'grid_orange_15': { x: gridStartX + gridSpacing * 6, y: gridStartY + gridSpacing * 2 },
    'grid_orange_16': { x: gridStartX + gridSpacing * 7, y: gridStartY + gridSpacing * 2 },
    'grid_white_11': { x: gridStartX + gridSpacing * 8, y: gridStartY + gridSpacing * 2 },

    // 第4行：橙 橙 白 橙 白 白 橙 白 橙
    'grid_orange_17': { x: gridStartX, y: gridStartY + gridSpacing * 3 },
    'grid_orange_18': { x: gridStartX + gridSpacing, y: gridStartY + gridSpacing * 3 },
    'grid_white_12': { x: gridStartX + gridSpacing * 2, y: gridStartY + gridSpacing * 3 },
    'grid_orange_19': { x: gridStartX + gridSpacing * 3, y: gridStartY + gridSpacing * 3 },
    'grid_white_13': { x: gridStartX + gridSpacing * 4, y: gridStartY + gridSpacing * 3 },
    'grid_white_14': { x: gridStartX + gridSpacing * 5, y: gridStartY + gridSpacing * 3 },
    'grid_orange_20': { x: gridStartX + gridSpacing * 6, y: gridStartY + gridSpacing * 3 },
    'grid_white_15': { x: gridStartX + gridSpacing * 7, y: gridStartY + gridSpacing * 3 },
    'grid_orange_21': { x: gridStartX + gridSpacing * 8, y: gridStartY + gridSpacing * 3 },
  }

  cy.layout({
    name: 'preset',
    positions: (node: any) => positions[node.id()] || { x: 400, y: 300 },
    fit: true,
    padding: 20,
    animate: true,
    animationDuration: 1000,
  }).run()
}
</script>

<style lang="scss" scoped>
.knowledge-graph-step-ppt {
  width: 100%;
  height: 100%;
  background: #F5FAFF;

  .ppt-content {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    background: #F5FAFF;

    .header {
      text-align: center;
      padding: 10px 60px 10px;

      .title {
        font-size: 48px;
        font-weight: bold;
        color: #1a1a2e;
        margin: 0;
        position: relative;
        display: inline-block;
        padding-bottom: 20px;

        &::after {
          content: '';
          position: absolute;
          bottom: 0;
          left: 50%;
          transform: translateX(-50%);
          width: 80px;
          height: 4px;
          background: #1890ff;
          border-radius: 2px;
        }
      }
    }

    .content-area {
      flex: 1;
      display: flex;
      flex-direction: column;
      padding: 0 80px 40px;
      gap: 16px;
      background: #F5FAFF;

      .text-section {
        padding: 0;

        .step-desc {
          text-align: left;

          h3 {
            font-size: 32px;
            color: #1890ff;
            margin-bottom: 12px;
            font-weight: 600;
          }

          p {
            font-size: 18px;
            line-height: 1.8;
            color: #333;
            text-align: justify;
            max-width: 85%;
          }
        }
      }

      .graph-section {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;

        .graph-container-wrapper {
          width: v-bind(graphWidth);
          height: v-bind(graphHeight);
          background: #fff;
          border-radius: 12px;
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
        }

        .graph-full-container {
          width: 100%;
          height: 100%;
          border-radius: 12px;
        }
      }
    }
  }
}
</style>
