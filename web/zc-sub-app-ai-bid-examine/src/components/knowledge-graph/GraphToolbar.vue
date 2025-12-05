<template>
  <div class="graph-toolbar-controls">
    <!-- 导航按钮（可选） -->
    <template v-if="showNavButton">
      <a-button
        type="default"
        size="small"
        :class="{ 'active': !navCollapsed }"
        @click="handleToggleNav"
      >
        <template #icon>
          <ApartmentOutlined />
        </template>
      </a-button>
      <a-divider type="vertical" style="height: 24px; margin: 0 8px" />
    </template>

    <!-- 图谱控制按钮 -->
    <GraphControls
      @reset="$emit('reset')"
      @fit="$emit('fit')"
      @zoomIn="$emit('zoomIn')"
      @zoomOut="$emit('zoomOut')"
    />
  </div>
</template>

<script setup lang="ts">
import { ApartmentOutlined } from '@ant-design/icons-vue'
import GraphControls from './GraphControls.vue'

interface Props {
  showNavButton?: boolean
  navCollapsed?: boolean
}

withDefaults(defineProps<Props>(), {
  showNavButton: false,
  navCollapsed: true
})

const emit = defineEmits<{
  reset: []
  fit: []
  zoomIn: []
  zoomOut: []
  toggleNav: []
}>()

const handleToggleNav = () => {
  emit('toggleNav')
}
</script>

<style scoped>
.graph-toolbar-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 确保按钮图标正确对齐 */
.graph-toolbar-controls :deep(.ant-btn > span) {
  display: inline-block;
}

.active {
  color: #1890ff;
  border-color: #1890ff;
}
</style>
