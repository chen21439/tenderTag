<template>
  <div
    class="document-element"
    :class="elementClass"
    :style="elementStyle"
    @click="handleClick"
  >


    <!-- 段落内容 -->
    <div v-if="element.type === 'paragraph'" class="element-paragraph">
      <component 
        :is="getHeadingTag(element.outline_level)"
        v-if="element.outline_level >= 0"
        class="heading"
        :class="`heading-${element.outline_level}`"
        v-html="processedText"
      />
      <p v-else class="paragraph-text" v-html="processedText" />
    </div>
    
    <!-- 表格内容 -->
    <div v-else-if="element.type === 'table'" class="element-table">
      <!-- 表格拆分信息提示 -->
      <div v-if="element.split_info?.is_table_split" class="table-split-info">
        <a-tag size="small" color="blue">
          表格第 {{ element.split_info.current_part }} 部分 / 共 {{ element.split_info.total_parts }} 部分
          <span v-if="element.split_info.page_row_range">
            (第 {{ element.split_info.page_row_range[0] }}-{{ element.split_info.page_row_range[1] }} 行)
          </span>
        </a-tag>
      </div>

      <div class="table-wrapper">
        <div v-html="processedTableHtml" class="table-content" />
      </div>
    </div>
    
    <!-- 图片内容 -->
    <div v-else-if="element.type === 'image'" class="element-image">
      <img 
        v-if="element.image_url"
        :src="element.image_url"
        :alt="element.text || '图片'"
        class="image-content"
        @load="handleImageLoad"
        @error="handleImageError"
      />
      <div v-else class="image-placeholder">
        <div class="placeholder-content">
          <span>{{ element.text || '图片' }}</span>
        </div>
      </div>
    </div>
    
    <!-- 标签显示 -->
    <div v-if="element.tags && element.tags.length > 0" class="element-tags">
      <a-tag 
        v-for="tag in element.tags" 
        :key="tag" 
        size="small"
        :color="getTagColor(tag)"
      >
        {{ tag }}
      </a-tag>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineProps, defineEmits } from 'vue'
import type { DocumentElement as DocumentElementType, RenderOptions } from './types'
import { 
  processTableHtml,
  highlightSearchKeyword,
  getElementClassName
} from './doc-utils'

interface Props {
  element: DocumentElementType
  zoom: number
  renderOptions: RenderOptions
  highlights?: Map<string, any>
}

