<template>
  <div class="markdown-viewer-container">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <a-spin size="large" tip="加载中..." />
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-state">
      <a-result status="error" title="内容加载失败" :sub-title="error">
        <template #extra>
          <a-button type="primary" @click="$emit('retry')">重试</a-button>
        </template>
      </a-result>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!content" class="empty-state">
      <a-empty description="暂无内容" />
    </div>

    <!-- Markdown 渲染 -->
    <div v-else class="markdown-content">
      <MdPreview
        :model-value="content"
        :theme="theme"
        :preview-theme="previewTheme"
        :code-theme="codeTheme"
        :sanitize="sanitizeHtml"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount, watch, ref } from 'vue'
import { MdPreview } from 'md-editor-v3'
import 'md-editor-v3/lib/preview.css'

interface Props {
  content?: string          // Markdown 内容
  loading?: boolean         // 加载状态
  error?: string           // 错误信息
  theme?: 'light' | 'dark' // 主题模式
  previewTheme?: string    // 预览主题：default/github/vuepress/mk-cute/smart-blue/cyanosis
  codeTheme?: string       // 代码高亮主题：atom/github/gradient/kimbie/stackoverflow 等
  enableSanitize?: boolean // 是否启用 HTML 清理
}

const props = withDefaults(defineProps<Props>(), {
  content: '',
  loading: false,
  error: '',
  theme: 'light',
  previewTheme: 'github',
  codeTheme: 'github',
  enableSanitize: true
})

const emit = defineEmits<{
  retry: []
  headerClick: [{ itemId: string, page: string, text: string }]
}>()

const markdownContentRef = ref<HTMLElement | null>(null)

// 处理标题点击事件
const handleHeaderClick = (event: MouseEvent) => {
  console.log('🖱️ 点击事件触发', event.target)
  const target = event.target as HTMLElement

  // 查找带有 data-item-id 的元素（可能是当前元素或其父元素）
  let headerSpan = target.closest('[data-item-id]') as HTMLElement

  // 如果找不到，尝试直接查看当前元素
  if (!headerSpan && target.hasAttribute && target.hasAttribute('data-item-id')) {
    headerSpan = target
  }

  if (headerSpan) {
    const itemId = headerSpan.getAttribute('data-item-id') || ''
    const page = headerSpan.getAttribute('data-page') || ''
    const text = headerSpan.textContent || ''
    console.log('📍 点击标题:', { itemId, page, text })
    emit('headerClick', { itemId, page, text })
  } else {
    console.log('⚠️ 未找到带有 data-item-id 的元素')
  }
}

// 添加事件监听
const setupEventListeners = () => {
  const container = document.querySelector('.markdown-content')
  if (container) {
    console.log('✅ 设置事件监听器')
    container.addEventListener('click', handleHeaderClick)
  } else {
    console.warn('⚠️ 未找到 .markdown-content 容器')
  }
}

// 移除事件监听
const removeEventListeners = () => {
  const container = document.querySelector('.markdown-content')
  if (container) {
    console.log('🗑️ 移除事件监听器')
    container.removeEventListener('click', handleHeaderClick)
  }
}

onMounted(() => {
  console.log('🎬 MarkdownViewer mounted')
  // 延迟设置事件监听器，确保内容已渲染
  setTimeout(() => {
    setupEventListeners()
  }, 200)
})

onBeforeUnmount(() => {
  removeEventListeners()
})

// 监听内容变化，重新设置事件监听
watch(() => props.content, (newContent) => {
  console.log('📝 内容变化，长度:', newContent?.length)
  // 等待 DOM 更新后重新设置
  setTimeout(() => {
    removeEventListeners()
    setupEventListeners()
  }, 200)
})

// HTML 安全过滤（可选）
const sanitizeHtml = computed(() => {
  if (!props.enableSanitize) return undefined

  return (html: string) => {
    // 移除潜在危险标签和属性
    const dangerous = /<script|<iframe|javascript:|on\w+=/gi
    return html.replace(dangerous, '')
  }
})
</script>

<style scoped lang="scss">
.markdown-viewer-container {
  width: 100%;
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background-color: #fff;
}

.loading-state,
.error-state,
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 40px 20px;
}

.markdown-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;

  // 优化滚动条样式
  &::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }

  &::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 4px;

    &:hover {
      background: #a8a8a8;
    }
  }
}

// 覆盖 md-editor-v3 默认样式，适配容器
:deep(.md-preview-wrapper) {
  padding: 0;
}

:deep(.md-editor-preview) {
  background-color: transparent;

  // 根据层级自动计算缩进
  // 公式：缩进 = (level - 2) * 20px
  // Level 1-2: 0px (顶级标题)
  // Level 3+: 每增加一级缩进 20px

  h1 {
    margin-left: 0 !important;
    padding-left: 0 !important;
  }

  h2 {
    margin-left: 0 !important;
    padding-left: 0 !important;
  }

  h3 {
    margin-left: calc((3 - 2) * 20px) !important;  // 20px
    padding-left: calc((3 - 2) * 20px) !important;
  }

  h4 {
    margin-left: calc((4 - 2) * 20px) !important;  // 40px
    padding-left: calc((4 - 2) * 20px) !important;
  }

  h5 {
    margin-left: calc((5 - 2) * 20px) !important;  // 60px
    padding-left: calc((5 - 2) * 20px) !important;
  }

  h6 {
    margin-left: calc((6 - 2) * 20px) !important;  // 80px
    padding-left: calc((6 - 2) * 20px) !important;
  }
}

// 标题中的 span 元素样式（使其可点击）
:deep([data-item-id]) {
  cursor: pointer;
  transition: all 0.2s ease;
  padding: 2px 4px;
  border-radius: 4px;

  &:hover {
    background-color: #e6f7ff;
    color: #1890ff;
  }
}
</style>
