<template>
  <div class="document-reader" :style="containerStyle">
    <!-- 工具栏 -->
    <div v-if="showToolbar" class="document-toolbar">
      <div class="toolbar-left">
        <!-- 缩放控件 -->
        <div class="zoom-controls">
          <a-button-group size="small">
            <a-button @click="zoomOut" :disabled="zoom.current <= zoom.min">
              <template #icon><ZoomOutOutlined /></template>
            </a-button>
            <a-button @click="resetZoom">
              {{ Math.round(zoom.current * 100) }}%
            </a-button>
            <a-button @click="zoomIn" :disabled="zoom.current >= zoom.max">
              <template #icon><ZoomInOutlined /></template>
            </a-button>
          </a-button-group>
          <a-button size="small" @click="fitToWidth" class="ml-2">
            适应宽度
          </a-button>
        </div>
      </div>
      
      <div class="toolbar-right">
        <!-- 分页控件 -->
        <div v-if="showPagination" class="pagination-controls">
          <a-button-group size="small">
            <a-button @click="prevPage" :disabled="pagination.current <= 1">
              <template #icon><LeftOutlined /></template>
            </a-button>
            <a-input
              v-model:value="pageInputValue"
              size="small"
              class="page-input"
              @keydown.enter="handlePageInputEnter" 
            />
            <span class="page-info">/ {{ pagination.total }}</span>
            <a-button @click="nextPage" :disabled="pagination.current >= pagination.total">
              <template #icon><RightOutlined /></template>
            </a-button>
          </a-button-group>
        </div>

        <!-- 滚动模式信息 -->
        <div class="scroll-info">
          <span class="current-page-info">当前: 第{{ currentVisiblePage }}页</span>
        </div>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="document-main" :style="mainStyle">
      <!-- 文档内容区域 -->
      <div
        class="document-content"
        :style="contentStyle"
        @wheel="handleWheel"
        @scroll="handleScroll"
        ref="contentRef"
      >
        <div class="content-wrapper continuous-scroll" :style="wrapperStyle">
          <DocumentPage
            v-for="pageNum in getAllPageNumbers()"
            :key="pageNum"
            :page-number="pageNum"
            :elements="getPageElements(pageNum)"
            :zoom="zoom.current"
            :render-options="renderOptions"
            :highlights="highlights"
            :class="{ 'page-separator': pageNum > 1 }"
            :data-page-number="pageNum"
            @element-click="handleElementClick"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { 
  ZoomInOutlined, 
  ZoomOutOutlined, 
  LeftOutlined, 
  RightOutlined 
} from '@ant-design/icons-vue'
import type {
  DocumentReaderProps,
  ParsedDocumentData,
  DocumentElement as DocumentElementType,
  ZoomConfig,
  PaginationConfig,
  RenderOptions
} from './types'
import { parseDocumentData } from './doc-utils'
import DocumentPage from './DocumentPage.vue'

// 组件Props
const props = withDefaults(defineProps<DocumentReaderProps>(), {
  height: '100%',
  width: '100%',
  showToc: true,
  showToolbar: true,
  showPagination: false,
  initialZoom: 1,
  enableVirtualScroll: false,
  pageSize: 1,
  tocWidth: 280,
  toolbarHeight: 48
})

// 组件事件
const emit = defineEmits(['page-change', 'zoom-change', 'toc-item-click', 'element-click', 'highlight-change'])

// 响应式数据
const parsedData = ref<ParsedDocumentData | null>(null)
const contentRef = ref<HTMLElement>()
const currentVisiblePage = ref(1)
const highlights = ref<Map<string, any>>(new Map())
const pageInputValue = ref('1')
const isScrollingProgrammatically = ref(false)
const targetPageNumber = ref<number | null>(null)

// 缩放配置
const zoom = ref<ZoomConfig>({
  current: props.initialZoom,
  min: 0.25,
  max: 3,
  step: 0.25,
  fitWidth: false,
  fitHeight: false
})

// 分页配置
const pagination = ref<PaginationConfig>({
  current: 1,
  total: 0,
  pageSize: props.pageSize,
  showSizeChanger: false,
  showQuickJumper: true
})

// 渲染选项
const renderOptions = ref<RenderOptions>({
  enableSelection: true,
  enableCopy: true,
  highlightSearch: false
})

// 计算属性
const containerStyle = computed(() => ({
  height: typeof props.height === 'number' ? `${props.height}px` : props.height,
  width: typeof props.width === 'number' ? `${props.width}px` : props.width
}))

