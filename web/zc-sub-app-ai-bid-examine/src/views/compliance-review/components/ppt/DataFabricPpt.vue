<template>
  <div class="data-fabric-ppt">
    <PptSlideBase>
      <div class="ppt-content">
        <!-- 顶部标题居中 -->
        <div class="header">
          <h1 class="title">业务本体与项目知识图谱平台</h1>
        </div>

        <!-- 内容区域 -->
        <div class="content-area">
          <!-- 左侧文字说明 - 三层架构描述 -->
          <div class="left-section">
            <div class="layer-descriptions">
              <!-- 顶层 -->
              <div class="layer-item">
                <h3 class="layer-title top-layer">项目生命周期管理</h3>
                <p class="layer-desc">
                  年度报表、审计、相似项目推荐、供应商关系分析、连接器等应用统一基于这张图谱获取数据，提升
                  <span style="color: #ff7a45">团队协作效率</span>
                </p>
              </div>

              <!-- 中间层 -->
              <div class="layer-item">
                <h3 class="layer-title middle-layer">基于业务本体构建知识图谱</h3>
                <p class="layer-desc">
                  基于
                  <span style="color: #ff7a45">文档智能</span>
                  ，通过本体与解析规则，从底层文档中抽取项目信息、合同信息、供应商信息等关键数据构建为相互关联的知识图谱网络
                </p>
              </div>

              <!-- 底层 -->
              <div class="layer-item">
                <h3 class="layer-title bottom-layer">信息孤岛</h3>
                <p class="layer-desc">散落在各处的项目相关文档</p>
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
import { ref, onMounted, onUnmounted } from 'vue'
import cytoscape from 'cytoscape'
import PptSlideBase from './PptSlideBase.vue'

defineOptions({
  name: 'DataFabricPpt'
})

const graphContainer = ref<HTMLElement | null>(null)
let cy: any = null

