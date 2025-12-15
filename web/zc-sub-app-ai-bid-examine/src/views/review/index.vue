<template>
  <div class="compliance-review-container">
    <LeftSideActions />
    <!-- 顶部导航区域 -->
    <div class="header-section">
      <div class="breadcrumb-area">
        <div class="nav-buttons">
          <a-button type="text" class="nav-btn history-btn" @click="showHistoryFiles">
            <template #icon>
              <Clock8 class="icon" :size="16" />
            </template>
            历史文件
          </a-button>
        </div>
        <div class="file-name">{{ statsData.fileName }}</div>
      </div>

      <div class="info-actions">
        <div class="review-time">
          <ClockFading class="icon" :size="16" />
          <span>解析完成时间：{{ statsData.analysisFinishTime || '-' }}</span>
        </div>
        <div class="review-time">
          <Calendar1 class="icon" :size="16" />
          <span>审查时间：{{ statsData.reviewTime || '-' }}</span>
        </div>
        <div class="action-buttons">
          <a-dropdown
            v-model:open="exportState.visible"
            :trigger="['click']"
            @openChange="handleExportDropdownChange"
            placement="bottomRight"
          >
            <a-button class="export-btn">
              <template #icon>
                <Download class="icon" :size="16" />
              </template>
              导出
              <DownOutlined />
            </a-button>
            <template #overlay>
              <div class="export-dropdown-content">
                <div class="export-options">
                  <div v-for="option in exportOptionsList" :key="option.key" class="export-option">
                    <a-checkbox v-model:checked="exportState.options[option.key]">
                      {{ option.label }}
                    </a-checkbox>
                  </div>
                </div>
                <div class="export-actions">
                  <a-button size="small" @click="cancelExport">取消</a-button>
                  <a-button
                    type="primary"
                    size="small"
                    :loading="exportState.loading"
                    :disabled="!hasSelectedOptions"
                    @click="confirmExport"
                  >
                    导出
                  </a-button>
                </div>
              </div>
            </template>
          </a-dropdown>
          <!-- 关键词查询与上传PDF（最小接入后端接口） -->
          <a-input
            v-model:value="searchKeyword"
            placeholder="输入关键词（可用空格分隔多个）"
            style="width: 220px"
            :disabled="searchLoading"
          />
          <a-button :loading="searchLoading" @click="handleSearch">查询</a-button>
          <a-button :loading="uploading" @click="handleUploadClick">上传PDF</a-button>
          <input ref="uploadInputRef" type="file" accept="application/pdf" style="display: none" @change="onFileSelected" />
          <a-button type="primary" @click="showCheckList">查看审查清单</a-button>
        </div>
      </div>
    </div>
    <!-- 主体内容区域 -->
    <div class="main-content">
      <!-- PDF阅读器区域 -->
      <div class="pdf-reader-wrapper">
        <PdfViewer
          v-if="pdfData.pdfUrl"
          ref="pdfReaderRef"
          :url="pdfData.pdfUrl"
          :page="pdfData.currentPage"
          @annotationsLoaded="handleAnnotationsLoaded"
        />
        <BaseEmpty v-else description="暂无文档" />
      </div>

      <!-- JSON元素列表面板 -->
      <div class="review-panel" ref="review-panel">
        <div class="panel-header">
          <span class="shrink-0 mr-[4px]">文档元素</span>
          <div class="statistics">
            共 <span class="num">{{ jsonElements.length }}</span> 个元素
          </div>
        </div>

        <!-- 元素列表 -->
        <div class="review-items json-elements-list">
          <div v-if="jsonElements.length === 0" style="padding: 20px; text-align: center; color: #999">
            暂无数据
          </div>
          <div v-else class="elements-container">
            <div
              v-for="(element, index) in jsonElements"
              :key="index"
              :class="['element-item', { active: selectedElement === element }]"
              @click="handleElementClick(element)"
            >
              <div class="element-header">
                <span class="element-index">#{{ index + 1 }}</span>
                <span class="element-page">Page {{ element.page + 1 }}</span>
              </div>
              <div class="element-text">{{ element.text }}</div>
              <div class="element-box">
                {{ Math.round(element.box[0]) }}, {{ Math.round(element.box[1]) }} -
                {{ Math.round(element.box[2]) }}, {{ Math.round(element.box[3]) }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 审查清单弹窗 -->
    <CheckListModal v-model:open="state.checkListVisible" :task-id="taskId" />

    <!-- 历史文件弹窗 -->
    <HistoryFilesModal
      v-model="state.historyFilesVisible"
      :task-id="taskId"
      placement="left"
      :filteredItems="filteredItems"
      @preview="handleFilePreview"
    />
    <!-- 下载中离开页面提示 -->
    <BaseDialog v-model="leaveConfirmVisible" title="提示" @confirm="confirmLeave">
      正在下载中，离开页面将中断下载，确定要离开吗？
    </BaseDialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, nextTick, onBeforeUnmount, onMounted, watch } from 'vue'