const mainStyle = computed(() => ({
  height: props.showToolbar ? `calc(100% - ${props.toolbarHeight}px)` : '100%'
}))



const contentStyle = computed(() => ({
  width: '100%',
  height: '100%'
}))

const wrapperStyle = computed(() => ({
  transform: `scale(${zoom.value.current})`,
  transformOrigin: 'top left',
  transition: 'transform 0.2s ease-in-out'
}))



// 方法
const initializeData = () => {
  if (!props.data) return

  try {
    parsedData.value = parseDocumentData(props.data)
    if (parsedData.value) {
      pagination.value.total = parsedData.value.totalPages
      pageInputValue.value = pagination.value.current.toString()
    }
  } catch (error) {
    console.error('Failed to parse document data:', error)
  }
}

const getPageElements = (pageNum: number): DocumentElementType[] => {
  if (!parsedData.value) return []
  return parsedData.value.pages.get(pageNum) || []
}





// 获取所有页面编号（用于连续滚动）
const getAllPageNumbers = () => {
  if (!parsedData.value) return []

  const pageNumbers = []
  for (let i = 1; i <= parsedData.value.totalPages; i++) {
    pageNumbers.push(i)
  }
  return pageNumbers
}

// 缩放控制
const zoomIn = () => {
  zoom.value.current = Math.min(zoom.value.max, zoom.value.current + zoom.value.step)
  emit('zoom-change', zoom.value.current)
}

const zoomOut = () => {
  zoom.value.current = Math.max(zoom.value.min, zoom.value.current - zoom.value.step)
  emit('zoom-change', zoom.value.current)
}

const resetZoom = () => {
  zoom.value.current = 1
  zoom.value.fitWidth = false
  zoom.value.fitHeight = false
  emit('zoom-change', zoom.value.current)
}

const fitToWidth = () => {
  if (!contentRef.value) return

  // 计算适合宽度的缩放比例
  const containerWidth = contentRef.value.clientWidth - 40 // 减去padding
  const pageWidth = 800 // 假设页面宽度为800px
  const calculatedZoom = Math.min(containerWidth / pageWidth, 2) // 最大不超过2倍

  zoom.value.current = Math.max(zoom.value.min, calculatedZoom)
  zoom.value.fitWidth = true
  emit('zoom-change', zoom.value.current)
}

// 鼠标滚轮缩放
const handleWheel = (event: WheelEvent) => {
  if (event.ctrlKey || event.metaKey) {
    event.preventDefault()

    const delta = event.deltaY > 0 ? -zoom.value.step : zoom.value.step
    const newZoom = zoom.value.current + delta

    if (newZoom >= zoom.value.min && newZoom <= zoom.value.max) {
      zoom.value.current = newZoom
      emit('zoom-change', zoom.value.current)
    }
  }
}

// 滚动事件处理（用于连续滚动模式）
const handleScroll = (event: Event) => {
  if (!contentRef.value || !parsedData.value || isScrollingProgrammatically.value) return

  const target = event.target as HTMLElement
  const scrollTop = target.scrollTop
  const containerHeight = target.clientHeight

  // 更精确的页面检测：基于页面元素的实际位置
  const pageElements = contentRef.value.querySelectorAll('.document-page')
  let currentPage = 1

  // 使用视口中心点来确定当前页面，这样更稳定
  const viewportCenter = scrollTop + containerHeight / 2

  for (let i = 0; i < pageElements.length; i++) {
    const pageElement = pageElements[i] as HTMLElement
    const pageTop = pageElement.offsetTop
    const pageBottom = pageTop + pageElement.offsetHeight

    // 如果视口中心点在这个页面范围内，就认为这是当前页
    if (viewportCenter >= pageTop && viewportCenter <= pageBottom) {
      currentPage = i + 1
      break
    }

    // 如果视口中心点在第一个页面之前，当前页就是第一页
    if (i === 0 && viewportCenter < pageTop) {
      currentPage = 1
      break
    }

    // 如果视口中心点在最后一个页面之后，当前页就是最后一页
    if (i === pageElements.length - 1 && viewportCenter > pageBottom) {
      currentPage = i + 1
      break
    }
  }

  if (currentPage !== currentVisiblePage.value && currentPage <= parsedData.value.totalPages) { 
    currentVisiblePage.value = currentPage
    pagination.value.current = currentPage
    pageInputValue.value = currentPage.toString()
    emit('page-change', currentPage)
  }
}

