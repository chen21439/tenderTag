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
          <!-- 左侧文字说明 -->
          <div class="left-section">
            <div class="step-desc">
              <div class="desc-item">
                <h3>{{ stepConfig.title }}</h3>
                <p>{{ stepConfig.description }}</p>
              </div>
            </div>
          </div>

          <!-- 右侧图谱容器 -->
          <div class="right-section">
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
}

const props = withDefaults(defineProps<Props>(), {
  step: 0
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

    // 占位节点（用于信息孤岛阶段的网格布局）
    { data: { id: 'placeholder_1', label: '', type: 'placeholder' }, classes: props.step === 0 ? 'visible' : 'hidden' },
    { data: { id: 'placeholder_2', label: '', type: 'placeholder' }, classes: props.step === 0 ? 'visible' : 'hidden' },
    { data: { id: 'placeholder_3', label: '', type: 'placeholder' }, classes: props.step === 0 ? 'visible' : 'hidden' },
    { data: { id: 'placeholder_4', label: '', type: 'placeholder' }, classes: props.step === 0 ? 'visible' : 'hidden' },
    { data: { id: 'placeholder_5', label: '', type: 'placeholder' }, classes: props.step === 0 ? 'visible' : 'hidden' },
    { data: { id: 'placeholder_6', label: '', type: 'placeholder' }, classes: props.step === 0 ? 'visible' : 'hidden' },
    { data: { id: 'placeholder_7', label: '', type: 'placeholder' }, classes: props.step === 0 ? 'visible' : 'hidden' },

    // 项目节点
    { data: { id: 'proj_led_screen', label: 'LED显示屏', type: 'project', projectType: '框架协议采购项目', year: '2024-2025年度' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'proj_scanner', label: '扫描仪', type: 'project', projectType: '框架协议采购项目', year: '2025-2026年度' }, classes: props.step >= 1 ? 'visible' : 'hidden' },
    { data: { id: 'proj_air_conditioner', label: '空调机', type: 'project', projectType: '框架协议采购项目', year: '2025年' }, classes: props.step >= 1 ? 'visible' : 'hidden' },

    // 年份节点
    { data: { id: 'year_2024', label: '2024年', type: 'year' }, classes: props.step === 2 ? 'visible' : 'hidden' },
    { data: { id: 'year_2025', label: '2025年', type: 'year' }, classes: props.step === 2 ? 'visible' : 'hidden' },
  ]

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

// 步骤0：信息孤岛
const showStep0 = () => {
  if (!cy) return

  const gridSize = 80
  const startX = 100
  const startY = 100

  const positions: any = {
    'doc_p1_tender': { x: startX, y: startY },
    'doc_p2_tender': { x: startX + gridSize, y: startY },
    'placeholder_1': { x: startX + gridSize * 2, y: startY },
    'doc_p3_tender': { x: startX + gridSize * 3, y: startY },

    'doc_p1_bid': { x: startX, y: startY + gridSize },
    'placeholder_2': { x: startX + gridSize, y: startY + gridSize },
    'doc_p2_bid': { x: startX + gridSize * 2, y: startY + gridSize },
    'doc_p3_bid': { x: startX + gridSize * 3, y: startY + gridSize },

    'doc_p1_contract': { x: startX, y: startY + gridSize * 2 },
    'placeholder_3': { x: startX + gridSize, y: startY + gridSize * 2 },
    'placeholder_4': { x: startX + gridSize * 2, y: startY + gridSize * 2 },
    'placeholder_5': { x: startX + gridSize * 3, y: startY + gridSize * 2 },

    'placeholder_6': { x: startX, y: startY + gridSize * 3 },
    'doc_p2_contract': { x: startX + gridSize, y: startY + gridSize * 3 },
    'placeholder_7': { x: startX + gridSize * 2, y: startY + gridSize * 3 },
    'doc_p3_contract': { x: startX + gridSize * 3, y: startY + gridSize * 3 },
  }

  cy.layout({
    name: 'preset',
    positions: (node: any) => positions[node.id()] || { x: 0, y: 0 },
    fit: true,
    padding: 60,
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

  const centerY = 200
  const spacing = 240
  const startX = 80
  const docSpacing = 75

  const positions: any = {
    'proj_led_screen': { x: startX, y: centerY },
    'proj_scanner': { x: startX + spacing, y: centerY },
    'proj_air_conditioner': { x: startX + spacing * 2, y: centerY },

    'doc_p1_tender': { x: startX, y: centerY - docSpacing },
    'doc_p1_bid': { x: startX, y: centerY },
    'doc_p1_contract': { x: startX, y: centerY + docSpacing },

    'doc_p2_tender': { x: startX + spacing, y: centerY - docSpacing },
    'doc_p2_bid': { x: startX + spacing, y: centerY },
    'doc_p2_contract': { x: startX + spacing, y: centerY + docSpacing },

    'doc_p3_tender': { x: startX + spacing * 2, y: centerY - docSpacing },
    'doc_p3_bid': { x: startX + spacing * 2, y: centerY },
    'doc_p3_contract': { x: startX + spacing * 2, y: centerY + docSpacing },
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

  const centerY = 180
  const spacing = 240
  const startX = 80
  const docSpacing = 75
  const yearY = 420

  const positions: any = {
    'proj_led_screen': { x: startX, y: centerY },
    'proj_scanner': { x: startX + spacing, y: centerY },
    'proj_air_conditioner': { x: startX + spacing * 2, y: centerY },

    'doc_p1_tender': { x: startX, y: centerY - docSpacing },
    'doc_p1_bid': { x: startX, y: centerY },
    'doc_p1_contract': { x: startX, y: centerY + docSpacing },

    'doc_p2_tender': { x: startX + spacing, y: centerY - docSpacing },
    'doc_p2_bid': { x: startX + spacing, y: centerY },
    'doc_p2_contract': { x: startX + spacing, y: centerY + docSpacing },

    'doc_p3_tender': { x: startX + spacing * 2, y: centerY - docSpacing },
    'doc_p3_bid': { x: startX + spacing * 2, y: centerY },
    'doc_p3_contract': { x: startX + spacing * 2, y: centerY + docSpacing },

    'year_2024': { x: startX + spacing * 2, y: yearY },
    'year_2025': { x: startX + spacing * 0.5, y: yearY },
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
      padding: 40px 60px 20px;

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
      padding: 20px 40px 40px;
      gap: 40px;
      background: #F5FAFF;

      .left-section {
        flex: 1;
        display: flex;
        flex-direction: column;
        justify-content: center;

        .step-desc {
          .desc-item {
            h3 {
              font-size: 28px;
              color: #1890ff;
              margin-bottom: 20px;
            }

            p {
              font-size: 18px;
              line-height: 1.8;
              color: #333;
              text-align: justify;
            }
          }
        }
      }

      .right-section {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;

        .graph-container-wrapper {
          width: 100%;
          height: 70%;
          position: relative;
        }

        .graph-full-container {
          width: 100%;
          height: 100%;
        }
      }
    }
  }
}
</style>
