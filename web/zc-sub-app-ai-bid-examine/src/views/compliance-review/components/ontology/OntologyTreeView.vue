<template>
  <div class="ontology-tree-view">
    <TreeNode
      v-for="node in treeData"
      :key="node.line_id"
      :node="node"
      :depth="0"
      :expanded-nodes="expandedNodes"
      :selected-id="selectedId"
      :node-map="nodeMap"
      :debug-mode="debugMode"
      @toggle="handleToggle"
      @select="handleSelect"
      @paragraphClick="handleParagraphClick"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import TreeNode from '../TreeNode.vue'
import { useOntologyTree } from './useOntologyTree'

const props = defineProps({
  rawTreeData: {
    type: Array,
    required: true
  },
  selectedId: {
    type: Number,
    default: null
  },
  nodeMap: {
    type: Object,
    default: () => ({})
  },
  debugMode: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['select', 'paragraphClick', 'update:treeData'])

const { buildOntologyTree, expandMoreNode } = useOntologyTree()

// 展开的节点集合
const expandedNodes = ref(new Set<number>())

// 构建后的树数据
const treeData = ref<any[]>([])

// 监听原始数据变化，重新构建树
watch(
  () => props.rawTreeData,
  (newData) => {
    if (newData && newData.length > 0) {
      treeData.value = buildOntologyTree(newData as any[])
      emit('update:treeData', treeData.value)
    }
  },
  { immediate: true, deep: true }
)

// 处理节点展开/折叠
const handleToggle = (lineId: number) => {
  const node = findNodeById(treeData.value, lineId)

  // 如果是"查看更多"指示器
  if (node && node.class === 'more-indicator') {
    const expanded = expandMoreNode(node)
    if (expanded) {
      // 强制更新树
      treeData.value = [...treeData.value]
      emit('update:treeData', treeData.value)
    }
    return
  }

  // 普通节点展开/折叠
  if (expandedNodes.value.has(lineId)) {
    expandedNodes.value.delete(lineId)
  } else {
    expandedNodes.value.add(lineId)
  }
  // 触发响应式更新
  expandedNodes.value = new Set(expandedNodes.value)
}

// 处理节点选择
const handleSelect = (lineId: number) => {
  emit('select', lineId)
}

// 处理段落点击
const handleParagraphClick = (paragraphIds: number[]) => {
  emit('paragraphClick', paragraphIds)
}

// 查找节点
const findNodeById = (nodes: any[], id: number): any => {
  for (const node of nodes) {
    if (node.line_id === id) return node
    if (node.children && node.children.length > 0) {
      const found = findNodeById(node.children, id)
      if (found) return found
    }
  }
  return null
}

// 导出数据供父组件使用
defineExpose({
  treeData,
  expandedNodes
})
</script>

<style scoped lang="scss">
.ontology-tree-view {
  width: 100%;
  height: 100%;
  overflow-y: auto;
  padding: 8px;
}
</style>
