<template>
  <div class="editable-tree-container">
    <!-- 工具栏 -->
    <div v-if="showToolbar" class="tree-toolbar">
      <div class="toolbar-left">
        <a-button
          v-if="editable"
          size="small"
          :type="editMode ? 'primary' : 'default'"
          @click="toggleEditMode"
        >
          {{ editMode ? '退出编辑' : '编辑模式' }}
        </a-button>
        <a-button size="small" @click="expandAll">全部展开</a-button>
        <a-button size="small" @click="collapseAll">全部折叠</a-button>
        <a-checkbox-group v-model="highlightRelations" style="margin-left: 12px;">
          <a-checkbox value="equality">Equality</a-checkbox>
          <a-checkbox value="contain">Contain</a-checkbox>
          <a-checkbox value="connect">Connect</a-checkbox>
        </a-checkbox-group>
      </div>
      <div class="toolbar-right">
        <span v-if="editMode && selectedNodeIds.length > 0" class="selection-info">
          已选中 {{ selectedNodeIds.length }} 个节点
        </span>
        <span class="node-count">共 {{ totalNodeCount }} 个节点</span>
      </div>
    </div>

    <!-- 树形结构 -->
    <div
      class="tree-content"
      :class="{ 'edit-mode': editMode }"
    >
      <div v-if="loading" class="tree-loading">
        <a-spin tip="加载中..." />
      </div>
      <div v-else-if="treeData.length === 0" class="tree-empty">
        <a-empty description="暂无数据" />
      </div>
      <div
        v-else
        class="tree-list"
        @dragover.prevent="handleGlobalDragOver"
        @drop="handleGlobalDrop"
      >
        <TreeNode
          v-for="node in treeData"
          :key="node.line_id || node.id"
          :node="node"
          :depth="0"
          :expanded-nodes="expandedNodes"
          :selected-ids="selectedNodeIds"
          :highlighted-nodes="new Set()"
          :node-map="nodeMap"
          :debug-mode="debugMode"
          :edit-mode="editMode"
          @toggle="handleToggle"
          @select="handleSelect"
          @paragraphClick="handleParagraphClick"
          @node-drop="handleNodeDrop"
          @drag-start-node="handleDragStartNode"
          @drag-over-node="handleDragOverNode"
          @drag-end="handleDragEnd"
          @update-label="handleUpdateLabel"
          @update-relation="handleUpdateRelation"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import TreeNode from '../../views/compliance-review/components/TreeNode.vue'
import { useTreeBuilder, TreeBuildStrategy } from '../../hooks/useTreeBuilder'
import { useTreeEditor } from '../../hooks/useTreeEditor'

