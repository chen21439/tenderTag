<template>
  <div class="pdf-viewer-container">
    <div class="toolbar">
      <a-space>
        <a-upload
          :before-upload="handleFileUpload"
          :show-upload-list="false"
          accept=".pdf"
        >
          <a-button type="primary">
            <UploadOutlined /> 选择 PDF 文件
          </a-button>
        </a-upload>

        <a-divider type="vertical" />

        <a-button @click="previousPage" :disabled="pageNum <= 1">
          <LeftOutlined /> 上一页
        </a-button>

        <span class="page-info">
          <a-input-number
            v-model:value="pageNum"
            :min="1"
            :max="numPages"
            @change="renderPage"
            style="width: 80px"
          />
          / {{ numPages }}
        </span>

        <a-button @click="nextPage" :disabled="pageNum >= numPages">
          下一页 <RightOutlined />
        </a-button>

        <a-divider type="vertical" />

        <a-button @click="zoomOut" :disabled="scale <= 0.5">
          <ZoomOutOutlined />
        </a-button>

        <span class="zoom-info">{{ Math.round(scale * 100) }}%</span>

        <a-button @click="zoomIn" :disabled="scale >= 3">
          <ZoomInOutlined />
        </a-button>

        <a-button @click="resetZoom">
          <SyncOutlined /> 重置
        </a-button>

        <a-divider type="vertical" />

        <a-button @click="toggleAnnotationPanel">
          <CommentOutlined /> 批注列表 ({{ annotations.length }})
        </a-button>

        <a-button @click="toggleAnnotationsInPdf" :type="showAnnotationsInPdf ? 'primary' : 'default'">
          <EyeOutlined v-if="showAnnotationsInPdf" />
          <EyeInvisibleOutlined v-else />
          {{ showAnnotationsInPdf ? '隐藏批注' : '显示批注' }}
        </a-button>
      </a-space>
    </div>

    <div class="main-content">
      <div class="pdf-content" ref="pdfContainer">
        <div class="canvas-wrapper" v-if="pdfDoc">
          <canvas ref="pdfCanvas" class="pdf-canvas"></canvas>
          <canvas ref="highlightCanvas" class="highlight-layer"></canvas>
        </div>
        <div v-if="loading" class="loading">
          <a-spin size="large" tip="加载中..." />
        </div>
        <div v-if="error" class="error">
          <a-alert :message="error" type="error" show-icon />
        </div>
        <div v-if="!pdfDoc && !loading && !error" class="empty">
          <a-empty description="请选择一个 PDF 文件">
            <template #image>
              <FileOutlined style="font-size: 48px; color: #bfbfbf;" />
            </template>
          </a-empty>
        </div>
      </div>

      <!-- 右侧批注面板 -->
      <div class="annotation-panel" :class="{ collapsed: !showAnnotationPanel }">
        <div class="panel-header">
          <h3>
            <CommentOutlined /> 批注列表
            <a-badge :count="annotations.length" :number-style="{ backgroundColor: '#52c41a' }" />
          </h3>
          <a-button type="text" @click="toggleAnnotationPanel">
            <CloseOutlined />
          </a-button>
        </div>

        <div class="panel-content">
          <a-empty v-if="annotations.length === 0" description="暂无批注" />

          <div v-else class="annotation-list">
            <div
              v-for="annotation in annotations"
              :key="annotation.id"
              class="annotation-item"
              :class="{ active: selectedAnnotationId === annotation.id }"
              @click="goToAnnotation(annotation)"
            >
              <div class="annotation-header">
                <a-tag :color="getAnnotationColor(annotation.subtype)">
                  {{ getAnnotationTypeName(annotation.subtype) }}
                </a-tag>
                <span class="page-number">第 {{ annotation.pageNum }} 页</span>
              </div>

              <div class="annotation-content">
                <p v-if="annotation.contents" class="contents">{{ annotation.contents }}</p>
                <p v-if="annotation.title" class="author">作者: {{ annotation.title }}</p>
                <p v-if="annotation.modificationDate" class="date">
                  {{ formatDate(annotation.modificationDate) }}
                </p>
              </div>

              <div class="annotation-rect" v-if="annotation.rect">
                <a-tooltip title="批注位置坐标">
                  <EnvironmentOutlined style="margin-right: 4px;" />
                  {{ formatRect(annotation.rect) }}
                </a-tooltip>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, shallowRef } from 'vue'
