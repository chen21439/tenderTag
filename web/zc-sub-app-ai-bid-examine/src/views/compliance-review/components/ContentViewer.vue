<template>
  <div class="content-viewer">
    <!-- 头部控制栏 -->
    <div class="content-header">
      <div class="nav-buttons">
        <a-button type="text" class="nav-btn back-btn" @click="handleGoHome">
          <template #icon>
            <CornerUpLeft class="icon" :size="16" />
          </template>
          返回首页
        </a-button>
      </div>
      <div class="file-name">{{ fileName }}</div>
      <div v-if="!hideDemoFeatures" class="mode-buttons">
        <a-button
          :type="contentType === 'ppt' ? 'primary' : 'default'"
          @click="togglePptMode"
        >
          {{ contentType === 'ppt' ? '退出演示' : '演示模式' }}
        </a-button>
      </div>
    </div>

    <!-- 内容区域 -->
    <div class="content-body">
      <!-- PDF 预览模式 -->
      <div v-show="contentType === 'pdf'" class="content-section">
        <PdfViewer
          v-if="pdfUrl"
          ref="pdfViewerRef"
          :url="pdfUrl"
          :page="currentPage"
          @annotationsLoaded="handleAnnotationsLoaded"
        />
        <BaseEmpty v-else description="暂无文档" />
      </div>

      <!-- 问答模式 -->
      <div v-show="contentType === 'qa'" class="content-section qa-container">
        <div class="qa-messages" ref="qaMessagesRef">
          <div v-for="(msg, index) in qaMessages" :key="index" class="qa-message" :class="msg.role">
            <div class="message-content">{{ msg.content }}</div>
          </div>
        </div>

        <!-- 建议问题气泡 -->
        <div v-if="inputFocused && !qaInput" class="qa-suggestions">
          <div class="suggestion-bubble" @mousedown.prevent="fillSuggestion('德云天科技创新参与了哪些项目？')">
            <span>德云天科技创新参与了哪些项目？</span>
          </div>
        </div>

        <div class="qa-input">
          <a-input
            v-model:value="qaInput"
            placeholder="输入问题..."
            @pressEnter="sendQaMessage"
            @focus="inputFocused = true"
            @blur="handleInputBlur"
            :disabled="qaSending"
          />
          <a-button type="primary" @click="sendQaMessage" :loading="qaSending">
            发送
          </a-button>
        </div>
      </div>

      <!-- PPT 预览模式 -->
      <div v-show="contentType === 'ppt'" class="content-section">
        <PptViewer :ppt-url="pptUrl" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { message } from 'ant-design-vue'
import { CornerUpLeft } from 'lucide-vue-next'
import PdfViewer from '@/views/pdf/PdfViewer.vue'
import BaseEmpty from '@/components/BaseEmpty/index.vue'
import PptViewer from './ppt/PptViewer.vue'

defineOptions({
  name: 'ContentViewer'
})

// Props
interface Props {
  contentType?: 'pdf' | 'qa' | 'ppt'
  fileName?: string
  pdfUrl?: string
  pptUrl?: string
  currentPage?: number
}

const props = withDefaults(defineProps<Props>(), {
  contentType: 'pdf',
  fileName: '',
  pdfUrl: '',
  pptUrl: '',
  currentPage: 1
})

// Emits
const emit = defineEmits<{
  goHome: []
  annotationsLoaded: [annotations: any]
  qaUpdate: [subgraph: any]
  switchMode: [mode: 'pdf' | 'qa' | 'ppt']
}>()

// 隐藏演示功能 - 所有环境都隐藏
const hideDemoFeatures = true

// Refs
const pdfViewerRef = ref<any>(null)
const qaMessagesRef = ref<HTMLElement | null>(null)

// 问答相关状态
const qaInput = ref<string>('')
const qaSending = ref<boolean>(false)
const qaMessages = ref<Array<{ role: 'user' | 'assistant'; content: string }>>([])
const inputFocused = ref<boolean>(false)

// 方法
const handleGoHome = () => {
  emit('goHome')
}

const handleAnnotationsLoaded = (annotations: any) => {
  emit('annotationsLoaded', annotations)
}

const togglePptMode = () => {
  if (props.contentType === 'ppt') {
    // 当前是 PPT 模式,退出到 PDF 模式
    emit('switchMode', 'pdf')
  } else {
    // 当前不是 PPT 模式,进入 PPT 模式
    emit('switchMode', 'ppt')
  }
}

// 处理输入框失焦
const handleInputBlur = () => {
  // 延迟关闭,给气泡点击事件时间执行
  setTimeout(() => {
    inputFocused.value = false
  }, 200)
}