onMounted(() => {
  if (!graphContainer.value) return

  // 构建三层架构的数据
  const elements = [
    // === 顶层：应用层（Apps, AI, BI Tools）===
    { data: { id: 'app_apps', label: 'Apps', type: 'application', layer: 3 } },
    { data: { id: 'app_ai', label: 'AI', type: 'application', layer: 3 } },
    { data: { id: 'app_bi', label: 'BI Tools', type: 'application', layer: 3 } },

    // === 中层：知识图谱网络层（蓝色和橙色的小圆点）===
    // 蓝色节点 - 数据管理系统侧
    { data: { id: 'kg_blue_1', label: '', type: 'kg_blue', layer: 2 } },
    { data: { id: 'kg_blue_2', label: '', type: 'kg_blue', layer: 2 } },
    { data: { id: 'kg_blue_3', label: '', type: 'kg_blue', layer: 2 } },
    { data: { id: 'kg_blue_4', label: '', type: 'kg_blue', layer: 2 } },
    { data: { id: 'kg_blue_5', label: '', type: 'kg_blue', layer: 2 } },
    { data: { id: 'kg_blue_6', label: '', type: 'kg_blue', layer: 2 } },
    { data: { id: 'kg_blue_7', label: '', type: 'kg_blue', layer: 2 } },
    { data: { id: 'kg_blue_8', label: '', type: 'kg_blue', layer: 2 } },
    { data: { id: 'kg_blue_9', label: '', type: 'kg_blue', layer: 2 } },
    { data: { id: 'kg_blue_10', label: '', type: 'kg_blue', layer: 2 } },

    // 橙色节点 - 业务单元侧
    { data: { id: 'kg_orange_1', label: '', type: 'kg_orange', layer: 2 } },
    { data: { id: 'kg_orange_2', label: '', type: 'kg_orange', layer: 2 } },
    { data: { id: 'kg_orange_3', label: '', type: 'kg_orange', layer: 2 } },
    { data: { id: 'kg_orange_4', label: '', type: 'kg_orange', layer: 2 } },
    { data: { id: 'kg_orange_5', label: '', type: 'kg_orange', layer: 2 } },
    { data: { id: 'kg_orange_6', label: '', type: 'kg_orange', layer: 2 } },
    { data: { id: 'kg_orange_7', label: '', type: 'kg_orange', layer: 2 } },
    { data: { id: 'kg_orange_8', label: '', type: 'kg_orange', layer: 2 } },

    // === 底层：数据孤岛层（文档方块）- 4x9网格，橙色和白色交错===
    // 第1行：橙 橙 白 橙 橙 白 橙 白 橙
    { data: { id: 'doc_orange_1', label: '', type: 'doc_orange', layer: 1 } },
    { data: { id: 'doc_orange_2', label: '', type: 'doc_orange', layer: 1 } },
    { data: { id: 'doc_white_1', label: '', type: 'doc_white', layer: 1 } },
    { data: { id: 'doc_orange_3', label: '', type: 'doc_orange', layer: 1 } },
    { data: { id: 'doc_orange_4', label: '', type: 'doc_orange', layer: 1 } },
    { data: { id: 'doc_white_2', label: '', type: 'doc_white', layer: 1 } },
    { data: { id: 'doc_orange_5', label: '', type: 'doc_orange', layer: 1 } },
    { data: { id: 'doc_white_3', label: '', type: 'doc_white', layer: 1 } },
    { data: { id: 'doc_orange_6', label: '', type: 'doc_orange', layer: 1 } },

    // 第2行：橙 白 橙 橙 白 橙 白 橙 橙
    { data: { id: 'doc_orange_7', label: '', type: 'doc_orange', layer: 1 } },
    { data: { id: 'doc_white_4', label: '', type: 'doc_white', layer: 1 } },
    { data: { id: 'doc_orange_8', label: '', type: 'doc_orange', layer: 1 } },
    { data: { id: 'doc_orange_9', label: '', type: 'doc_orange', layer: 1 } },
    { data: { id: 'doc_white_5', label: '', type: 'doc_white', layer: 1 } },
    { data: { id: 'doc_orange_10', label: '', type: 'doc_orange', layer: 1 } },
    { data: { id: 'doc_white_6', label: '', type: 'doc_white', layer: 1 } },
    { data: { id: 'doc_orange_11', label: '', type: 'doc_orange', layer: 1 } },
    { data: { id: 'doc_orange_12', label: '', type: 'doc_orange', layer: 1 } },

    // 第3行：白 橙 白 白 橙 白 橙 橙 白
    { data: { id: 'doc_white_7', label: '', type: 'doc_white', layer: 1 } },
    { data: { id: 'doc_orange_13', label: '', type: 'doc_orange', layer: 1 } },
    { data: { id: 'doc_white_8', label: '', type: 'doc_white', layer: 1 } },
    { data: { id: 'doc_white_9', label: '', type: 'doc_white', layer: 1 } },
    { data: { id: 'doc_orange_14', label: '', type: 'doc_orange', layer: 1 } },
    { data: { id: 'doc_white_10', label: '', type: 'doc_white', layer: 1 } },
    { data: { id: 'doc_orange_15', label: '', type: 'doc_orange', layer: 1 } },
    { data: { id: 'doc_orange_16', label: '', type: 'doc_orange', layer: 1 } },
    { data: { id: 'doc_white_11', label: '', type: 'doc_white', layer: 1 } },

    // 第4行：橙 橙 白 橙 白 白 橙 白 橙
    { data: { id: 'doc_orange_17', label: '', type: 'doc_orange', layer: 1 } },
    { data: { id: 'doc_orange_18', label: '', type: 'doc_orange', layer: 1 } },
    { data: { id: 'doc_white_12', label: '', type: 'doc_white', layer: 1 } },
    { data: { id: 'doc_orange_19', label: '', type: 'doc_orange', layer: 1 } },
    { data: { id: 'doc_white_13', label: '', type: 'doc_white', layer: 1 } },
    { data: { id: 'doc_white_14', label: '', type: 'doc_white', layer: 1 } },
    { data: { id: 'doc_orange_20', label: '', type: 'doc_orange', layer: 1 } },
    { data: { id: 'doc_white_15', label: '', type: 'doc_white', layer: 1 } },
    { data: { id: 'doc_orange_21', label: '', type: 'doc_orange', layer: 1 } }
  ]

  // 添加边：构建三层之间的连接
  const edges = [
    // 应用层 -> 知识图谱层的连接
    { data: { source: 'app_apps', target: 'kg_blue_2' } },
    { data: { source: 'app_apps', target: 'kg_blue_5' } },
    { data: { source: 'app_ai', target: 'kg_blue_3' } },
    { data: { source: 'app_ai', target: 'kg_orange_2' } },
    { data: { source: 'app_ai', target: 'kg_orange_5' } },
    { data: { source: 'app_bi', target: 'kg_orange_3' } },
    { data: { source: 'app_bi', target: 'kg_orange_7' } },

    // 知识图谱层内部的连接（蓝色之间、橙色之间、蓝色-橙色交叉）
    { data: { source: 'kg_blue_1', target: 'kg_blue_3' } },
    { data: { source: 'kg_blue_2', target: 'kg_blue_4' } },
    { data: { source: 'kg_blue_3', target: 'kg_blue_5' } },
    { data: { source: 'kg_blue_4', target: 'kg_blue_6' } },
    { data: { source: 'kg_blue_5', target: 'kg_blue_7' } },
    { data: { source: 'kg_blue_6', target: 'kg_blue_8' } },
    { data: { source: 'kg_blue_7', target: 'kg_blue_9' } },

    { data: { source: 'kg_orange_1', target: 'kg_orange_3' } },
    { data: { source: 'kg_orange_2', target: 'kg_orange_4' } },
    { data: { source: 'kg_orange_3', target: 'kg_orange_5' } },
    { data: { source: 'kg_orange_4', target: 'kg_orange_6' } },
    { data: { source: 'kg_orange_5', target: 'kg_orange_7' } },

    // 蓝色和橙色之间的交叉连接
    { data: { source: 'kg_blue_2', target: 'kg_orange_2' } },
    { data: { source: 'kg_blue_4', target: 'kg_orange_3' } },
    { data: { source: 'kg_blue_6', target: 'kg_orange_5' } },
    { data: { source: 'kg_blue_8', target: 'kg_orange_6' } },

    // 知识图谱层 -> 数据孤岛层的连接（只连接橙色方块，共21个橙色）
    { data: { source: 'kg_orange_1', target: 'doc_orange_1' } },
    { data: { source: 'kg_orange_1', target: 'doc_orange_2' } },
    { data: { source: 'kg_orange_1', target: 'doc_orange_3' } },
    { data: { source: 'kg_orange_2', target: 'doc_orange_4' } },
    { data: { source: 'kg_orange_2', target: 'doc_orange_5' } },
    { data: { source: 'kg_orange_2', target: 'doc_orange_6' } },
    { data: { source: 'kg_orange_3', target: 'doc_orange_7' } },
    { data: { source: 'kg_orange_3', target: 'doc_orange_8' } },
    { data: { source: 'kg_orange_3', target: 'doc_orange_9' } },
    { data: { source: 'kg_orange_4', target: 'doc_orange_10' } },
    { data: { source: 'kg_orange_4', target: 'doc_orange_11' } },
    { data: { source: 'kg_orange_5', target: 'doc_orange_12' } },
    { data: { source: 'kg_orange_5', target: 'doc_orange_13' } },
    { data: { source: 'kg_orange_5', target: 'doc_orange_14' } },
    { data: { source: 'kg_orange_6', target: 'doc_orange_15' } },
    { data: { source: 'kg_orange_6', target: 'doc_orange_16' } },
    { data: { source: 'kg_orange_7', target: 'doc_orange_17' } },
    { data: { source: 'kg_orange_7', target: 'doc_orange_18' } },
    { data: { source: 'kg_orange_8', target: 'doc_orange_19' } },
    { data: { source: 'kg_orange_8', target: 'doc_orange_20' } },
    { data: { source: 'kg_blue_1', target: 'doc_orange_21' } }
  ]

  // 定义样式
  const styles = [
    {
      selector: 'node',
      style: {
        'text-valign': 'center',
        'text-halign': 'center',
        'font-size': '12px',
        'border-width': 2
      }
    },
    // 顶层：应用节点
    {
      selector: 'node[type="application"]',
      style: {
        'background-color': '#f0f5ff',
        'border-color': '#adc6ff',
        'border-width': 2,
        width: 80,
        height: 60,
        shape: 'roundrectangle',
        label: 'data(label)',
        'font-size': '14px',
        'font-weight': 'bold',
        color: '#1890ff'
      }
    },
    // 中层：蓝色知识图谱节点
    {
      selector: 'node[type="kg_blue"]',
      style: {
        'background-color': '#1890ff',
        'border-color': '#096dd9',
        width: 12,
        height: 12,
        shape: 'ellipse',
        label: ''
      }
    },
    // 中层：橙色知识图谱节点
    {
      selector: 'node[type="kg_orange"]',
      style: {
        'background-color': '#fa8c16',
        'border-color': '#d46b08',
        width: 12,
        height: 12,
        shape: 'ellipse',
        label: ''
      }
    },
    // 底层：橙色文档方块
    {
      selector: 'node[type="doc_orange"]',
      style: {
        'background-color': '#fa8c16',
        'border-color': '#d46b08',
        width: 32,
        height: 32,
        shape: 'rectangle',
        label: ''
      }
    },
    // 底层：白色文档方块（占位符）
    {
      selector: 'node[type="doc_white"]',
      style: {
        'background-color': '#fff',
        'border-color': '#d9d9d9',
        'border-width': 2,
        width: 32,
        height: 32,
        shape: 'rectangle',
        label: ''
      }
    },
    // 边的样式
    {
      selector: 'edge',
      style: {
        width: 1,
        'line-color': '#d9d9d9',
        'curve-style': 'bezier',
        opacity: 0.5
      }
    }
  ]

  cy = cytoscape({
    container: graphContainer.value,
    elements: [...elements, ...edges],
    style: styles,
    layout: {
      name: 'preset'
    }
  })

  // 使用 preset 布局手动设置三层架构的位置
  layoutThreeLayers()
})

