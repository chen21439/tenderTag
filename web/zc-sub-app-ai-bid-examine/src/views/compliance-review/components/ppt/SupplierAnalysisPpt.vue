<template>
  <div class="supplier-analysis-ppt">
    <PptSlideBase>
      <div class="ppt-content">
        <!-- 顶部标题 -->
        <div class="header">
          <h1 class="title">业务本体与项目知识图谱平台</h1>
        </div>

        <!-- 子标题 -->
        <div class="subtitle-section">
          <h2 class="subtitle">业务本体约束校验</h2>
          <p class="description">约束条件可以发现数据孤岛中的不一致之处，并标记出冲突的数据</p>
        </div>

        <!-- 内容区域 -->
        <div class="content-area">
          <!-- 图谱容器 -->
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
import { cytoscapeStyles } from './mockGraphData'

defineOptions({
  name: 'SupplierAnalysisPpt'
})

const graphContainer = ref<HTMLElement | null>(null)
let cy: any = null

onMounted(() => {
  if (!graphContainer.value) return

  // 行容器节点（每行一个要素类型）
  const rowContainers = [
    { id: 'container_code', label: '', type: 'container' },
    { id: 'container_amount', label: '', type: 'container' },
    { id: 'container_name', label: '', type: 'container' }
  ]

  // 行头节点（要素名称）
  const rowHeaders = [
    { id: 'header_code', label: '项目编号', type: 'row-header', parent: 'container_code' },
    { id: 'header_amount', label: '项目金额', type: 'row-header', parent: 'container_amount' },
    { id: 'header_name', label: '项目名称', type: 'row-header', parent: 'container_name' }
  ]

  // 文档节点数据（每行3个文档）
  const elements_data = [
    // 第一行：项目编号
    {
      id: 'code_notice',
      label: '招标公告\n\nPSCG2025000096_1',
      parent: 'container_code',
      field: 'code',
      doc: 'notice',
      status: 'valid'
    },
    {
      id: 'code_tender',
      label: '招标文件\n\nPSCG2025000096_1',
      parent: 'container_code',
      field: 'code',
      doc: 'tender',
      status: 'valid'
    },
    {
      id: 'code_contract',
      label: '合同\n\nPSCG2025000096',
      parent: 'container_code',
      field: 'code',
      doc: 'contract',
      status: 'error'
    },

    // 第二行：项目金额
    {
      id: 'amount_notice',
      label: '招标公告\n\n189万元',
      parent: 'container_amount',
      field: 'amount',
      doc: 'notice',
      status: 'valid'
    },
    {
      id: 'amount_tender',
      label: '招标文件\n\n189万元',
      parent: 'container_amount',
      field: 'amount',
      doc: 'tender',
      status: 'valid'
    },
    {
      id: 'amount_contract',
      label: '合同\n\n189万元',
      parent: 'container_amount',
      field: 'amount',
      doc: 'contract',
      status: 'valid'
    },

    // 第三行：项目名称
    {
      id: 'name_notice',
      label: '招标公告\n\n深圳市实验坪山学校及\n办公食堂家具采购项目',
      parent: 'container_name',
      field: 'name',
      doc: 'notice',
      status: 'valid'
    },
    {
      id: 'name_tender',
      label: '招标文件\n\n深圳市实验坪山学校及\n办公食堂家具采购项目',
      parent: 'container_name',
      field: 'name',
      doc: 'tender',
      status: 'valid'
    },
    {
      id: 'name_contract',
      label: '合同\n\n深圳市实验坪山学校及\n办公食堂家具采购项目',
      parent: 'container_name',
      field: 'name',
      doc: 'contract',
      status: 'valid'
    }
  ]

  // 初始化 Cytoscape 元素
  const elements: any[] = [
    // 行容器节点（虚线框）
    ...rowContainers.map(container => ({
      data: {
        id: container.id,
        label: container.label,
        type: 'container'
      },
      classes: 'visible'
    })),

    // 行头节点
    ...rowHeaders.map(header => ({
      data: {
        id: header.id,
        label: header.label,
        type: 'row-header',
        parent: header.parent
      },
      classes: 'visible'
    })),

    // 文档节点
    ...elements_data.map(elem => ({
      data: {
        id: elem.id,
        label: elem.label,
        type: 'field',
        parent: elem.parent,
        field: elem.field,
        doc: elem.doc,
        status: elem.status
      },
      classes: 'visible'
    }))
  ]

  // 添加每行内横向连接箭头（公告 -> 文件 -> 合同）
  const fields = ['name', 'amount', 'code']
  fields.forEach(field => {
    // 公告 -> 文件
    elements.push({
      data: {
        id: `edge_${field}_notice_tender`,
        source: `${field}_notice`,
        target: `${field}_tender`
      },
      classes: 'row-flow'
    })

    // 文件 -> 合同
    elements.push({
      data: {
        id: `edge_${field}_tender_contract`,
        source: `${field}_tender`,
        target: `${field}_contract`
      },
      classes: 'row-flow'
    })
  })

  // 自定义样式
  const customStyles = [
    ...cytoscapeStyles,
    // 容器样式（虚线框）
    {
      selector: 'node[type="container"]',
      style: {
        'background-color': 'transparent',
        'background-opacity': 0,
        'border-color': '#8b5cf6',
        'border-width': 3,
        'border-style': 'dashed',
        shape: 'roundrectangle',
        label: ''
      }
    },
    // 行头节点样式
    {
      selector: 'node[type="row-header"]',
      style: {
        'background-color': '#1890ff',
        'border-color': '#0050b3',
        'border-width': 2,
        color: '#fff',
        'font-size': 18,
        'font-weight': 'bold',
        width: 120,
        height: 60,
        shape: 'roundrectangle'
      }
    },
    // 要素节点根据状态显示不同颜色
    {
      selector: 'node[type="field"][status="valid"]',
      style: {
        'background-color': '#52c41a',
        'border-color': '#389e0d',
        'border-width': 2,
        color: '#fff',
        'font-size': 14,
        width: 140,
        height: 70,
        shape: 'roundrectangle',
        'text-wrap': 'wrap',
        'text-max-width': 120
      }
    },
    {
      selector: 'node[type="field"][status="warning"]',
      style: {
        'background-color': '#faad14',
        'border-color': '#d48806',
        'border-width': 2,
        color: '#fff',
        'font-size': 14,
        width: 140,
        height: 70,
        shape: 'roundrectangle',
        'text-wrap': 'wrap',
        'text-max-width': 120
      }
    },
    {
      selector: 'node[type="field"][status="error"]',
      style: {
        'background-color': '#ff4d4f',
        'border-color': '#cf1322',
        'border-width': 2,
        color: '#fff',
        'font-size': 14,
        width: 140,
        height: 70,
        shape: 'roundrectangle',
        'text-wrap': 'wrap',
        'text-max-width': 120
      }
    },
    // 行内连接箭头样式
    {
      selector: '.row-flow',
      style: {
        width: 3,
        'line-color': '#52c41a',
        'target-arrow-color': '#52c41a',
        'target-arrow-shape': 'triangle',
        'arrow-scale': 1.5,
        'curve-style': 'bezier'
      }
    }
  ]

  cy = cytoscape({
    container: graphContainer.value,
    elements: elements,
    style: customStyles,
    layout: {
      name: 'preset',
      fit: true,
      padding: 40
    }
  })

  // 设置节点位置（行头+横向文档布局）
  const headerX = 100
  const contentStartX = 260
  const startY = 100
  const rowSpacing = 140
  const colSpacing = 200

  const positions: Record<string, { x: number; y: number }> = {
    // 行容器（虚线框）- 每行一个
    container_code: { x: contentStartX + colSpacing, y: startY },
    container_amount: { x: contentStartX + colSpacing, y: startY + rowSpacing },
    container_name: { x: contentStartX + colSpacing, y: startY + rowSpacing * 2 },

    // 行头（左侧，与虚线框分离）
    header_code: { x: headerX, y: startY },
    header_amount: { x: headerX, y: startY + rowSpacing },
    header_name: { x: headerX, y: startY + rowSpacing * 2 },

    // 第一行：项目编号（横向排列：公告 -> 文件 -> 合同）
    code_notice: { x: contentStartX, y: startY },
    code_tender: { x: contentStartX + colSpacing, y: startY },
    code_contract: { x: contentStartX + colSpacing * 2, y: startY },

    // 第二行：项目金额（横向排列：公告 -> 文件 -> 合同）
    amount_notice: { x: contentStartX, y: startY + rowSpacing },
    amount_tender: { x: contentStartX + colSpacing, y: startY + rowSpacing },
    amount_contract: { x: contentStartX + colSpacing * 2, y: startY + rowSpacing },

    // 第三行：项目名称（横向排列：公告 -> 文件 -> 合同）
    name_notice: { x: contentStartX, y: startY + rowSpacing * 2 },
    name_tender: { x: contentStartX + colSpacing, y: startY + rowSpacing * 2 },
    name_contract: { x: contentStartX + colSpacing * 2, y: startY + rowSpacing * 2 }
  }

  cy.layout({
    name: 'preset',
    positions: (node: any) => positions[node.id()] || { x: 0, y: 0 },
    fit: true,
    padding: 50,
    animate: true,
    animationDuration: 800
  }).run()
})

onUnmounted(() => {
  if (cy) {
    cy.destroy()
    cy = null
  }
})
</script>

<style lang="scss" scoped>
.supplier-analysis-ppt {
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

    .subtitle-section {
      padding: 0 80px 20px;

      .subtitle {
        font-size: 32px;
        color: #1890ff;
        margin-bottom: 12px;
        font-weight: 600;
      }

      .description {
        font-size: 18px;
        line-height: 1.8;
        color: #333;
        text-align: left;
        max-width: 85%;
      }
    }

    .content-area {
      flex: 1;
      display: flex;
      flex-direction: column;
      padding: 20px 40px 40px;
      gap: 20px;

      .graph-section {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;

        .graph-container-wrapper {
          width: 90%;
          height: 100%;
          max-height: 500px;
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