// 填充建议问题
const fillSuggestion = (question: string) => {
  qaInput.value = question
  // 填充后保持焦点
  inputFocused.value = true
}

const sendQaMessage = async () => {
  const question = qaInput.value.trim()
  if (!question || qaSending.value) return

  qaMessages.value.push({
    role: 'user',
    content: question
  })

  qaInput.value = ''
  qaSending.value = true

  try {
    const response = await fetch('/python/api/graph_qa/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    })
    const result = await response.json()
    console.log('📥 问答接口返回:', result)

    if (result.success && result.answer) {
      qaMessages.value.push({
        role: 'assistant',
        content: result.answer
      })

      // 如果返回了 subgraph，通知父组件更新图谱
      if (result.subgraph && result.subgraph.nodes && result.subgraph.edges) {
        console.log('📊 发现 subgraph 数据，通知父组件更新:', result.subgraph)
        emit('qaUpdate', result.subgraph)
      } else {
        console.log('⚠️ 没有 subgraph 数据')
      }
    } else {
      qaMessages.value.push({
        role: 'assistant',
        content: result.error || '抱歉，问答失败，请重试。'
      })
    }

    nextTick(() => {
      if (qaMessagesRef.value) {
        qaMessagesRef.value.scrollTop = qaMessagesRef.value.scrollHeight
      }
    })
  } catch (error) {
    console.error('❌ 问答失败:', error)
    message.error('问答失败')
  } finally {
    qaSending.value = false
  }
}

// 暴露方法给父组件
defineExpose({
  pdfViewerRef,
  sendQaMessage
})
</script>

<style lang="scss" scoped>
.content-viewer {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;

  .content-header {
    height: 48px;
    display: flex;
    align-items: center;
    padding: 0 16px;
    border-bottom: 1px solid #e8e8e8;
    background: #fafafa;

    .nav-buttons {
      display: flex;
      gap: 8px;
      margin-right: 16px;

      .nav-btn {
        display: flex;
        align-items: center;
        gap: 4px;
        color: #666;

        &:hover {
          color: #1890ff;
        }

        .icon {
          flex-shrink: 0;
        }
      }
    }

    .file-name {
      flex: 1;
      font-size: 14px;
      font-weight: 500;
      color: #333;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .mode-buttons {
      display: flex;
      gap: 8px;
      margin-left: 16px;
    }
  }

  .content-body {
    flex: 1;
    overflow: hidden;
    position: relative;

    // 内容区块样式
    .content-section {
      width: 100%;
      height: 100%;
      position: absolute;
      top: 0;
      left: 0;
    }

    // 问答容器样式
    .qa-container {
      display: flex;
      flex-direction: column;
      background: #fff;

      .qa-messages {
        flex: 1;
        overflow-y: auto;
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 12px;

        .qa-message {
          display: flex;

          .message-content {
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 8px;
            word-wrap: break-word;
            line-height: 1.6;
            font-size: 14px;
            white-space: pre-wrap;
          }

          &.user {
            justify-content: flex-end;

            .message-content {
              background: #1890ff;
              color: #fff;
              border-radius: 8px 8px 0 8px;
            }
          }

          &.assistant {
            justify-content: flex-start;

            .message-content {
              background: #f5f5f5;
              color: #333;
              border-radius: 8px 8px 8px 0;
            }
          }
        }
      }

      // 建议问题气泡
      .qa-suggestions {
        padding: 16px;
        display: flex;
        gap: 12px;
        flex-wrap: wrap;

        .suggestion-bubble {
          display: inline-flex;
          align-items: center;
          padding: 10px 16px;
          background: #e6f7ff;
          color: #1890ff;
          border: 1px solid #91d5ff;
          border-radius: 20px;
          font-size: 14px;
          cursor: pointer;
          transition: all 0.3s ease;
          box-shadow: 0 2px 8px rgba(24, 144, 255, 0.15);

          &:hover {
            background: #bae7ff;
            border-color: #69c0ff;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(24, 144, 255, 0.25);
          }

          &:active {
            transform: translateY(0);
          }

          span {
            user-select: none;
          }
        }
      }

      .qa-input {
        padding: 16px;
        border-top: 1px solid #e8e8e8;
        display: flex;
        gap: 8px;
        background: #fafafa;

        :deep(.ant-input) {
          flex: 1;
        }

        :deep(.ant-btn) {
          flex-shrink: 0;
        }
      }
    }

    // PPT 容器样式
    .ppt-container {
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
    }
  }
}
</style>