onUnmounted(() => {
  if (cy) {
    cy.destroy()
  }
})

const layoutThreeLayers = () => {
  if (!cy) return

  const width = graphContainer.value?.clientWidth || 800
  const height = graphContainer.value?.clientHeight || 600

  // 定义三层的 Y 坐标
  const topLayerY = height * 0.15 // 顶层（应用层）15%
  const middleLayerY = height * 0.45 // 中层（知识图谱）45%
  const bottomLayerY = height * 0.75 // 底层（数据孤岛）75%

  const leftZone = width * 0.3 // 左侧区域（蓝色 - Data management）
  const rightZone = width * 0.7 // 右侧区域（橙色 - Business Unit）

  // === 顶层：三个应用横向排列 ===
  cy.$id('app_apps').position({ x: width * 0.25, y: topLayerY })
  cy.$id('app_ai').position({ x: width * 0.5, y: topLayerY })
  cy.$id('app_bi').position({ x: width * 0.75, y: topLayerY })

  // === 中层：知识图谱网络节点 ===
  // 蓝色节点（左侧，稍微随机分布形成网络感）
  const blueNodes = [
    'kg_blue_1',
    'kg_blue_2',
    'kg_blue_3',
    'kg_blue_4',
    'kg_blue_5',
    'kg_blue_6',
    'kg_blue_7',
    'kg_blue_8',
    'kg_blue_9',
    'kg_blue_10'
  ]
  blueNodes.forEach((id, i) => {
    const row = Math.floor(i / 5)
    const col = i % 5
    cy.$id(id).position({
      x: leftZone - 80 + col * 40 + (Math.random() - 0.5) * 20,
      y: middleLayerY - 40 + row * 40 + (Math.random() - 0.5) * 20
    })
  })

  // 橙色节点（右侧，稍微随机分布）
  const orangeNodes = [
    'kg_orange_1',
    'kg_orange_2',
    'kg_orange_3',
    'kg_orange_4',
    'kg_orange_5',
    'kg_orange_6',
    'kg_orange_7',
    'kg_orange_8'
  ]
  orangeNodes.forEach((id, i) => {
    const row = Math.floor(i / 4)
    const col = i % 4
    cy.$id(id).position({
      x: rightZone - 60 + col * 40 + (Math.random() - 0.5) * 20,
      y: middleLayerY - 30 + row * 40 + (Math.random() - 0.5) * 20
    })
  })

  // === 底层：文档方块 - 4x9网格，橙色和白色交错 ===
  const gridStartX = width * 0.15 // 网格起始X坐标（更靠左以容纳9列）
  const gridStartY = bottomLayerY - 30 // 网格起始Y坐标
  const gridSpacing = 40 // 方块间距

  // 按照行列定义的顺序放置所有节点
  const docLayout = [
    // 第1行：橙 橙 白 橙 橙 白 橙 白 橙
    [
      'doc_orange_1',
      'doc_orange_2',
      'doc_white_1',
      'doc_orange_3',
      'doc_orange_4',
      'doc_white_2',
      'doc_orange_5',
      'doc_white_3',
      'doc_orange_6'
    ],
    // 第2行：橙 白 橙 橙 白 橙 白 橙 橙
    [
      'doc_orange_7',
      'doc_white_4',
      'doc_orange_8',
      'doc_orange_9',
      'doc_white_5',
      'doc_orange_10',
      'doc_white_6',
      'doc_orange_11',
      'doc_orange_12'
    ],
    // 第3行：白 橙 白 白 橙 白 橙 橙 白
    [
      'doc_white_7',
      'doc_orange_13',
      'doc_white_8',
      'doc_white_9',
      'doc_orange_14',
      'doc_white_10',
      'doc_orange_15',
      'doc_orange_16',
      'doc_white_11'
    ],
    // 第4行：橙 橙 白 橙 白 白 橙 白 橙
    [
      'doc_orange_17',
      'doc_orange_18',
      'doc_white_12',
      'doc_orange_19',
      'doc_white_13',
      'doc_white_14',
      'doc_orange_20',
      'doc_white_15',
      'doc_orange_21'
    ]
  ]

  docLayout.forEach((row, rowIdx) => {
    row.forEach((nodeId, colIdx) => {
      cy.$id(nodeId).position({
        x: gridStartX + colIdx * gridSpacing,
        y: gridStartY + rowIdx * gridSpacing
      })
    })
  })

  // 刷新视图
  cy.fit(undefined, 30)
}
</script>

