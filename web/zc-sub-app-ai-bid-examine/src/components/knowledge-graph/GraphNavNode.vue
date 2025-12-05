<template>
  <div class="graph-nav-node">
    <div
      class="nav-node-header"
      :class="{
        'selected': selectedId === node.id,
        [`depth-${Math.min(depth, 6)}`]: true,
        [`type-${node.nodeType}`]: true
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

      <!-- 节点标签 -->
      <span class="node-label">
        <span class="node-text">{{ node.label }}</span>
      </span>
    </div>

    <!-- 子节点 -->
    <div v-if="isExpanded && hasChildren" class="children">
      <GraphNavNode
        v-for="child in node.children"
        :key="child.id"
        :node="child"
        :depth="depth + 1"
        :selected-id="selectedId"
        @select="$emit('select', $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

defineOptions({
  name: 'GraphNavNode'
})

const props = defineProps({
  node: {
    type: Object,
    required: true
  },
  depth: {
    type: Number,
    default: 0
  },
  selectedId: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['select'])

const isExpanded = ref(false)

// 是否有子节点
const hasChildren = computed(() => {
  return props.node.children && props.node.children.length > 0
})

// 处理展开/折叠
const handleToggle = () => {
  isExpanded.value = !isExpanded.value
}

// 处理选择
const handleSelect = () => {
  emit('select', props.node.id)
}
</script>

<style scoped lang="scss">
.graph-nav-node {
  user-select: none;
}

.nav-node-header {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  margin: 2px 0;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  gap: 8px;
  border-left: 3px solid transparent;

  &:hover {
    background: #f5f5f5;
  }

  &.selected {
    background: #e3f2fd;
    border-left-color: #1976d2;
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

/* 根据节点类型设置样式 */
.nav-node-header.type-normal {
  .node-text {
    color: #2f4554;
    font-weight: 500;
    font-size: 13px;
  }

  &.selected {
    background: #e6f7ff;
    border-left-color: #2f4554;
  }
}

.nav-node-header.type-element {
  .node-text {
    color: #722ed1;
    font-size: 12px;
  }

  &.selected {
    background: #f9f0ff;
    border-left-color: #722ed1;
  }
}

.nav-node-header.type-doc {
  .node-text {
    color: #95a5a6;
    font-size: 12px;
  }

  &.selected {
    background: #f5f5f5;
    border-left-color: #95a5a6;
  }
}

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

.node-label {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.node-text {
  color: #333;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.4;
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