import { onBeforeRouteLeave, useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { DownOutlined } from '@ant-design/icons-vue'
import { CornerUpLeft, Clock8, Calendar1, Download, ClockFading } from 'lucide-vue-next'
import { SKELETON_CONFIG, createFilterTabs, DEFAULT_REVIEW_RESULT, exportOptionsList } from '@/views/hooks/examine'
import { useExport } from '@/views/hooks/use-export'
import { getTaskReview, apiGetFile, reviewTipList, getLocalTaskList } from '@/api/examine'
import { BaseDialog } from '@/components/BaseDialog'
import PdfViewer from '@/views/pdf/PdfViewer.vue'
import BaseEmpty from '@/components/BaseEmpty/index.vue'
import LeftSideActions from '@/components/LeftSideActions/index.vue'
import CheckListModal from './components/CheckListModal.vue'
import HistoryFilesModal from './components/HistoryFilesModal.vue'
import ReviewItem from './components/ReviewItem.vue'
import config from '../../config'

defineOptions({
  name: 'ComplianceReview'
})

const router = useRouter()
const route = useRoute()

const isDev = import.meta.env.DEV === true || import.meta.env.MODE === 'dev'

//是否存在风险
const existRisk = ref(true)
const taskId = ref('')
const isDevMode = ref(false)
const unmatchedData = ref<any[]>([])
const expandedState = reactive<Record<string, boolean>>({})
const state = reactive({
  loading: false,
  activeFilter: 1 as number | null,
  checkListVisible: false,
  historyFilesVisible: false
})
const markList = ref<any[]>([])
const getMarkList = async () => {
  if (isDev || config.isTest) {
    console.log('开发/测试模式：跳过 getMarkList 接口调用')
    markList.value = []
    return
  }

  markList.value = []
  const { err, data } = await reviewTipList({ taskId: taskId.value })
  if (err) return
  const list = data.dataList ?? []
  list.forEach(item => {
    let obj = {
      uniqueId: item.uniqueId,
      annotations: item.fileText ? [{ content: item.fileText }] : []
    }
    if (item.position?.length)
      obj = {
        ...obj,
        ...item.position[0]
      }
    markList.value.push(obj)
  })
  pdfData.highlightRects = [...markList.value]
}
const statsData = ref<Record<string, any>>({})

const pdfData = reactive({
  pdfUrl: '',
  currentPage: 1,
  highlightRects: [] as any[]
})

// JSON数据存储
const jsonElements = ref<any[]>([])
const selectedElement = ref<any>(null)

const resultData = reactive<Record<string, any>>({ ...DEFAULT_REVIEW_RESULT })
const activeItem = ref<Record<string, any>>({})

const resultBarWidth = computed(() => {
  if (statsData.value.resultFinishNum && statsData.value.resultNum) {
    const percentage = ((statsData.value.resultFinishNum / statsData.value.resultNum) * 100).toFixed(2)
    return `${percentage}%`
  } else return '0%'
})

const filterTabs = computed(() => createFilterTabs(statsData.value))

const filteredItems = computed(() => {
  if (isDevMode.value) {
    return [{
      reviewItemCode: 'dev_unmatched',
      reviewItemName: '未匹配数据（开发模式）',
      children: unmatchedData.value.map((item, index) => ({
        uniqueId: `unmatched_${index}`,
        reviewItemName: '未匹配数据',
        reviewItemCode: 'dev_unmatched',
        sceneDesc: item.reason,
        fileText: item.span.targetText,
        page: item.span.page,
        spanList: [{
          pid: item.span.pid,
          text: item.span.targetText,
          pdfAnnotations: item.bestMatch ? [{
            pageNum: item.bestMatch.pageNum,
            rect: item.bestMatch.rect,
            quadPoints: item.bestMatch.quadPoints
          }] : []
        }],
        _originalSpan: {
          page: item.span.page,
          quadPoints: item.span.quadPoints,
          pid: item.span.pid
        },
        legalBasicSourceList: [],
        showRiskTip: `annotation.json: uniqueId=${item.uniqueId}, page=${item.span.page}, pid=${item.span.pid}\n` +
                     `最接近PDF批注: ${item.bestMatch ? `page=${item.bestMatch.pageNum}, IOU=${item.matchInfo.iou}, 文本相似度=${item.matchInfo.textSim}` : '无'}`,
        acceptStatus: 0,
        handleStatus: 0,
        _isDevMode: true
      }))
    }]
  }

  const dataList = resultData.dataList || []

  console.log('过滤后的审查项:', {
    总数: dataList.length,
    匹配数: dataList.filter((item: any) => item.spanList?.some((span: any) => span.pdfAnnotations?.length > 0)).length
  })

  const grouped = dataList.reduce((acc, item) => {
    let group = acc.find(group => group.reviewItemCode === item.reviewItemCode)
    if (!group) {
      group = {
        reviewItemCode: item.reviewItemCode,
        reviewItemName: item.reviewItemName,
        children: []
      }
      acc.push(group)
    }
    group.children.push(item)
    return acc
  }, [] as { reviewItemCode: string; reviewItemName: string; children: any[] }[])

  grouped.forEach(group => {
    const seenLegalBasis = new Map()
    group.children.forEach(item => {
      if (!item.legalBasicSourceList?.length) return
      const legalBasisKey = item.legalBasicSourceList
        .map(
          basis =>
            `${item.sceneDesc}${basis.source}${basis.basicIssue}${basis.basicNumber}${basis.basicDesc}${basis.sourceLink}`
        )
        .sort()
        .join('|')

      if (seenLegalBasis.has(legalBasisKey)) {
        item.legalBasicHide = true
      } else {
        seenLegalBasis.set(legalBasisKey, true)
      }
    })
  })

  return grouped
})

const pdfReaderRef = ref<InstanceType<typeof PdfViewer>>()
const handleReviewItemClick = async (item: any) => {
  if (!item) return
  activeItem.value = item ?? {}

  console.log('点击审查项:', {
    uniqueId: item.uniqueId,
    spanList: item.spanList,
    hasPdfAnnotations: item.spanList?.some((s: any) => s.pdfAnnotations?.length > 0)
  })

  const spanList = item.spanList ?? []
  let targetPage = -1
  let highlightRects: any[] = []

  if (spanList.length > 0) {
    spanList.forEach((span: any) => {
      const pdfAnns = span.pdfAnnotations ?? []
      if (pdfAnns.length > 0) {
        const firstAnn = pdfAnns[0]
        if (targetPage === -1) {
          targetPage = firstAnn.pageNum
        }

        pdfAnns.forEach((ann: any) => {
          console.log('添加高亮区域:', ann)
          highlightRects.push({
            pageNum: ann.pageNum,
            quadPoints: ann.quadPoints,
            rect: ann.rect,
            jump: true,
            annotations: item.acceptStatus === 1 && item.acceptText
              ? [{ content: item.acceptText }]
              : []
          })
        })
      }
    })
  }

  if (targetPage === -1) {
    const position = item.position ?? []
    const annotations =
      item.acceptStatus === 1 && item.acceptText
        ? [{ content: item.acceptText }]
        : []

    if (position?.length) {
      highlightRects = [
        {
          ...position[0],
          jump: true,
          annotations
        },
        ...(markList.value || [])
      ]
      targetPage = item.page ?? -1
    }
  }

  pdfData.highlightRects = highlightRects

  if (targetPage > 0 && highlightRects.length > 0) {
    const firstHighlight = highlightRects[0]

    if (pdfReaderRef.value?.scrollToAnnotation) {
      await pdfReaderRef.value.scrollToAnnotation(firstHighlight)
    } else {
      pdfData.currentPage = -1
      await nextTick()
      pdfData.currentPage = targetPage
    }

    console.log('跳转到 PDF 位置:', {
      page: targetPage,
      highlightCount: highlightRects.length,
      uniqueId: item.uniqueId,
      rect: firstHighlight.rect
    })
  } else {
    console.warn('无法跳转：未找到有效的 PDF 位置信息', {
      uniqueId: item.uniqueId,
      spanList: item.spanList,
      targetPage,
      highlightRects
    })
  }
}

const handleShowBestMatch = async (item: any) => {
  console.log('定位到最接近的PDF批注:', item)
  await handleReviewItemClick(item)
}

const handleShowOriginalSpan = async (item: any) => {
  console.log('定位到annotation.json的原始位置:', item)

  if (!item._originalSpan || !item._originalSpan.quadPoints) {
    console.warn('没有找到原始span数据')
    return
  }

  const originalSpan = item._originalSpan
  const targetPage = originalSpan.page

  const highlightRects = [{
    pageNum: targetPage,
    quadPoints: originalSpan.quadPoints,
    rect: null,
    jump: true
  }]

  pdfData.highlightRects = highlightRects

  if (pdfReaderRef.value?.scrollToAnnotation) {
    await pdfReaderRef.value.scrollToAnnotation(highlightRects[0])
  } else {
    pdfData.currentPage = -1
    await nextTick()
    pdfData.currentPage = targetPage
  }

  console.log('跳转到annotation.json位置:', {
    page: targetPage,
    pid: originalSpan.pid,
    quadPoints: originalSpan.quadPoints?.slice(0, 8)
  })
}

const isOnlyReviewData = ref(false)
const getData = async () => {
  state.loading = true
  Object.assign(resultData, DEFAULT_REVIEW_RESULT)

  if (reviewListData.value) {
    console.log('使用本地 JSON 数据渲染列表')
    const data = reviewListData.value
    state.loading = false

    const stats = data?.stats ?? {}
    if (!isOnlyReviewData.value) {
      statsData.value = {
        resultFinishNum: 0,
        ...stats,
        finalFileId: data.finalFileId || '1978018096320905217',
        fileName: data.fileName || '测试文件',
        reviewTime: data.reviewTime,
        analysisFinishTime: data.analysisFinishTime
      }
      isOnlyReviewData.value = false
    }
    Object.assign(resultData, DEFAULT_REVIEW_RESULT, data)

    if (!statsData.value.resultNum && existRisk.value) {
      existRisk.value = false
      setActiveFilter(null)
    }
    return
  }

  if (isDev || config.isTest) {
    console.log('开发/测试模式：跳过 getTaskReview 接口调用，无本地数据')
    state.loading = false
    return
  }

  const { data, err } = await getTaskReview({
    taskId: taskId.value,
    reviewResult: state.activeFilter
  })
  state.loading = false
  if (err) return
  const stats = data?.stats ?? {}
  if (!isOnlyReviewData.value) {
    statsData.value = {
      resultFinishNum: 0,
      ...stats,
      finalFileId: data.finalFileId,
      fileName: data.fileName,
      reviewTime: data.reviewTime,
      analysisFinishTime: data.analysisFinishTime
    }
    isOnlyReviewData.value = false
  }
  Object.assign(resultData, DEFAULT_REVIEW_RESULT, data)

  if (!statsData.value.resultNum && existRisk.value) {
    existRisk.value = false
    setActiveFilter(null)
  }
}

const goHome = () => {
  router.push({ name: 'HomeIndex' })
}

const goToReview = () => {
  router.push({ name: 'ComplianceReview' })
}
const goToDemo = () => {
  router.push('/review')
}

const uploadInputRef = ref<HTMLInputElement | null>(null)
const uploading = ref(false)
const handleUploadClick = () => {
  uploadInputRef.value?.click()
}
const onFileSelected = async (e: Event) => {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  try {
    uploading.value = true
    const form = new FormData()
    form.append('file', file)
    const resp = await fetch('/python/api/pdf/upload_pdf', {
      method: 'POST',
      body: form
    })
    const json = await resp.json().catch(() => ({}))
    if (resp.ok && (json?.success !== false)) {
      message.success('PDF上传成功')
      await refreshData()
    } else {
      message.error('PDF上传失败')
    }
  } catch (err) {
    console.error(err)
    message.error('PDF上传失败')
  } finally {
    uploading.value = false
    if (uploadInputRef.value) uploadInputRef.value.value = ''
  }
}

const searchKeyword = ref('')
const searchLoading = ref(false)
const searchResults = ref<any[]>([])
const handleSearch = async () => {
  const raw = (searchKeyword.value || '').trim()
  if (!raw) {
    message.info('请输入关键词')
    return
  }
  const keywords = raw.split(/\s+/).filter(Boolean)
  try {
    searchLoading.value = true
    const resp = await fetch('/python/api/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ keywords, top_k: 5, collection_name: 'pdf' })
    })
    const json = await resp.json()
    if (json.success) {
      searchResults.value = json.results || []
      message.success('查询成功，返回 ' + (json.total ?? searchResults.value.length) + ' 条结果')
      console.log('搜索结果：', searchResults.value)
    } else {
      message.error('查询失败')
    }
  } catch (err) {
    console.error(err)
    message.error('查询接口异常')
  } finally {
    searchLoading.value = false
  }
}

