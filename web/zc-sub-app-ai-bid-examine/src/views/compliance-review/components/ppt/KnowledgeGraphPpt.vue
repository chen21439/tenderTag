<template>
  <div class="knowledge-graph-ppt">
    <PptSlideBase>
      <!-- 左侧内容区 -->
      <div class="left-content">
        <h1 class="title">知识图谱打通数据孤岛</h1>

        <div class="description">
          <p class="paragraph">
            系统将"采购单位、框架协议、项目、合同、供应商、履约记录以及原始文档（Word/PDF/Excel）"统一抽取并映射到知识图谱中。
          </p>

          <p class="paragraph">
            通过多层级的图谱视图，将不同单位、不同项目下的文档以层级方式呈现：同一项目内的招标文件、合同文本、验收报告等文档被自动聚集到项目节点下；同一供应商在不同单位、不同项目中的履约记录被集中到同一供应商节点下。
          </p>

          <p class="paragraph">
            在宏观视角，各个单位及其项目如同一个个"信息孤岛"；而在知识图谱视角，通过供应商、框架协议、跨项目履约记录等关键节点，这些"孤岛"被打通，形成跨文档、跨项目、跨单位的一张业务关联图。
          </p>
        </div>
      </div>

      <!-- 右侧图谱展示区 -->
      <div class="right-content">
        <div class="graph-container" ref="graphContainer"></div>
      </div>
    </PptSlideBase>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import cytoscape from 'cytoscape'
import PptSlideBase from './PptSlideBase.vue'

defineOptions({
  name: 'KnowledgeGraphPpt'
})

const graphContainer = ref<HTMLElement | null>(null)
let cy: any = null