// 滚动到指定页面
const scrollToPage = (pageNumber: number) => {
  if (!contentRef.value || !parsedData.value) return

  // 标记为程序化滚动，防止滚动事件干扰
  isScrollingProgrammatically.value = true

  // 使用 nextTick 确保 DOM 已更新
  nextTick(() => {
    const pageElements = contentRef.value!.querySelectorAll('.document-page')
    const targetPageElement = pageElements[pageNumber - 1] as HTMLElement

    if (targetPageElement) {
      // 获取页面元素的实际位置
      const targetScrollTop = targetPageElement.offsetTop - 20 // 减去一些padding

      // 平滑滚动到目标位置
      contentRef.value!.scrollTo({
        top: targetScrollTop,
        behavior: 'smooth'
      })

      // 更新当前可见页面
      currentVisiblePage.value = pageNumber

      // 滚动完成后重新启用滚动事件处理，并确保页码正确
      setTimeout(() => {
        isScrollingProgrammatically.value = false
        // 双重保险：确保页码是正确的
        if (targetPageNumber.value !== null) {
          console.log('滚动完成后修正页码:', pagination.value.current, '->', targetPageNumber.value)
          pagination.value.current = targetPageNumber.value
          pageInputValue.value = targetPageNumber.value.toString()
          currentVisiblePage.value = targetPageNumber.value
          targetPageNumber.value = null // 清除目标页码
        }
      }, 800) // 给平滑滚动更多时间完成
    } else {
      // 如果没有找到目标元素，立即重新启用滚动事件处理
      isScrollingProgrammatically.value = false
    }
  })
}

// 分页控制
const prevPage = () => {
  if (pagination.value.current > 1) {
    goToPage(pagination.value.current - 1)
  }
}

const nextPage = () => {
  if (pagination.value.current < pagination.value.total) {
    goToPage(pagination.value.current + 1)
  }
}

const goToPage = (page: number) => {
  console.log('goToPage - 目标页码:', page)
  if (page >= 1 && page <= pagination.value.total) {
    // 记录目标页码
    targetPageNumber.value = page

    pagination.value.current = page
    pageInputValue.value = page.toString()
    console.log('goToPage - 设置后的当前页码:', pagination.value.current)
    console.log('goToPage - 设置后的输入框值:', pageInputValue.value)
    scrollToPage(pagination.value.current)
    emit('page-change', pagination.value.current)
  }
}

// 处理页码输入变化
const handlePageInputChange = (value: string) => {
  // 只允许数字输入
  const numericValue = value.replace(/[^\d]/g, '')
  if (numericValue !== value) {
    pageInputValue.value = numericValue
  }
}

// 处理页码输入框Enter键事件
const handlePageInputEnter = () => {
  const targetPage = parseInt(pageInputValue.value.toString())
  console.log('handlePageInputEnter - 输入的页码:', targetPage)
  console.log('handlePageInputEnter - 当前页码:', pagination.value.current)

  if (!isNaN(targetPage) && targetPage >= 1 && targetPage <= pagination.value.total) {
    goToPage(targetPage)
  } else {
    // 如果输入的页码无效，恢复到当前页码
    pageInputValue.value = pagination.value.current.toString()
  }
}

// 事件处理

const handleElementClick = (element: DocumentElementType) => {
  emit('element-click', element)
}

// 高亮相关方法
const addHighlight = (id: string, highlight: any) => {
  console.log('添加高亮:', id, highlight)
  highlights.value.set(id, highlight)
  emit('highlight-change', { action: 'add', id, highlight })
}

const removeHighlight = (id: string) => {
  highlights.value.delete(id)
  emit('highlight-change', { action: 'remove', id })
}

const clearAllHighlights = () => {
  console.log('清除所有高亮，当前高亮数量:', highlights.value.size)
  highlights.value.clear()
  emit('highlight-change', { action: 'clear' })
}

