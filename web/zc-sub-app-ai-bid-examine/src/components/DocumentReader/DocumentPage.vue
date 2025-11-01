<template>
  <div
    class="document-page"
    :style="pageStyle"
    :data-page="pageNumber"
  >
    <div class="page-header">
      <span class="page-number">第 {{ pageNumber }} 页</span>
    </div>

    <div class="page-content">
      <!-- 主要内容区域 -->
      <div class="main-content">
        <DocumentElementComponent
          v-for="element in mainElements"
          :key="`${element.page_id}-${element.paragraph_id}`"
          :element="element"
          :zoom="zoom"
          :render-options="renderOptions"
          :highlights="highlights"
          @element-click="handleElementClick"
        />
      </div>

      <!-- 页脚区域 -->
      <div class="footer-content" v-if="footerElements.length > 0">
        <DocumentElementComponent
          v-for="element in footerElements"
          :key="`${element.page_id}-${element.paragraph_id}`"
          :element="element"
          :zoom="zoom"
          :render-options="renderOptions"
          :highlights="highlights"
          @element-click="handleElementClick"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineProps, defineEmits } from 'vue'
import type { DocumentElement as DocumentElementType, RenderOptions } from './types'
import DocumentElementComponent from './DocumentElement.vue'

interface Props {
  pageNumber: number
  elements: DocumentElementType[]
  zoom: number
  renderOptions: RenderOptions
  highlights?: Map<string, any>
}

interface Emits {
  (e: 'element-click', element: DocumentElementType): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 分离主要内容和页脚
const mainElements = computed(() => {
  return props.elements.filter(element => element.sub_type !== 'footer')
})

const footerElements = computed(() => {
  return props.elements.filter(element => element.sub_type === 'footer')
})

const pageStyle = computed(() => ({
  minHeight: '200px',
  marginBottom: '20px',
  background: '#fff',
  boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
  borderRadius: '4px',
  overflow: 'hidden'
})) 
const handleElementClick = (element: DocumentElementType) => {
  emit('element-click', element)
}
</script>

<style lang="scss" scoped>
.document-page {
  position: relative;
  display: flex;
  flex-direction: column;
  min-height: 600px; // 设置最小高度

  .page-header {
    padding: 12px 20px;
    background: #fafafa;
    border-bottom: 1px solid #f0f0f0;
    flex-shrink: 0; // 页头不收缩

    .page-number {
      font-size: 12px;
      color: #666;
      font-weight: 500;
    }
  }

  .page-content {
    padding: 20px;
    position: relative;
    display: flex;
    flex-direction: column;
    flex: 1; // 占据剩余空间

    .main-content {
      flex: 1; // 主要内容占据大部分空间
    }

    .footer-content {
      margin-top: auto; // 推到底部
      padding-top: 20px;
      border-top: 1px solid #f0f0f0;
    }
  }

  .highlight-overlay {
    border-radius: 2px;
    opacity: 0.3;
    animation: highlightPulse 2s ease-in-out infinite;

    &.highlight-add {
      background-color: #52c41a;
      border: 2px solid #389e0d;
    }

    &.highlight-delete {
      background-color: #ff4d4f;
      border: 2px solid #cf1322;
    }

    &.highlight-modify {
      background-color: #fa8c16;
      border: 2px solid #d46b08;
    }

    &.highlight-risk {
      background-color: #ff7875;
      border: 2px solid #ff4d4f;
    }
  }
}

@keyframes highlightPulse {
  0%, 100% {
    opacity: 0.3;
  }
  50% {
    opacity: 0.6;
  }
}
</style>
