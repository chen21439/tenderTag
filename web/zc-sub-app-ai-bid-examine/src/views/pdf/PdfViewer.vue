<template>
  <div class="pdf-viewer-container">
    <div class="toolbar">
      <a-space>

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
      </a-space>
    </div>

    <div class="main-content">
      <div class="pdf-content" ref="pdfContainer">
        <!-- 分页模式：单页显示 -->
        <div class="canvas-wrapper" v-if="pdfDoc && !isAllPagesMode" ref="canvasWrapper">
          <canvas ref="pdfCanvas" class="pdf-canvas"></canvas>
          <!-- 高亮层 -->
          <canvas ref="highlightCanvas" class="highlight-canvas"></canvas>
        </div>

        <!-- 全量模式：所有页面 -->
        <div class="all-pages-wrapper" v-if="pdfDoc && isAllPagesMode">
          <div
            v-for="page in numPages"
            :key="page"
            class="page-container"
            :data-page="page"
          >
            <div class="page-number">第 {{ page }} 页</div>
            <div class="canvas-container">
              <canvas :ref="el => { if (el) allPagesCanvasRefs[page - 1] = el }"></canvas>
              <!-- 每页都有独立的高亮层 -->
              <canvas :ref="el => { if (el) allPagesHighlightRefs[page - 1] = el }" class="highlight-canvas"></canvas>
            </div>
          </div>
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

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick, shallowRef, watch } from 'vue'
import * as pdfjsLib from 'pdfjs-dist'
import pdfjsWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url'
import config from '@/config'
import {
  LeftOutlined,
  RightOutlined,
  ZoomInOutlined,
  ZoomOutOutlined,
  SyncOutlined,
  FileOutlined
} from '@ant-design/icons-vue'

// 组件 Props
const props = defineProps({
  url: {
    type: String,
    default: ''
  },
  page: {
    type: Number,
    default: 1
  }
})

// 组件 Emits
const emit = defineEmits(['annotationsLoaded'])

// 存储当前高亮的批注位置
const highlightAnnotations = ref<any[]>([])

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
const canvasWrapper = ref(null)
const showAnnotationsInPdf = ref(true) // 是否在 PDF 中显示批注
const isAllPagesMode = ref(false) // 是否全量显示模式
const allPagesCanvasRefs = ref<HTMLCanvasElement[]>([]) // 全量模式下的所有canvas引用
const highlightCanvas = ref<HTMLCanvasElement | null>(null) // 分页模式的高亮层
const allPagesHighlightRefs = ref<HTMLCanvasElement[]>([]) // 全量模式下的所有高亮层canvas
let currentAnimationId: number | null = null // 当前动画ID，用于取消
let currentRenderTask: any = null // 当前渲染任务，用于取消（分页模式）
let allPagesRenderTasks: any[] = [] // 所有页面渲染任务（全量模式）