import * as pdfjsLib from 'pdfjs-dist'
import pdfjsWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url'
import {
  UploadOutlined,
  LeftOutlined,
  RightOutlined,
  ZoomInOutlined,
  ZoomOutOutlined,
  SyncOutlined,
  FileOutlined,
  CommentOutlined,
  CloseOutlined,
  EnvironmentOutlined,
  EyeOutlined,
  EyeInvisibleOutlined
} from '@ant-design/icons-vue'

// 配置 PDF.js worker（使用本地文件）
pdfjsLib.GlobalWorkerOptions.workerSrc = pdfjsWorker

// 响应式数据
const pdfDoc = shallowRef(null) // 使用 shallowRef 避免深度响应式代理
const pageNum = ref(1)
const numPages = ref(0)
const scale = ref(1.5)
const loading = ref(false)
const error = ref(null)
const pdfCanvas = ref(null)
const pdfContainer = ref(null)
const annotations = ref([]) // 批注列表
const showAnnotationPanel = ref(true) // 显示批注面板
const selectedAnnotationId = ref(null) // 当前选中的批注ID
const showAnnotationsInPdf = ref(true) // 是否在 PDF 中显示批注
const highlightCanvas = ref(null) // 高亮图层 canvas
let flickerAnimationId = null // 闪烁动画 ID

// 提取 PDF 所有批注
const extractAnnotations = async () => {
  if (!pdfDoc.value) return

  const allAnnotations = []
  let annotationIdCounter = 0

  console.log(`
═══════════════════════════════════════════════════════
    开始提取 PDF 全量批注数据
    PDF 总页数: ${numPages.value}
═══════════════════════════════════════════════════════
`)

  try {
    for (let pageIndex = 1; pageIndex <= numPages.value; pageIndex++) {
      const page = await pdfDoc.value.getPage(pageIndex)
      const annotationsData = await page.getAnnotations()

      console.log(`📄 第 ${pageIndex} 页 - 找到 ${annotationsData.length} 个批注`)

      annotationsData.forEach((annotation, idx) => {
        const annotationObj = {
          id: `annotation-${annotationIdCounter++}`, // 添加唯一ID
          pageNum: pageIndex,
          subtype: annotation.subtype,
          name: annotation.name, // Name 字段
          rect: annotation.rect,
          quadPoints: annotation.quadPoints, // 高亮区域的四边形坐标
          contents: annotation.contents || '',
          title: annotation.title || '',
          modificationDate: annotation.modificationDate || '',
          creationDate: annotation.creationDate || '',
          color: annotation.color,
          opacity: annotation.opacity,
          borderStyle: annotation.borderStyle,
          pdfAnnotationId: annotation.id, // PDF原始ID
          原始数据: annotation // 完整的原始数据
        }

        console.log(`  ✓ 批注 #${idx + 1}:`, {
          页码: pageIndex,
          类型: annotationObj.subtype,
          Name字段: annotationObj.name,
          内容: annotationObj.contents,
          标题: annotationObj.title,
          坐标: annotationObj.rect,
          颜色: annotationObj.color,
          PDF原始ID: annotationObj.pdfAnnotationId,
          创建时间: annotationObj.creationDate,
          修改时间: annotationObj.modificationDate
        })

        allAnnotations.push(annotationObj)
      })
    }

    annotations.value = allAnnotations

    console.log(`
═══════════════════════════════════════════════════════
    ✅ 批注提取完成
    总批注数: ${allAnnotations.length} 条
═══════════════════════════════════════════════════════
`)

    // 打印全量批注汇总表格
    if (allAnnotations.length > 0) {
      console.log('\n📊 批注汇总表格:')
      console.table(allAnnotations.map(a => ({
        ID: a.id,
        页码: a.pageNum,
        类型: a.subtype,
        Name: a.name,
        标题: a.title,
        内容: a.contents?.substring(0, 30) + (a.contents?.length > 30 ? '...' : ''),
        修改时间: formatDate(a.modificationDate)
      })))

      // 按页码统计批注数量
      const pageStats = {}
      allAnnotations.forEach(a => {
        pageStats[a.pageNum] = (pageStats[a.pageNum] || 0) + 1
      })
      console.log('\n📈 各页面批注统计:')
      console.table(pageStats)

      // 按类型统计批注数量
      const typeStats = {}
      allAnnotations.forEach(a => {
        typeStats[a.subtype] = (typeStats[a.subtype] || 0) + 1
      })
      console.log('\n📊 批注类型统计:')
      console.table(typeStats)
    } else {
      console.log('⚠️  未找到任何批注')
    }

    return allAnnotations
  } catch (err) {
    console.error('❌ 提取批注失败:', err)
    return []
  }
}