const scrollToHighlight = (pageId: number, position: any, fileText?: string) => {
  // 先跳转到对应页面
  goToPage(pageId)

  // 等待页面渲染完成后高亮元素
  nextTick(() => {
    const pageElements = contentRef.value?.querySelectorAll('.document-page')
    if (pageElements && pageElements[pageId - 1]) {
      const pageElement = pageElements[pageId - 1] as HTMLElement

      // 如果有原文内容，尝试找到包含该文本的元素
      if (fileText) {
        const textElements = pageElement.querySelectorAll('.document-element')
        let targetElement: HTMLElement | null = null

        for (let i = 0; i < textElements.length; i++) {
          const element = textElements[i]
          const elementText = element.textContent || ''
          const trimmedFileText = fileText.trim()

          // 精确匹配
          if (elementText.includes(trimmedFileText)) {
            targetElement = element as HTMLElement
            break
          }

          // 如果精确匹配失败，尝试模糊匹配
          if (!targetElement && trimmedFileText.length > 10) {
            // 去除标点符号和空格进行匹配
            const normalizedElement = elementText.replace(/[^\w\u4e00-\u9fff]/g, '')
            const normalizedTarget = trimmedFileText.replace(/[^\w\u4e00-\u9fff]/g, '')

            if (normalizedElement.includes(normalizedTarget)) {
              targetElement = element as HTMLElement
              // 不break，继续寻找更精确的匹配
            }
          }
        }

        if (targetElement) {
          // 滚动到包含目标文本的元素
          targetElement.scrollIntoView({
            behavior: 'smooth',
            block: 'center',
            inline: 'nearest'
          })
          return
        }
      }

      // 如果没有找到具体元素，使用位置信息定位
      if (position && position.y1) {
        const targetY = position.y1 * zoom.value.current
        const scrollContainer = contentRef.value
        if (scrollContainer) {
          const pageRect = pageElement.getBoundingClientRect()
          const containerRect = scrollContainer.getBoundingClientRect()
          const scrollTop = scrollContainer.scrollTop + pageRect.top - containerRect.top + targetY

          scrollContainer.scrollTo({
            top: scrollTop,
            behavior: 'smooth'
          })
          return
        }
      }

      // 默认滚动到页面中心
      pageElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  })
}

// 暴露方法给父组件
defineExpose({
  addHighlight,
  removeHighlight,
  clearAllHighlights,
  scrollToHighlight,
  scrollToPage
})

// 键盘事件处理
const handleKeydown = (event: KeyboardEvent) => {
  switch (event.key) {
    case 'ArrowLeft':
      event.preventDefault()
      prevPage()
      break
    case 'ArrowRight':
      event.preventDefault()
      nextPage()
      break
    case 'Home':
      event.preventDefault()
      goToPage(1)
      break
    case 'End':
      event.preventDefault()
      goToPage(pagination.value.total)
      break
  }
}

// 生命周期
onMounted(() => {
  initializeData()
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})

// 监听数据变化
watch(() => props.data, initializeData, { deep: true })
</script>

<style lang="scss" scoped>
.document-reader {
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  overflow: hidden;

  .document-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 16px;
    background: #fff;
    border-bottom: 1px solid #d9d9d9;
    height: 48px;
    box-sizing: border-box;

    .toolbar-left,
    .toolbar-right {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .zoom-controls {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .pagination-controls {
      display: flex;
      align-items: center;
      gap: 8px;

      .page-input {
        width: 60px;
      }

      .page-info {
        color: #666;
        font-size: 12px;
        margin: 0 4px;
      }
    }
  }

  .document-main {
    display: flex;
    flex: 1;
    overflow: hidden;

    .document-content {
      background: #fff;
      overflow: auto;
      position: relative;

      /* 确保滚动条可见 */
      &::-webkit-scrollbar {
        width: 12px;
        height: 12px;
      }

      &::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 6px;
      }

      &::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 6px;

        &:hover {
          background: #a8a8a8;
        }
      }

      /* Firefox 滚动条样式 */
      scrollbar-width: thin;
      scrollbar-color: #c1c1c1 #f1f1f1;

      .content-wrapper {
        min-height: 100%;
        padding: 20px;

        &.continuous-scroll {
          .document-page {
            margin-bottom: 20px;
            border: 1px solid #e8e8e8;
            border-radius: 4px;
            background: #fff;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

            &.page-separator {
              margin-top: 40px;
              position: relative;

              &::before {
                content: '第' attr(data-page-number) '页';
                position: absolute;
                top: -30px;
                left: 50%;
                transform: translateX(-50%);
                background: #f5f5f5;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 12px;
                color: #666;
                border: 1px solid #d9d9d9;
              }
            }
          }
        }
      }
    }
  }
}

.ml-2 {
  margin-left: 8px;
}
</style>