// 提取 PDF 所有批注
const extractAllAnnotations = async () => {
  if (!pdfDoc.value) return []

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
          pageNum: pageIndex,
          subtype: annotationObj.subtype,
          name: annotationObj.name,
          contents: annotationObj.contents,
          title: annotationObj.title,
          rect: annotationObj.rect,
          color: annotationObj.color,
          pdfAnnotationId: annotationObj.pdfAnnotationId,
          creationDate: annotationObj.creationDate,
          modificationDate: annotationObj.modificationDate,
          原始数据: annotationObj.原始数据
        })

        allAnnotations.push(annotationObj)
      })
    }

    console.log(`
═══════════════════════════════════════════════════════
    ✅ 批注提取完成
    总批注数: ${allAnnotations.length} 条
═══════════════════════════════════════════════════════
`)

    // 打印全量批注汇总表格
    if (allAnnotations.length > 0) {
      console.log('\n📊 All Annotations Table:')
      console.table(allAnnotations.map(a => ({
        id: a.id,
        pageNum: a.pageNum,
        subtype: a.subtype,
        name: a.name,
        title: a.title,
        contents: a.contents?.substring(0, 30) + (a.contents?.length > 30 ? '...' : ''),
        modificationDate: a.modificationDate
      })))

      // 按页码统计批注数量
      const pageStats = {}
      allAnnotations.forEach(a => {
        pageStats[a.pageNum] = (pageStats[a.pageNum] || 0) + 1
      })
      console.log('\n📈 Annotations by Page:')
      console.table(pageStats)

      // 按类型统计批注数量
      const typeStats = {}
      allAnnotations.forEach(a => {
        typeStats[a.subtype] = (typeStats[a.subtype] || 0) + 1
      })
      console.log('\n📊 Annotations by Type:')
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

    // 使用 fetch 获取数据，然后用 typedarray 方式加载（避免 URL.parse 兼容性问题）
    const response = await fetch(url, {
      mode: 'cors',
      credentials: 'omit'
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const arrayBuffer = await response.arrayBuffer()
    const typedArray = new Uint8Array(arrayBuffer)

    const loadingTask = pdfjsLib.getDocument({
      data: typedArray
    })

    pdfDoc.value = await loadingTask.promise
    numPages.value = pdfDoc.value.numPages
    pageNum.value = props.page || 1

    console.log('PDF 加载成功, 总页数:', numPages.value)

    // 提取全量批注
    console.log('🔍 准备提取批注...')
    const allAnnotations = await extractAllAnnotations()
    console.log('🔍 批注提取完成，返回结果:', allAnnotations)

    // 触发事件，传递批注数据给父组件
    emit('annotationsLoaded', allAnnotations)

    // 等待 DOM 更新后再渲染（根据当前模式选择渲染方式）
    await nextTick()
    if (isAllPagesMode.value) {
      await renderAllPages()
    } else {
      await renderPage()
    }
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

  // 取消之前的渲染任务
  if (currentRenderTask) {
    try {
      currentRenderTask.cancel()
      console.log('取消之前的渲染任务')
    } catch (e) {
      // 忽略取消错误
    }
    currentRenderTask = null
  }

  try {
    const page = await pdfDoc.value.getPage(pageNum.value)
    const viewport = page.getViewport({ scale: scale.value })

    const canvas = pdfCanvas.value
    const context = canvas.getContext('2d')

    canvas.height = viewport.height
    canvas.width = viewport.width

    const renderContext = {
      canvasContext: context,
      viewport: viewport,
      // 控制是否渲染批注
      annotationMode: showAnnotationsInPdf.value ? 2 : 0  // 2=ENABLE, 0=DISABLE
    }

    // 保存渲染任务引用
    currentRenderTask = page.render(renderContext)
    await currentRenderTask.promise

    // 渲染完成后清空引用
    currentRenderTask = null

    // 读取批注信息（用于调试）
    if (showAnnotationsInPdf.value) {
      await logAnnotations(page)
    }
  } catch (err) {
    // 忽略取消错误
    if (err.name === 'RenderingCancelledException') {
      console.log('渲染被取消')
      return
    }
    error.value = `渲染页面失败: ${err.message}`
    console.error('渲染错误:', err)
  }
}

// 读取批注信息
const logAnnotations = async (page) => {
  try {
    const annotations = await page.getAnnotations()

    if (annotations && annotations.length > 0) {
      console.log(`页面 ${pageNum.value} 的批注信息:`)
      annotations.forEach((annotation, index) => {
        console.log(`批注 ${index + 1}:`, {
          id: annotation.id,
          subtype: annotation.subtype,
          name: annotation.name,  // Name 字段
          contents: annotation.contents,
          title: annotation.title,
          rect: annotation.rect,
          color: annotation.color,
          原始数据: annotation
        })
      })
    }
  } catch (err) {
    console.error('读取批注失败:', err)
  }
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

// 切换视图模式
const toggleViewMode = async () => {
  isAllPagesMode.value = !isAllPagesMode.value
  console.log('切换视图模式:', isAllPagesMode.value ? '全量显示' : '分页显示')

  if (isAllPagesMode.value) {
    // 切换到全量模式，渲染所有页面
    await nextTick()
    await renderAllPages()
  } else {
    // 切换到分页模式，渲染当前页
    await nextTick()
    await renderPage()
  }
}

// 渲染所有页面（全量模式）
const renderAllPages = async () => {
  if (!pdfDoc.value) return

  // 取消之前的所有渲染任务
  if (allPagesRenderTasks.length > 0) {
    console.log('取消之前的所有页面渲染任务')
    allPagesRenderTasks.forEach(task => {
      try {
        task.cancel()
      } catch (e) {
        // 忽略取消错误
      }
    })
    allPagesRenderTasks = []
  }

  console.log('开始渲染所有页面，共', numPages.value, '页')

  for (let i = 1; i <= numPages.value; i++) {
    try {
      const page = await pdfDoc.value.getPage(i)
      const viewport = page.getViewport({ scale: scale.value })

      const canvas = allPagesCanvasRefs.value[i - 1]
      if (!canvas) {
        console.warn('Canvas not found for page', i)
        continue
      }

      const context = canvas.getContext('2d')
      canvas.height = viewport.height
      canvas.width = viewport.width

      const renderContext = {
        canvasContext: context,
        viewport: viewport,
        annotationMode: showAnnotationsInPdf.value ? 2 : 0
      }

      // 保存渲染任务
      const renderTask = page.render(renderContext)
      allPagesRenderTasks.push(renderTask)
      await renderTask.promise
    } catch (err) {
      // 忽略取消错误
      if (err.name === 'RenderingCancelledException') {
        console.log(`页面 ${i} 渲染被取消`)
        continue
      }
      console.error('渲染第', i, '页失败:', err)
    }
  }

  // 清空渲染任务列表
  allPagesRenderTasks = []
  console.log('所有页面渲染完成')
}

// 缩放控制
const zoomIn = () => {
  if (scale.value < 3) {
    scale.value = Math.min(scale.value + 0.25, 3)
    if (isAllPagesMode.value) {
      renderAllPages()
    } else {
      renderPage()
    }
  }
}

const zoomOut = () => {
  if (scale.value > 0.5) {
    scale.value = Math.max(scale.value - 0.25, 0.5)
    if (isAllPagesMode.value) {
      renderAllPages()
    } else {
      renderPage()
    }
  }
}

const resetZoom = () => {
  scale.value = 1.5
  if (isAllPagesMode.value) {
    renderAllPages()
  } else {
    renderPage()
  }
}

// 切换 PDF 中批注的显示/隐藏（checkbox 变化时触发）
const handleAnnotationsToggle = () => {
  if (isAllPagesMode.value) {
    renderAllPages()
  } else {
    renderPage()
  }
}

// 跳转到指定的批注位置（暴露给父组件）
const scrollToAnnotation = async (annotationData: any) => {
  if (!annotationData || !pdfDoc.value) return

  let { pageNum: targetPageNum, rect, quadPoints, needsConversion } = annotationData

  console.log('📍 scrollToAnnotation 调用:', {
    targetPageNum,
    rect,
    needsConversion,
    currentPage: pageNum.value,
    isAllPagesMode: isAllPagesMode.value
  })

  if (!targetPageNum) {
    console.warn('目标页码为空，无法跳转')
    return
  }

  // 如果标记了需要坐标转换（屏幕坐标 → PDF坐标）
  if (needsConversion && rect && rect.length === 4) {
    try {
      const page = await pdfDoc.value.getPage(targetPageNum)
      const viewport = page.getViewport({ scale: 1.0 })
      const pageHeight = viewport.height

      console.log('🔄 坐标转换: 屏幕坐标 → PDF坐标')
      console.log('  原始坐标 (屏幕):', rect)
      console.log('  页面高度:', pageHeight)

      // 屏幕坐标转PDF坐标
      const pdfRect = [
        rect[0],              // x1 不变
        pageHeight - rect[3], // y1 = pageHeight - screenY2
        rect[2],              // x2 不变
        pageHeight - rect[1]  // y2 = pageHeight - screenY1
      ]

      console.log('  转换后 (PDF):', pdfRect)

      // 更新坐标
      rect = pdfRect
      annotationData.rect = pdfRect

      // 同时更新 quadPoints（支持多个矩形）
      if (quadPoints && quadPoints.length >= 8 && quadPoints.length % 8 === 0) {
        const convertedQuadPoints: number[] = []

        // 每8个点代表一个矩形，分别转换
        for (let i = 0; i < quadPoints.length; i += 8) {
          const boxQuadPoints = quadPoints.slice(i, i + 8)
          // 提取原始屏幕坐标的 box
          const screenX1 = boxQuadPoints[0]
          const screenY1 = boxQuadPoints[1]
          const screenX2 = boxQuadPoints[4]
          const screenY2 = boxQuadPoints[5]

          // 转换为 PDF 坐标
          const pdfY1 = pageHeight - screenY2
          const pdfY2 = pageHeight - screenY1

          // 添加转换后的 quadPoints
          convertedQuadPoints.push(
            screenX1, pdfY2,  // 左上
            screenX2, pdfY2,  // 右上
            screenX2, pdfY1,  // 右下
            screenX1, pdfY1   // 左下
          )
        }

        annotationData.quadPoints = convertedQuadPoints
        console.log('🔄 转换了', quadPoints.length / 8, '个矩形的坐标')
      }
    } catch (error) {
      console.error('❌ 坐标转换失败:', error)
    }
  }

  // 全量模式：平滑滚动到对应页面
  if (isAllPagesMode.value) {
    await nextTick()
    const container = pdfContainer.value
    if (!container) return

    // 找到目标页面的容器元素
    const targetPageContainer = container.querySelector(`[data-page="${targetPageNum}"]`) as HTMLElement
    if (targetPageContainer) {
      // 获取目标位置
      const containerRect = container.getBoundingClientRect()
      const targetRect = targetPageContainer.getBoundingClientRect()

      // 计算需要滚动的距离（目标位置相对于容器顶部，留出一些边距）
      const scrollOffset = targetRect.top - containerRect.top + container.scrollTop - 80

      // 使用平滑滚动
      container.scrollTo({
        top: scrollOffset,
        behavior: 'smooth'
      })

      console.log('全量模式：平滑滚动到第', targetPageNum, '页', {
        from: container.scrollTop,
        to: scrollOffset,
        distance: Math.abs(scrollOffset - container.scrollTop)
      })
    } else {
      console.warn('未找到第', targetPageNum, '页的容器')
    }

    // 等待滚动完成后再绘制高亮（让用户先看到目标位置）
    // 平滑滚动大约需要300-500ms，我们延迟600ms再显示高亮
    setTimeout(() => {
      drawHighlightAnimation(targetPageNum, annotationData)
    }, 600)
    return
  }

  // 分页模式：切换到目标页面
  if (targetPageNum !== pageNum.value) {
    pageNum.value = targetPageNum
    await nextTick()
    await renderPage()
  }

  // 滚动到批注位置（分页模式）
  if (rect && rect.length === 4) {
    await nextTick()
    const page = await pdfDoc.value.getPage(targetPageNum)
    const viewport = page.getViewport({ scale: scale.value })

    // 将 PDF 坐标转换为 Canvas 坐标
    const [x1, y1, x2, y2] = rect
    const [canvasX, canvasY] = viewport.convertToViewportPoint(x1, y2)

    // 计算滚动位置
    const container = pdfContainer.value
    if (container) {
      container.scrollTop = canvasY - container.clientHeight / 2
      container.scrollLeft = canvasX - container.clientWidth / 2
    }

    console.log('分页模式：滚动到批注位置:', { targetPageNum, rect, canvasX, canvasY })
  }

  // 绘制淡入淡出高亮效果
  await drawHighlightAnimation(targetPageNum, annotationData)
}

/**
 * 绘制高亮动画效果（淡入 → 保持 → 淡出）
 * 行业最佳实践：使用独立的高亮层Canvas + requestAnimationFrame
 *
 * @param pageNum - 页码
 * @param annotationData - 批注数据，包含 rect 和 quadPoints
 */
const drawHighlightAnimation = async (pageNum: number, annotationData: any) => {
  // 优先使用 quadPoints（精确坐标），没有则使用 rect
  const quadPoints = annotationData?.quadPoints || annotationData
  const rect = annotationData?.rect || annotationData

  if (!pdfDoc.value) return

  // 取消之前的动画
  if (currentAnimationId !== null) {
    cancelAnimationFrame(currentAnimationId)
    currentAnimationId = null
  }

  // 获取目标canvas（高亮层）
  let canvas: HTMLCanvasElement | null = null

  if (isAllPagesMode.value) {
    // 全量模式：获取对应页面的高亮层
    canvas = allPagesHighlightRefs.value[pageNum - 1]
  } else {
    // 分页模式：获取单页高亮层
    canvas = highlightCanvas.value
  }

  if (!canvas) {
    console.warn('未找到高亮层canvas')
    return
  }

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  // 获取页面viewport计算坐标
  const page = await pdfDoc.value.getPage(pageNum)
  const viewport = page.getViewport({ scale: scale.value })

  // 同步canvas尺寸（与PDF canvas一致）
  canvas.width = viewport.width
  canvas.height = viewport.height

  // 存储所有需要绘制的矩形区域
  const highlightRegions: { x: number, y: number, width: number, height: number }[] = []

  // 优先使用 quadPoints（支持跨行文本的精确高亮）
  if (quadPoints && Array.isArray(quadPoints) && quadPoints.length >= 8) {
    // quadPoints 格式：[x1,y1, x2,y2, x3,y3, x4,y4, ...]
    // 每8个点表示一个矩形（可能有多个矩形，表示多行文本）
    for (let i = 0; i < quadPoints.length; i += 8) {
      const [x1, y1, x2, y2, x3, y3, x4, y4] = quadPoints.slice(i, i + 8)

      // 转换为 Canvas 坐标
      const [cx1, cy1] = viewport.convertToViewportPoint(x1, y1)
      const [cx2, cy2] = viewport.convertToViewportPoint(x2, y2)
      const [cx3, cy3] = viewport.convertToViewportPoint(x3, y3)
      const [cx4, cy4] = viewport.convertToViewportPoint(x4, y4)

      // 计算矩形的边界
      const minX = Math.min(cx1, cx2, cx3, cx4)
      const maxX = Math.max(cx1, cx2, cx3, cx4)
      const minY = Math.min(cy1, cy2, cy3, cy4)
      const maxY = Math.max(cy1, cy2, cy3, cy4)

      highlightRegions.push({
        x: minX,
        y: minY,
        width: maxX - minX,
        height: maxY - minY
      })
    }
    console.log('使用 quadPoints 绘制高亮:', { pageNum, quadPoints, regions: highlightRegions })
  }
  // 回退到 rect（简单矩形）
  else if (rect && Array.isArray(rect) && rect.length === 4) {
    const [x1, y1, x2, y2] = rect
    const [canvasX1, canvasY1] = viewport.convertToViewportPoint(x1, y1)
    const [canvasX2, canvasY2] = viewport.convertToViewportPoint(x2, y2)

    highlightRegions.push({
      x: Math.min(canvasX1, canvasX2),
      y: Math.min(canvasY1, canvasY2),
      width: Math.abs(canvasX2 - canvasX1),
      height: Math.abs(canvasY2 - canvasY1)
    })
    console.log('使用 rect 绘制高亮:', { pageNum, rect, regions: highlightRegions })
  } else {
    console.warn('无效的坐标数据:', { quadPoints, rect })
    return
  }

  // 动画参数 - 方案A：外圈脉冲 + 微呼吸
  const PULSE_DURATION = 800       // 单次脉冲时长 (ms)
  const STROKE_COLOR = '#00C853'   // 绿色（与PDF批注同色系）
  const LINE_WIDTH = 3             // 基础边框宽度（像素）
  const GLOW_MAX_RADIUS = 12       // 外圈光晕最大半径（像素）
  const GLOW_COLOR = '#00C853'     // 光晕颜色（同绿色系）
  const SCALE_MIN = 0.98           // 呼吸缩放最小值
  const SCALE_MAX = 1.00           // 呼吸缩放最大值

  const startTime = performance.now()

  const animate = (currentTime: number) => {
    const elapsed = currentTime - startTime

    // 动画结束条件
    if (elapsed >= PULSE_DURATION) {
      ctx.clearRect(0, 0, canvas!.width, canvas!.height)
      currentAnimationId = null
      return
    }

    // 计算进度（0 → 1）使用 ease-out 缓动
    const rawProgress = elapsed / PULSE_DURATION
    const progress = 1 - Math.pow(1 - rawProgress, 3) // cubic ease-out

    // 清除画布
    ctx.clearRect(0, 0, canvas!.width, canvas!.height)

    // 计算动画参数
    // 1. 外圈光晕半径：0 → GLOW_MAX_RADIUS → 0
    const glowRadius = GLOW_MAX_RADIUS * Math.sin(progress * Math.PI)

    // 2. 光晕透明度：0.6 → 0
    const glowOpacity = 0.6 * (1 - progress)

    // 3. 呼吸缩放：0.98 → 1.00 → 0.98
    const breathProgress = Math.sin(progress * Math.PI * 2) // 两次完整呼吸
    const scale = SCALE_MIN + (SCALE_MAX - SCALE_MIN) * (0.5 + breathProgress * 0.5)

    // 绘制所有高亮区域
    highlightRegions.forEach(region => {
      const centerX = region.x + region.width / 2
      const centerY = region.y + region.height / 2

      // 保存当前状态
      ctx.save()

      // 应用呼吸缩放（围绕中心点）
      ctx.translate(centerX, centerY)
      ctx.scale(scale, scale)
      ctx.translate(-centerX, -centerY)

      // 1. 绘制外圈光晕（shadowBlur）
      if (glowRadius > 0) {
        ctx.shadowColor = GLOW_COLOR
        ctx.shadowBlur = glowRadius
        ctx.shadowOffsetX = 0
        ctx.shadowOffsetY = 0
        ctx.globalAlpha = glowOpacity
      }

      // 2. 绘制绿色边框（不透明，始终可见）
      ctx.strokeStyle = STROKE_COLOR
      ctx.lineWidth = LINE_WIDTH
      ctx.globalAlpha = 1.0
      ctx.strokeRect(region.x, region.y, region.width, region.height)

      // 恢复状态
      ctx.restore()
    })

    // 继续动画
    currentAnimationId = requestAnimationFrame(animate)
  }

  // 启动动画
  currentAnimationId = requestAnimationFrame(animate)
}

// 暴露方法给父组件
defineExpose({
  scrollToAnnotation
})

// 键盘快捷键
const handleKeydown = (e) => {
  if (e.key === 'ArrowLeft') previousPage()
  if (e.key === 'ArrowRight') nextPage()
  if (e.key === '+' || e.key === '=') zoomIn()
  if (e.key === '-') zoomOut()
}

// 监听 props 变化
watch(() => props.url, (newUrl) => {
  if (newUrl) {
    loadPdfFromUrl(newUrl)
  }
})

watch(() => props.page, (newPage) => {
  if (newPage && newPage !== pageNum.value) {
    pageNum.value = newPage
    renderPage()
  }
})

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
  // 如果 props.url 已经存在，则加载
  if (props.url) {
    loadPdfFromUrl(props.url)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.pdf-viewer-container {
  display: flex;
  flex-direction: column;
  height: 100%;
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

/* 高亮层Canvas - 叠加在PDF Canvas上方 */
.highlight-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none; /* 不阻止鼠标事件 */
  z-index: 1;
  background: transparent !important; /* 强制透明，不继承白色背景 */
}

/* 全量模式样式 */
.all-pages-wrapper {
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
  align-items: center;
}

.page-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.page-number {
  font-size: 14px;
  color: #666;
  font-weight: 500;
  padding: 4px 12px;
  background: #f0f0f0;
  border-radius: 4px;
  transition: all 0.3s ease;
}

/* 页码闪烁动画 - 跳转时的视觉反馈 */
.page-highlight-flash {
  animation: pageFlash 1.2s ease-out;
}

@keyframes pageFlash {
  0% {
    background: #FFD700;
    color: #000;
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(255, 215, 0, 0.7);
  }
  15% {
    transform: scale(1.1);
    box-shadow: 0 0 10px 5px rgba(255, 215, 0, 0.4);
  }
  50% {
    background: #FFD700;
    color: #000;
    transform: scale(1.05);
    box-shadow: 0 0 8px 3px rgba(255, 215, 0, 0.3);
  }
  100% {
    background: #f0f0f0;
    color: #666;
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(255, 215, 0, 0);
  }
}

/* 全量模式的canvas容器 */
.canvas-container {
  position: relative;
  display: inline-block;
}

.page-container canvas:not(.highlight-canvas) {
  max-width: 100%;
  height: auto;
  display: block;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
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
</style>