const toggleDevMode = () => {
  isDevMode.value = !isDevMode.value
  console.log('开发模式:', isDevMode.value ? '开启' : '关闭')
}

// 处理元素点击事件
const handleElementClick = async (element: any) => {
  selectedElement.value = element

  // 构造高亮数据
  const targetPage = element.page + 1  // JSON中page从0开始,PDF从1开始
  const box = element.box  // [x1, y1, x2, y2]

  // 转换为 quadPoints 格式 (8个点: 左上、右上、右下、左下的x,y坐标)
  const quadPoints = [
    box[0], box[1],  // 左上
    box[2], box[1],  // 右上
    box[2], box[3],  // 右下
    box[0], box[3]   // 左下
  ]

  // 构造高亮矩形
  const highlightRect = {
    pageNum: targetPage,
    rect: box,
    quadPoints: quadPoints,
    jump: true,
    needsConversion: true  // 需要坐标转换 (屏幕坐标 → PDF坐标)
  }

  // 更新高亮区域
  pdfData.highlightRects = [highlightRect]

  // 跳转到对应页面并高亮
  if (pdfReaderRef.value?.scrollToAnnotation) {
    await pdfReaderRef.value.scrollToAnnotation(highlightRect)
  } else {
    // 回退方案: 简单页面跳转
    pdfData.currentPage = -1
    await nextTick()
    pdfData.currentPage = targetPage
  }

  console.log('选中元素:', {
    text: element.text,
    page: targetPage,
    box: box,
    quadPoints: quadPoints
  })
}

