<template>
  <div class="demo-review-container">
    <!-- 左侧悬浮图标与菜单（与 ComplianceReview 一致的交互） -->
    <div class="left-side-actions">
      <a-popover placement="right" trigger="hover">
        <template #content>
          <div class="side-menu">
            <a-button type="text" class="side-menu-item" @click="goToReview">文件审查</a-button>
            <a-button type="text" class="side-menu-item" @click="goToDemo">演示文件查看</a-button>
          </div>
        </template>
        <a-button class="side-icon" shape="circle">AI</a-button>
      </a-popover>
    </div>

    <div class="header">
      <div class="title">演示文件查看</div>
      <div class="actions">
        <a-button type="primary" @click="loadDemo">加载演示文件</a-button>
      </div>
    </div>

    <div class="content">
      <PdfViewer
        v-if="pdfUrl"
        :url="pdfUrl"
        :page="currentPage"
        :annotations="highlightRects"
      />
      <BaseEmpty v-else description="暂无演示文档，请点击上方按钮加载" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import PdfViewer from '@/views/pdf/PdfViewer.vue'
import BaseEmpty from '@/components/BaseEmpty/index.vue'
import config from '../../config'

defineOptions({ name: 'DemoReview' })

const router = useRouter()

// PDF相关数据（简化版）
const pdfUrl = ref('')
const currentPage = ref(1)
const highlightRects = ref<any[]>([])

const isDev = import.meta.env.DEV === true || import.meta.env.MODE === 'dev'

// 路由跳转
const goToReview = () => router.push({ name: 'ComplianceReview' })
const goToDemo = () => router.push({ name: 'DemoReview' })

// 加载演示任务（从 public 读取与 ComplianceReview 同结构的演示文件）
const demoTaskId = 'demo-task'
const loadDemo = async () => {
  currentPage.value = 1
  highlightRects.value.splice(0, highlightRects.value.length)

  // PDF 路径
  pdfUrl.value = isDev
    ? '/task/' + demoTaskId + '/' + demoTaskId + '_highlighted.pdf'
    : (config.env.VITE_APP_PUBLIC_URL + '/task/' + demoTaskId + '/' + demoTaskId + '_highlighted.pdf')

  // 可选：加载演示高亮 JSON（若存在）
  try {
    const annUrl = isDev
      ? '/task/' + demoTaskId + '/' + demoTaskId + '_pdf_annotations.json'
      : (config.env.VITE_APP_PUBLIC_URL + '/task/' + demoTaskId + '/' + demoTaskId + '_pdf_annotations.json')
    const resp = await fetch(annUrl)
    if (resp.ok) {
      const json = await resp.json()
      // 如果结构为 { annotations: [...] }，可以做最小转换以便 PdfViewer 使用
      const anns = json.annotations || []
      // 这里直接赋空数组或简单数据，具体结构由 PdfViewer 支持情况而定
      // highlightRects.splice(0, highlightRects.length, ...anns)
      console.log('演示批注加载完成', anns.length)
    }
  } catch (e) {
    console.warn('演示批注未找到', e)
  }

  await nextTick()
}
</script>

<style scoped>
.demo-review-container {
  color: #111827;
  height: 100vh;
  display: flex;
  flex-direction: column;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--line-2);
}
.title {
  font-size: 16px;
  font-weight: 600;
}
.content {
  flex: 1;
  min-height: 0;
  display: flex;
  padding: 8px;
}
.left-side-actions {
  position: fixed;
  left: 12px;
  top: 140px;
  z-index: 1000;
}
.side-icon {
  width: 36px;
  height: 36px;
  border: 1px solid var(--line-3);
  font-weight: 600;
}
.side-menu {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.side-menu-item {
  text-align: left;
  padding: 0 8px;
}
</style>