onMounted(() => {
  if (!graphContainer.value) return

  // 定义图谱元素 - 精简版示例数据
  const elements = [
    // 1. 组织单位
    { data: { id: 'org_sz_hc', label: '某市住建局', type: 'org', layer: 0 } },

    // 2. 框架协议
    { data: { id: 'fa_led_2025', label: '2025年LED城市照明框架协议', type: 'framework', layer: 1, parent: 'org_sz_hc' } },

    // 3. 项目
    { data: { id: 'proj_road_001', label: '市主干道智慧照明项目', type: 'project', layer: 2, parent: 'fa_led_2025' } },
    { data: { id: 'proj_square_002', label: '市政广场亮化项目', type: 'project', layer: 2, parent: 'fa_led_2025' } },

    // 4. 项目1文档
    { data: { id: 'doc_p1_tender', label: 'P1-招标文件', type: 'doc', docType: 'tender', layer: 3, parent: 'proj_road_001' } },
    { data: { id: 'doc_p1_eval', label: 'P1-评标报告', type: 'doc', docType: 'evaluation', layer: 3, parent: 'proj_road_001' } },
    { data: { id: 'doc_p1_contract', label: 'P1-合同文本', type: 'doc', docType: 'contract', layer: 3, parent: 'proj_road_001' } },
    { data: { id: 'doc_p1_accept', label: 'P1-验收报告', type: 'doc', docType: 'acceptance', layer: 3, parent: 'proj_road_001' } },

    // 5. 项目2文档
    { data: { id: 'doc_p2_tender', label: 'P2-招标文件', type: 'doc', docType: 'tender', layer: 3, parent: 'proj_square_002' } },
    { data: { id: 'doc_p2_eval', label: 'P2-评标报告', type: 'doc', docType: 'evaluation', layer: 3, parent: 'proj_square_002' } },
    { data: { id: 'doc_p2_contract', label: 'P2-合同文本', type: 'doc', docType: 'contract', layer: 3, parent: 'proj_square_002' } },
    { data: { id: 'doc_p2_accept', label: 'P2-验收报告', type: 'doc', docType: 'acceptance', layer: 3, parent: 'proj_square_002' } },

    // 6. 供应商（跨项目）
    { data: { id: 'sup_star_light', label: '星辰光电', type: 'supplier', layer: 2 } },
    { data: { id: 'sup_local_led', label: '本地照明科技', type: 'supplier', layer: 2 } },

    // 7. 履约记录
    { data: { id: 'perf_p1_star', label: 'P1-星辰光电履约', type: 'performance', layer: 3, parent: 'proj_road_001' } },
    { data: { id: 'perf_p2_star', label: 'P2-星辰光电履约', type: 'performance', layer: 3, parent: 'proj_square_002' } },
    { data: { id: 'perf_p2_local', label: 'P2-本地照明履约', type: 'performance', layer: 3, parent: 'proj_square_002' } },

    // 8. 关系边 - 项目与供应商（中标关系，关键：星辰光电跨两个项目）
    { data: { source: 'proj_road_001', target: 'sup_star_light', type: 'awardedTo' } },
    { data: { source: 'proj_square_002', target: 'sup_star_light', type: 'awardedTo' } },
    { data: { source: 'proj_square_002', target: 'sup_local_led', type: 'awardedTo' } },

    // 9. 关系边 - 履约记录与供应商
    { data: { source: 'perf_p1_star', target: 'sup_star_light', type: 'performanceOf' } },
    { data: { source: 'perf_p2_star', target: 'sup_star_light', type: 'performanceOf' } },
    { data: { source: 'perf_p2_local', target: 'sup_local_led', type: 'performanceOf' } },
  ]

  // 初始化 Cytoscape
  cy = cytoscape({
    container: graphContainer.value,
    elements: elements,
    style: [
      {
        selector: 'node',
        style: {
          'label': 'data(label)',
          'text-valign': 'center',
          'text-halign': 'center',
          'text-wrap': 'wrap',
          'text-max-width': '80px',
          'font-size': '10px',
          'color': '#fff',
          'background-color': '#666',
          'border-width': 2,
          'border-color': '#333',
        }
      },
      {
        selector: 'node[type="org"]',
        style: {
          'background-color': '#1890ff',
          'border-color': '#096dd9',
          'width': 120,
          'height': 120,
          'font-size': '16px',
          'font-weight': 'bold',
          'shape': 'roundrectangle',
        }
      },
      {
        selector: 'node[type="framework"]',
        style: {
          'background-color': '#52c41a',
          'border-color': '#389e0d',
          'width': 100,
          'height': 100,
          'font-size': '11px',
          'shape': 'roundrectangle',
        }
      },
      {
        selector: 'node[type="project"]',
        style: {
          'background-color': '#722ed1',
          'border-color': '#531dab',
          'width': 90,
          'height': 90,
          'font-size': '12px',
          'shape': 'ellipse',
        }
      },
      {
        selector: 'node[type="doc"]',
        style: {
          'background-color': '#fa8c16',
          'border-color': '#d46b08',
          'width': 40,
          'height': 40,
          'font-size': '9px',
          'shape': 'rectangle',
        }
      },
      {
        selector: 'node[type="supplier"]',
        style: {
          'background-color': '#eb2f96',
          'border-color': '#c41d7f',
          'width': 90,
          'height': 90,
          'font-size': '13px',
          'font-weight': 'bold',
          'shape': 'diamond',
        }
      },
      {
        selector: 'node[type="performance"]',
        style: {
          'background-color': '#13c2c2',
          'border-color': '#08979c',
          'width': 35,
          'height': 35,
          'font-size': '8px',
          'shape': 'triangle',
        }
      },
      {
        selector: 'edge',
        style: {
          'width': 2,
          'line-color': '#d9d9d9',
          'target-arrow-color': '#d9d9d9',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          'arrow-scale': 1.2,
        }
      },
      {
        selector: 'edge[type="awardedTo"]',
        style: {
          'line-color': '#eb2f96',
          'target-arrow-color': '#eb2f96',
          'width': 4,
          'line-style': 'solid',
        }
      },
      {
        selector: 'edge[type="performanceOf"]',
        style: {
          'line-color': '#13c2c2',
          'target-arrow-color': '#13c2c2',
          'width': 2,
          'line-style': 'dashed',
        }
      },
      {
        selector: ':parent',
        style: {
          'background-opacity': 0.1,
          'border-width': 3,
          'border-style': 'dashed',
          'border-opacity': 0.5,
          'padding': 15,
        }
      },
    ],
    layout: {
      name: 'preset',
      positions: function(node: any) {
        const id = node.id()
        const type = node.data('type')

        // 手动布局以展示层级和"打通孤岛"效果
        const positions: any = {
          // 组织单位（最左）
          'org_sz_hc': { x: 150, y: 250 },

          // 框架协议
          'fa_led_2025': { x: 300, y: 250 },

          // 项目
          'proj_road_001': { x: 450, y: 150 },
          'proj_square_002': { x: 450, y: 350 },

          // 项目1文档
          'doc_p1_tender': { x: 600, y: 80 },
          'doc_p1_eval': { x: 650, y: 120 },
          'doc_p1_contract': { x: 600, y: 160 },
          'doc_p1_accept': { x: 650, y: 200 },

          // 项目2文档
          'doc_p2_tender': { x: 600, y: 280 },
          'doc_p2_eval': { x: 650, y: 320 },
          'doc_p2_contract': { x: 600, y: 360 },
          'doc_p2_accept': { x: 650, y: 400 },

          // 供应商（右侧，跨项目位置）
          'sup_star_light': { x: 800, y: 250 },
          'sup_local_led': { x: 800, y: 380 },

          // 履约记录
          'perf_p1_star': { x: 520, y: 100 },
          'perf_p2_star': { x: 520, y: 300 },
          'perf_p2_local': { x: 520, y: 400 },
        }

        return positions[id] || { x: 0, y: 0 }
      },
      fit: true,
      padding: 50,
    }
  })

  // 适应视图
  setTimeout(() => {
    cy.fit(null, 40)
  }, 100)
})

onUnmounted(() => {
  if (cy) {
    cy.destroy()
  }
})
</script>

<style lang="scss" scoped>
.knowledge-graph-ppt {
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
    background: #f5f5f5;

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

    .description {
      .paragraph {
        font-size: 16px;
        line-height: 1.8;
        color: #333;
        margin-bottom: 20px;
        text-align: justify;

        &:last-child {
          margin-bottom: 0;
        }
      }
    }
  }

  .right-content {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 40px;
    background: #fff;

    .graph-container {
      width: 100%;
      height: 100%;
      border-radius: 8px;
      border: 1px solid #e8e8e8;
      background: #fafafa;
    }
  }
}
</style>