const pdfAnnotationsData = ref<any>(null)
const reviewListData = ref<any>(null)
const pdfAnnotations = ref<any[]>([])

const calculateIOU = (quad1: number[], quad2: number[]) => {
  if (!quad1 || !quad2 || quad1.length < 8 || quad2.length < 8) return 0
  const getBBox = (quad: number[]) => {
    const xs = [quad[0], quad[2], quad[4], quad[6]]
    const ys = [quad[1], quad[3], quad[5], quad[7]]
    return {
      x1: Math.min(...xs),
      y1: Math.min(...ys),
      x2: Math.max(...xs),
      y2: Math.max(...ys)
    }
  }
  const box1 = getBBox(quad1)
  const box2 = getBBox(quad2)
  const x1 = Math.max(box1.x1, box2.x1)
  const y1 = Math.max(box1.y1, box2.y1)
  const x2 = Math.min(box1.x2, box2.x2)
  const y2 = Math.min(box1.y2, box2.y2)

  if (x2 < x1 || y2 < y1) return 0
  const intersection = (x2 - x1) * (y2 - y1)
  const area1 = (box1.x2 - box1.x1) * (box1.y2 - box1.y1)
  const area2 = (box2.x2 - box2.x1) * (box2.y2 - box2.y1)
  const union = area1 + area2 - intersection
  return intersection / union
}

