<template>
  <div class="full-graph-ppt">
    <PptSlideBase>
      <div class="graph-full-container" ref="graphContainer"></div>
    </PptSlideBase>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import cytoscape from 'cytoscape'
import PptSlideBase from './PptSlideBase.vue'

defineOptions({
  name: 'FullGraphPpt'
})

const graphContainer = ref<HTMLElement | null>(null)
let cy: any = null

onMounted(() => {
  if (!graphContainer.value) return

  // 相同的数据结构
  const elements = [
    { data: { id: 'org_sz_hc', label: '某市住建局', type: 'org', layer: 0 } },
    { data: { id: 'fa_led_2025', label: '2025年LED城市照明框架协议', type: 'framework', layer: 1, parent: 'org_sz_hc' } },
    { data: { id: 'proj_road_001', label: '市主干道智慧照明项目', type: 'project', layer: 2, parent: 'fa_led_2025' } },
    { data: { id: 'proj_square_002', label: '市政广场亮化项目', type: 'project', layer: 2, parent: 'fa_led_2025' } },
    { data: { id: 'doc_p1_tender', label: 'P1-招标文件', type: 'doc', docType: 'tender', layer: 3, parent: 'proj_road_001' } },
    { data: { id: 'doc_p1_eval', label: 'P1-评标报告', type: 'doc', docType: 'evaluation', layer: 3, parent: 'proj_road_001' } },
    { data: { id: 'doc_p1_contract', label: 'P1-合同文本', type: 'doc', docType: 'contract', layer: 3, parent: 'proj_road_001' } },
    { data: { id: 'doc_p1_accept', label: 'P1-验收报告', type: 'doc', docType: 'acceptance', layer: 3, parent: 'proj_road_001' } },
    { data: { id: 'doc_p2_tender', label: 'P2-招标文件', type: 'doc', docType: 'tender', layer: 3, parent: 'proj_square_002' } },
    { data: { id: 'doc_p2_eval', label: 'P2-评标报告', type: 'doc', docType: 'evaluation', layer: 3, parent: 'proj_square_002' } },
    { data: { id: 'doc_p2_contract', label: 'P2-合同文本', type: 'doc', docType: 'contract', layer: 3, parent: 'proj_square_002' } },
    { data: { id: 'doc_p2_accept', label: 'P2-验收报告', type: 'doc', docType: 'acceptance', layer: 3, parent: 'proj_square_002' } },
    { data: { id: 'sup_star_light', label: '星辰光电', type: 'supplier', layer: 2 } },
    { data: { id: 'sup_local_led', label: '本地照明科技', type: 'supplier', layer: 2 } },
    { data: { id: 'perf_p1_star', label: 'P1-星辰光电履约', type: 'performance', layer: 3, parent: 'proj_road_001' } },
    { data: { id: 'perf_p2_star', label: 'P2-星辰光电履约', type: 'performance', layer: 3, parent: 'proj_square_002' } },
    { data: { id: 'perf_p2_local', label: 'P2-本地照明履约', type: 'performance', layer: 3, parent: 'proj_square_002' } },
    { data: { source: 'proj_road_001', target: 'sup_star_light', type: 'awardedTo' } },
    { data: { source: 'proj_square_002', target: 'sup_star_light', type: 'awardedTo' } },
    { data: { source: 'proj_square_002', target: 'sup_local_led', type: 'awardedTo' } },
    { data: { source: 'perf_p1_star', target: 'sup_star_light', type: 'performanceOf' } },
    { data: { source: 'perf_p2_star', target: 'sup_star_light', type: 'performanceOf' } },
    { data: { source: 'perf_p2_local', target: 'sup_local_led', type: 'performanceOf' } },
  ]

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
          'text-max-width': '100px',
          'font-size': '12px',
          'color': '#fff',
          'background-color': '#666',
          'border-width': 3,
          'border-color': '#333',
        }
      },
      {
        selector: 'node[type="org"]',
        style: {
          'background-color': '#1890ff',
          'border-color': '#096dd9',
          'width': 140,
          'height': 140,
          'font-size': '18px',
          'font-weight': 'bold',
          'shape': 'roundrectangle',
        }
      },
      {
        selector: 'node[type="framework"]',
        style: {
          'background-color': '#52c41a',
          'border-color': '#389e0d',
          'width': 120,
          'height': 120,
          'font-size': '13px',
          'shape': 'roundrectangle',
        }
      },
      {
        selector: 'node[type="project"]',
        style: {
          'background-color': '#722ed1',
          'border-color': '#531dab',
          'width': 110,
          'height': 110,
          'font-size': '14px',
          'shape': 'ellipse',
        }
      },
      {
        selector: 'node[type="doc"]',
        style: {
          'background-color': '#fa8c16',
          'border-color': '#d46b08',
          'width': 50,
          'height': 50,
          'font-size': '10px',
          'shape': 'rectangle',
        }
      },
      {
        selector: 'node[type="supplier"]',
        style: {
          'background-color': '#eb2f96',
          'border-color': '#c41d7f',
          'width': 110,
          'height': 110,
          'font-size': '15px',
          'font-weight': 'bold',
          'shape': 'diamond',
        }
      },
      {
        selector: 'node[type="performance"]',
        style: {
          'background-color': '#13c2c2',
          'border-color': '#08979c',
          'width': 45,
          'height': 45,
          'font-size': '9px',
          'shape': 'triangle',
        }
      },
      {
        selector: 'edge',
        style: {
          'width': 3,
          'line-color': '#d9d9d9',
          'target-arrow-color': '#d9d9d9',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          'arrow-scale': 1.5,
        }
      },
      {
        selector: 'edge[type="awardedTo"]',
        style: {
          'line-color': '#eb2f96',
          'target-arrow-color': '#eb2f96',
          'width': 5,
          'line-style': 'solid',
        }
      },
      {
        selector: 'edge[type="performanceOf"]',
        style: {
          'line-color': '#13c2c2',
          'target-arrow-color': '#13c2c2',
          'width': 3,
          'line-style': 'dashed',
        }
      },
      {
        selector: ':parent',
        style: {
          'background-opacity': 0.08,
          'border-width': 4,
          'border-style': 'dashed',
          'border-opacity': 0.4,
          'padding': 20,
        }
      },
    ],
    layout: {
      name: 'preset',
      positions: function(node: any) {
        const id = node.id()
        const positions: any = {
          'org_sz_hc': { x: 200, y: 350 },
          'fa_led_2025': { x: 400, y: 350 },
          'proj_road_001': { x: 600, y: 200 },
          'proj_square_002': { x: 600, y: 500 },
          'doc_p1_tender': { x: 800, y: 100 },
          'doc_p1_eval': { x: 880, y: 150 },
          'doc_p1_contract': { x: 800, y: 200 },
          'doc_p1_accept': { x: 880, y: 250 },
          'doc_p2_tender': { x: 800, y: 400 },
          'doc_p2_eval': { x: 880, y: 450 },
          'doc_p2_contract': { x: 800, y: 500 },
          'doc_p2_accept': { x: 880, y: 550 },
          'sup_star_light': { x: 1100, y: 350 },
          'sup_local_led': { x: 1100, y: 530 },
          'perf_p1_star': { x: 700, y: 130 },
          'perf_p2_star': { x: 700, y: 430 },
          'perf_p2_local': { x: 700, y: 560 },
        }
        return positions[id] || { x: 0, y: 0 }
      },
      fit: true,
      padding: 60,
    }
  })

  setTimeout(() => {
    cy.fit(null, 50)
  }, 100)
})

onUnmounted(() => {
  if (cy) {
    cy.destroy()
  }
})
</script>

<style lang="scss" scoped>
.full-graph-ppt {
  width: 100%;
  height: 100%;
  background: #fff;

  .graph-full-container {
    width: 100%;
    height: 100%;
    background: #fafafa;
  }
}
</style>
