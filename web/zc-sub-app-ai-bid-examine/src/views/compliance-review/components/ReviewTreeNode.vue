<template>
  <div class="review-tree-node">
    <div
      class="node-header"
      :class="{
        'selected': selectedId === nodeId,
        [`depth-${Math.min(depth, 6)}`]: true,
        'has-risk': node.reviewResult === 1
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

      <!-- 风险状态图标 -->
      <span class="risk-icon" v-if="node.reviewResult === 1">⚠️</span>
      <span class="safe-icon" v-else-if="node.reviewResult === 0">✓</span>
      <span class="normal-icon" v-else>•</span>

      <!-- 节点标签 -->
      <span class="node-label">
        <span class="node-name">{{ node.reviewItemName || node.sceneDesc }}</span>
        <span v-if="node.children && node.children.length" class="child-count">
          ({{ node.children.length }})
        </span>
      </span>

      <!-- 状态标记 -->
      <span v-if="node.handleStatus === 1" class="status-badge handled">已处理</span>
      <span v-if="node.acceptStatus === 1" class="status-badge accepted">已采纳</span>
    </div>

    <!-- 子节点 -->
    <div v-if="hasChildren && isExpanded" class="children">
      <ReviewTreeNode
        v-for="child in node.children"
        :key="child.uniqueId || child.reviewItemCode"
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

<script setup lang="ts">
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
    type: String,
    default: null
  }
})

const emit = defineEmits(['toggle', 'select'])

// 节点ID - 优先使用 uniqueId，否则使用 reviewItemCode
const nodeId = computed(() => {
  return props.node.uniqueId || props.node.reviewItemCode
})

// 是否有子节点
const hasChildren = computed(() => {
  return props.node.children && props.node.children.length > 0
})

// 是否展开
const isExpanded = computed(() => {
  return props.expandedNodes.has(nodeId.value)
})

// 处理展开/折叠
const handleToggle = () => {
  emit('toggle', nodeId.value)
}

// 处理选择
const handleSelect = () => {
  emit('select', props.node)
}
</script>

<style scoped lang="scss">
.review-tree-node {
  user-select: none;
}

.node-header {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  margin: 2px 0;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  gap: 8px;
  border-left: 3px solid transparent;
  background: white;

  &:hover {
    background: #f5f5f5;
  }

  &.selected {
    background: #e3f2fd;
    border-left-color: #1976d2;
  }

  &.has-risk {
    background: #fff3e0;

    &.selected {
      background: #ffe0b2;
      border-left-color: #ff6f00;
    }
  }
}

/* 深度缩进 */
.depth-0 { margin-left: 0; }
.depth-1 { margin-left: 20px; }
.depth-2 { margin-left: 40px; }
.depth-3 { margin-left: 60px; }
.depth-4 { margin-left: 80px; }
.depth-5 { margin-left: 100px; }
.depth-6 { margin-left: 120px; }

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

.risk-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.safe-icon {
  font-size: 16px;
  flex-shrink: 0;
  color: #4caf50;
}

.normal-icon {
  font-size: 16px;
  flex-shrink: 0;
  color: #9e9e9e;
}

.node-label {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.node-name {
  color: #333;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.5;
}

.child-count {
  color: #999;
  font-size: 12px;
  flex-shrink: 0;
}

.status-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  flex-shrink: 0;
  font-weight: 500;

  &.handled {
    background: #e8f5e9;
    color: #2e7d32;
  }

  &.accepted {
    background: #e3f2fd;
    color: #1976d2;
  }
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