const textSimilarity = (text1: string, text2: string) => {
  if (!text1 || !text2) return 0
  const t1 = text1.trim().toLowerCase()
  const t2 = text2.trim().toLowerCase()
  if (t1 === t2) return 1
  if (t1.includes(t2) || t2.includes(t1)) return 0.8
  const longer = t1.length > t2.length ? t1 : t2
  const shorter = t1.length > t2.length ? t2 : t1
  let maxMatch = 0
  for (let i = 0; i < shorter.length; i++) {
    for (let j = i + 1; j <= shorter.length; j++) {
      const substr = shorter.substring(i, j)
      if (longer.includes(substr) && substr.length > maxMatch) {
        maxMatch = substr.length
      }
    }
  }
  return maxMatch / longer.length
}

const matchAnnotations = () => {
  console.log('开始匹配 Span 和 PDF 批注...')
  const annotationJson = pdfAnnotationsData.value?.annotations || []
  const pdfAnns = pdfAnnotations.value || []
  if (!annotationJson.length || !pdfAnns.length) {
    console.warn('数据不完整，无法匹配', {
      annotationJsonCount: annotationJson.length,
      pdfAnnsCount: pdfAnns.length
    })
    return
  }

  const pdfAnnsByPage = new Map<number, any[]>()
  const matchedPdfAnnIds = new Set<string>()
  pdfAnns.forEach(ann => {
    if (!pdfAnnsByPage.has(ann.pageNum)) {
      pdfAnnsByPage.set(ann.pageNum, [])
    }
    pdfAnnsByPage.get(ann.pageNum)!.push(ann)
  })

  let matchCount = 0
  let totalSpans = 0
  const unmatchedSpans: any[] = []

  annotationJson.forEach(annotation => {
    annotation.spanList?.forEach((span: any) => {
      totalSpans++
      const page = span.page
      const quadPoints = span.quadPoints
      const targetText = span.targetText

      const samePage = pdfAnnsByPage.get(page) || []
      if (!samePage.length) {
        unmatchedSpans.push({
          reason: '该页无批注',
          span,
          annotation
        })
        return
      }

      let bestMatch: any = null
      let bestScore = 0

      samePage.forEach(pdfAnn => {
        const iou = calculateIOU(quadPoints, pdfAnn.quadPoints)
        const textSim = textSimilarity(targetText, pdfAnn.原始数据?.contentsObj?.str || pdfAnn.contents)
        const score = iou * 0.6 + textSim * 0.4
        if (score > bestScore) {
          bestScore = score
          bestMatch = pdfAnn
        }
      })

      if (bestMatch && bestScore > 0.5) {
        const iou = calculateIOU(quadPoints, bestMatch.quadPoints)
        const textSim = textSimilarity(targetText, bestMatch.原始数据?.contentsObj?.str || bestMatch.contents)

        const matchInfo = {
          id: bestMatch.id,
          pdfAnnotationId: bestMatch.pdfAnnotationId,
          pageNum: bestMatch.pageNum,
          rect: Array.from(bestMatch.rect || []),
          quadPoints: Array.from(bestMatch.quadPoints || []),
          subtype: bestMatch.subtype,
          color: bestMatch.color ? Array.from(bestMatch.color) : null,
          opacity: bestMatch.opacity,
          score: bestScore.toFixed(3),
          iou: iou.toFixed(3),
          textSim: textSim.toFixed(3)
        }

        if (!span.pdfAnnotations) {
          span.pdfAnnotations = []
        }
        span.pdfAnnotations.push(matchInfo)

        let foundInReviewList = false
        let foundSpan = false
        if (reviewListData.value?.dataList) {
          reviewListData.value.dataList.forEach((item: any) => {
            if (item.uniqueId === annotation.uniqueId) {
              foundInReviewList = true
              const availablePids = item.spanList?.map((s: any) => s.pid) || []

              item.spanList?.forEach((reviewSpan: any) => {
                if (reviewSpan.pid === span.pid) {
                  foundSpan = true
                  if (!reviewSpan.pdfAnnotations) {
                    reviewSpan.pdfAnnotations = []
                  }
                  reviewSpan.pdfAnnotations.push(matchInfo)
                  console.log(`    ✓ Step2 成功写入 reviewListData`, {
                    uniqueId: annotation.uniqueId,
                    pid: span.pid,
                    text: reviewSpan.text
                  })
                }
              })

              if (!foundSpan) {
                console.warn(`    ⚠️ Step2 失败: pid 不匹配`, {
                  uniqueId: annotation.uniqueId,
                  '期望的 pid (annotation.json)': span.pid,
                  '实际的 pid (reviewListData)': availablePids,
                  '期望的 text': span.targetText,
                  '实际的 text': item.spanList?.map((s: any) => s.text)
                })
              }
            }
          })
        }

        if (!foundInReviewList) {
          console.warn(`    ⚠️ Step2 失败: uniqueId 在 reviewListData 中未找到`, {
            uniqueId: annotation.uniqueId,
            '所有可用 uniqueId': reviewListData.value?.dataList?.map((item: any) => item.uniqueId).slice(0, 10)
          })
        }

        matchedPdfAnnIds.add(bestMatch.id)
        matchCount++

      } else {
        let failureReasons = []
        if (!bestMatch) {
          failureReasons.push('page字段：同页无PDF批注')
        } else {
          const iou = calculateIOU(quadPoints, bestMatch.quadPoints)
          const textSim = textSimilarity(targetText, bestMatch.原始数据?.contentsObj?.str || bestMatch.contents)

          if (!quadPoints || quadPoints.length === 0) {
            failureReasons.push('quadPoints字段：为空')
          } else if (iou < 0.3) {
            failureReasons.push(`quadPoints字段：不匹配`)
          }

          if (!targetText || targetText.trim() === '') {
            failureReasons.push('targetText字段：为空')
          } else if (textSim < 0.3) {
            failureReasons.push(`targetText字段：不匹配`)
          }

          if (failureReasons.length === 0) {
            failureReasons.push(`综合得分不足(${bestScore.toFixed(3)}<0.5)`)
          }
        }

        unmatchedSpans.push({
          reason: failureReasons.join(', '),
          span,
          annotation,
          bestMatch,
          bestScore
        })
      }
    })
  })

  const unmatchedPdfAnns = pdfAnns.filter(ann => !matchedPdfAnnIds.has(ann.id))
  console.log('未匹配 PDF 批注数量:', unmatchedPdfAnns.length)

  unmatchedData.value = unmatchedSpans.map(item => ({
    uniqueId: item.annotation.uniqueId,
    reason: item.reason,
    span: {
      page: item.span.page,
      pid: item.span.pid,
      targetText: item.span.targetText,
      quadPoints: item.span.quadPoints
    },
    bestMatch: item.bestMatch ? {
      id: item.bestMatch.id,
      pageNum: item.bestMatch.pageNum,
      text: item.bestMatch.原始数据?.contentsObj?.str,
      quadPoints: item.bestMatch.quadPoints,
      rect: item.bestMatch.rect
    } : null,
    matchInfo: {}
  }))
}

