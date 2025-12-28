<template>
  <div class="tree-node">
    <div
      class="node-header"
      :class="{
        'selected': selectedId === node.line_id,
        [`depth-${Math.min(depth, 6)}`]: true,
        [`class-${node.class}`]: true,
        'is-meta': node.is_meta
      }"
      @click="handleSelect"
    >
      <!-- 展开/折叠图标 -->
      <span
        v-if="hasChildren"
        class="toggle-icon"
        @click.stop="handleToggle"
      >
        {{ isExpanded ? '▼' : '▶' }}
      </span>
      <span v-else class="toggle-icon placeholder"></span>

      <!-- 节点类型图标 -->
      <span class="node-icon">{{ getNodeIcon(node.class) }}</span>

      <!-- 节点标签 -->
      <span class="node-label">
        <span class="node-class">{{ node.class }}</span>
        <span v-if="node.text" class="node-text">{{ truncateText(node.text) }}</span>
        <span v-else class="node-id">#{{ node.line_id }}</span>
      </span>

      <!-- 关系类型标记 -->
      <span class="relation-badge" :class="node.relation">
        {{ getRelationLabel(node.relation) }}
      </span>

      <!-- 页码标记 -->
      <span v-if="node.page !== undefined" class="page-badge">
        P{{ node.page + 1 }}
      </span>
    </div>

    <!-- 子节点 -->
    <div v-if="hasChildren && isExpanded" class="children">
      <TreeNode
        v-for="child in node.children"
        :key="child.line_id"
        :node="child"
        :depth="depth + 1"
        :expanded-nodes="expandedNodes"
        :selected-id="selectedId"
        @toggle="$emit('toggle', $event)"
        @select="$emit('select', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  node: {
    type: Object,
    required: true
  },
  depth: {
    type: Number,
    default: 0
  },
  expandedNodes: {
    type: Set,
    required: true
  },
  selectedId: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['toggle', 'select'])

// 是否有子节点
const hasChildren = computed(() => {
  return props.node.children && props.node.children.length > 0
})

// 是否展开
const isExpanded = computed(() => {
  return props.expandedNodes.has(props.node.line_id)
})

// 处理展开/折叠
const handleToggle = () => {
  emit('toggle', props.node.line_id)
}

// 处理选择
const handleSelect = () => {
  emit('select', props.node.line_id)
}

// 获取节点图标
const getNodeIcon = (nodeClass) => {
  const iconMap = {
    title: '📄',
    author: '👤',
    affili: '🏛️',
    mail: '✉️',
    sec1: '📌',
    sec2: '📍',
    sec3: '📎',
    para: '¶',
    fstline: '▸',
    default: '•'
  }
  return iconMap[nodeClass] || iconMap.default
}

// 获取关系类型标签
const getRelationLabel = (relation) => {
  const labelMap = {
    contain: '包含',
    equality: '并列',
    connect: '连接',
    meta: '元信息'
  }
  return labelMap[relation] || relation
}

// 截断文本
const truncateText = (text, maxLength = 60) => {
  if (!text) return ''
  text = text.trim().replace(/\s+/g, ' ')
  return text.length > maxLength
    ? text.substring(0, maxLength) + '...'
    : text
}
</script>

<style scoped>
.tree-node {
  user-select: none;
}

.node-header {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  margin: 2px 0;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  gap: 8px;
  border-left: 3px solid transparent;
}

.node-header:hover {
  background: #f5f5f5;
}

.node-header.selected {
  background: #e3f2fd;
  border-left-color: #1976d2;
}

.node-header.is-meta {
  background: #fafafa;
}

.node-header.is-meta.selected {
  background: #f3e5f5;
  border-left-color: #7b1fa2;
}

/* 深度缩进 */
.depth-0 { margin-left: 0; }
.depth-1 { margin-left: 20px; }
.depth-2 { margin-left: 40px; }
.depth-3 { margin-left: 60px; }
.depth-4 { margin-left: 80px; }
.depth-5 { margin-left: 100px; }
.depth-6 { margin-left: 120px; }

/* 根据class类型设置样式 */
.node-header.class-title .node-class { color: #1976d2; font-weight: 700; }
.node-header.class-author .node-class { color: #7b1fa2; font-weight: 600; }
.node-header.class-affili .node-class { color: #c2185b; }
.node-header.class-mail .node-class { color: #e65100; }
.node-header.class-sec1 .node-class { color: #c62828; font-weight: 700; font-size: 13px; }
.node-header.class-sec2 .node-class { color: #2e7d32; font-weight: 600; font-size: 12px; }
.node-header.class-sec3 .node-class { color: #00695c; font-weight: 500; font-size: 12px; }

.toggle-icon {
  width: 16px;
  font-size: 10px;
  color: #757575;
  flex-shrink: 0;
  text-align: center;
}

.toggle-icon.placeholder {
  visibility: hidden;
}

.node-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.node-label {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.node-class {
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
  flex-shrink: 0;
  letter-spacing: 0.5px;
}

.node-text {
  color: #333;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.4;
}

.node-id {
  color: #999;
  font-size: 11px;
  font-family: 'Courier New', monospace;
}

.relation-badge {
  font-size: 9px;
  padding: 2px 6px;
  border-radius: 8px;
  background: #e0e0e0;
  color: #616161;
  flex-shrink: 0;
  font-weight: 500;
}

.relation-badge.contain {
  background: #c8e6c9;
  color: #2e7d32;
}

.relation-badge.equality {
  background: #fff9c4;
  color: #f57f17;
}

.relation-badge.connect {
  background: #b3e5fc;
  color: #01579b;
}

.relation-badge.meta {
  background: #f3e5f5;
  color: #6a1b9a;
}

.page-badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 8px;
  background: #e0e0e0;
  color: #424242;
  flex-shrink: 0;
  font-family: 'Courier New', monospace;
  font-weight: 500;
}

.children {
  position: relative;
}

.children::before {
  content: '';
  position: absolute;
  left: 8px;
  top: 0;
  bottom: 0;
  width: 1px;
  background: #e0e0e0;
}
</style>