// 从 URL 加载 PDF 文件
const loadPdfFromUrl = async (url) => {
  try {
    loading.value = true
    error.value = null

    console.log('开始加载 PDF:', url)

    // 使用 fetch 获取 PDF 数据，避免 URL.parse 兼容性问题
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    const arrayBuffer = await response.arrayBuffer()

    const loadingTask = pdfjsLib.getDocument({ data: arrayBuffer })
    pdfDoc.value = await loadingTask.promise
    numPages.value = pdfDoc.value.numPages
    pageNum.value = 1

    console.log('PDF 加载成功, 总页数:', numPages.value)

    // 提取批注
    console.log('🔍 准备提取批注...')
    const result = await extractAnnotations()
    console.log('🔍 批注提取完成，返回结果:', result)

    // 等待 DOM 更新后再渲染
    await nextTick()
    await renderPage()
  } catch (err) {
    error.value = `加载 PDF 失败: ${err.message}`
    console.error('加载 PDF 错误:', err)
  } finally {
    loading.value = false
  }
}

// 加载 PDF 文件
const loadPdf = async (file) => {
  try {
    loading.value = true
    error.value = null

    const arrayBuffer = await file.arrayBuffer()
    const loadingTask = pdfjsLib.getDocument({ data: arrayBuffer })
    pdfDoc.value = await loadingTask.promise
    numPages.value = pdfDoc.value.numPages
    pageNum.value = 1

    // 提取批注
    await extractAnnotations()

    // 等待 DOM 更新后再渲染
    await nextTick()
    await renderPage()
  } catch (err) {
    error.value = `加载 PDF 失败: ${err.message}`
    console.error('加载 PDF 错误:', err)
  } finally {
    loading.value = false
  }
}

// 渲染指定页面
const renderPage = async () => {
  if (!pdfDoc.value || !pdfCanvas.value) return

  try {
    const page = await pdfDoc.value.getPage(pageNum.value)
    const viewport = page.getViewport({ scale: scale.value })

    const canvas = pdfCanvas.value
    const context = canvas.getContext('2d')

    canvas.height = viewport.height
    canvas.width = viewport.width

    // 同步高亮 canvas 的尺寸
    if (highlightCanvas.value) {
      highlightCanvas.value.height = viewport.height
      highlightCanvas.value.width = viewport.width
    }

    const renderContext = {
      canvasContext: context,
      viewport: viewport,
      // 控制是否渲染批注
      annotationMode: showAnnotationsInPdf.value ? 2 : 0  // 2=ENABLE, 1=ENABLE_FORMS, 0=DISABLE
    }

    await page.render(renderContext).promise
  } catch (err) {
    error.value = `渲染页面失败: ${err.message}`
    console.error('渲染错误:', err)
  }
}

// 文件上传处理
const handleFileUpload = (file) => {
  if (file.type !== 'application/pdf') {
    error.value = '请选择 PDF 文件'
    return false
  }
  loadPdf(file)
  return false
}

// 页面导航
const previousPage = () => {
  if (pageNum.value > 1) {
    pageNum.value--
    renderPage()
  }
}

const nextPage = () => {
  if (pageNum.value < numPages.value) {
    pageNum.value++
    renderPage()
  }
}

// 缩放控制
const zoomIn = () => {
  if (scale.value < 3) {
    scale.value = Math.min(scale.value + 0.25, 3)
    renderPage()
  }
}

