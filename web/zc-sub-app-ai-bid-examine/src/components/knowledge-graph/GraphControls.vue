<template>
  <div class="graph-controls">
    <a-tooltip title="重置布局">
      <a-button type="default" shape="circle" @click="handleReset">
        <template #icon>
          <ReloadOutlined />
        </template>
      </a-button>
    </a-tooltip>
    <a-tooltip title="适应视图">
      <a-button type="default" shape="circle" @click="handleFit">
        <template #icon>
          <FullscreenOutlined />
        </template>
      </a-button>
    </a-tooltip>
    <a-tooltip title="放大">
      <a-button type="default" shape="circle" @click="handleZoomIn">
        <template #icon>
          <ZoomInOutlined />
        </template>
      </a-button>
    </a-tooltip>
    <a-tooltip title="缩小">
      <a-button type="default" shape="circle" @click="handleZoomOut">
        <template #icon>
          <ZoomOutOutlined />
        </template>
      </a-button>
    </a-tooltip>
  </div>
</template>

<script setup lang="ts">
import {
  ReloadOutlined,
  FullscreenOutlined,
  ZoomInOutlined,
  ZoomOutOutlined
} from '@ant-design/icons-vue'

defineOptions({
  name: 'GraphControls'
})

const emit = defineEmits(['reset', 'fit', 'zoomIn', 'zoomOut'])

const handleReset = () => {
  emit('reset')
}

const handleFit = () => {
  emit('fit')
}

const handleZoomIn = () => {
  emit('zoomIn')
}

const handleZoomOut = () => {
  emit('zoomOut')
}
</script>

<style lang="scss" scoped>
.graph-controls {
  display: flex;
  flex-direction: row;
  gap: 8px;

  :deep(.ant-btn) {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #fff;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    border: 1px solid #d9d9d9;

    &:hover {
      border-color: #1890ff;
      color: #1890ff;
    }
  }
}
</style>