interface Emits {
  (e: 'element-click', element: DocumentElementType, extra?: any): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 计算元素样式
const elementStyle = computed(() => { 
  return {
    position: 'relative' as const,
    marginBottom: '12px' 
  }
})

// 元素类名
const elementClass = computed(() => {
  return getElementClassName(props.element)
})

// 处理后的文本内容
const processedText = computed(() => {
  let text = props.element.text || ''

  // 搜索高亮
  if (props.renderOptions.highlightSearch && props.renderOptions.searchKeyword) {
    text = highlightSearchKeyword(text, props.renderOptions.searchKeyword)
  }

  // 修订建议文本高亮
  if (props.highlights) {
    let hasHighlight = false // 防止重复高亮

    for (const [highlightId, highlight] of props.highlights.entries()) {
      if (highlight.pageId === props.element.page_id && highlight.fileText && !hasHighlight) {
        // 检查当前元素的文本是否包含修订建议的原文
        const originalText = highlight.fileText.trim()

        // 尝试精确匹配
        if (text.includes(originalText)) {
          const highlightClass = `revision-highlight revision-highlight-${highlight.type || 'risk'}`
          // 只替换第一个匹配项，避免重复高亮
          text = text.replace(
            new RegExp(escapeRegExp(originalText), 'i'),
            `<span class="${highlightClass}" data-highlight-id="${highlightId}">${originalText}</span>`
          )
          hasHighlight = true
          console.log('应用文本高亮:', originalText, '在元素:', props.element.paragraph_id)
        } else {
          // 尝试模糊匹配（去除标点符号和空格）
          const normalizedOriginal = originalText.replace(/[^\w\u4e00-\u9fff]/g, '')
          const normalizedText = text.replace(/[^\w\u4e00-\u9fff]/g, '')

          if (normalizedText.includes(normalizedOriginal) && normalizedOriginal.length > 5) {
            // 找到最相似的文本片段进行高亮
            const words = originalText.split(/\s+/).filter((word: string) => word.length > 1)
            for (const word of words) {
              if (text.includes(word) && word.length > 2) {
                const highlightClass = `revision-highlight revision-highlight-${highlight.type || 'risk'}`
                text = text.replace(
                  new RegExp(escapeRegExp(word), 'gi'),
                  `<span class="${highlightClass}" data-highlight-id="${highlightId}">${word}</span>`
                )
                hasHighlight = true
                break // 找到一个匹配就停止
              }
            }
          }
        }
      }
    }
  }

  return text
})

// 转义正则表达式特殊字符
const escapeRegExp = (string: string): string => {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

// 处理后的表格HTML
const processedTableHtml = computed(() => {
  if (props.element.type !== 'table') return ''
  let html = processTableHtml(props.element.text || '')

  // 修订建议文本高亮（表格内容）
  if (props.highlights) {
    let hasTableHighlight = false // 防止重复高亮

    for (const [highlightId, highlight] of props.highlights.entries()) {
      if (highlight.pageId === props.element.page_id && highlight.fileText && !hasTableHighlight) {
        const originalText = highlight.fileText.trim()

        // 在表格HTML中查找并高亮文本
        if (html.includes(originalText)) {
          const highlightClass = `revision-highlight revision-highlight-${highlight.type || 'risk'}`
          // 只替换第一个匹配项，避免重复高亮
          html = html.replace(
            new RegExp(escapeRegExp(originalText), 'i'),
            `<span class="${highlightClass}" data-highlight-id="${highlightId}">${originalText}</span>`
          )
          hasTableHighlight = true
          console.log('应用表格高亮:', originalText, '在表格元素:', props.element.paragraph_id)
        }
      }
    }
  }

  return html
})

// 获取标题标签
const getHeadingTag = (level: number): string => {
  const headingMap: Record<number, string> = {
    0: 'h1',
    1: 'h2', 
    2: 'h3',
    3: 'h4',
    4: 'h5'
  }
  return headingMap[level] || 'h6'
}

// 获取标签颜色
const getTagColor = (tag: string): string => {
  const colorMap: Record<string, string> = {
    'formula': 'blue',
    'handwritten': 'green',
    'stamp': 'red',
    'chart': 'orange',
    'qrcode': 'purple',
    'barcode': 'cyan'
  }
  return colorMap[tag] || 'default'
}



// 事件处理
const handleClick = (event: Event) => {
  // 检查是否点击了高亮文本
  const target = event.target as HTMLElement
  if (target.classList.contains('revision-highlight')) {
    const highlightId = target.getAttribute('data-highlight-id')
    if (highlightId && props.highlights?.has(highlightId)) {
      // 触发高亮点击事件
      emit('element-click', props.element, { type: 'highlight-click', highlightId })
      return
    }
  }

  emit('element-click', props.element)
}

const handleImageLoad = (event: Event) => {
  console.log('Image loaded:', event)
}

const handleImageError = (event: Event) => {
  console.error('Image load error:', event)
}
</script>

<style lang="scss" scoped>
.document-element {
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: 4px;
  padding: 8px;

  &:hover {
    background-color: rgba(24, 144, 255, 0.05);
  }


  
  // 段落样式
  .element-paragraph {
    .heading {
      margin: 0 0 12px 0;
      font-weight: 600;
      line-height: 1.4;
      
      &.heading-0 {
        font-size: 24px;
        color: #262626;
      }
      
      &.heading-1 {
        font-size: 20px;
        color: #262626;
      }
      
      &.heading-2 {
        font-size: 18px;
        color: #434343;
      }
      
      &.heading-3 {
        font-size: 16px;
        color: #434343;
      }
      
      &.heading-4 {
        font-size: 14px;
        color: #595959;
      }
    }
    
    .paragraph-text {
      margin: 0;
      line-height: 1.6;
      color: #262626;
      font-size: 14px;
      white-space: break-spaces;
      word-break: break-all;
    }
  }
  
  // 表格样式
  .element-table {
    .table-split-info {
      margin-bottom: 8px;
      padding: 4px 0;

      .ant-tag {
        font-size: 12px;
      }
    }

    .table-wrapper {
      overflow-x: auto;
      border-radius: 4px;
      border: 1px solid #f0f0f0;
      
      :deep(.table-content) {
        table {
          width: 100%;
          border-collapse: collapse;
          font-size: 13px;
          
          th, td {
            padding: 8px 12px;
            border: 1px solid #f0f0f0;
            text-align: left;
            vertical-align: top;
            line-height: 1.5;
          }
          
          th {
            background-color: #fafafa;
            font-weight: 600;
            color: #262626;
          }
          
          td {
            color: #595959;
          }
          
          tr:nth-child(even) {
            background-color: #fafafa;
          }
        }
      }
    }
  }
  
  // 图片样式
  .element-image {
    text-align: center;
    
    .image-content {
      max-width: 100%;
      height: auto;
      border-radius: 4px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    .image-placeholder {
      min-height: 200px;
      background: #f5f5f5;
      border: 2px dashed #d9d9d9;
      border-radius: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      
      .placeholder-content {
        text-align: center;
        color: #999;
        font-size: 14px;
      }
    }
  }
  
  // 标签样式
  .element-tags {
    margin-top: 8px;
    
    .ant-tag {
      margin-right: 4px;
      margin-bottom: 4px;
    }
  }
  
  // 特殊类型样式
  &.sub-type-header,
  &.sub-type-footer {
    opacity: 0.7;
    font-size: 12px;
    color: #999;
  }
  
  &.sub-type-sidebar {
    border-left: 3px solid #1890ff;
    padding-left: 12px;
    background-color: #f6ffed;
  }
  
  // 标签特殊样式
  &.tag-formula {
    .paragraph-text {
      font-family: 'Times New Roman', serif;
      font-style: italic;
    }
  }
  
  &.tag-handwritten {
    .paragraph-text {
      font-family: cursive;
    }
  }
}

// 搜索高亮样式
:deep(mark) {
  background-color: #fff566;
  padding: 0 2px;
  border-radius: 2px;
}

// 修订建议高亮样式
:deep(.revision-highlight) {
  padding: 3px 6px;
  border-radius: 4px;
  font-weight: 600;
  animation: revisionPulse 3s ease-in-out infinite;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-block;
  margin: 0 1px;

  &:hover {
    transform: scale(1.05);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  }

  &.revision-highlight-risk {
    background: linear-gradient(135deg, rgba(255, 77, 79, 0.25), rgba(255, 77, 79, 0.35));
    color: #a8071a;
    border: 2px solid #ff4d4f;
    box-shadow: 0 0 10px rgba(255, 77, 79, 0.3);
  }

  &.revision-highlight-add {
    background: linear-gradient(135deg, rgba(82, 196, 26, 0.25), rgba(82, 196, 26, 0.35));
    color: #237804;
    border: 2px solid #52c41a;
    box-shadow: 0 0 10px rgba(82, 196, 26, 0.3);
  }

  &.revision-highlight-delete {
    background: linear-gradient(135deg, rgba(255, 77, 79, 0.25), rgba(255, 77, 79, 0.35));
    color: #a8071a;
    border: 2px solid #ff4d4f;
    text-decoration: line-through;
    box-shadow: 0 0 10px rgba(255, 77, 79, 0.3);
  }

  &.revision-highlight-modify {
    background: linear-gradient(135deg, rgba(250, 140, 22, 0.25), rgba(250, 140, 22, 0.35));
    color: #ad4e00;
    border: 2px solid #fa8c16;
    box-shadow: 0 0 10px rgba(250, 140, 22, 0.3);
  }
}

@keyframes revisionPulse {
  0%, 100% {
    opacity: 0.9;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.02);
  }
}
</style>