const zoomOut = () => {
  if (scale.value > 0.5) {
    scale.value = Math.max(scale.value - 0.25, 0.5)
    renderPage()
  }
}

const resetZoom = () => {
  scale.value = 1.5
  renderPage()
}

// 批注面板控制
const toggleAnnotationPanel = () => {
  showAnnotationPanel.value = !showAnnotationPanel.value
}

// 切换 PDF 中批注的显示/隐藏
const toggleAnnotationsInPdf = () => {
  showAnnotationsInPdf.value = !showAnnotationsInPdf.value
  renderPage() // 重新渲染当前页面
}

// 绘制批注闪烁效果
const flashAnnotation = async (annotation) => {
  if (!highlightCanvas.value || !pdfDoc.value) return

  // 清除之前的动画
  if (flickerAnimationId) {
    clearTimeout(flickerAnimationId)
    flickerAnimationId = null
  }

  // 等待页面渲染完成
  await nextTick()

  try {
    const page = await pdfDoc.value.getPage(annotation.pageNum)
    const viewport = page.getViewport({ scale: scale.value })
    const ctx = highlightCanvas.value.getContext('2d')

    // 转换 PDF 坐标到 Canvas 坐标
    const convertRect = (rect) => {
      if (!rect || rect.length !== 4) return null

      const [x1, y1, x2, y2] = rect
      // PDF.js viewport 提供坐标转换方法
      const [canvasX1, canvasY1] = viewport.convertToViewportPoint(x1, y1)
      const [canvasX2, canvasY2] = viewport.convertToViewportPoint(x2, y2)

      return {
        x: Math.min(canvasX1, canvasX2),
        y: Math.min(canvasY1, canvasY2),
        width: Math.abs(canvasX2 - canvasX1),
        height: Math.abs(canvasY2 - canvasY1)
      }
    }

    const rectCoords = convertRect(annotation.rect)
    if (!rectCoords) return

    // 闪烁动画
    let flickerCount = 0
    const maxFlickers = 6 // 闪烁 3 次（显示/隐藏算 2 次）

    const flicker = () => {
      ctx.clearRect(0, 0, highlightCanvas.value.width, highlightCanvas.value.height)

      // 奇数次显示高亮
      if (flickerCount % 2 === 0) {
        // 绘制边框
        ctx.strokeStyle = 'rgba(255, 68, 68, 0.9)'
        ctx.lineWidth = 4
        ctx.strokeRect(rectCoords.x, rectCoords.y, rectCoords.width, rectCoords.height)

        // 绘制半透明填充
        ctx.fillStyle = 'rgba(255, 68, 68, 0.15)'
        ctx.fillRect(rectCoords.x, rectCoords.y, rectCoords.width, rectCoords.height)
      }

      flickerCount++
      if (flickerCount < maxFlickers) {
        flickerAnimationId = setTimeout(flicker, 300) // 每 300ms 闪烁一次
      } else {
        // 动画结束，清除画布
        ctx.clearRect(0, 0, highlightCanvas.value.width, highlightCanvas.value.height)
        flickerAnimationId = null
      }
    }

    flicker()
  } catch (err) {
    console.error('闪烁动画错误:', err)
  }
}

// 跳转到批注所在页面
const goToAnnotation = async (annotation) => {
  selectedAnnotationId.value = annotation.id // 设置选中的批注ID

  // 如果是同一页，直接闪烁
  if (pageNum.value === annotation.pageNum) {
    await flashAnnotation(annotation)
  } else {
    // 跳转到新页面
    pageNum.value = annotation.pageNum
    await renderPage()
    // 等待渲染完成后再闪烁
    await nextTick()
    await flashAnnotation(annotation)
  }
}

// 获取批注类型名称
const getAnnotationTypeName = (subtype) => {
  const typeMap = {
    'Highlight': '高亮',
    'Underline': '下划线',
    'StrikeOut': '删除线',
    'Squiggly': '波浪线',
    'Text': '文本注释',
    'FreeText': '自由文本',
    'Line': '线条',
    'Square': '矩形',
    'Circle': '圆形',
    'Polygon': '多边形',
    'PolyLine': '折线',
    'Ink': '墨迹',
    'Stamp': '印章',
    'Link': '链接'
  }
  return typeMap[subtype] || subtype
}