const props = defineProps({
  // 原始数据
  rawData: {
    type: Array,
    default: () => []
  },
  // 构建策略
  buildStrategy: {
    type: String as () => TreeBuildStrategy,
    default: 'parentId'
  },
  // 构建选项
  buildOptions: {
    type: Object,
    default: () => ({})
  },
  // 是否可编辑
  editable: {
    type: Boolean,
    default: false
  },
  // 是否显示工具栏
  showToolbar: {
    type: Boolean,
    default: true
  },
  // 调试模式
  debugMode: {
    type: Boolean,
    default: false
  },
  // 加载状态
  loading: {
    type: Boolean,
    default: false
  },
  // 节点映射表
  nodeMap: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits([
  'node-move',
  'label-update',
  'relation-update',
  'node-delete',
  'node-select',
  'paragraph-click',
  'tree-built'
])

// 树数据
const treeData = ref<any[]>([])

// 树构建器（支持两个版本）
import { useTreeBuilderV2 } from '@/hooks/useTreeBuilderV2'
const { buildTree: buildTreeV1 } = useTreeBuilder()
const { buildTree: buildTreeV2 } = useTreeBuilderV2()

// 使用 V2 版本（参考 Python tree_utils.py 的实现）
const buildTree = buildTreeV2

// 树编辑器
const {
  editMode,
  selectedNodeIds,
  expandedNodes,
  moveNode,
  updateLabel,
  deleteNode,
  toggleNodeSelection,
  clearSelection,
  toggleEditMode: toggleEdit,
  toggleNode,
  expandAll: expandAllNodes,
  collapseAll: collapseAllNodes
} = useTreeEditor(treeData, {
  onNodeMove: async (nodeId, newParentId) => {
    emit('node-move', { nodeId, newParentId })
  },
  onLabelUpdate: async (nodeId, newLabel) => {
    emit('label-update', { nodeId, newLabel })
  },
  onNodeDelete: async (nodeId) => {
    emit('node-delete', { nodeId })
  }
})

// 构建树数据（函数需要在 watch 之前定义）
const buildTreeData = () => {
  if (!props.rawData || props.rawData.length === 0) {
    treeData.value = []
    return
  }

  treeData.value = buildTree(
    props.rawData as any[],
    props.buildStrategy,
    props.buildOptions
  )

  emit('tree-built', treeData.value)
}

// 监听原始数据变化，重新构建树
watch(
  () => props.rawData,
  (newData) => {
    if (newData && newData.length > 0) {
      console.log('🔄 原始数据变化，重新构建树')
      buildTreeData()
    }
  },
  { immediate: true, deep: true }
)

// 计算总节点数
const totalNodeCount = computed(() => {
  const countNodes = (nodes: any[]): number => {
    let count = nodes.length
    nodes.forEach(node => {
      if (node.children && node.children.length > 0) {
        count += countNodes(node.children)
      }
    })
    return count
  }
  return countNodes(treeData.value)
})

// 已移除高亮关系节点功能

// 在树中查找节点
const findNodeInTree = (nodes: any[], targetId: any): any => {
  for (const node of nodes) {
    const nodeId = node.id || node.line_id
    if (String(nodeId) === String(targetId)) {
      return node
    }
    if (node.children && node.children.length > 0) {
      const found = findNodeInTree(node.children, targetId)
      if (found) return found
    }
  }
  return null
}

// 事件处理
const handleToggle = (nodeId: any) => {
  toggleNode(nodeId)
}

const handleSelect = (nodeId: any) => {
  emit('node-select', nodeId)
}

const handleParagraphClick = (paragraphIds: any[]) => {
  emit('paragraph-click', paragraphIds)
}

const handleNodeDrop = (data: any) => {
  const { draggedNodeId, targetNodeId, nodeId, targetId } = data
  // 兼容新旧参数名称
  const sourceId = draggedNodeId || nodeId
  const destId = targetNodeId || targetId
  console.log('📦 EditableTree收到drop事件:', { sourceId, destId })
  moveNode(sourceId, destId)
}

// 记录拖拽状态
let draggedNodeId: any = null
let lastDragOverNodeId: any = null

const handleDragStartNode = (nodeId: any) => {
  draggedNodeId = nodeId
  console.log('🖱️ 开始拖拽节点:', nodeId)
}

const handleDragOverNode = (nodeId: any) => {
  lastDragOverNodeId = nodeId
  // console.log('🖱️ 拖拽经过节点:', nodeId)
}

const handleDragEnd = () => {
  console.log('🖱️ 拖拽结束', {
    draggedNodeId,
    lastDragOverNodeId,
    editMode: editMode.value
  })

  // 如果 drop 事件没有触发，但我们有记录的目标节点，就在这里执行移动
  if (editMode.value && draggedNodeId && lastDragOverNodeId && draggedNodeId !== lastDragOverNodeId) {
    console.log('✅ dragEnd 中执行节点移动（drop 未触发）:', { draggedNodeId, lastDragOverNodeId })
    moveNode(draggedNodeId, lastDragOverNodeId)
  }

  // 重置状态
  draggedNodeId = null
  lastDragOverNodeId = null
}

// 全局 dragOver 处理（允许拖放）
const handleGlobalDragOver = (event: DragEvent) => {
  console.log('🌐 EditableTree 全局 dragOver 触发')
  // 什么都不做，只是为了 prevent default
}

// 全局 drop 处理（使用最后记录的目标节点）
const handleGlobalDrop = (event: DragEvent) => {
  console.log('🎯 EditableTree 全局 drop 触发', {
    draggedNodeId,
    lastDragOverNodeId,
    editMode: editMode.value
  })

  if (!editMode.value) {
    console.log('⚠️ 非编辑模式，忽略 drop')
    return
  }

  if (!lastDragOverNodeId) {
    console.log('⚠️ 没有记录到目标节点')
    return
  }

  if (draggedNodeId && lastDragOverNodeId && draggedNodeId !== lastDragOverNodeId) {
    console.log('✅ 执行节点移动:', { draggedNodeId, lastDragOverNodeId })
    moveNode(draggedNodeId, lastDragOverNodeId)
  } else {
    console.log('⚠️ 无效的拖拽操作')
  }

  // 重置状态
  draggedNodeId = null
  lastDragOverNodeId = null
}

const handleUpdateLabel = (data: any) => {
  const { nodeId, newLabel } = data
  updateLabel(nodeId, newLabel)
}

const handleUpdateRelation = (data: any) => {
  const { nodeId, class: nodeClass, relation, parent_id } = data
  console.log('🔗 更新节点关系:', { nodeId, class: nodeClass, relation, parent_id })
  emit('relation-update', { nodeId, class: nodeClass, relation, parent_id })
}

const toggleEditMode = () => {
  toggleEdit()
}

const expandAll = () => {
  expandAllNodes()
}

const collapseAll = () => {
  collapseAllNodes()
}

// 导出方法供父组件使用
defineExpose({
  treeData,
  editMode,
  selectedNodeIds,
  expandedNodes,
  moveNode,
  updateLabel,
  deleteNode,
  buildTreeData,
  expandAll,
  collapseAll
})
</script>

<style scoped lang="scss">
.editable-tree-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
}

.tree-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e8e8e8;
  background: #fafafa;

  .toolbar-left {
    display: flex;
    gap: 8px;
  }

  .toolbar-right {
    display: flex;
    align-items: center;
    gap: 16px;
    color: #666;
    font-size: 12px;

    .selection-info {
      color: #1890ff;
      font-weight: 500;
    }

    .node-count {
      color: #999;
    }
  }
}

.tree-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;

  &.edit-mode {
    background: #f5f5f5;
  }
}

.tree-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

.tree-empty {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

.tree-list {
  width: 100%;
}
</style>
