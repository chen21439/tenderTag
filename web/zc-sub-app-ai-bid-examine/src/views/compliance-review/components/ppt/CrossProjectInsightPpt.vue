<template>
  <div class="cross-project-insight-ppt">
    <PptSlideBase>
      <div class="ppt-content">
        <!-- 顶部标题 -->
        <div class="header">
          <h1 class="title">业务本体与项目知识图谱平台</h1>
        </div>

        <!-- 内容区域（左右布局） -->
        <div class="content-area">
          <!-- 左侧文字说明 -->
          <div class="text-section">
            <h2 class="subtitle">数据连接</h2>
            <p class="description">
              基于文档智能，通过知识图谱，将散落在各系统和文档中的项目、合同、框架协议、供应商等数据在语义层面实现统一和关联，打通数据孤岛，为项目管理、BI 报表和 AI 问答提供一致的数据视图。
            </p>
          </div>

          <!-- 右侧图谱容器 -->
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
import { ref, onMounted, onUnmounted } from 'vue'
import cytoscape from 'cytoscape'
import PptSlideBase from './PptSlideBase.vue'

defineOptions({
  name: 'CrossProjectInsightPpt'
})

const graphContainer = ref<HTMLElement | null>(null)
let cy: any = null

onMounted(() => {
  if (!graphContainer.value) return

  // 创建节点：输入 -> 平台 -> 输出能力
  const nodes = [
    // 输入节点（左侧）
    { id: 'input', label: '文档', type: 'input' },

    // 中间平台节点
    { id: 'platform', label: '知识图谱\n平台', type: 'platform' },

    // 输出能力节点（右侧）
    { id: 'output1', label: 'Apps', type: 'output' },
    { id: 'output2', label: '数据报表', type: 'output' },
    { id: 'output3', label: '框采交易\n商城', type: 'output' },
    { id: 'output4', label: 'AI问答', type: 'output' },
    { id: 'output5', label: '项目生命\n周期管理', type: 'output' }
  ]

  // 创建边：输入 -> 平台 -> 各个输出
  const edges = [
    // 输入到平台
    { id: 'edge_input', source: 'input', target: 'platform' },

    // 平台到各个输出能力
    { id: 'edge_out1', source: 'platform', target: 'output1' },
    { id: 'edge_out2', source: 'platform', target: 'output2' },
    { id: 'edge_out3', source: 'platform', target: 'output3' },
    { id: 'edge_out4', source: 'platform', target: 'output4' },
    { id: 'edge_out5', source: 'platform', target: 'output5' }
  ]

  // 初始化 Cytoscape
  const elements = [
    ...nodes.map(node => ({
      data: { id: node.id, label: node.label, type: node.type },
      classes: 'visible'
    })),
    ...edges.map(edge => ({
      data: { id: edge.id, source: edge.source, target: edge.target },
      classes: 'connection'
    }))
  ]

  // 样式定义
  const customStyles = [
    {
      selector: 'node',
      style: {
        'background-color': '#0c4a6e',
        'border-color': '#0369a1',
        'border-width': 3,
        label: 'data(label)',
        color: '#fff',
        'font-size': 16,
        'font-weight': 'bold',
        'text-valign': 'center',
        'text-halign': 'center',
        'text-wrap': 'wrap',
        'text-max-width': '100px',
        shape: 'hexagon',
        width: 120,
        height: 120
      }
    },
    // 输入节点样式
    {
      selector: 'node[type="input"]',
      style: {
        'background-color': '#0c4a6e',
        'border-color': '#38bdf8',
        'border-width': 3,
        color: '#fff',
        width: 120,
        height: 120,
        'font-size': 18,
        'text-max-width': '100px'
      }
    },
    // 平台节点样式
    {
      selector: 'node[type="platform"]',
      style: {
        'background-color': '#0c4a6e',
        'border-color': '#38bdf8',
        'border-width': 4,
        color: '#fff',
        width: 150,
        height: 150,
        'font-size': 20,
        'text-max-width': '130px'
      }
    },
    // 输出节点样式
    {
      selector: 'node[type="output"]',
      style: {
        'background-color': '#0c4a6e',
        'border-color': '#0ea5e9',
        'border-width': 3,
        color: '#fff',
        width: 110,
        height: 110,
        'font-size': 14,
        'text-max-width': '90px'
      }
    },
    {
      selector: 'edge',
      style: {
        width: 3,
        'line-color': '#38bdf8',
        'target-arrow-color': '#38bdf8',
        'target-arrow-shape': 'triangle',
        'arrow-scale': 1.2,
        'curve-style': 'bezier'
      }
    }
  ]

  cy = cytoscape({
    container: graphContainer.value,
    elements: elements,
    style: customStyles,
    layout: {
      name: 'preset'
    }
  })

  // 设置节点位置（扇形展开布局）
  const leftX = 150
  const centerX = 400
  const centerY = 220

  // 输入节点（左侧）
  cy.getElementById('input').position({ x: leftX, y: centerY })

  // 平台节点（中间）
  cy.getElementById('platform').position({ x: centerX, y: centerY })

  // 输出能力节点（右侧，扇形分布）
  const outputPositions = [
    { id: 'output1', x: 600, y: 40 },    // Apps - 最上方
    { id: 'output2', x: 650, y: 120 },   // 数据报表
    { id: 'output3', x: 680, y: 220 },   // 框采交易商城 - 中间
    { id: 'output4', x: 650, y: 320 },   // AI问答
    { id: 'output5', x: 600, y: 400 }    // 项目生命周期管理 - 最下方
  ]

  outputPositions.forEach(pos => {
    cy.getElementById(pos.id).position({ x: pos.x, y: pos.y })
  })

  // 适配视图
  cy.fit(undefined, 40)
})

onUnmounted(() => {
  if (cy) {
    cy.destroy()
    cy = null
  }
})
</script>

<style lang="scss" scoped>
.cross-project-insight-ppt {
  width: 100%;
  height: 100%;
  background: #f5faff;

  .ppt-content {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    background: #f5faff;
    position: relative;

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
      flex-direction: column;
      padding: 20px 60px 40px;
      gap: 30px;

      .text-section {
        display: flex;
        flex-direction: column;

        .subtitle {
          font-size: 32px;
          color: #1890ff;
          margin-bottom: 15px;
          margin-top: 0;
          font-weight: 600;
        }

        .description {
          font-size: 18px;
          line-height: 1.8;
          color: #333;
          text-align: justify;
        }
      }

      .graph-section {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;

        .graph-container-wrapper {
          width: 85%;
          height: 100%;
          max-height: 450px;
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