const handleAnnotationsLoaded = (annotations: any[]) => {
  console.log('📄 PDF.js 批注提取完成:', annotations?.length, '条')
  pdfAnnotations.value = annotations

  if (pdfAnnotationsData.value?.annotations) {
    console.log('✅ annotation.json 已就绪，触发匹配')
    matchAnnotations()
  } else {
    console.log('⏳ 等待 annotation.json 加载...')
  }
}

const loadJsonFiles = async (taskId: string) => {
  try {
    const baseUrl = isDev
      ? `/task/${taskId}`
      : `${config.env.VITE_APP_PUBLIC_URL}/task/${taskId}`

    console.log('📦 开始加载 JSON 文件，taskId:', taskId)

    const annotationsUrl = `${baseUrl}/${taskId}_pdf_annotations.json`
    const annotationsResponse = await fetch(annotationsUrl)
    if (annotationsResponse.ok) {
      pdfAnnotationsData.value = await annotationsResponse.json()
      console.log('✅ annotation.json 加载完成:', pdfAnnotationsData.value?.annotations?.length, '条')

      if (pdfAnnotations.value?.length) {
        console.log('✅ PDF 批注已存在，触发匹配')
        matchAnnotations()
      } else {
        console.log('⏳ 等待 PDF 批注加载...')
      }
    } else {
      console.warn('❌ 未找到PDF批注文件:', annotationsUrl)
    }

    const reviewDataUrl = `${baseUrl}/${taskId}.json`
    const reviewDataResponse = await fetch(reviewDataUrl)
    if (reviewDataResponse.ok) {
      const jsonData = await reviewDataResponse.json()
      console.log('✅ 审查列表数据加载完成')
      reviewListData.value = jsonData.data || jsonData
      console.log('提取后的数据:', reviewListData.value)
    } else {
      console.warn('❌ 未找到审查数据文件:', reviewDataUrl)
    }

    console.log('📦 JSON 文件加载完成')
  } catch (error) {
    console.error('❌ 加载JSON文件失败:', error)
  }
}

const getFile = async () => {
  pdfData.currentPage = 1
  pdfData.highlightRects = []
  pdfData.pdfUrl = ''

  // 从本地PDF服务器加载PDF文件
  const pdfFileName = '少年宫.pdf'
  pdfData.pdfUrl = `http://localhost:3000/pdf/${encodeURIComponent(pdfFileName)}`
  console.log('使用 PDF 文件:', pdfData.pdfUrl)

  // 更新文件名显示
  statsData.value.fileName = pdfFileName

  // 加载对应的JSON数据
  try {
    const jsonResp = await fetch(`http://localhost:3000/api/json/${encodeURIComponent(pdfFileName)}`)
    if (jsonResp.ok) {
      const jsonData = await jsonResp.json()
      jsonElements.value = jsonData.data || []
      console.log('加载JSON数据成功:', jsonData.total, '个元素')
    } else {
      console.error('JSON数据加载失败:', jsonResp.status)
      jsonElements.value = []
    }
  } catch (error) {
    console.error('JSON数据加载异常:', error)
    jsonElements.value = []
  }

  return

  // 原有逻辑保留但不执行
  if (reviewListData.value && taskId.value) {
    pdfData.pdfUrl = isDev
      ? `/task/${taskId.value}/${taskId.value}_highlighted.pdf`
      : `${config.env.VITE_APP_PUBLIC_URL}/task/${taskId.value}/${taskId.value}_highlighted.pdf`
    console.log('使用 PDF 文件:', pdfData.pdfUrl)
    return
  }

  if (isDev || config.isTest) {
    console.log('开发/测试模式：跳过 apiGetFile 接口调用，无本地数据')
    return
  }

  const finalFileId = statsData.value.finalFileId
  if (!finalFileId) {
    message.info('缺少文件ID')
    return
  }

  const { data, err } = await apiGetFile(finalFileId)
  if (err) return
  console.log('apiGetFile 返回数据:', data)
  pdfData.pdfUrl = data.pdfUrl || data.fileUrl
}

