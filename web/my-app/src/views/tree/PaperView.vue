<template>
  <div class="bbox-view">
    <div class="page-selector">
      <button
        v-for="pageNum in totalPages"
        :key="pageNum"
        @click="currentPage = pageNum - 1"
        :class="{ active: currentPage === pageNum - 1 }"
        class="page-btn"
      >
        第 {{ pageNum }} 页
      </button>
    </div>

    <div class="canvas-container">
      <div class="page-canvas" ref="canvasRef">
        <!-- 页面背景 -->
        <div
          class="page-background"
          :style="{
            width: pageWidth + 'px',
            height: pageHeight + 'px'
          }"
        >
          <!-- 渲染当前页的所有bbox -->
          <div
            v-for="node in currentPageNodes"
            :key="node.line_id"
            class="bbox-element"
            :class="[
              node.class,
              {
                selected: selectedId === node.line_id,
                'is-meta': node.is_meta
              }
            ]"
            :style="getBboxStyle(node)"
            @click="$emit('select', node.line_id)"
          >
            <div class="bbox-label">
              <span class="label-class">{{ node.class }}</span>
              <span class="label-id">#{{ node.line_id }}</span>
            </div>
            <div class="bbox-text">{{ node.text }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  nodes: {
    type: Array,
    required: true
  },
  selectedId: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['select'])

const currentPage = ref(0)
const zoom = ref(1)
const canvasRef = ref(null)

// 计算总页数
const totalPages = computed(() => {
  if (!props.nodes.length) return 0
  return Math.max(...props.nodes.map(n => n.page || 0)) + 1
})

// 计算页面尺寸（基于bbox的最大值）
const pageWidth = computed(() => {
  const nodesOnPage = props.nodes.filter(n => (n.page || 0) === currentPage.value)
  if (!nodesOnPage.length) return 595 // A4 width in points
  const maxX = Math.max(...nodesOnPage.map(n => n.box ? n.box[2] : 0))
  return Math.max(maxX + 50, 595)
})

const pageHeight = computed(() => {
  const nodesOnPage = props.nodes.filter(n => (n.page || 0) === currentPage.value)
  if (!nodesOnPage.length) return 842 // A4 height in points
  const maxY = Math.max(...nodesOnPage.map(n => n.box ? n.box[3] : 0))
  return Math.max(maxY + 50, 842)
})

// 当前页的所有节点
const currentPageNodes = computed(() => {
  return props.nodes.filter(n => (n.page || 0) === currentPage.value && n.box)
})

// 所有节点类型
const nodeTypes = computed(() => {
  const types = new Set(props.nodes.map(n => n.class).filter(Boolean))
  return Array.from(types).sort()
})

// 获取bbox样式
const getBboxStyle = (node) => {
  if (!node.box) return {}

  const [x1, y1, x2, y2] = node.box
  const width = x2 - x1
  const height = y2 - y1

  return {
    left: x1 + 'px',
    top: y1 + 'px',
    width: width + 'px',
    height: height + 'px',
    transform: `scale(${zoom.value})`,
    transformOrigin: 'top left'
  }
}

// 缩放控制
const zoomIn = () => {
  zoom.value = Math.min(zoom.value + 0.1, 3)
}

const zoomOut = () => {
  zoom.value = Math.max(zoom.value - 0.1, 0.3)
}

const resetZoom = () => {
  zoom.value = 1
}

// 监听选中节点，自动切换到对应页面
watch(() => props.selectedId, (newId) => {
  if (newId !== null && newId !== undefined) {
    const node = props.nodes.find(n => n.line_id === newId)
    if (node && node.page !== undefined) {
      currentPage.value = node.page
    }
  }
})
</script>

<style scoped>
.bbox-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

.page-selector {
  padding: 15px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  gap: 8px;
  overflow-x: auto;
}

.page-btn {
  padding: 8px 16px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
  white-space: nowrap;
}

.page-btn:hover {
  background: #f5f5f5;
  border-color: #1976d2;
}

.page-btn.active {
  background: #1976d2;
  color: white;
  border-color: #1976d2;
}

.canvas-container {
  flex: 1;
  overflow: hidden;
}

.page-canvas {
  width: 100%;
  height: 100%;
  overflow: auto;
  padding: 30px;
  background: #e0e0e0;
}

.page-background {
  background: white;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  position: relative;
  margin: 0 auto;
}

.bbox-element {
  position: absolute;
  border: 2px solid;
  cursor: pointer;
  transition: all 0.2s;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.bbox-element:hover {
  z-index: 10;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  transform: scale(1.02) !important;
}

.bbox-element.selected {
  z-index: 20;
  box-shadow: 0 4px 16px rgba(25, 118, 210, 0.4);
  border-width: 3px;
}

/* 不同类型的颜色 */
.bbox-element.title {
  border-color: #1976d2;
  background: rgba(25, 118, 210, 0.05);
}
.bbox-element.author {
  border-color: #7b1fa2;
  background: rgba(123, 31, 162, 0.05);
}
.bbox-element.affili {
  border-color: #c2185b;
  background: rgba(194, 24, 91, 0.05);
}
.bbox-element.mail {
  border-color: #e65100;
  background: rgba(230, 81, 0, 0.05);
}
.bbox-element.sec1 {
  border-color: #c62828;
  background: rgba(198, 40, 40, 0.05);
}
.bbox-element.sec2 {
  border-color: #2e7d32;
  background: rgba(46, 125, 50, 0.05);
}
.bbox-element.sec3 {
  border-color: #00695c;
  background: rgba(0, 105, 92, 0.05);
}
.bbox-element.para {
  border-color: #757575;
  background: rgba(117, 117, 117, 0.03);
}
.bbox-element.fstline {
  border-color: #9e9e9e;
  background: rgba(158, 158, 158, 0.03);
}

.bbox-element.is-meta {
  border-style: dashed;
}

.bbox-label {
  background: rgba(0,0,0,0.7);
  color: white;
  padding: 2px 6px;
  font-size: 10px;
  display: flex;
  gap: 4px;
  align-items: center;
  flex-shrink: 0;
}

.label-class {
  font-weight: bold;
  text-transform: uppercase;
}

.label-id {
  opacity: 0.7;
  font-family: monospace;
}

.bbox-text {
  padding: 4px 6px;
  font-size: 11px;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #333;
}

</style>
