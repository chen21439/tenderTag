<template>
  <div class="full-graph-ppt">
    <PptSlideBase>
      <!-- 左侧文字说明 -->
      <div class="left-content">
        <h1 class="title">从信息孤岛到知识图谱</h1>
        <div class="step-desc">
          <div v-if="currentStep === 0" class="desc-item">
            <h3>步骤1：信息孤岛</h3>
            <p>传统模式下，招标文件、评标报告、合同文本、验收报告等文档分散存储在不同位置，彼此孤立，难以关联。</p>
          </div>
          <div v-if="currentStep === 1" class="desc-item">
            <h3>步骤2：按项目聚合</h3>
            <p>通过AI提取和语义分析，将同一项目下的所有文档自动聚合到项目节点下，形成项目级的文档集合。</p>
          </div>
          <div v-if="currentStep === 2" class="desc-item">
            <h3>步骤3：按年份聚合</h3>
            <p>根据项目年份进行归类，建立项目与年份的关联关系，便于跨年度的项目追溯和统计分析。</p>
          </div>
        </div>

        <!-- 控制按钮 -->
        <div class="control-buttons-inline">
          <a-button
            v-if="currentStep > 0"
            size="large"
            @click="prevStep"
          >
            上一步
          </a-button>
          <a-button
            v-if="currentStep < steps.length - 1"
            type="primary"
            size="large"
            @click="nextStep"
          >
            下一步
          </a-button>
          <a-button
            v-if="currentStep === steps.length - 1"
            size="large"
            @click="resetSteps"
          >
            重新演示
          </a-button>
        </div>
      </div>

      <!-- 右侧图谱容器 -->
      <div class="right-content">
        <div class="graph-container-wrapper">
          <!-- 图谱容器 -->
          <div class="graph-full-container" ref="graphContainer"></div>

          <!-- 步骤指示器 -->
          <div class="step-indicator">
          <div
            v-for="(step, index) in steps"
            :key="index"
            class="step-item"
            :class="{ active: currentStep === index }"
            @click="goToStep(index)"
          >
            <div class="step-dot"></div>
            <div class="step-label">{{ step }}</div>
          </div>
        </div>
        </div>
      </div>
    </PptSlideBase>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { Button as AButton } from 'ant-design-vue'
import cytoscape from 'cytoscape'
import PptSlideBase from './PptSlideBase.vue'
import { documents, cytoscapeStyles } from './mockGraphData'

defineOptions({
  name: 'FullGraphPpt'
})

const graphContainer = ref<HTMLElement | null>(null)
let cy: any = null

const currentStep = ref(0)
const steps = [
  '信息孤岛',
  '按项目聚合',
  '按年份聚合'
]

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

    // 占位节点（用于信息孤岛阶段的网格布局，白色空格，穿插在橙色格子中间）
    { data: { id: 'placeholder_1', label: '', type: 'placeholder' }, classes: 'visible' },
    { data: { id: 'placeholder_2', label: '', type: 'placeholder' }, classes: 'visible' },
    { data: { id: 'placeholder_3', label: '', type: 'placeholder' }, classes: 'visible' },
    { data: { id: 'placeholder_4', label: '', type: 'placeholder' }, classes: 'visible' },
    { data: { id: 'placeholder_5', label: '', type: 'placeholder' }, classes: 'visible' },
    { data: { id: 'placeholder_6', label: '', type: 'placeholder' }, classes: 'visible' },
    { data: { id: 'placeholder_7', label: '', type: 'placeholder' }, classes: 'visible' },

    // 项目节点（初始隐藏）
    { data: { id: 'proj_led_screen', label: 'LED显示屏', type: 'project', projectType: '框架协议采购项目', year: '2024-2025年度' }, classes: 'hidden' },
    { data: { id: 'proj_scanner', label: '扫描仪', type: 'project', projectType: '框架协议采购项目', year: '2025-2026年度' }, classes: 'hidden' },
    { data: { id: 'proj_air_conditioner', label: '空调机', type: 'project', projectType: '框架协议采购项目', year: '2025年' }, classes: 'hidden' },

    // 年份节点（初始隐藏）- 根据文档实际年份创建
    { data: { id: 'year_2024', label: '2024年', type: 'year' }, classes: 'hidden' },
    { data: { id: 'year_2025', label: '2025年', type: 'year' }, classes: 'hidden' },

    // 组织和框架（初始隐藏）
    { data: { id: 'org_sz_hc', label: '某市政府采购中心', type: 'org' }, classes: 'hidden' },
    { data: { id: 'fa_equipment_2024', label: '2024年设备框架协议', type: 'framework', parent: 'org_sz_hc' }, classes: 'hidden' },
    { data: { id: 'fa_equipment_2025', label: '2025年设备框架协议', type: 'framework', parent: 'org_sz_hc' }, classes: 'hidden' },
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

  // 初始化第一步
  showStep0()
})