const {
  state: exportState,
  hasSelectedOptions,
  cancel: cancelExport,
  show: showExport,
  confirm: confirmExport
} = useExport(exportOptionsList, taskId.value)
const handleExportDropdownChange = (open: boolean) => {
  if (open) {
    showExport()
  }
}

const showCheckList = () => {
  state.checkListVisible = true
}

const showHistoryFiles = () => {
  state.historyFilesVisible = true
}

const handleFilePreview = (file: any) => {
  console.log('📂 切换任务:', file.fileName, file.taskId)
  taskId.value = file.taskId
  refreshData()
  state.historyFilesVisible = false
}

const toggleItemExpand = (reviewItemCode: string) => {
  const currentState = expandedState[reviewItemCode]
  expandedState[reviewItemCode] = currentState === false ? true : false
}

const setActiveFilter = (filterKey: number | null) => {
  state.activeFilter = filterKey
  getData()
}

const refreshData = async () => {
  console.log('🔄 开始刷新数据，taskId:', taskId.value)
  pdfAnnotationsData.value = null
  pdfAnnotations.value = []
  reviewListData.value = null

  if (taskId.value) {
    await loadJsonFiles(taskId.value)
  }
  await getData()
  await getFile()
  await getMarkList()
  console.log('✅ 数据刷新完成')
}

const leaveConfirmVisible = ref(false)
const nextRoute = ref<any>(null)
const confirmLeave = () => {
  leaveConfirmVisible.value = false
  if (nextRoute.value) {
    nextRoute.value.next()
  }
}

onMounted(async () => {
  try {
    const taskList = await getLocalTaskList()
    if (taskList && taskList.length > 0) {
      taskId.value = taskList[0].taskId
      console.log('📋 加载第一个任务:', taskList[0].fileName, taskList[0].taskId)
    } else {
      console.error('❌ taskList 为空')
    }
  } catch (error) {
    console.error('❌ 加载 taskList 失败:', error)
  }

  refreshData()
})

onBeforeRouteLeave((to, from, next) => {
  if (exportState.loading) {
    nextRoute.value = { to, from, next }
    leaveConfirmVisible.value = true
    return
  }
  next()
})
onBeforeUnmount(() => {
  nextRoute.value = null
})
</script>

<style lang="scss" scoped>
.compliance-review-container {
  color: #111827;
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.header-section {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 11px 24px;
  border-bottom: 1px solid var(--line-2);
  box-sizing: border-box;
  .breadcrumb-area {
    display: flex;
    align-items: center;
    .nav-buttons {
      display: flex;
      gap: 16px;
      .nav-btn {
        display: flex;
        align-items: center;
        &.back-btn {
          padding: 8px 16px;
          border: 1px solid var(--line-3);
          border-radius: 4px;
          .icon {
            margin-right: 8px;
          }
        }
        &.history-btn {
          border: 1px solid var(--line-3);
          padding: 8px;
          margin-right: 16px;
          &:hover {
            background-color: transparent;
          }
        }
      }
    }
  }

  .info-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
    .review-time {
      display: flex;
      align-items: center;
      gap: 10px;
      color: #4b5563;
    }

    .action-buttons {
      display: flex;
      gap: 10px;

      .export-btn {
        display: flex;
        align-items: center;
        gap: 4px;
        border: 1px solid var(--line-3);

        .icon {
          margin-right: 4px;
        }
      }
    }
  }
}

.main-content {
  display: flex;
  flex: 1;
  min-height: 0;
}