<style lang="scss" scoped>
.data-fabric-ppt {
  width: 100%;
  height: 100%;
  background: #f5faff;

  .ppt-content {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    background: #f5faff;

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
      background: #f5faff;

      .left-section {
        flex: 1;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        padding: 0 20px;
        position: relative;

        .layer-descriptions {
          display: flex;
          flex-direction: column;
          justify-content: flex-start;
          height: 100%;
          position: relative;

          .layer-item {
            position: absolute;
            width: 100%;
            display: flex;
            flex-direction: column;
            align-items: flex-start;

            // 顶层 - 对齐应用层（15%位置）
            &:nth-child(1) {
              top: 5%;
            }

            // 中间层 - 对齐知识图谱层（45%位置）
            &:nth-child(2) {
              top: 35%;
            }

            // 底层 - 对齐文档层（75%位置）
            &:nth-child(3) {
              top: 65%;
            }

            .layer-title {
              font-size: 22px;
              font-weight: bold;
              margin-bottom: 12px;
              position: relative;
              text-align: center;
              width: 100%;

              &::before {
                display: none;
              }

              &.top-layer {
                color: #52c41a;
                &::before {
                  background: #52c41a;
                }
              }

              &.middle-layer {
                color: #1890ff;
                &::before {
                  background: #1890ff;
                }
              }

              &.bottom-layer {
                color: #fa8c16;
                &::before {
                  background: #fa8c16;
                }
              }
            }

            .layer-desc {
              font-size: 16px;
              line-height: 1.6;
              color: #666;
              text-align: center;
              width: 100%;
            }
          }
        }
      }

      .right-section {
        flex: 1.2;
        display: flex;
        align-items: flex-start;
        justify-content: center;
        padding-top: 0;

        .graph-container-wrapper {
          width: 100%;
          height: 90%;
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