// 获取批注类型颜色
const getAnnotationColor = (subtype) => {
  const colorMap = {
    'Highlight': 'gold',
    'Underline': 'blue',
    'StrikeOut': 'red',
    'Squiggly': 'orange',
    'Text': 'green',
    'FreeText': 'cyan',
    'Line': 'purple',
    'Square': 'magenta',
    'Circle': 'geekblue',
    'Ink': 'volcano',
    'Stamp': 'lime',
    'Link': 'blue'
  }
  return colorMap[subtype] || 'default'
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return ''

  // PDF 日期格式: D:YYYYMMDDHHmmSSOHH'mm'
  const match = dateStr.match(/D:(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})/)
  if (match) {
    const [, year, month, day, hour, minute, second] = match
    return `${year}-${month}-${day} ${hour}:${minute}:${second}`
  }

  return dateStr
}

// 格式化坐标
const formatRect = (rect) => {
  if (!rect || rect.length !== 4) return ''
  const [x1, y1, x2, y2] = rect.map(v => Math.round(v))
  return `(${x1}, ${y1}) - (${x2}, ${y2})`
}

// 键盘快捷键
const handleKeydown = (e) => {
  if (e.key === 'ArrowLeft') previousPage()
  if (e.key === 'ArrowRight') nextPage()
  if (e.key === '+' || e.key === '=') zoomIn()
  if (e.key === '-') zoomOut()
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
  // 默认加载指定的 PDF 文件
  const defaultPdfUrl = 'http://localhost:3000/api/pdf/1978018096320905217_highlighted.pdf'
  loadPdfFromUrl(defaultPdfUrl)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.pdf-viewer-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f0f2f5;
}

.toolbar {
  padding: 16px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.page-info,
.zoom-info {
  margin: 0 8px;
  font-size: 14px;
  color: #595959;
  display: inline-flex;
  align-items: center;
}

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.pdf-content {
  flex: 1;
  overflow: auto;
  padding: 20px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

.canvas-wrapper {
  position: relative;
  display: inline-block;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.pdf-canvas {
  max-width: 100%;
  height: auto;
  display: block;
  background: white;
  position: relative;
  z-index: 0;
}

.highlight-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none; /* 不阻止鼠标事件 */
  z-index: 1; /* 在 PDF canvas 之上 */
}

.loading,
.error,
.empty {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  padding: 40px;
}

.error {
  max-width: 600px;
}

/* 批注面板样式 */
.annotation-panel {
  width: 360px;
  background: white;
  border-left: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
}

.annotation-panel.collapsed {
  width: 0;
  overflow: hidden;
  border: none;
}

.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.annotation-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.annotation-item {
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
}

.annotation-item:hover {
  background: #f0f0f0;
  border-color: #1890ff;
  transform: translateX(-2px);
  box-shadow: 2px 0 8px rgba(24, 144, 255, 0.1);
}

.annotation-item.active {
  background: #e6f7ff;
  border-color: #1890ff;
}

.annotation-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.page-number {
  font-size: 12px;
  color: #8c8c8c;
  font-weight: 500;
}

.annotation-content {
  margin-top: 8px;
}

.annotation-content p {
  margin: 4px 0;
  font-size: 13px;
  line-height: 1.5;
}

.annotation-content .contents {
  color: #262626;
  font-weight: 500;
  white-space: pre-wrap;
  word-break: break-word;
}

.annotation-content .author {
  color: #595959;
  font-size: 12px;
}

.annotation-content .date {
  color: #8c8c8c;
  font-size: 12px;
}

.annotation-rect {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #e8e8e8;
  font-size: 11px;
  color: #8c8c8c;
  font-family: monospace;
}

/* 滚动条美化 */
.panel-content::-webkit-scrollbar {
  width: 6px;
}

.panel-content::-webkit-scrollbar-track {
  background: #f0f0f0;
  border-radius: 3px;
}

.panel-content::-webkit-scrollbar-thumb {
  background: #bfbfbf;
  border-radius: 3px;
}

.panel-content::-webkit-scrollbar-thumb:hover {
  background: #8c8c8c;
}
</style>
