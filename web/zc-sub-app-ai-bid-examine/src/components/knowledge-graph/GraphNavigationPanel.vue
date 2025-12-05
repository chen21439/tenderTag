<template>
  <div class="graph-navigation-panel" :class="{ 'layout-sidebar': layout === 'sidebar', 'layout-floating': layout === 'floating' }">
    <!-- 导航面板 (可折叠) -->
    <div v-show="!collapsed" class="graph-nav-panel-wrapper">
      <div class="graph-nav-panel">
        <div v-if="treeData.length > 0" class="nav-tree-list">
          <GraphNavNode
            v-for="node in treeData"
            :key="node.id"
            :node="node"
            :depth="0"
            :selected-id="selectedNodeId"
            @select="handleNavNodeSelect"
          />
        </div>
        <a-empty v-else description="暂无数据" :image="Empty.PRESENTED_IMAGE_SIMPLE" />
      </div>
    </div>

    <!-- 图谱画布 -->
    <div class="graph-canvas">
      <slot name="graph"></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Empty } from 'ant-design-vue'
import GraphNavNode from './GraphNavNode.vue'

defineOptions({
  name: 'GraphNavigationPanel'
})

interface Props {
  treeData: Array<any>
  selectedNodeId?: string | null
  collapsed?: boolean
  layout?: 'sidebar' | 'floating' // 布局模式：侧边栏 or 浮动
}

const props = withDefaults(defineProps<Props>(), {
  treeData: () => [],
  selectedNodeId: null,
  collapsed: false,
  layout: 'sidebar'
})

const emit = defineEmits<{
  (e: 'node-select', nodeId: string): void
}>()

const handleNavNodeSelect = (nodeId: string) => {
  emit('node-select', nodeId)
}
</script>

<style scoped lang="scss">
.graph-navigation-panel {
  width: 100%;
  height: 100%;
  position: relative;

  // 侧边栏布局（默认）
  &.layout-sidebar {
    display: flex;

    .graph-nav-panel-wrapper {
      width: 280px;
      height: 100%;
      border-right: 1px solid #e0e0e0;
      background: #fff;
      overflow-y: auto;
      flex-shrink: 0;
    }

    .graph-canvas {
      flex: 1;
      position: relative;
      overflow: hidden;
    }
  }

  // 浮动布局（compliance-review 使用）
  &.layout-floating {
    display: flex;
    flex-direction: column;

    .graph-nav-panel-wrapper {
      position: absolute;
      top: 8px;
      right: 16px;
      z-index: 10;
      max-width: 400px;
      max-height: 500px;
      background: #ffffff;
      border: 1px solid #e5e6eb;
      border-radius: 4px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
      overflow-y: auto;
    }

    .graph-canvas {
      flex: 1;
      position: relative;
      min-height: 0;
    }
  }
}

.graph-nav-panel {
  padding: 12px 8px;
}

.nav-tree-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
</style>