onUnmounted(() => {
  if (cy) {
    cy.destroy()
  }
})

// 步骤0：信息孤岛 - 文档随机散落
const showStep0 = () => {
  if (!cy) return

  // 隐藏所有项目、年份、供应商、组织节点
  cy.nodes('[type="project"], [type="year"], [type="supplier"], [type="org"], [type="framework"]').addClass('hidden')
  cy.edges().remove()

  // 移除文档节点的parent关系（恢复到独立状态）
  documents.forEach(doc => {
    cy.nodes(`#${doc.id}`).move({ parent: null })
  })

  // 显示所有文档，使用网格布局
  cy.nodes('[type="doc"]').removeClass('hidden')

  // 显示占位节点
  cy.nodes('[type="placeholder"]').removeClass('hidden')

  // 使用preset布局精确控制位置，形成左右分组效果
  // 左侧：LED和扫描仪项目的文档（蓝色系统区域）
  // 右侧：空调机项目的文档（橙色业务区域）
  const gridSize = 80
  const startX = 100
  const startY = 100

  // 定义每个节点的位置（4x4网格）
  const positions: any = {
    // 第1行：橙色 橙色 空白 橙色
    'doc_p1_tender': { x: startX, y: startY },
    'doc_p2_tender': { x: startX + gridSize, y: startY },
    'placeholder_1': { x: startX + gridSize * 2, y: startY },
    'doc_p3_tender': { x: startX + gridSize * 3, y: startY },

    // 第2行：橙色 空白 橙色 橙色
    'doc_p1_bid': { x: startX, y: startY + gridSize },
    'placeholder_2': { x: startX + gridSize, y: startY + gridSize },
    'doc_p2_bid': { x: startX + gridSize * 2, y: startY + gridSize },
    'doc_p3_bid': { x: startX + gridSize * 3, y: startY + gridSize },

    // 第3行：橙色 空白 空白 空白
    'doc_p1_contract': { x: startX, y: startY + gridSize * 2 },
    'placeholder_3': { x: startX + gridSize, y: startY + gridSize * 2 },
    'placeholder_4': { x: startX + gridSize * 2, y: startY + gridSize * 2 },
    'placeholder_5': { x: startX + gridSize * 3, y: startY + gridSize * 2 },

    // 第4行：空白 橙色 空白 橙色
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

// 步骤1：按项目聚合 - 文档放入项目容器内
const showStep1 = () => {
  if (!cy) return

  // 隐藏占位节点和年份节点
  cy.nodes('[type="placeholder"], [type="year"]').addClass('hidden')

  // 显示项目节点（作为容器）
  cy.nodes('[type="project"]').removeClass('hidden')

  // 将文档节点移入对应的项目容器（设置parent关系）
  documents.forEach(doc => {
    cy.nodes(`#${doc.id}`).move({ parent: doc.project })
  })

  // 添加同项目内文档的流程连接：招标文件 -> 投标文件 -> 合同
  const projectGroups = {
    'proj_led_screen': ['doc_p1_tender', 'doc_p1_bid', 'doc_p1_contract'],
    'proj_scanner': ['doc_p2_tender', 'doc_p2_bid', 'doc_p2_contract'],
    'proj_air_conditioner': ['doc_p3_tender', 'doc_p3_bid', 'doc_p3_contract']
  }

  Object.values(projectGroups).forEach(docIds => {
    for (let i = 0; i < docIds.length - 1; i++) {
      const edgeId = `edge_flow_${docIds[i]}_${docIds[i + 1]}`
      // 检查边是否已存在，避免重复添加
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

  // 使用preset布局精确控制项目容器位置，横向并排
  const centerY = 200
  const spacing = 240  // 增大项目间距，让整体更宽
  const startX = 80
  const docSpacing = 75  // 文档之间的垂直间距

  const positions: any = {
    // 3个项目容器横向排列
    'proj_led_screen': { x: startX, y: centerY },
    'proj_scanner': { x: startX + spacing, y: centerY },
    'proj_air_conditioner': { x: startX + spacing * 2, y: centerY },

    // LED项目的文档（竖向排列：招标文件 -> 投标文件 -> 合同）
    'doc_p1_tender': { x: startX, y: centerY - docSpacing },
    'doc_p1_bid': { x: startX, y: centerY },
    'doc_p1_contract': { x: startX, y: centerY + docSpacing },

    // 扫描仪项目的文档（竖向排列）
    'doc_p2_tender': { x: startX + spacing, y: centerY - docSpacing },
    'doc_p2_bid': { x: startX + spacing, y: centerY },
    'doc_p2_contract': { x: startX + spacing, y: centerY + docSpacing },

    // 空调机项目的文档（竖向排列）
    'doc_p3_tender': { x: startX + spacing * 2, y: centerY - docSpacing },
    'doc_p3_bid': { x: startX + spacing * 2, y: centerY },
    'doc_p3_contract': { x: startX + spacing * 2, y: centerY + docSpacing },
  }

  cy.layout({
    name: 'preset',
    positions: (node: any) => positions[node.id()] || { x: 400, y: 300 },
    fit: true,
    padding: 20,  // 进一步减小padding，让视角更近
    animate: true,
    animationDuration: 1000,
  }).run()
}

// 步骤2：按年份聚合 - 显示年份节点并连接项目
const showStep2 = () => {
  if (!cy) return

  // 显示年份节点
  cy.nodes('[type="year"]').removeClass('hidden')

  // 根据文档数据动态添加项目到年份的边
  // LED项目 -> 2025年
  // 扫描仪项目 -> 2025年
  // 空调机项目 -> 2024年
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

  // 使用preset布局，保持项目容器横向排列，年份节点在下方
  const centerY = 180
  const spacing = 240
  const startX = 80
  const docSpacing = 75
  const yearY = 420  // 年份节点Y坐标，在项目容器下方

  const positions: any = {
    // 3个项目容器横向排列（保持与步骤1相同的位置）
    'proj_led_screen': { x: startX, y: centerY },
    'proj_scanner': { x: startX + spacing, y: centerY },
    'proj_air_conditioner': { x: startX + spacing * 2, y: centerY },

    // 项目内的文档（竖向排列）
    'doc_p1_tender': { x: startX, y: centerY - docSpacing },
    'doc_p1_bid': { x: startX, y: centerY },
    'doc_p1_contract': { x: startX, y: centerY + docSpacing },

    'doc_p2_tender': { x: startX + spacing, y: centerY - docSpacing },
    'doc_p2_bid': { x: startX + spacing, y: centerY },
    'doc_p2_contract': { x: startX + spacing, y: centerY + docSpacing },

    'doc_p3_tender': { x: startX + spacing * 2, y: centerY - docSpacing },
    'doc_p3_bid': { x: startX + spacing * 2, y: centerY },
    'doc_p3_contract': { x: startX + spacing * 2, y: centerY + docSpacing },

    // 年份节点在下方：2024年（左）、2025年（中右）
    'year_2024': { x: startX + spacing * 2, y: yearY },  // 空调机下方
    'year_2025': { x: startX + spacing * 0.5, y: yearY },  // LED和扫描仪之间
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


const nextStep = () => {
  if (currentStep.value < steps.length - 1) {
    currentStep.value++
    goToStep(currentStep.value)
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
    goToStep(currentStep.value)
  }
}

const resetSteps = () => {
  currentStep.value = 0
  goToStep(0)
}

const goToStep = (step: number) => {
  currentStep.value = step

  switch (step) {
    case 0:
      showStep0()
      break
    case 1:
      showStep1()
      break
    case 2:
      showStep2()
      break
  }
}
</script>

<style lang="scss" scoped>
.full-graph-ppt {
  width: 100%;
  height: 100%;
  background: #fff;
  display: flex;

  .left-content {
    flex: 1;
    padding: 60px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    background: #F5FAFF;  // 统一背景色

    .title {
      font-size: 48px;
      font-weight: bold;
      color: #1a1a2e;
      margin-bottom: 40px;
      position: relative;
      padding-bottom: 20px;

      &::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 80px;
        height: 4px;
        background: #1890ff;
        border-radius: 2px;
      }
    }

    .step-desc {
      flex: 1;
      display: flex;
      align-items: center;

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

    .control-buttons-inline {
      display: flex;
      gap: 12px;
      margin-top: 30px;
    }
  }

  .right-content {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 40px;
    background: #F5FAFF;  // 统一背景色

    .graph-container-wrapper {
      width: 100%;  // 保持全宽
      height: 70%;  // 高度70%
      position: relative;
    }

    .graph-full-container {
      width: 100%;
      height: 100%;
    }
  }

  .step-indicator {
    position: absolute;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    gap: 30px;
    background: rgba(255, 255, 255, 0.95);
    padding: 12px 24px;
    border-radius: 30px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    z-index: 10;

    .step-item {
      display: flex;
      align-items: center;
      gap: 10px;
      cursor: pointer;
      transition: all 0.3s;
      padding: 8px 12px;
      border-radius: 20px;

      &:hover {
        background: rgba(24, 144, 255, 0.1);
      }

      &.active {
        .step-dot {
          background: #1890ff;
          transform: scale(1.3);
          box-shadow: 0 0 0 4px rgba(24, 144, 255, 0.2);
        }

        .step-label {
          color: #1890ff;
          font-weight: bold;
        }
      }

      .step-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #d9d9d9;
        transition: all 0.3s;
      }

      .step-label {
        font-size: 12px;
        color: #666;
        transition: all 0.3s;
        white-space: nowrap;
      }
    }
  }
}
</style>