.pdf-reader-wrapper {
  border-right: 1px solid #e5e7eb;
  position: relative;
  flex: 1;
  min-width: 860px;
  overflow-y: auto;
  .pdf-placeholder {
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}
.review-panel {
  position: relative;
  flex: 1;
  max-width: 832px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  background: var(--fill-0);
  .handle-result {
    position: sticky;
    display: flex;
    align-items: center;
    bottom: 0;
    height: 45px;
    line-height: 45px;
    padding: 0 12px;
    z-index: 10;
    background-color: var(--fill-0);
    box-shadow: 0px -2px 4px -2px #0000001a;
    color: #374151;
    margin-top: auto;
    .tip {
      display: flex;
      align-items: center;
    }
    .icon {
      width: 16px;
      height: 16px;
      margin-right: 4px;
    }
    .tip {
      font-size: 14px;
      font-weight: 400;
      color: #4b5563;
    }
    .num {
      color: var(--main-6);
      flex-shrink: 0;
    }
    .text {
      flex-shrink: 0;
    }
    .percent-bar {
      flex: 1;
      min-width: 0;
      margin-left: 6px;
      background-color: #e5e7eb;
      height: 8px;
      display: flex;
      border-radius: 8px;
      .percent {
        border-radius: 8px;
        background-color: var(--main-6);
      }
    }
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px;
    font-size: 16px;
    .statistics {
      font-size: 14px;
      .num {
        font-weight: 500;
        color: var(--main-6);
        padding: 0 4px;
        &.error {
          color: var(--error-6);
        }
      }
    }
  }

  .filter-tabs {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 4px;
    background-color: #f5f5f5;
    border-radius: 4px;
    margin: 0 16px 16px 16px;
    .filter-tab {
      display: flex;
      align-items: center;
      justify-content: center;
      flex: 1;
      height: 38px;
      min-width: 60px;
      border-radius: 4px;
      text-align: center;
      cursor: pointer;
      transition: all 0.2s;
      .tab-label {
        font-size: var(--font-14);
        color: var(--text-4);
      }
      .tab-count {
        display: inline-block;
        text-align: center;
        color: #4b5563;
        border-radius: 50%;
        background-color: #f3f4f6;
        margin-left: 8px;
        padding: 0 4px;
        min-width: 20px;
      }

      &:nth-child(2) {
        .tab-count,
        .skeleton-count {
          background: #fee2e2;
          color: #dc2626;
        }
      }
      &:nth-child(3) {
        .tab-count,
        .skeleton-count {
          background-color: #dcfce7;
          color: #16a34a;
        }
      }

      &:hover,
      &.active {
        background: var(--fill-0);
      }

      &.skeleton-tab {
        cursor: default;

        .tab-label {
          color: #9ca3af;
        }

        .skeleton-count {
          background-color: #e5e7eb;
          color: #9ca3af;
          animation: skeleton-loading 1.5s ease-in-out infinite;
        }

        &.active {
          background: var(--fill-0);

          .skeleton-count {
            background-color: #d1d5db;
          }
        }

        &:nth-child(2) {
          .skeleton-count {
            background: rgba(254, 226, 226, 0.7);
            color: rgba(220, 38, 38, 0.7);
          }
        }
        &:nth-child(3) {
          .skeleton-count {
            background-color: rgba(220, 252, 231, 0.7);
            color: rgba(22, 163, 74, 0.7);
          }
        }
      }
    }
  }

  .review-items {
    .skeleton-title-bar,
    .item-title-bar {
      display: flex;
      align-items: center;
      padding: 12px 16px;
      background: #f5f5f5;
      border-bottom: 1px solid #e5e7eb;
      cursor: pointer;
      transition: background-color 0.2s;

      &:hover {
        background: #ebebeb;
      }

      .item-index {
        width: 6px;
        height: 16px;
        background-color: var(--main-6);
        border-radius: 2px;
        margin-right: 12px;
      }

      .item-title {
        font-size: var(--font-16);
        flex: 1;
      }

      .item-count {
        color: #4b5563;
        border-radius: 50%;
        background-color: #e5e7eb;
        margin-left: 8px;
        padding: 0 4px;
        min-width: 20px;
        text-align: center;
      }

      .expand-text {
        margin-left: 8px;
        font-size: 12px;
        color: var(--main-6);
        user-select: none;

        &:hover {
          opacity: 0.8;
        }
      }
    }
  }
}

.empty-state {
  padding: 40px 0;
  text-align: center;
}

.skeleton-container {
  .skeleton-item-group {
    margin-bottom: 24px;
    .skeleton-content {
      padding: 16px;

      .skeleton-review-item {
        padding: 16px 0;
        border-bottom: 1px solid #e5e7eb;

        &:last-child {
          border-bottom: none;
        }

        .skeleton-line {
          height: 16px;
          background: linear-gradient(90deg, #f3f4f6 25%, #e5e7eb 50%, #f3f4f6 75%);
          background-size: 200% 100%;
          border-radius: 4px;
          margin-bottom: 12px;
          animation: skeleton-loading 1.5s ease-in-out infinite;

          &:last-child {
            margin-bottom: 0;
          }

          &.skeleton-line-long {
            width: 85%;
          }

          &.skeleton-line-medium {
            width: 65%;
          }

          &.skeleton-line-short {
            width: 45%;
          }
        }
      }
    }
  }
}

@keyframes skeleton-loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
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

/* JSON元素列表样式 */
.json-elements-list {
  flex: 1;
  overflow-y: auto;
}

.elements-container {
  padding: 12px;
}

.element-item {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    border-color: var(--main-6);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  }

  &.active {
    border-color: var(--main-6);
    background: #f0f7ff;
  }
}

.element-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.element-index {
  font-weight: 600;
  color: var(--main-6);
  font-size: 12px;
}

.element-page {
  font-size: 12px;
  color: #6b7280;
  background: #f3f4f6;
  padding: 2px 8px;
  border-radius: 4px;
}

.element-text {
  color: #111827;
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 8px;
  word-break: break-all;
}

.element-box {
  font-size: 11px;
  color: #9ca3af;
  font-family: monospace;
}
</style>