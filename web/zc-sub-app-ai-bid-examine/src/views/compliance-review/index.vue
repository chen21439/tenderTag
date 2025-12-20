<template>
  <div class="compliance-review-container">
    <!-- 主体内容区域 -->
    <div class="main-content">
      <!-- 左侧内容查看器 -->
      <div class="content-viewer-wrapper">
        <ContentViewer
          ref="contentViewerRef"
          :content-type="leftContentType"
          :file-name="statsData.fileName"
          :pdf-url="pdfData.pdfUrl"
          :ppt-url="pptData.pptUrl"
          :current-page="pdfData.currentPage"
          @go-home="goHome"
          @annotations-loaded="handleAnnotationsLoaded"
          @qa-update="handleQaGraphUpdate"
          @switch-mode="handleSwitchMode"
        />
      </div>

      <!-- 实时搜索面板（红框区域） -->
      <div v-if="viewMode === 'search'" class="review-panel search-panel" style="padding: 16px">
        <div class="search-bar" style="display: flex; gap: 10px; align-items: center; margin-bottom: 12px">
          <a-input
            v-model:value="searchKeyword"
            placeholder="输入关键词（可用空格分隔多个）"
            style="width: 320px"
            :disabled="searchLoading"
            @pressEnter="handleSearch"
          />
          <a-button type="primary" :loading="searchLoading" @click="handleSearch">查询</a-button>
        </div>
        <div class="search-results">
          <a-spin v-if="searchLoading" />
          <div v-else-if="searchResults.length">
            <a-list :data-source="searchResults">
              <template #renderItem="{ item }">
                <a-list-item class="search-item">
                  <div class="result-text">{{ item.text || item.content || JSON.stringify(item) }}</div>
                </a-list-item>
              </template>
            </a-list>
          </div>
          <BaseEmpty v-else description="暂无数据" />
        </div>
      </div>
      <!-- 审查结果面板 -->
      <div v-if="viewMode === 'result'" class="review-panel" ref="review-panel">
        <div class="panel-header">
          <span class="shrink-0 mr-[4px]">文档结构</span>
          <a-checkbox :checked="treeEditMode" @change="handleEditModeChange" style="margin-left: 12px">
            编辑模式
          </a-checkbox>
          <!-- 上传和下载按钮 -->
          <div style="margin-left: 12px; display: flex; gap: 4px; align-items: center">
            <Download
              :size="18"
              :stroke-width="2"
              style="cursor: pointer; color: #666; transition: color 0.2s;"
              @click="handleDownloadOntology"
              @mouseenter="(e) => e.target.style.color = '#1890ff'"
              @mouseleave="(e) => e.target.style.color = '#666'"
              title="下载"
            />
            <Upload
              :size="18"
              :stroke-width="2"
              style="cursor: pointer; color: #666; transition: color 0.2s;"
              @click="handleUploadOntology"
              @mouseenter="(e) => e.target.style.color = '#1890ff'"
              @mouseleave="(e) => e.target.style.color = '#666'"
              title="上传"
            />
          </div>
          <div style="margin-left: auto; display: flex; gap: 12px; align-items: center">
            <a-radio-group v-model:value="treeGroupMode" size="middle" button-style="solid">
              <a-radio-button value="label">业务语义结构树</a-radio-button>
              <a-radio-button value="ontology">业务本体树</a-radio-button>
              <a-radio-button value="original">采购标签图谱</a-radio-button>
              <a-radio-button v-if="!hideDemoFeatures" value="folder">文件夹</a-radio-button>
            </a-radio-group>
          </div>
        </div>

        <!-- JSON树形结构展示 -->
        <div class="review-items tree-view">
          <!-- 采购标签图谱模式：显示 Cytoscape 组件 -->
          <div v-show="treeGroupMode === 'original'" class="graph-view-container">
            <!-- 顶部控制栏 -->
            <div class="graph-toolbar">
              <div class="toolbar-right">
                <a-button
                  type="default"
                  size="small"
                  :class="{ 'active': !isNavCollapsed }"
                  @click="toggleNavPanel"
                >
                  <template #icon>
                    <ApartmentOutlined />
                  </template>
                </a-button>

                <a-divider type="vertical" style="height: 24px; margin: 0 8px" />

                <GraphControls
                  @reset="handleGraphReset"
                  @fit="handleGraphFit"
                  @zoomIn="handleGraphZoomIn"
                  @zoomOut="handleGraphZoomOut"
                />
              </div>
            </div>

            <!-- 使用共享的图谱导航面板组件（浮动布局） -->
            <GraphNavigationPanel
              :tree-data="graphTreeData"
              :selected-node-id="selectedGraphNodeId"
              :collapsed="isNavCollapsed"
              layout="floating"
              @node-select="handleNavNodeSelect"
            >
              <template #graph>
                <CytoscapeComponent
                  ref="cytoscapeRef"
                  :use-sample-data="false"
                  :nodes="graphNodes"
                  :edges="graphEdges"
                  layout="cose"
                  element-label-mode="value"
                  @node-click="handleNodeClick"
                  @edge-click="handleEdgeClick"
                />
                <div style="position: absolute; bottom: 16px; left: 16px; z-index: 10">
                  <GraphLegend />
                </div>
              </template>
            </GraphNavigationPanel>
          </div>


          <!-- 文件夹模式 -->
          <div v-show="treeGroupMode === 'folder'" class="folder-view-container">
            <FolderTree
              ref="folderTreeRef"
              @node-select="handleFolderNodeSelect"
              @toggle-qa="handleToggleQa"
            />
          </div>

          <!-- 业务语义结构树模式 -->
          <div
            v-show="treeGroupMode === 'label' && builtTreeData.length > 0"
            class="tree-list"
            @dragover.prevent="handleTreeDragOver"
            @drop.prevent="handleTreeDrop"
          >
            <TreeNode
              v-for="node in builtTreeData"
              :key="node.line_id"
              :node="node"
              :depth="0"
              :expanded-nodes="treeExpandedNodes"
              :selected-ids="selectedNodeIds"
              :node-map="nodeMap"
              :debug-mode="false"
              :edit-mode="treeEditMode"
              @toggle="toggleTreeNode"
              @select="selectTreeNode"
              @paragraphClick="handleParagraphClick"
              @node-drop="handleNodeDrop"
              @drag-start-node="handleDragStartNode"
              @drag-over-node="handleDragOverNode"
              @drag-end="handleDragEndOnNode"
              @update-label="handleUpdateLabel"
            />
          </div>

          <!-- 业务本体树模式 -->
          <div
            v-show="treeGroupMode === 'ontology' && ontologyTreeData.length > 0"
            class="tree-list"
            @dragover.prevent="handleTreeDragOver"
            @drop.prevent="handleTreeDrop"
          >
            <TreeNode
              v-for="node in ontologyTreeData"
              :key="node.line_id"
              :node="node"
              :depth="0"
              :expanded-nodes="treeExpandedNodes"
              :selected-ids="selectedNodeIds"
              :node-map="nodeMap"
              :debug-mode="false"
              :edit-mode="treeEditMode"
              @toggle="toggleTreeNode"
              @select="selectTreeNode"
              @paragraphClick="handleParagraphClick"
              @node-drop="handleNodeDrop"
              @drag-start-node="handleDragStartNode"
              @drag-over-node="handleDragOverNode"
              @drag-end="handleDragEndOnNode"
              @update-label="handleUpdateLabel"
            />
          </div>

          <div v-show="treeGroupMode !== 'original' && treeGroupMode !== 'folder' && builtTreeData.length === 0 && ontologyTreeData.length === 0" style="padding: 20px; text-align: center; color: #999">暂无数据</div>
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
import { ApartmentOutlined, DownloadOutlined, UploadOutlined } from '@ant-design/icons-vue'
import { Empty } from 'ant-design-vue'
import { CornerUpLeft, Clock8, Calendar1, Download, ClockFading, Upload } from 'lucide-vue-next'
import { SKELETON_CONFIG, createFilterTabs, DEFAULT_REVIEW_RESULT, exportOptionsList } from '@/views/hooks/examine'
import { useExport } from '@/views/hooks/use-export'
import { getTaskReview, reviewTipList } from '@/api/examine'
import { BaseDialog } from '@/components/BaseDialog'
import PdfViewer from '@/views/pdf/PdfViewer.vue'
import BaseEmpty from '@/components/BaseEmpty/index.vue'
import ContentViewer from './components/ContentViewer.vue'
import LeftSideActions from '@/components/LeftSideActions/index.vue'
import CheckListModal from './components/CheckListModal.vue'
import HistoryFilesModal from './components/HistoryFilesModal.vue'
import ReviewItem from './components/ReviewItem.vue'
import ReviewTreeNode from './components/ReviewTreeNode.vue'
import TreeNode from './components/TreeNode.vue'
import FolderTree from './components/FolderTree.vue'
import CytoscapeComponent from './components/CytoscapeComponent.vue'
import { GraphLegend, GraphNavigationPanel } from '../../components/knowledge-graph'
import GraphControls from '../../components/knowledge-graph/GraphControls.vue'
import { getGraphData } from '../../components/knowledge-graph/graphData'
import config from '../../config'
import { useOntologyTree } from './components/ontology/useOntologyTree'

defineOptions({
  name: 'ComplianceReview'
})

const router = useRouter()
const route = useRoute()

/* 使用 Vite 的开发环境变量判断
   - 本地开发（vite --mode dev / 默认 development）为 true
   - 仅调整判断，不改现有业务逻辑与数据加载 URL */
const isDev = import.meta.env.DEV === true || import.meta.env.MODE === 'dev'

// 隐藏演示功能（文件夹和演示模式按钮）- 所有环境都隐藏
const hideDemoFeatures = true

// 是否启用PDF高亮功能
const enablePdfHighlight = ref(true)

//是否存在风险
const existRisk = ref(true)
// 获取任务ID（初始为空，在 onMounted 中从 taskList.json 加载第一个）
const taskId = ref((route.query.taskId as string) || '')
// 视图模式切换：result | search
const viewMode = ref<'result' | 'search'>('result')
// 树形结构分组模式：original（采购标签图谱）| label（业务语义结构树）| ontology（业务本体树）| entity（业务实体图谱）| folder（文件夹）
// 默认显示业务语义结构树
const treeGroupMode = ref<'original' | 'label' | 'ontology' | 'entity' | 'folder'>('label')

// 树编辑模式：允许拖拽节点改变父节点
const treeEditMode = ref(false)

// 拖拽状态：记录被拖拽的节点和最后一个dragOver的目标节点
let draggedNodeId: number | null = null
let draggedNodeIds: number[] = [] // 批量拖拽的节点列表
let lastDragOverNodeId: number | null = null

// 处理编辑模式切换
const handleEditModeChange = (e: any) => {
  const checked = e.target?.checked ?? e
  console.log('📝 编辑模式change事件:', checked, 'event:', e)
  treeEditMode.value = checked
}

// 处理下载本体数据
const handleDownloadOntology = async () => {
  try {
    if (!taskId.value) {
      message.error('无效的任务ID')
      return
    }

    // 使用正确的参数：result_type=ontology，并添加时间戳
    const timestamp = Date.now()
    const apiUrl = `/python/api/pdf/task/${taskId.value}/result?result_type=ontology&t=${timestamp}`
    console.log('📥 下载 ontology 数据:', apiUrl)

    // 直接触发下载
    const link = document.createElement('a')
    link.href = apiUrl
    link.download = `ontology_${taskId.value}_${timestamp}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    message.success('开始下载')
  } catch (error) {
    console.error('下载失败:', error)
    message.error('下载失败')
  }
}

// 处理上传本体数据
const handleUploadOntology = () => {
  // 创建隐藏的文件选择器
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  input.onchange = async (e: any) => {
    const file = e.target?.files?.[0]
    if (!file) return

    try {
      if (!taskId.value) {
        message.error('无效的任务ID')
        return
      }

      console.log('📤 开始上传 ontology 文件:', file.name)
      const loadingMsg = message.loading('上传中...', 0)

      const formData = new FormData()
      formData.append('file', file)

      const apiUrl = `/python/api/pdf/task/${taskId.value}/ontology`
      const response = await fetch(apiUrl, {
        method: 'PUT',
        body: formData
      })

      const result = await response.json()
      loadingMsg()

      if (result.success) {
        message.success('上传成功')
        console.log('✅ 上传成功:', result.data)
        // TODO: 可能需要刷新页面数据
      } else {
        message.error(result.errMsg || '上传失败')
        console.error('❌ 上传失败:', result)
      }
    } catch (error) {
      console.error('上传出错:', error)
      message.error('上传失败')
    }
  }
  input.click()
}

// 处理拖拽开始
const handleDragStartNode = (nodeId: number) => {
  draggedNodeId = nodeId

  // 如果有多选节点，且拖拽的节点在选中列表中，则批量拖拽
  if (selectedNodeIds.value.length > 1 && selectedNodeIds.value.includes(nodeId)) {
    draggedNodeIds = [...selectedNodeIds.value]
    console.log('🎯 批量拖拽节点:', draggedNodeIds)
  } else {
    draggedNodeIds = [nodeId]
    console.log('🎯 单个拖拽节点:', nodeId)
  }
}

// 处理拖拽经过节点
const handleDragOverNode = (nodeId: number) => {
  lastDragOverNodeId = nodeId
}

// 处理树的全局 dragOver（记录目标节点）
const handleTreeDragOver = (event: DragEvent) => {
  // 这个函数什么都不做，只是为了 prevent default
}

// 处理树的全局 drop
const handleTreeDrop = (event: DragEvent) => {
  console.log('🎯 tree-list全局drop触发')

  if (!treeEditMode.value) return
  if (!lastDragOverNodeId) {
    console.log('⚠️ 没有记录到目标节点')
    return
  }

  // 获取拖拽的节点ID
  const draggedNodeId = Number(event.dataTransfer?.getData('text/plain'))

  console.log('📦 全局Drop:', {
    draggedNodeId,
    lastDragOverNodeId
  })

  if (draggedNodeId && lastDragOverNodeId && draggedNodeId !== lastDragOverNodeId) {
    handleNodeDrop(draggedNodeId, lastDragOverNodeId)
  }

  // 重置
  lastDragOverNodeId = null
}

// 处理 dragEnd（拖拽结束）
// dragEndNodeId 是被拖拽的节点ID（应该与 draggedNodeId 相同）
const handleDragEndOnNode = (dragEndNodeId: number) => {
  console.log('🎯 dragEnd事件触发:', {
    dragEndNodeId,
    draggedNodeId,
    lastDragOverNodeId
  })

  if (!treeEditMode.value) {
    console.log('⚠️ 非编辑模式，跳过处理')
    draggedNodeId = null
    lastDragOverNodeId = null
    return
  }

  if (!draggedNodeId) {
    console.log('⚠️ 没有记录到被拖拽的节点')
    return
  }

  if (lastDragOverNodeId === null || lastDragOverNodeId === undefined) {
    console.log('⚠️ 没有记录到目标节点（用户可能拖到空白处）')
    draggedNodeId = null
    lastDragOverNodeId = null
    return
  }

  // 验证：dragEndNodeId 应该与 draggedNodeId 相同
  if (dragEndNodeId !== draggedNodeId) {
    console.error('❌ dragEnd节点ID与dragStart节点ID不一致:', { dragEndNodeId, draggedNodeId })
    draggedNodeId = null
    lastDragOverNodeId = null
    return
  }

  console.log('✅ 拖拽完成，调用移动节点API:', {
    from: draggedNodeId,
    to: lastDragOverNodeId
  })

  handleNodeDrop(draggedNodeId, lastDragOverNodeId)

  // 清理拖拽状态
  draggedNodeId = null
  lastDragOverNodeId = null
}

// 监控编辑模式变化
watch(treeEditMode, async (newVal, oldVal) => {
  console.log('📝 树编辑模式watch触发:', newVal)

  // 退出编辑模式时，重新加载数据
  if (oldVal === true && newVal === false && taskId.value) {
    console.log('🔄 退出编辑模式，重新加载 ontology 数据...')
    message.info('正在刷新数据...')

    try {
      await loadOntologyData(taskId.value)
      message.success('数据已更新')
      console.log('✅ ontology 数据刷新完成')
    } catch (error) {
      console.error('❌ 刷新数据失败:', error)
      message.error('刷新数据失败')
    }
  }
})

// 初始化本体树构建逻辑
const { buildOntologyTree, expandMoreNode } = useOntologyTree()
// 开发模式（显示未匹配数据）
const isDevMode = ref(false)
// 未匹配的数据
const unmatchedData = ref<any[]>([])
// 展开/收起状态（使用 reviewItemCode 作为 key）
const expandedState = reactive<Record<string, boolean>>({})
// 树形结构的展开状态
const treeExpandedNodes = ref(new Set<any>())
// 选中的节点ID（支持多选）- 使用数组以确保响应式
const selectedNodeIds = ref<number[]>([])
// 兼容性：保持 selectedNodeId 用于单选场景
const selectedNodeId = computed(() => {
  return selectedNodeIds.value.length > 0 ? selectedNodeIds.value[0] : null
})
// 页面状态管理
const state = reactive({
  loading: false,
  activeFilter: 1 as number | null,
  checkListVisible: false,
  historyFilesVisible: false
})
// 批注提示信息
const markList = ref<any[]>([])
const getMarkList = async () => {
  // 开发/测试模式下，使用本地数据，不调用接口
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
// 统计数据
const statsData = ref<Record<string, any>>({})

// PDF相关数据
const pdfData = reactive({
  pdfUrl: '',
  currentPage: 1,
  highlightRects: [] as any[]
})

const pptData = reactive({
  pptUrl: ''
})

// 审查结果数据
const resultData = reactive<Record<string, any>>({ ...DEFAULT_REVIEW_RESULT })

// 当前选中的审查项
const activeItem = ref<Record<string, any>>({})

const resultBarWidth = computed(() => {
  if (statsData.value.resultFinishNum && statsData.value.resultNum) {
    const percentage = ((statsData.value.resultFinishNum / statsData.value.resultNum) * 100).toFixed(2)
    return `${percentage}%`
  } else return '0%'
})

// 筛选标签
const filterTabs = computed(() => createFilterTabs(statsData.value))

// 过滤后的审查项目
const filteredItems = computed(() => {
  // 开发模式：显示未匹配数据
  if (isDevMode.value) {
    return [
      {
        reviewItemCode: 'dev_unmatched',
        reviewItemName: '未匹配数据（开发模式）',
        children: unmatchedData.value.map((item, index) => ({
          uniqueId: `unmatched_${index}`,
          reviewItemName: '未匹配数据',
          reviewItemCode: 'dev_unmatched',
          sceneDesc: item.reason,
          fileText: item.span.targetText,
          page: item.span.page,
          spanList: [
            {
              pid: item.span.pid,
              text: item.span.targetText,
              // PDF中找到的最接近批注（用于第一个按钮）
              pdfAnnotations: item.bestMatch
                ? [
                    {
                      pageNum: item.bestMatch.pageNum,
                      rect: item.bestMatch.rect,
                      quadPoints: item.bestMatch.quadPoints
                    }
                  ]
                : []
            }
          ],
          // 保存原始span数据（用于第二个按钮：显示annotation.json期望的位置）
          _originalSpan: {
            page: item.span.page,
            quadPoints: item.span.quadPoints,
            pid: item.span.pid
          },
          legalBasicSourceList: [],
          showRiskTip:
            `annotation.json: uniqueId=${item.uniqueId}, page=${item.span.page}, pid=${item.span.pid}\n` +
            `最接近PDF批注: ${
              item.bestMatch
                ? `page=${item.bestMatch.pageNum}, IOU=${item.matchInfo.iou}, 文本相似度=${item.matchInfo.textSim}`
                : '无'
            }`,
          acceptStatus: 0,
          handleStatus: 0,
          _isDevMode: true // 标记为开发模式数据
        }))
      }
    ]
  }

  // 正常模式
  const dataList = resultData.dataList || []

  console.log('🌳 filteredItems 计算:', {
    原始数据长度: dataList.length,
    resultData: resultData,
    匹配数: dataList.filter((item: any) => item.spanList?.some((span: any) => span.pdfAnnotations?.length > 0)).length
  })

  // 按 reviewItemCode 分类
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

  // 处理相同审查依据的项目，重复的显示"同上"
  grouped.forEach(group => {
    const seenLegalBasis = new Map()
    group.children.forEach(item => {
      if (!item.legalBasicSourceList?.length) return
      // 生成审查依据的唯一标识
      const legalBasisKey = item.legalBasicSourceList
        .map(
          basis =>
            `${item.sceneDesc}${basis.source}${basis.basicIssue}${basis.basicNumber}${basis.basicDesc}${basis.sourceLink}`
        )
        .sort()
        .join('|')

      if (seenLegalBasis.has(legalBasisKey)) {
        // 重复的审查依据显示"同上"
        item.legalBasicHide = true
      } else {
        seenLegalBasis.set(legalBasisKey, true)
      }
    })
  })

  return grouped
})

// 点击审查项处理
const pdfReaderRef = ref<InstanceType<typeof PdfViewer>>()
const contentViewerRef = ref<any>(null)
const leftContentType = ref<'pdf' | 'qa' | 'ppt'>('pdf')  // 默认显示PDF
const folderTreeRef = ref<any>(null)
const handleReviewItemClick = async (item: any) => {
  if (!item) return
  activeItem.value = item ?? {}

  console.log('点击审查项:', {
    uniqueId: item.uniqueId,
    spanList: item.spanList,
    hasPdfAnnotations: item.spanList?.some((s: any) => s.pdfAnnotations?.length > 0)
  })

  // 优先使用 PDF 批注数据进行跳转
  const spanList = item.spanList ?? []
  let targetPage = -1
  let highlightRects: any[] = []

  if (spanList.length > 0) {
    // 遍历所有 span，查找有 pdfAnnotations 的
    spanList.forEach((span: any) => {
      const pdfAnns = span.pdfAnnotations ?? []
      if (pdfAnns.length > 0) {
        // 使用第一个批注的位置信息
        const firstAnn = pdfAnns[0]
        if (targetPage === -1) {
          targetPage = firstAnn.pageNum
        }

        // 将所有批注的位置添加到高亮列表
        pdfAnns.forEach((ann: any) => {
          console.log('添加高亮区域:', ann)
          highlightRects.push({
            pageNum: ann.pageNum, // 使用 pageNum 而不是 page
            quadPoints: ann.quadPoints,
            rect: ann.rect,
            jump: true, // 可滚动到对应的选区
            annotations: item.acceptStatus === 1 && item.acceptText ? [{ content: item.acceptText }] : []
          })
        })
      }
    })
  }

  // 如果没有 PDF 批注数据，回退到原有的 position 逻辑
  if (targetPage === -1) {
    const position = item.position ?? []
    const annotations = item.acceptStatus === 1 && item.acceptText ? [{ content: item.acceptText }] : []

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

  // 更新 PDF 显示
  pdfData.highlightRects = highlightRects

  // 只有在有效页码时才跳转（页码必须 >= 1）
  if (targetPage > 0 && highlightRects.length > 0) {
    // 使用第一个高亮区域进行跳转
    const firstHighlight = highlightRects[0]

    // 方法1: 使用 PdfViewer 的 scrollToAnnotation 方法（推荐）
    const pdfViewer = contentViewerRef.value?.pdfViewerRef
    if (pdfViewer?.scrollToAnnotation) {
      await pdfViewer.scrollToAnnotation(firstHighlight)
    } else {
      // 方法2: 回退到简单的页面跳转
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

// 开发模式：定位到最接近的PDF批注
const handleShowBestMatch = async (item: any) => {
  console.log('定位到最接近的PDF批注:', item)

  // 直接使用现有逻辑（与 handleReviewItemClick 相同）
  await handleReviewItemClick(item)
}

// 开发模式：定位到annotation.json的原始位置
const handleShowOriginalSpan = async (item: any) => {
  console.log('定位到annotation.json的原始位置:', item)

  if (!item._originalSpan || !item._originalSpan.quadPoints) {
    console.warn('没有找到原始span数据')
    return
  }

  const originalSpan = item._originalSpan
  const targetPage = originalSpan.page

  // 构造高亮区域（使用annotation.json中的quadPoints）
  const highlightRects = [
    {
      pageNum: targetPage,
      quadPoints: originalSpan.quadPoints,
      rect: null, // 可以不提供rect，使用quadPoints
      jump: true
    }
  ]

  // 更新 PDF 显示
  pdfData.highlightRects = highlightRects

  // 跳转到对应位置
  const pdfViewer = contentViewerRef.value?.pdfViewerRef
  if (pdfViewer?.scrollToAnnotation) {
    await pdfViewer.scrollToAnnotation(highlightRects[0])
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

// 获取审查数据
const isOnlyReviewData = ref(false)
const getData = async () => {
  state.loading = true
  Object.assign(resultData, DEFAULT_REVIEW_RESULT)

  // 优先使用本地 JSON 文件数据
  if (reviewListData.value) {
    console.log('✅ 使用本地 JSON 数据渲染列表', {
      'reviewListData.value': reviewListData.value,
      dataList长度: reviewListData.value?.dataList?.length
    })
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

    //如果审查结果没有存在风险项，切换至全部，默认在发现风险标签下
    if (!statsData.value.resultNum && existRisk.value) {
      existRisk.value = false
      setActiveFilter(null)
    }

    // 初始化树形结构的展开状态 - 默认展开第一级节点
    initTreeExpandState()
    return
  }

  // 如果没有本地数据，使用接口数据
  // 开发/测试模式下，跳过接口调用
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

  //如果审查结果没有存在风险项，切换至全部，默认在发现风险标签下
  if (!statsData.value.resultNum && existRisk.value) {
    existRisk.value = false
    setActiveFilter(null)
  }

  // 初始化树形结构的展开状态
  initTreeExpandState()
}

// 初始化树形结构的展开状态 - 默认展开第一级节点
const initTreeExpandState = () => {
  const firstLevelNodes = new Set<string>()
  resultData.dataList?.forEach((item: any) => {
    // 添加一级节点（审查项）
    if (item.reviewItemCode) {
      firstLevelNodes.add(item.reviewItemCode)
    }
  })
  treeExpandedNodes.value = firstLevelNodes
  console.log('🌳 初始化树形展开状态:', firstLevelNodes)
}
// ==================== 业务方法 ====================

// 导航方法
const goHome = () => {
  try {
    sessionStorage.setItem('clearHomeUpload', '1')
  } catch {}
  router.push({ name: 'HomeIndex' })
}

// 左侧悬浮菜单跳转
const goToReview = () => {
  router.push({ name: 'ComplianceReview' })
}
const goToDemo = () => {
  router.push('/review')
}

// ========== 上传与查询（最小接入） ==========
// 上传PDF
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
    // 如需附加任务ID等字段，可按需追加：form.append('taskId', taskId.value)
    const resp = await fetch('/python/api/pdf/upload_pdf', {
      method: 'POST',
      body: form
    })
    const json = await resp.json().catch(() => ({}))
    if (resp.ok && json?.success !== false) {
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

// 关键词查询
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
    // 后端查询接口（app/routers/search.py）
    const currentTaskId = String((route.query.taskId as string) || taskId.value || '')
    const url = `/python/api/search${currentTaskId ? `?taskId=${encodeURIComponent(currentTaskId)}` : ''}`
    const resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ keywords, top_k: 5, collection_name: 'pdf', taskId: currentTaskId || undefined })
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

// 切换开发模式
const toggleDevMode = () => {
  isDevMode.value = !isDevMode.value
  console.log('开发模式:', isDevMode.value ? '开启' : '关闭')
}

// PDF 批注数据
const pdfAnnotationsData = ref<any>(null)
const reviewListData = ref<any>(null)
const pdfAnnotations = ref<any[]>([]) // 从 PDF 中提取的批注

/**
 * 计算两个矩形的重叠度（IOU - Intersection over Union）
 */
const calculateIOU = (quad1: number[], quad2: number[]) => {
  if (!quad1 || !quad2 || quad1.length < 8 || quad2.length < 8) return 0

  // quadPoints 格式: [x1,y1, x2,y2, x3,y3, x4,y4] - 4个顶点坐标
  // 简化计算：提取边界框
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

  // 计算交集
  const x1 = Math.max(box1.x1, box2.x1)
  const y1 = Math.max(box1.y1, box2.y1)
  const x2 = Math.min(box1.x2, box2.x2)
  const y2 = Math.min(box1.y2, box2.y2)

  if (x2 < x1 || y2 < y1) return 0 // 无交集

  const intersection = (x2 - x1) * (y2 - y1)
  const area1 = (box1.x2 - box1.x1) * (box1.y2 - box1.y1)
  const area2 = (box2.x2 - box2.x1) * (box2.y2 - box2.y1)
  const union = area1 + area2 - intersection

  return intersection / union
}

/**
 * 文本相似度计算（简单的包含关系检查）
 */
const textSimilarity = (text1: string, text2: string) => {
  if (!text1 || !text2) return 0
  const t1 = text1.trim().toLowerCase()
  const t2 = text2.trim().toLowerCase()

  if (t1 === t2) return 1
  if (t1.includes(t2) || t2.includes(t1)) return 0.8

  // 计算最长公共子串比例
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

/**
 * ═══════════════════════════════════════════════════════════════════
 * 核心匹配逻辑 - 三方数据关联
 * ═══════════════════════════════════════════════════════════════════
 *
 * 数据源：
 * 1. annotation.json (来自后端) - 包含 uniqueId 和 span 位置信息
 *    结构: { annotations: [{ uniqueId, spanList: [{ page, quadPoints, targetText, pid }] }] }
 *
 * 2. PDF.js 批注数据 (从 PDF 文件提取) - 包含真实的批注位置和内容
 *    结构: [{ id, pageNum, quadPoints, rect, contents, 原始数据.contentsObj.str }]
 *
 * 3. 右侧列表数据 (reviewListData.dataList) - 包含审查项详情
 *    结构: [{ uniqueId, spanList: [{ pid, start, end, text }] }]
 *
 * 匹配流程：
 * Step 1: annotation.json 的 span ←→ PDF.js 批注数据
 *         通过 (page/pageNum + quadPoints IOU + targetText 相似度) 进行匹配
 *         得到: span.pdfAnnotations = [批注数据]
 *
 * Step 2: 使用 uniqueId 将匹配结果写入右侧列表
 *         annotation.uniqueId → reviewListData.dataList 中找到对应 item
 *         span.pid → item.spanList 中找到对应 reviewSpan
 *         写入: reviewSpan.pdfAnnotations = [批注数据 (含 pageNum, rect, quadPoints)]
 *
 * Step 3: 点击右侧列表项时
 *         读取 item.spanList[].pdfAnnotations
 *         使用 pageNum + rect 调用 scrollToAnnotation() 跳转到 PDF 位置
 *
 * 问题诊断：
 * - 如果右侧列表无法跳转，可能原因：
 *   ✓ Step1 匹配率过低 (IOU < 0.5 或文本相似度低)
 *   ✓ Step2 uniqueId 无法在 reviewListData 中找到 (数据源不一致)
 *   ✓ Step2 pid 无法在 spanList 中找到 (pid 不匹配)
 *   ✓ pdfAnnotations 中缺少 pageNum 或 rect
 *
 * 匹配策略（基于行业最佳实践）：
 * 1. 按页码分组 - 减少匹配范围
 * 2. 使用 quadPoints IOU (Intersection over Union) - 计算区域重叠度
 * 3. 使用 targetText 相似度 - 文本验证
 * 4. 综合得分 = IOU * 0.6 + 文本相似度 * 0.4
 * 5. 阈值 > 0.5 才建立映射
 * ═══════════════════════════════════════════════════════════════════
 */
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

  console.log('数据概览:', {
    'annotation.json 数量': annotationJson.length,
    'PDF.js 批注数量': pdfAnns.length,
    右侧列表数据数量: reviewListData.value?.dataList?.length || 0
  })

  // 1. 按页码分组 PDF 批注
  const pdfAnnsByPage = new Map<number, any[]>()
  const matchedPdfAnnIds = new Set<string>() // 记录已匹配的 PDF 批注
  pdfAnns.forEach(ann => {
    if (!pdfAnnsByPage.has(ann.pageNum)) {
      pdfAnnsByPage.set(ann.pageNum, [])
    }
    pdfAnnsByPage.get(ann.pageNum)!.push(ann)
  })

  let matchCount = 0
  let totalSpans = 0
  const unmatchedSpans: any[] = [] // 未匹配的 span

  // 2. 遍历每个 annotation 的 spanList
  annotationJson.forEach(annotation => {
    annotation.spanList?.forEach((span: any) => {
      totalSpans++
      const page = span.page
      const quadPoints = span.quadPoints
      const targetText = span.targetText

      // 获取同页的 PDF 批注
      const samePage = pdfAnnsByPage.get(page) || []
      if (!samePage.length) {
        unmatchedSpans.push({
          reason: '该页无批注',
          span,
          annotation
        })
        return
      }

      // 3. 寻找最佳匹配
      let bestMatch: any = null
      let bestScore = 0

      samePage.forEach(pdfAnn => {
        // 计算 IOU
        const iou = calculateIOU(quadPoints, pdfAnn.quadPoints)

        // 计算文本相似度
        const textSim = textSimilarity(targetText, pdfAnn.原始数据?.contentsObj?.str || pdfAnn.contents)

        // 综合得分：IOU 权重 0.6，文本相似度权重 0.4
        const score = iou * 0.6 + textSim * 0.4

        if (score > bestScore) {
          bestScore = score
          bestMatch = pdfAnn
        }
      })

      // 4. 如果匹配度超过阈值，建立映射
      if (bestMatch && bestScore > 0.5) {
        // 计算匹配详情
        const iou = calculateIOU(quadPoints, bestMatch.quadPoints)
        const textSim = textSimilarity(targetText, bestMatch.原始数据?.contentsObj?.str || bestMatch.contents)

        // PDF.js 跳转和高亮所需的最小数据集
        const matchInfo = {
          // 基本标识
          id: bestMatch.id,
          pdfAnnotationId: bestMatch.pdfAnnotationId,

          // 跳转定位数据（必需）
          pageNum: bestMatch.pageNum, // 页码
          rect: Array.from(bestMatch.rect || []), // 矩形边界 [x1, y1, x2, y2]
          quadPoints: Array.from(bestMatch.quadPoints || []), // 精确四边形坐标（8个点）

          // 高亮显示数据（可选）
          subtype: bestMatch.subtype, // "Highlight" 等
          color: bestMatch.color ? Array.from(bestMatch.color) : null, // RGB 颜色
          opacity: bestMatch.opacity, // 透明度

          // 匹配信息（调试用）
          score: bestScore.toFixed(3),
          iou: iou.toFixed(3),
          textSim: textSim.toFixed(3)
        }

        // 在 annotation.json 的 span 中添加批注引用
        if (!span.pdfAnnotations) {
          span.pdfAnnotations = []
        }
        span.pdfAnnotations.push(matchInfo)

        // ═══════════════════════════════════════════════════════
        // Step 2: 同时写入右侧列表数据的 spanList 中
        // ═══════════════════════════════════════════════════════
        // 逻辑：
        // 1. 遍历 reviewListData.dataList (右侧列表数据)
        // 2. 通过 item.uniqueId === annotation.uniqueId 找到父类 item
        // 3. 遍历 item.spanList，通过 reviewSpan.pid === span.pid 找到子类 span
        // 4. 将 PDF 批注数据写入 reviewSpan.pdfAnnotations
        // 5. 右侧列表点击时，从 reviewSpan.pdfAnnotations 读取跳转数据
        // ═══════════════════════════════════════════════════════
        let foundInReviewList = false
        let foundSpan = false
        if (reviewListData.value?.dataList) {
          reviewListData.value.dataList.forEach((item: any) => {
            if (item.uniqueId === annotation.uniqueId) {
              foundInReviewList = true

              // 记录 spanList 中所有的 pid，用于诊断
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

              // 如果 pid 匹配失败，输出详细的诊断信息
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

        // Step 2 失败诊断
        if (!foundInReviewList) {
          console.warn(`    ⚠️ Step2 失败: uniqueId 在 reviewListData 中未找到`, {
            uniqueId: annotation.uniqueId,
            '所有可用 uniqueId': reviewListData.value?.dataList?.map((item: any) => item.uniqueId).slice(0, 10)
          })
        }

        matchedPdfAnnIds.add(bestMatch.id)
        matchCount++

        console.log(`✓ 匹配成功 [${matchCount}]: page=${page}, score=${bestScore.toFixed(3)}`, {
          uniqueId: annotation.uniqueId,
          pid: span.pid,
          spanText: targetText?.substring(0, 30),
          pdfText: (bestMatch.原始数据?.contentsObj?.str || bestMatch.contents)?.substring(0, 30),
          iou: calculateIOU(quadPoints, bestMatch.quadPoints).toFixed(3)
        })
      } else {
        // 简化：直接说哪个字段没匹配
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
          bestScore,
          details: {
            hasQuadPoints: !!quadPoints && quadPoints.length > 0,
            hasTargetText: !!targetText && targetText.trim() !== '',
            iou: bestMatch ? calculateIOU(quadPoints, bestMatch.quadPoints).toFixed(3) : 'N/A',
            textSim: bestMatch
              ? textSimilarity(targetText, bestMatch.原始数据?.contentsObj?.str || bestMatch.contents).toFixed(3)
              : 'N/A'
          }
        })
      }
    })
  })

  // 找出未匹配的 PDF 批注
  const unmatchedPdfAnns = pdfAnns.filter(ann => !matchedPdfAnnIds.has(ann.id))

  console.log(`
═══════════════════════════════════════════════════════
    匹配完成
    总 Span 数: ${totalSpans}
    成功匹配: ${matchCount}
    未匹配 Span: ${unmatchedSpans.length}
    未匹配 PDF 批注: ${unmatchedPdfAnns.length}
    匹配率: ${((matchCount / totalSpans) * 100).toFixed(2)}%
═══════════════════════════════════════════════════════
`)

  // 打印未匹配的 Span
  if (unmatchedSpans.length > 0) {
    console.log('\n❌ 未匹配的 Span:')
    unmatchedSpans.forEach((item, index) => {
      console.log(`[${index + 1}] ${item.reason}`)
      console.log('  annotation.json数据:', {
        uniqueId: item.annotation.uniqueId,
        page: item.span.page,
        pid: item.span.pid,
        targetText: item.span.targetText?.substring(0, 50),
        quadPoints: item.span.quadPoints?.slice(0, 8)
      })

      if (item.bestMatch) {
        console.log('  最接近的PDF批注:', {
          id: item.bestMatch.id,
          pageNum: item.bestMatch.pageNum,
          text: item.bestMatch.原始数据?.contentsObj?.str?.substring(0, 50),
          quadPoints: item.bestMatch.quadPoints?.slice(0, 8),
          iou: item.details.iou,
          textSim: item.details.textSim
        })
      } else {
        console.log('  最接近的PDF批注: 无')
      }
    })
  }

  // 打印未匹配的 PDF 批注
  if (unmatchedPdfAnns.length > 0) {
    console.log('\n❌ 未匹配的 PDF 批注:')
    unmatchedPdfAnns.forEach((ann, index) => {
      console.log(`[${index + 1}]`, {
        id: ann.id,
        pageNum: ann.pageNum,
        name: ann.name,
        subtype: ann.subtype,
        contents: ann.contents?.substring(0, 50),
        contentsObjStr: ann.原始数据?.contentsObj?.str?.substring(0, 50),
        quadPoints: ann.quadPoints
      })
    })
  }

  // 保存未匹配数据（供开发模式使用）
  unmatchedData.value = unmatchedSpans.map(item => ({
    uniqueId: item.annotation.uniqueId,
    reason: item.reason,
    span: {
      page: item.span.page,
      pid: item.span.pid,
      targetText: item.span.targetText,
      quadPoints: item.span.quadPoints
    },
    bestMatch: item.bestMatch
      ? {
          id: item.bestMatch.id,
          pageNum: item.bestMatch.pageNum,
          text: item.bestMatch.原始数据?.contentsObj?.str,
          quadPoints: item.bestMatch.quadPoints,
          rect: item.bestMatch.rect
        }
      : null,
    matchInfo: {
      iou: item.details?.iou,
      textSim: item.details?.textSim
    }
  }))

  console.log('保存未匹配数据:', unmatchedData.value.length, '条')

  // ═══════════════════════════════════════════════════════
  // 统计右侧列表中未匹配的项
  // ═══════════════════════════════════════════════════════
  if (reviewListData.value?.dataList) {
    let totalReviewItems = 0
    let matchedReviewItems = 0
    let unmatchedReviewItems: any[] = []

    reviewListData.value.dataList.forEach((item: any) => {
      totalReviewItems++

      // 检查该项是否有任何 span 匹配到了 PDF 批注
      const hasMatch = item.spanList?.some((span: any) => span.pdfAnnotations?.length > 0)

      if (hasMatch) {
        matchedReviewItems++
      } else {
        unmatchedReviewItems.push({
          uniqueId: item.uniqueId,
          sceneDesc: item.sceneDesc,
          spanList: item.spanList
        })
      }
    })

    console.log(`
═══════════════════════════════════════════════════════
    右侧列表匹配统计
    总项数: ${totalReviewItems}
    已匹配: ${matchedReviewItems}
    未匹配: ${unmatchedReviewItems.length}
    匹配率: ${((matchedReviewItems / totalReviewItems) * 100).toFixed(2)}%
═══════════════════════════════════════════════════════
`)

    if (unmatchedReviewItems.length > 0) {
      console.log('\n❌ 右侧列表中未匹配的项:')
      unmatchedReviewItems.forEach((item, index) => {
        console.log(`[${index + 1}] uniqueId: ${item.uniqueId}`)
        console.log(`    场景描述: ${item.sceneDesc}`)
        console.log(
          `    spanList:`,
          item.spanList?.map((s: any) => ({
            pid: s.pid,
            text: s.text?.substring(0, 30)
          }))
        )
      })
    }
  }

  // 更新数据
  pdfAnnotationsData.value = { annotations: annotationJson }
}

// 处理 PDF 批注加载完成
const handleAnnotationsLoaded = (annotations: any[]) => {
  console.log('📄 PDF.js 批注提取完成:', annotations?.length, '条')
  pdfAnnotations.value = annotations

  // 如果 annotation.json 已经加载，立即进行匹配
  if (pdfAnnotationsData.value?.annotations) {
    console.log('✅ annotation.json 已就绪，触发匹配')
    matchAnnotations()
  } else {
    console.log('⏳ 等待 annotation.json 加载...')
  }
}

// 处理问答返回的图谱数据
const handleQaGraphUpdate = (subgraph: any) => {
  console.log('🔔 handleQaGraphUpdate 被调用, subgraph:', subgraph)

  if (!subgraph || !subgraph.nodes || !subgraph.edges) {
    console.log('⚠️ subgraph 数据不完整，跳过更新')
    return
  }

  console.log('📊 问答返回图谱数据:', subgraph)
  console.log('📊 节点数量:', subgraph.nodes.length, '边数量:', subgraph.edges.length)

  // 提取节点和边数据
  const nodesData = subgraph.nodes.map((n: any) => n.data)
  const edgesData = subgraph.edges.map((e: any) => e.data)

  console.log('📊 提取后的节点数据:', nodesData)
  console.log('📊 提取后的边数据:', edgesData)

  // 更新 FolderTree 组件的图谱数据
  if (folderTreeRef.value && folderTreeRef.value.updateGraphData) {
    folderTreeRef.value.updateGraphData(nodesData, edgesData)
    console.log('✅ 已更新 FolderTree 图谱数据')
  } else {
    console.warn('⚠️ FolderTree ref 不可用')
  }
}

// 处理切换问答模式
const handleToggleQa = (isActive: boolean) => {
  console.log('🔄 切换问答模式:', isActive ? '打开' : '关闭')
  leftContentType.value = isActive ? 'qa' : 'pdf'
}

// 处理切换内容模式
const handleSwitchMode = (mode: 'pdf' | 'qa' | 'ppt') => {
  console.log('🔄 切换内容模式:', mode)
  leftContentType.value = mode
}

// 树形结构的原始数据
const rawTreeData = ref<any[]>([])
// agentTreeData 已移除，直接使用 rawTreeData (ontology)
const allTreeNodes = ref<any[]>([])
const builtTreeData = ref<any[]>([])
// 业务本体树数据（独立数据源，按 directory_path 分组）
const ontologyTreeData = ref<any[]>([])
const ontologyRawData = ref<any[]>([])  // 业务本体树的原始数据（独立加载）
// 预构建的树数据（从 _labeled_tree.json 加载的）
const prebuiltTreeData = ref<any[]>([])
// 是否使用了预构建的树
const hasPrebuiltTree = ref(false)
// 节点映射表（line_id -> node）
const nodeMap = ref<Record<number, any>>({})

// 结构化数据（包含 fields 信息，用于知识图谱）
const structuredData = ref<any[]>([])

// 有 fields 的节点（用于过滤图谱）
const nodesWithFields = ref<any[]>([])

// 采购标签图谱数据
const graphNodes = ref<Array<{ id: string; label: string; type: string }>>([])
const graphEdges = ref<Array<{ id: string; source: string; target: string; label: string }>>([])

// 采购标签图谱导航面板
const isNavCollapsed = ref(false)
const graphTreeData = ref<any[]>([])
const selectedGraphNodeId = ref<string | null>(null)
const cytoscapeRef = ref<any>(null)


// 是否启用 ontology 字段过滤（控制是否只显示 fields 不为空的节点）
const enableOntologyFieldFilter = ref(false)

// 标签层级顺序（从 label_hierarchy.json 加载）
const labelHierarchy = ref<{ label: string; children: string[] }[]>([])
const labelOrderMap = ref<Map<string, number>>(new Map())

// 显示的树数据
const displayTreeData = computed(() => {
  return builtTreeData.value
})

// 合并段落：将 connect 关系的 fstline/para 合并成一个 paragraph 节点
const mergeParagraphs = (nodes: any[]): any[] => {
  const processedIds = new Set<number>()
  const mergedNodes: any[] = []

  nodes.forEach(node => {
    if (processedIds.has(node.line_id)) return

    // 如果是 fstline 或 para，尝试合并
    if (node.class === 'fstline' || node.class === 'para') {
      // 查找所有通过 connect 关系连接的节点
      const paragraphNodes: any[] = [node]
      processedIds.add(node.line_id)

      // 查找所有 parent_id 指向当前节点且 relation 为 connect 的节点
      const findConnectedNodes = (currentId: number) => {
        nodes.forEach(n => {
          if (n.parent_id === currentId && n.relation === 'connect' && !processedIds.has(n.line_id)) {
            paragraphNodes.push(n)
            processedIds.add(n.line_id)
            // 递归查找连接到这个节点的节点
            findConnectedNodes(n.line_id)
          }
        })
      }

      findConnectedNodes(node.line_id)

      // 提取所有行的 box 和 page 信息
      const boxes = paragraphNodes
        .filter(n => n.box && n.box.length === 4)
        .map(n => ({
          box: n.box,
          page: n.page,
          line_id: n.line_id
        }))

      console.log(`📝 合并段落 [line_id=${node.line_id}]:`, {
        原始行数: paragraphNodes.length,
        box数量: boxes.length,
        页码范围: [...new Set(boxes.map(b => b.page))],
        文本长度: paragraphNodes
          .map(n => n.text || n.content)
          .filter(Boolean)
          .join(' ').length
      })

      // 创建合并后的段落节点
      const mergedNode = {
        ...node,
        class: 'paragraph', // 改为 paragraph 类型
        text: paragraphNodes
          .map(n => n.text || n.content)
          .filter(Boolean)
          .join(' '), // 合并文本
        boxes: boxes, // 保存所有行的 box 信息（用于多区域高亮）
        _originalNodes: paragraphNodes, // 保存原始节点（用于调试）
        children: []
      }

      mergedNodes.push(mergedNode)
    } else {
      // 其他类型节点直接添加
      mergedNodes.push(node)
      processedIds.add(node.line_id)
    }
  })

  return mergedNodes
}

// 构建树形结构（参考 my-app/tree）
const buildTree = async () => {
  if (!rawTreeData.value.length) {
    console.log('⚠️ 原始数据为空，无法构建树')
    return
  }

  console.log('🌲 开始构建树形结构，原始数据数量:', rawTreeData.value.length)

  // 第一步：合并段落节点
  const mergedData = mergeParagraphs(rawTreeData.value)
  console.log('📝 段落合并后的数据数量:', mergedData.length)

  // 过滤掉 meta 类型的节点（author、affili、mail 等）和 footer 节点
  const filteredData = mergedData.filter(n => n.relation !== 'meta' && n.class !== 'footer')
  console.log('🗑️ 过滤 meta/footer 节点后的数据数量:', filteredData.length)

  // 更新 allTreeNodes 为过滤后的数据（重要！用于查找节点）
  allTreeNodes.value = filteredData

  // 调试：查看合并后的段落节点
  const paragraphNodes = mergedData.filter(n => n.class === 'paragraph')
  console.log('📝 paragraph 节点数量:', paragraphNodes.length)
  if (paragraphNodes.length > 0) {
    console.log('📝 第一个 paragraph 节点示例:', paragraphNodes[0])
  }

  // 创建节点映射（使用过滤后的数据）
  const nodeMap = new Map()
  filteredData.forEach(item => {
    nodeMap.set(item.line_id, {
      ...item,
      children: []
    })
  })

  // 先找到每个节点的真正父节点（处理 equality 链）
  const findRealParent = (item: any): number => {
    if (item.parent_id === -1) {
      return -1
    }

    if (item.relation === 'contain') {
      // contain 关系：parent_id 就是真正的父节点
      return item.parent_id
    }

    if (item.relation === 'equality') {
      // equality 关系：沿着 parent_id 链追溯，找到第一个 contain 关系的节点
      let current = filteredData.find(n => n.line_id === item.parent_id)
      while (current) {
        if (current.relation === 'contain') {
          // 找到了 contain 节点，它的 parent_id 就是真正的父节点
          return current.parent_id
        } else if (current.relation === 'equality') {
          // 继续往上找
          current = filteredData.find(n => n.line_id === current.parent_id)
        } else {
          break
        }
      }
    }

    // 其他情况或找不到，返回原 parent_id
    return item.parent_id
  }

  // 构建父子关系
  const roots: any[] = []
  filteredData.forEach(item => {
    const node = nodeMap.get(item.line_id)

    // 跳过 connect 关系（已在段落合并中处理）
    if (item.relation === 'connect') {
      return
    }

    const realParentId = findRealParent(item)

    if (realParentId === -1) {
      // 根节点
      roots.push(node)
    } else {
      // 添加到父节点的 children
      const parent = nodeMap.get(realParentId)
      if (parent) {
        parent.children.push(node)
      } else {
        // 找不到父节点，作为根节点
        console.warn('找不到父节点:', realParentId, '节点:', item)
        roots.push(node)
      }
    }
  })

  builtTreeData.value = roots
  console.log('✅ 树形结构构建完成，根节点数量:', roots.length)

  // 生成知识图谱数据
  await buildGraphData()

  // 调试：检查 SEC1 和 SEC2 节点的层级结构
  const sec1Nodes = filteredData.filter(n => n.class === 'sec1')
  const sec2Nodes = filteredData.filter(n => n.class === 'sec2')

  console.log(
    '🔍 SEC1 节点检查:',
    sec1Nodes.map(n => ({
      line_id: n.line_id,
      text: n.text?.substring(0, 30),
      parent_id: n.parent_id,
      relation: n.relation,
      realParent: findRealParent(n),
      计算后的父节点: nodeMap.get(findRealParent(n))?.text?.substring(0, 30)
    }))
  )

  console.log(
    '🔍 SEC2 节点检查:',
    sec2Nodes.map(n => ({
      line_id: n.line_id,
      text: n.text?.substring(0, 30),
      parent_id: n.parent_id,
      relation: n.relation,
      realParent: findRealParent(n),
      计算后的父节点: nodeMap.get(findRealParent(n))?.text?.substring(0, 30)
    }))
  )

  // 默认展开第一层（根节点）
  const firstLevel = new Set<number>()
  filteredData.filter(n => n.parent_id === -1 && n.relation !== 'meta').forEach(n => firstLevel.add(n.line_id))

  treeExpandedNodes.value = firstLevel
  console.log('🌲 默认展开节点:', firstLevel)
}

// 构建按标签分组的树形结构
const buildTreeByLabel = async () => {
  // 直接使用 rawTreeData（ontology 数据）
  const dataSource = rawTreeData.value

  if (!dataSource.length) {
    console.log('⚠️ 原始数据为空，无法构建树')
    return
  }

  console.log('🏗️ 业务语义结构树数据源: rawTreeData (ontology)')
  console.log('   - 数据节点数:', dataSource.length)

  let labelRoots

  // ontology 数据已经是完整的树形结构，直接使用
  console.log('📦 数据已包含 children 结构，直接使用')
  labelRoots = dataSource

  // 如果没有标签，回退到原始结构
  if (!labelRoots || labelRoots.length === 0) {
    console.warn('⚠️ 数据中没有标签字段，回退到原始结构')
    buildTree()
    return
  }

  // 使用统一的排序函数
  sortTreeByHierarchy(labelRoots)

  builtTreeData.value = labelRoots
  console.log('✅ 按标签分组的树形结构构建完成')
  console.log('  - 根标签数量:', labelRoots.length)

  // 生成知识图谱数据
  await buildGraphData()

  // 默认全部关闭（不展开任何节点）
  treeExpandedNodes.value = new Set<number>()
  console.log('🌲 默认展开节点: 0 (全部关闭)')
}

// 加载业务本体树数据（独立数据源）
const loadOntologyTreeData = async (taskId: string) => {
  try {
    const apiUrl = `/python/api/pdf/task/${taskId}/result?result_type=ontology&t=${Date.now()}`
    console.log(`🔄 加载业务本体树数据:`, apiUrl)
    const response = await fetch(apiUrl)
    if (response.ok) {
      const jsonData = await response.json()

      // 处理 API 格式
      let treeData
      if (jsonData.success && jsonData.data && jsonData.data.dataList) {
        treeData = jsonData.data.dataList
      } else if (jsonData.tree) {
        treeData = jsonData.tree
      } else {
        treeData = jsonData
      }

      const processedData = Array.isArray(treeData) ? treeData : [treeData]

      // 转换格式
      const convertedData = convertAPITreeData(processedData)

      ontologyRawData.value = convertedData
      console.log('✅ 业务本体树原始数据已保存，节点数:', ontologyRawData.value.length)

      // 构建业务本体树
      await buildTreeByDirectoryPath()
    }
  } catch (e) {
    console.error('❌ 业务本体树数据加载失败:', e)
  }
}

// 构建按 directory_path 分组的业务本体树
const buildTreeByDirectoryPath = async () => {
  // 使用 ontologyRawData（业务本体树独立数据源）
  const dataSource = ontologyRawData.value

  if (!dataSource.length) {
    console.log('⚠️ 业务本体树原始数据为空，无法构建')
    return
  }

  console.log('🏗️ 构建业务本体树，数据源: ontologyRawData')
  console.log('   - 数据节点数:', dataSource.length)

  // 按路径构建树形结构
  const buildTreeByPath = (nodes: any[]): any[] => {
    const pathMap = new Map<string, any>() // path -> 路径节点
    const result: any[] = []
    let virtualNodeIdCounter = 100000

    // 第一步：扁平化所有节点，保留原始父子关系
    const flattenNodesWithParent = (nodes: any[], parent: any = null): any[] => {
      const flat: any[] = []
      nodes.forEach(node => {
        const nodeWithParent = { ...node, _parent: parent }
        flat.push(nodeWithParent)
        if (node.children && node.children.length > 0) {
          flat.push(...flattenNodesWithParent(node.children, nodeWithParent))
        }
      })
      return flat
    }

    const allNodes = flattenNodesWithParent(nodes)
    console.log('   - 扁平化节点总数:', allNodes.length)

    // 第二步：收集所有非空 label，构建路径树骨架
    const labelsSet = new Set<string>()
    allNodes.forEach(node => {
      const label = node.directory_path || node.label || ''
      if (label && label.trim()) {
        labelsSet.add(label)
      }
    })
    console.log('   - 非空 label 数量:', labelsSet.size)

    // 第三步：根据 label 构建路径树骨架
    Array.from(labelsSet).forEach(label => {
      const parts = label.split('/').filter(p => p.trim())
      let currentPath = ''
      let currentParent: any = null

      parts.forEach((part) => {
        currentPath = currentPath ? `${currentPath}/${part}` : part

        if (!pathMap.has(currentPath)) {
          const pathNode: any = {
            line_id: virtualNodeIdCounter++,
            text: part,
            type: 'label',  // 标记为业务本体
            _isPathNode: true,
            _path: currentPath,
            children: []
          }
          pathMap.set(currentPath, pathNode)

          if (currentParent) {
            currentParent.children.push(pathNode)
          } else {
            result.push(pathNode)
          }
        }
        currentParent = pathMap.get(currentPath)
      })
    })
    console.log('   - 路径树根节点数:', result.length)

    // 第四步：挂载所有节点
    // 建立原始节点到内容节点的映射
    const nodeToContentNodeMap = new Map<any, any>()

    allNodes.forEach(node => {
      const label = node.directory_path || node.label || ''

      if (label && label.trim()) {
        // label 不为空：在路径节点下创建内容节点（显示 content）
        const pathNode = pathMap.get(label)
        if (pathNode) {
          const contentNode = {
            line_id: node.line_id || virtualNodeIdCounter++,
            text: node.content?.substring(0, 100) || node.title || '',
            type: 'aggregate',  // 标记为业务实体
            content: node.content,
            title: node.title,
            pid: node.pid,
            location: node.location,
            fields: node.fields,
            boxes: node.boxes,
            page: node.page,
            children: [],
            _originalNode: node
          }

          pathNode.children.push(contentNode)
          nodeToContentNodeMap.set(node, contentNode)
        }
      }
    })

    // 第五步：处理 label 为空的节点
    allNodes.forEach(node => {
      const label = node.directory_path || node.label || ''

      if (!label || !label.trim()) {
        // label 为空：作为父节点的内容节点的子节点
        const parent = node._parent
        if (parent) {
          const parentContentNode = nodeToContentNodeMap.get(parent)
          if (parentContentNode) {
            const childNode = {
              line_id: node.line_id || virtualNodeIdCounter++,
              text: node.title || node.content?.substring(0, 50) || '',
              type: 'aggregate',  // 标记为业务实体
              content: node.content,
              title: node.title,
              pid: node.pid,
              location: node.location,
              fields: node.fields,
              boxes: node.boxes,
              page: node.page,
              children: [],
              _originalNode: node
            }
            parentContentNode.children.push(childNode)
          }
        }
      }
    })

    console.log('   - 第一个根节点:', result[0]?.text, ', children:', result[0]?.children?.length)
    return result
  }

  ontologyTreeData.value = buildTreeByPath(dataSource)

  console.log('✅ 业务本体树构建完成')
  console.log('  - 根节点数量:', ontologyTreeData.value.length)

  // 默认全部关闭（不展开任何节点）
  treeExpandedNodes.value = new Set<number>()
  console.log('🌲 默认展开节点: 0 (全部关闭)')
}

// ============ 旧代码（已废弃，仅供参考）============
/*
const buildTreeByLabel_OLD = async () => {
  level1Groups.forEach((level2Map, label1) => {
    // 创建一级标签虚拟节点
    const level1Node = {
      line_id: virtualLineId--,
      text: label1,
      class: 'label-group',
      label_level1: label1,
      label_level2: '无',
      children: [],
      isVirtual: true
    }

    // 遍历二级标签
    level2Map.forEach((items, label2) => {
      if (label2 === '无') {
        // 如果二级标签是"无"，直接将内容添加到一级标签下
        const subTree = buildSubTree(items)

        // 保存完整子元素列表到父节点
        level1Node._fullChildren = subTree

        // 限制子元素数量为3个(默认预览模式)
        const previewChildren = subTree.slice(0, 3)
        level1Node.children.push(...previewChildren)

        // 如果有更多子元素,添加一个"查看更多"节点
        if (subTree.length > 3) {
          const moreNode = {
            line_id: virtualLineId--,
            text: `... 更多 ... 还有 ${subTree.length - 3} 个元素`,
            class: 'more-indicator',
            isVirtual: true,
            _parentNode: level1Node // 保存父节点引用
          }
          level1Node.children.push(moreNode)
        }
      } else {
        // 创建二级标签虚拟节点
        const level2Node = {
          line_id: virtualLineId--,
          text: label2,
          class: 'label-group-2',
          label_level1: label1,
          label_level2: label2,
          children: [],
          isVirtual: true
        }

        // 在二级标签下构建树
        const subTree = buildSubTree(items)

        // 保存完整子元素列表到节点
        level2Node._fullChildren = subTree

        // 限制子元素数量为3个(默认预览模式)
        const previewChildren = subTree.slice(0, 3)
        level2Node.children = previewChildren

        // 如果有更多子元素,添加一个"查看更多"节点
        if (subTree.length > 3) {
          const moreNode = {
            line_id: virtualLineId--,
            text: `... 更多 ... 还有 ${subTree.length - 3} 个元素`,
            class: 'more-indicator',
            isVirtual: true,
            _parentNode: level2Node // 保存父节点引用
          }
          level2Node.children.push(moreNode)
        }

        // 将二级标签节点添加到一级标签下
        level1Node.children.push(level2Node)
      }
    })

    labelRoots.push(level1Node)
  })

  // 使用统一的排序函数
  sortTreeByHierarchy(labelRoots)

  builtTreeData.value = labelRoots
  console.log('✅ 按标签分组的树形结构构建完成')
  console.log('  - 一级标签数量:', labelRoots.length)

  // 生成知识图谱数据
  await buildGraphData()

  // 只在子节点有标签的时候展开
  const expandedLabels = new Set<number>()

  const shouldExpand = (node: any): boolean => {
    if (!node.children || node.children.length === 0) return false
    // 检查子节点是否有标签（label字段存在且不为空）
    return node.children.some((child: any) => child.label && child.label.trim() !== '')
  }

  // 只检查一级节点，不递归
  labelRoots.forEach(node => {
    if (shouldExpand(node)) {
      expandedLabels.add(node.line_id)
    }
  })

  treeExpandedNodes.value = expandedLabels
}
*/

// 统一的树构建入口（根据 treeGroupMode 切换）
const rebuildTree = () => {
  if (treeGroupMode.value === 'label') {
    buildTreeByLabel()
  } else {
    buildTree()
  }
}

// 监听分组模式切换
watch(treeGroupMode, async () => {
  console.log('🔄 树形结构分组模式切换:', treeGroupMode.value)

  if (treeGroupMode.value === 'original') {
    // 切换到采购标签图谱
    console.log('📊 切换到采购标签图谱...')
    console.log('  - graphNodes 数量:', graphNodes.value.length)
    console.log('  - graphEdges 数量:', graphEdges.value.length)
  } else if (treeGroupMode.value === 'label') {
    // 切换到业务语义结构树
    console.log('🔄 切换到业务语义结构树...')
    console.log('  - rawTreeData 数量:', rawTreeData.value.length)
    console.log('  - builtTreeData 数量:', builtTreeData.value.length)
  } else if (treeGroupMode.value === 'ontology') {
    // 切换到业务本体树
    console.log('🔄 切换到业务本体树...')
    // 如果数据未加载，则加载数据
    if (ontologyTreeData.value.length === 0 && taskId.value) {
      await loadOntologyTreeData(taskId.value)
    }
    console.log('  - ontologyTreeData 数量:', ontologyTreeData.value.length)
  } else if (treeGroupMode.value === 'folder') {
    // 切换到文件夹视图
    console.log('📁 切换到文件夹视图...')
    // 文件夹数据由 FolderTree 组件自己管理，不需要在这里加载
  }
})

// 转换 API 返回的树数据格式为组件所需格式
const convertAPITreeData = (nodes: any[]): any[] => {
  let nodeIdCounter = 0

  const convertNode = (node: any): any => {
    // 简单的递增ID，不再从 pid 提取
    const lineId = nodeIdCounter++

    // 保留原始节点的所有字段，然后覆盖需要转换的字段
    const converted: any = {
      ...node, // 保留所有原始字段（包括 fields, title, label 等）
      line_id: lineId,
      text: node.content || '', // 只使用 content
      class: node.label || 'text', // 保留 label 字段用于业务语义树
      page: node.page ? node.page - 1 : 0, // API 的 page 从 1 开始，组件需要从 0 开始
      _originalId: node.id || node.pid // 保存原始 ID 用于调试
    }

    // 转换 bboxes 或 location 为 boxes 格式
    const locationData = node.bboxes || node.location
    if (locationData && Array.isArray(locationData) && locationData.length > 0) {
      converted.boxes = locationData.map((bbox: any) => ({
        page: (bbox.page || node.page || 1) - 1, // 确保 page 从 0 开始
        box: [bbox.l, bbox.t, bbox.r, bbox.b], // [left, top, right, bottom] - TOPLEFT 坐标
        coord_origin: bbox.coord_origin || 'TOPLEFT'
      }))
      // 兼容旧格式，设置第一个 box
      converted.box = converted.boxes[0]?.box
      // 同时更新 page 为第一个位置的页码
      if (locationData[0]?.page) {
        converted.page = locationData[0].page - 1
      }
    }

    // 递归转换子节点
    if (node.children && Array.isArray(node.children) && node.children.length > 0) {
      converted.children = node.children.map(convertNode)
    } else {
      // 确保没有 children 的节点也有一个空数组
      converted.children = []
    }

    return converted
  }

  return nodes.map(convertNode)
}

// 加载 agent 数据（业务语义结构树专用）
// loadAgentData 已移除，不再使用 agent API

// 加载 ontology 数据（知识图谱专用）
const loadOntologyData = async (taskId: string) => {
  try {
    const apiUrl = `/python/api/pdf/task/${taskId}/result?result_type=ontology&t=${Date.now()}`
    console.log(`🔄 加载 ontology 数据:`, apiUrl)
    const response = await fetch(apiUrl)
    if (response.ok) {
      const jsonData = await response.json()

      // 处理 API 格式
      let treeData
      if (jsonData.success && jsonData.data && jsonData.data.dataList) {
        treeData = jsonData.data.dataList
      } else if (jsonData.tree) {
        treeData = jsonData.tree
      } else {
        treeData = jsonData
      }

      const processedData = Array.isArray(treeData) ? treeData : [treeData]
      prebuiltTreeData.value = processedData

      // 转换格式
      prebuiltTreeData.value = convertAPITreeData(prebuiltTreeData.value)

      // 调试：检查转换后的数据
      console.log('🔍 convertAPITreeData 转换后的数据:')
      prebuiltTreeData.value.forEach((node, idx) => {
        console.log(`  ${idx}. content="${node.text?.substring(0, 20)}", children=${node.children?.length || 0}`)
        if (node.text?.includes('政府采购')) {
          console.log('    ⚠️ 政府采购节点 children:', node.children)
        }
      })

      sortTreeByHierarchy(prebuiltTreeData.value)
      rawTreeData.value = prebuiltTreeData.value

      // 扁平化用于知识图谱
      const flattenTree = (nodes: any[]): any[] => {
        const result: any[] = []
        const traverse = (node: any) => {
          result.push(node)
          if (node.children && Array.isArray(node.children)) {
            node.children.forEach(traverse)
          }
        }
        nodes.forEach(traverse)
        return result
      }

      structuredData.value = flattenTree(rawTreeData.value)
      console.log('✅ ontology 数据已保存，节点数:', structuredData.value.length)

      // 提取 fields 不为空的节点
      const nodesWithFieldsArray = structuredData.value.filter((n: any) => n.fields && Object.keys(n.fields).length > 0)
      nodesWithFields.value = nodesWithFieldsArray
      console.log('   其中包含 fields 的节点数:', nodesWithFieldsArray.length)
      console.log('   📋 所有包含 fields 的节点:')
      nodesWithFieldsArray.forEach((n: any, index: number) => {
        console.log(`      ${index + 1}. label: "${n.label}", fields: ${Object.keys(n.fields).length}个 (${Object.keys(n.fields).join(', ')})`)
      })

      // 生成知识图谱
      await buildGraphData()

      // 构建业务语义结构树
      await buildTreeByLabel()
    }
  } catch (e) {
    console.error('❌ ontology API 加载失败:', e)
  }
}

// 读取 JSON 文件（从 API 接口）- 保留用于兼容
const loadJsonFiles = async (taskId: string) => {
  try {
    console.log('📦 开始加载 JSON 文件，taskId:', taskId)

    let treeDataUrl = ''
    let jsonData = null
    let isTreeJson = false
    let agentData = null  // 业务语义结构树专用数据源

    // 1. 加载 agent 数据（业务语义结构树专用）
    try {
      const apiUrl = `/python/api/pdf/task/${taskId}/result?result_type=agent`
      console.log(`🔄 从 API 加载数据 (result_type=agent):`, apiUrl)
      const response = await fetch(apiUrl)
      if (response.ok) {
        agentData = await response.json()
        console.log(`✅ 业务语义结构树数据源: API (result_type=agent)`)
        console.log(`   - agent 数据类型:`, typeof agentData, Array.isArray(agentData) ? '(数组)' : '(非数组)')
        console.log(`   - agent 数据内容:`, agentData)
        console.log(`   - agent 数据节点数:`, Array.isArray(agentData) ? agentData.length : 0)
      }
    } catch (e) {
      console.log('⚠️ agent API 加载失败:', e)
    }

    // 2. 加载 ontology 数据（知识标签图谱专用，包含 label 和 fields）
    try {
      const apiUrl = `/python/api/pdf/task/${taskId}/result?result_type=ontology&t=${Date.now()}`
      console.log(`🔄 从 API 加载数据 (result_type=ontology):`, apiUrl)
      const response = await fetch(apiUrl)
      if (response.ok) {
        jsonData = await response.json()
        treeDataUrl = apiUrl
        isTreeJson = true
        console.log(`✅ 知识标签图谱数据源: API (result_type=ontology)`)
      }
    } catch (e) {
      console.log('⚠️ ontology API 加载失败，尝试从 public 目录加载:', e)
    }

    // 如果 API 加载失败，回退到 public 目录
    if (!jsonData) {
      const urlPriority = [
        `${import.meta.env.BASE_URL}hrdoc/${taskId}_labeled_tree.json`,
        `${import.meta.env.BASE_URL}hrdoc/${taskId}_labeled.json`,
        `${import.meta.env.BASE_URL}hrdoc/${taskId}.json`
      ]

      for (const url of urlPriority) {
        try {
          const response = await fetch(url)
          if (response.ok) {
            jsonData = await response.json()
            treeDataUrl = url
            isTreeJson = url.includes('_labeled_tree.json')
            console.log('✅ 数据源:', treeDataUrl)
            break
          }
        } catch (e) {
          continue
        }
      }
    }

    if (!jsonData) {
      console.warn('❌ 未找到任何JSON文件')
      return
    }

    console.log('✅ 树形数据加载完成，数据类型:', Array.isArray(jsonData) ? '数组' : '对象')

    // 如果加载的是 _labeled_tree.json 或 API tree，直接使用
    if (isTreeJson) {
      console.log('🌲 使用预构建的树形JSON')

      // 处理不同的数据格式
      // API 格式: { success: true, data: { dataList: [...] } }
      // 文件格式: { tree: [...] } 或 [...]
      let treeData
      if (jsonData.success && jsonData.data && jsonData.data.dataList) {
        // API 格式
        treeData = jsonData.data.dataList
        console.log('📊 检测到 API 格式 (success/data/dataList)')
      } else if (jsonData.tree) {
        // 文件格式 { tree: [...] }
        treeData = jsonData.tree
        console.log('📊 检测到文件格式 (tree)')
      } else {
        // 直接数组格式
        treeData = jsonData
        console.log('📊 检测到数组格式')
      }

      prebuiltTreeData.value = Array.isArray(treeData) ? treeData : [treeData]

      // 如果是 API 数据，需要转换格式
      if (jsonData.success && jsonData.data && jsonData.data.dataList) {
        console.log('🔄 转换 API 数据格式为组件所需格式')
        prebuiltTreeData.value = convertAPITreeData(prebuiltTreeData.value)
      }

      // 对预构建的树按照 hierarchy 顺序排序
      sortTreeByHierarchy(prebuiltTreeData.value)

      // 保存到 rawTreeData 用于后续构建
      rawTreeData.value = prebuiltTreeData.value

      // 如果是业务语义结构树模式，需要按标签重新构建
      if (treeGroupMode.value === 'label') {
        console.log('🏷️ 业务语义结构树模式，按标签重新构建...')
        hasPrebuiltTree.value = false
        // 不直接赋值，等待 buildTreeByLabel 构建
      } else {
        builtTreeData.value = prebuiltTreeData.value
        hasPrebuiltTree.value = true
      }

      // 如果有pdf_path字段,可以使用它
      if (jsonData.pdf_path) {
        console.log('📄 PDF路径:', jsonData.pdf_path)
        // 未来可以用这个路径加载PDF
      }

      // 保存原始数据用于查找节点
      allTreeNodes.value = []
      const extractNodes = (nodes: any[]) => {
        nodes.forEach(node => {
          if (!node.isVirtual) {
            allTreeNodes.value.push(node)
          }
          if (node.children) {
            extractNodes(node.children)
          }
        })
      }
      extractNodes(builtTreeData.value)

      // 🎯 使用 rawTreeData 作为知识图谱 fields 数据源（包含原始的 label 和 fields）
      const flattenTree = (nodes: any[]): any[] => {
        const result: any[] = []
        const traverse = (node: any) => {
          // 先添加当前节点
          result.push(node)
          // 递归处理子节点
          if (node.children && Array.isArray(node.children)) {
            node.children.forEach(traverse)
          }
        }
        nodes.forEach(traverse)
        return result
      }

      const flattenedData = flattenTree(rawTreeData.value)
      structuredData.value = flattenedData

      console.log('✅ 扁平化 rawTreeData，节点数:', flattenedData.length)
      const nodesWithFieldsArray = flattenedData.filter(n => n.fields && Object.keys(n.fields).length > 0)
      nodesWithFields.value = nodesWithFieldsArray  // 保存到 ref 变量
      console.log('   其中包含 fields 的节点数:', nodesWithFieldsArray.length)
      console.log('   📋 前3个包含 fields 的节点:', nodesWithFieldsArray.slice(0, 3).map(n => ({
        pid: n.pid,
        label: n.label,
        fields: n.fields,
        title: n.title,
        location: n.location // 检查 location 信息
      })))

      // 只在子节点有标签的时候展开
      const expandedLabels = new Set<number>()

      const shouldExpand = (node: any): boolean => {
        if (!node.children || node.children.length === 0) return false
        return node.children.some((child: any) => child.label && child.label.trim() !== '')
      }

      // 只检查一级节点，不递归
      builtTreeData.value.forEach(node => {
        if (shouldExpand(node)) {
          expandedLabels.add(node.line_id)
        }
      })

      treeExpandedNodes.value = expandedLabels

      console.log('✅ 树形结构加载完成，一级标签数量:', builtTreeData.value.length)

      // 根据不同模式构建对应的数据
      if (treeGroupMode.value === 'label' && rawTreeData.value.length > 0) {
        console.log('🔄 调用 buildTreeByLabel 重新构建业务语义结构树...')
        await buildTreeByLabel()
      } else if (treeGroupMode.value === 'original') {
        console.log('🔄 采购标签图谱模式，生成知识图谱数据...')
        await buildGraphData()
      }
    } else {
      // 使用扁平JSON，需要客户端构建树
      console.log('📋 使用扁平JSON，客户端构建树')
      rawTreeData.value = Array.isArray(jsonData) ? jsonData : [jsonData]
      allTreeNodes.value = rawTreeData.value

      // 构建树形结构（使用统一入口，支持切换模式）
      rebuildTree()
    }

    // agentData 处理已移除，不再使用

    console.log('📦 JSON 文件加载完成')
  } catch (error) {
    console.error('❌ 加载JSON文件失败:', error)
  }
}

// 获取文件URL
const getFile = async () => {
  pdfData.currentPage = 1
  pdfData.highlightRects = []
  pdfData.pdfUrl = ''

  if (!taskId.value) {
    message.info('缺少任务ID')
    return
  }

  // 从 API 接口读取 PDF
  pdfData.pdfUrl = `/python/api/pdf/task/${taskId.value}/result?result_type=pdf`
  console.log('从 API 接口读取 PDF:', pdfData.pdfUrl)
}

// ==================== 导出相关方法 ====================
const {
  state: exportState,
  hasSelectedOptions,
  cancel: cancelExport,
  show: showExport,
  confirm: confirmExport
} = useExport(exportOptionsList, taskId.value)
const handleExportDropdownChange = (open: boolean) => {
  if (open) {
    showExport() // 打开时重置为全选
  }
}
// ==================== 弹窗控制方法 ====================

// 显示审查清单
const showCheckList = () => {
  state.checkListVisible = true
}

// 显示历史文件
const showHistoryFiles = () => {
  state.historyFilesVisible = true
}

// 文件预览处理
const handleFilePreview = (file: any) => {
  console.log('📂 切换任务:', file.fileName, file.taskId)
  taskId.value = file.taskId
  refreshData()
  // 关闭历史文件抽屉
  state.historyFilesVisible = false
}

// 切换项目展开/收缩
const toggleItemExpand = (reviewItemCode: string) => {
  // 如果未设置，默认为 true（展开），所以点击后设为 false（收起）
  // 如果已经是 false（收起），点击后设为 true（展开）
  const currentState = expandedState[reviewItemCode]
  expandedState[reviewItemCode] = currentState === false ? true : false
}

// 切换树节点展开/折叠
const toggleTreeNode = (nodeId: any) => {
  console.log('切换节点:', nodeId, '当前状态:', treeExpandedNodes.value.has(nodeId))

  const isCurrentlyExpanded = treeExpandedNodes.value.has(nodeId)

  if (isCurrentlyExpanded) {
    // 折叠节点
    treeExpandedNodes.value.delete(nodeId)

    // 如果是标签节点且之前展开过全部子元素,重置为只显示3个
    const node = findNodeById(builtTreeData.value, nodeId)
    if (node && (node.class === 'label-group' || node.class === 'label-group-2')) {
      if (node._isExpanded && node._fullChildren && node._fullChildren.length > 3) {
        console.log('🔄 重置标签节点为预览模式(只显示3个)')

        // 恢复为只显示前3个
        const previewChildren = node._fullChildren.slice(0, 3)

        // 创建"查看更多"节点
        const moreNode = {
          line_id: -Date.now(), // 使用时间戳生成唯一负数ID
          text: `... 更多 ... 还有 ${node._fullChildren.length - 3} 个元素`,
          class: 'more-indicator',
          isVirtual: true,
          _parentNode: node
        }

        node.children = [...previewChildren, moreNode]
        node._isExpanded = false
      }
    }
  } else {
    // 展开节点
    treeExpandedNodes.value.add(nodeId)
  }

  treeExpandedNodes.value = new Set(treeExpandedNodes.value)
}

/**
 * 处理节点拖拽放置事件
 * @param draggedNodeId - 被拖拽节点的ID
 * @param targetNodeId - 目标节点的ID
 */
const handleNodeDrop = (draggedNodeId: number, targetNodeId: number) => {
  // 使用批量拖拽列表
  const nodesToMove = draggedNodeIds.length > 0 ? draggedNodeIds : [draggedNodeId]
  console.log('🎯 节点拖拽:', { nodesToMove, targetNodeId })

  // 获取节点的 pid（支持数组和字符串）
  const getNodePid = (node: any): string => {
    if (Array.isArray(node.pid)) {
      return node.pid[0] // 如果是数组，取第一个
    }
    return node.pid || ''
  }

  // 查找目标节点
  const targetNode = findNodeById(builtTreeData.value, targetNodeId)
  if (!targetNode) {
    console.error('❌ 未找到目标节点')
    return
  }

  const targetPid = getNodePid(targetNode)
  const nodePids: string[] = []

  // 验证所有节点
  for (const nodeId of nodesToMove) {
    const node = findNodeById(builtTreeData.value, nodeId)
    if (!node) {
      console.error('❌ 未找到节点:', nodeId)
      return
    }

    // 防止将节点拖到自己或自己的子节点下
    if (nodeId === targetNodeId || isDescendant(targetNode, nodeId)) {
      console.warn('⚠️ 不能将节点拖到自己或自己的子节点下:', nodeId)
      return
    }

    nodePids.push(getNodePid(node))
  }

  console.log('📦 准备发送批量移动API请求:', {
    node_ids: nodePids,
    target_parent_id: targetPid,
    taskId: taskId.value,
    count: nodePids.length
  })

  // 发送 API 请求（完全异步，不阻塞页面）
  // 如果是单个节点，使用原API；如果是多个节点，使用批量API
  const apiUrl = nodePids.length === 1
    ? `/python/ontology/task/${taskId.value}/move-node`
    : `/python/ontology/task/${taskId.value}/move-nodes`

  const requestBody = nodePids.length === 1
    ? { node_id: nodePids[0], target_parent_id: targetPid }
    : { node_ids: nodePids, target_parent_id: targetPid }

  fetch(apiUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(requestBody)
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`API请求失败: ${response.status} ${response.statusText}`)
      }
      return response.json()
    })
    .then((result) => {
      console.log('✅ API响应:', result)
      const count = nodePids.length
      console.log(`💡 ${count}个节点移动成功，退出编辑模式后会自动刷新数据`)

      // 显示成功提示
      message.success(`成功移动 ${count} 个节点`)

      // 不立即重新加载数据，避免阻塞
      // 当用户退出编辑模式时会自动刷新
    })
    .catch((error) => {
      console.error('❌ 移动节点失败:', error)
      message.error(`移动节点失败: ${error.message}`)
    })
    .finally(() => {
      // 清空批量拖拽列表
      draggedNodeIds = []
    })

  // 立即清空选中状态
  selectedNodeIds.value = []
  console.log(`🚀 ${nodePids.length}个节点移动请求已发送，已清空选中状态`)
}

/**
 * 处理更新节点标签
 */
const handleUpdateLabel = async (data: { nodeId: number; pid: string; label: string }) => {
  console.log('🏷️ 更新节点标签:', data)

  if (!taskId.value) {
    message.error('无效的任务ID')
    return
  }

  try {
    // 发送API请求更新标签
    const apiUrl = `/python/ontology/task/${taskId.value}/update-label`
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        node_id: data.pid,
        label: data.label
      })
    })

    if (!response.ok) {
      throw new Error(`API请求失败: ${response.status} ${response.statusText}`)
    }

    const result = await response.json()
    console.log('✅ 标签更新成功:', result)
    message.success('标签已更新')

    // 在本地数据中更新标签（立即反映）
    const updateNodeLabel = (nodes: any[]): boolean => {
      for (const node of nodes) {
        if (node.line_id === data.nodeId || node.pid === data.pid) {
          node.label = data.label
          return true
        }
        if (node.children && updateNodeLabel(node.children)) {
          return true
        }
      }
      return false
    }

    // 更新所有树结构中的节点标签
    updateNodeLabel(builtTreeData.value)
    updateNodeLabel(ontologyTreeData.value)
    updateNodeLabel(allTreeNodes.value)

    // 触发响应式更新
    builtTreeData.value = [...builtTreeData.value]
  } catch (error) {
    console.error('❌ 更新标签失败:', error)
    message.error(`更新标签失败: ${error.message}`)
  }
}

/**
 * 判断节点是否是另一个节点的后代
 */
const isDescendant = (node: any, ancestorId: number): boolean => {
  if (!node.children) return false

  for (const child of node.children) {
    if (child.line_id === ancestorId) return true
    if (isDescendant(child, ancestorId)) return true
  }

  return false
}

/**
 * 从树中递归移除节点
 */
const removeNodeFromTree = (nodes: any[], nodeId: number): boolean => {
  for (let i = 0; i < nodes.length; i++) {
    if (nodes[i].line_id === nodeId) {
      nodes.splice(i, 1)
      return true
    }

    if (nodes[i].children) {
      if (removeNodeFromTree(nodes[i].children, nodeId)) {
        return true
      }
    }
  }

  return false
}

/**
 * 智能合并 boxes：将同一栏的连续行合并成一个大矩形
 *
 * 分栏判断标准：
 * 1. 页码变化 → 新区域
 * 2. X 坐标显著跳变（超过阈值）→ 换栏
 * 3. Y 坐标向上跳（非连续）→ 换栏
 *
 * @param boxInfos - 包含 {box, page, line_id} 的数组
 * @returns 合并后的 box 数组 [x1, y1, x2, y2]
 */
const mergeBoxesByColumn = (boxInfos: any[]): number[][] => {
  if (!boxInfos || boxInfos.length === 0) return []
  if (boxInfos.length === 1) return [boxInfos[0].box]

  const mergedBoxes: number[][] = []
  let currentGroup: any[] = [boxInfos[0]]

  for (let i = 1; i < boxInfos.length; i++) {
    const prev = boxInfos[i - 1]
    const curr = boxInfos[i]

    // 计算Y轴间隔（当前box的上边界 - 前一个box的下边界）
    const yGap = curr.box[1] - prev.box[3]

    // 判断是否需要开始新区域
    const shouldStartNewRegion =
      // 1. 页码变化
      curr.page !== prev.page ||
      // 2. X 坐标显著跳变（左边界相差超过 100 像素，说明换栏了）
      Math.abs(curr.box[0] - prev.box[0]) > 100 ||
      // 3. Y 坐标向上跳（y1 减小，说明不连续）
      curr.box[1] < prev.box[1] ||
      // 4. Y轴间隔过大（超过50像素，说明中间有大片空白，可能是不同段落）
      yGap > 50

    if (shouldStartNewRegion) {
      // 合并当前组的所有 box
      mergedBoxes.push(mergeBoxGroup(currentGroup))
      // 开始新组
      currentGroup = [curr]
    } else {
      // 添加到当前组
      currentGroup.push(curr)
    }
  }

  // 处理最后一组
  if (currentGroup.length > 0) {
    mergedBoxes.push(mergeBoxGroup(currentGroup))
  }

  return mergedBoxes
}

/**
 * 合并一组 box 为一个大矩形
 */
const mergeBoxGroup = (boxInfos: any[]): number[] => {
  const boxes = boxInfos.map(info => info.box)

  const x1 = Math.min(...boxes.map(b => b[0]))
  const y1 = Math.min(...boxes.map(b => b[1]))
  const x2 = Math.max(...boxes.map(b => b[2]))
  const y2 = Math.max(...boxes.map(b => b[3]))

  return [x1, y1, x2, y2]
}

// 递归查找第一个非标签节点
const findFirstNonLabelNode = (node: any): any => {
  // 如果当前节点不是标签节点也不是"查看更多"节点，返回自身
  if (node.class !== 'label-group' && node.class !== 'label-group-2' && node.class !== 'more-indicator') {
    return node
  }

  // 如果是标签节点，递归查找子节点
  if (node.children && node.children.length > 0) {
    for (const child of node.children) {
      const result = findFirstNonLabelNode(child)
      if (result) return result
    }
  }

  return null
}

// 选择树节点并跳转到PDF位置
// 处理文件夹节点选择
const handleFolderNodeSelect = async (nodeData: any) => {
  console.log('📁 文件夹节点被选中:', nodeData)

  // 调用原有的 selectTreeNode 逻辑
  if (nodeData.line_id) {
    await selectTreeNode(nodeData.line_id)
  } else if (nodeData.location && nodeData.location.length > 0) {
    // 使用 location 信息跳转
    const firstLocation = nodeData.location[0]
    const pageNum = firstLocation.page_index + 1
    pdfData.currentPage = pageNum

    // 高亮
    const highlightRect = {
      pageNum: pageNum,
      box: firstLocation.bbox,
      color: 'rgba(255, 255, 0, 0.3)'
    }
    pdfData.highlightRects = [highlightRect]

    console.log('✅ 已跳转到页面', pageNum)
  }
}

const selectTreeNode = async (nodeId: number, event?: MouseEvent) => {
  // 支持 Ctrl/Cmd 多选
  const isMultiSelect = event && (event.ctrlKey || event.metaKey)

  // 编辑模式下：只更新选中状态，不跳转
  if (treeEditMode.value) {
    const index = selectedNodeIds.value.indexOf(nodeId)

    // 切换选中状态（点击已选中的节点会取消选中）
    if (index > -1) {
      // 取消选中
      selectedNodeIds.value.splice(index, 1)
      console.log('❌ 取消选中节点:', nodeId, '当前选中:', selectedNodeIds.value)
    } else {
      // 添加选中
      selectedNodeIds.value.push(nodeId)
      console.log('✅ 添加选中节点:', nodeId, '当前选中:', selectedNodeIds.value)
    }

    // 编辑模式下不执行后续的页面跳转逻辑
    return
  }

  // 非编辑模式：单选并跳转
  selectedNodeIds.value = [nodeId]
  console.log('🎯 选中节点 line_id:', nodeId)

  // 先在构建好的树中查找（用于处理虚拟节点）
  let node = findNodeById(builtTreeData.value, nodeId)

  // 如果在构建树中没找到，尝试在原始数据中查找
  if (!node) {
    console.log('⚠️ 在构建树中未找到，尝试在原始数据中查找')
    node = findNodeById(allTreeNodes.value, nodeId)
  }

  if (!node) {
    console.warn('❌ 未找到节点 line_id:', nodeId)
    return
  }

  // 🔍 添加详细日志
  console.log('📋 找到的节点完整信息:', {
    line_id: node.line_id,
    pid: node.pid,
    title: node.title,
    text: node.text,
    class: node.class,
    page: node.page,
    has_boxes: !!node.boxes,
    boxes_count: node.boxes?.length,
    has_location: !!node.location,
    location_count: node.location?.length,
    content_preview: node.content?.substring(0, 100)
  })

  // 如果点击的是"查看更多"节点，展开所有子元素
  if (node.class === 'more-indicator') {
    console.log('🔍 点击了"查看更多"，展开所有子元素')
    const expanded = expandMoreNode(node)
    if (expanded) {
      // 强制触发响应式更新
      builtTreeData.value = [...builtTreeData.value]
      console.log('✓ 已展开所有子元素')
    }
    return
  }

  // 记录是否是标签节点(用于控制高亮行为)
  const isLabelNode = node.class === 'label-group' || node.class === 'label-group-2'

  // 如果点击的是标签节点，只跳转页面不高亮
  if (isLabelNode) {
    console.log('🏷️ 点击的是标签节点，只跳转页面不高亮')
    const targetNode = findFirstNonLabelNode(node)
    if (targetNode) {
      console.log('✓ 找到目标节点:', targetNode.line_id, targetNode.class)

      // 只跳转到页面,不高亮
      if (targetNode.boxes && targetNode.boxes.length > 0) {
        const firstBox = targetNode.boxes[0]
        const pageNum = firstBox.page + 1
        pdfData.currentPage = pageNum
        pdfData.highlightRects = []
        console.log('✅ 已跳转到页面', pageNum, '(不高亮)')
      } else if (targetNode.page !== undefined) {
        const pageNum = targetNode.page + 1
        pdfData.currentPage = pageNum
        pdfData.highlightRects = []
        console.log('✅ 已跳转到页面', pageNum, '(不高亮)')
      }
    } else {
      console.warn('❌ 该标签下没有非标签节点')
    }
    return
  }

  console.log('📄 节点详情:', {
    pid: node.pid,
    title: node.title,
    label: node.label,
    hasBoxes: !!node.boxes,
    hasLocation: !!node.location,
    boxes: node.boxes,
    location: node.location
  })

  // 解包 Proxy (使用 JSON 序列化/反序列化)
  let boxes = node.boxes ? JSON.parse(JSON.stringify(node.boxes)) : null

  console.log('📦 节点boxes:', {
    类型: typeof boxes,
    是数组: Array.isArray(boxes),
    长度: boxes?.length,
    数据: boxes
  })

  try {
    // 判断是否为段落节点（有 boxes 数组）
    if (boxes && boxes.length > 0) {
      // 段落节点：跳转并高亮所有行
      console.log('📝 段落节点，包含', boxes.length, '个 box')

      // 跳转到第一个 box 所在的页面
      const firstBox = boxes[0]
      const pageNum = firstBox.page + 1
      pdfData.currentPage = pageNum

      // 如果启用了高亮功能
      if (enablePdfHighlight.value) {
        // 过滤：只保留当前页的 boxes
        const currentPageBoxes = boxes.filter(b => b.page === firstBox.page)
        console.log('📦 boxes详情:', {
          原始boxes数量: boxes.length,
          当前页boxes数量: currentPageBoxes.length,
          当前页码: firstBox.page,
          数据: currentPageBoxes
        })

        // 智能合并 boxes 并高亮 (mergeBoxesByColumn 期望接收 {page, box} 格式)
        const mergedBoxes = mergeBoxesByColumn(currentPageBoxes)

        console.log('📦 Box 合并结果:', {
          原始box数: currentPageBoxes.length,
          合并后区域数: mergedBoxes.length,
          合并详情: mergedBoxes
        })

        // 将合并后的 boxes 转换为 quadPoints
        const allQuadPoints: number[] = []
        mergedBoxes.forEach((box: number[]) => {
          // 每个 box 贡献 8 个坐标点
          allQuadPoints.push(
            box[0],
            box[1], // 左上
            box[2],
            box[1], // 右上
            box[2],
            box[3], // 右下
            box[0],
            box[3] // 左下
          )
        })

        console.log('📌 多区域高亮:', {
          区域数量: mergedBoxes.length,
          quadPoints长度: allQuadPoints.length,
          页码: pageNum
        })

        // 创建单个高亮对象，包含所有合并后的 box 的 quadPoints
        const highlightData = {
          pageNum: pageNum,
          rect: mergedBoxes[0], // 使用第一个合并后的 box 的 rect（用于定位）
          quadPoints: allQuadPoints, // 包含所有合并后区域的 quadPoints
          needsConversion: true, // TOPLEFT 坐标，需要转换为 PDF 坐标
          jump: true
        }

        // 更新 PDF 高亮区域
        pdfData.highlightRects = [highlightData]

        // 跳转并高亮
        const pdfViewer = contentViewerRef.value?.pdfViewerRef
        if (pdfViewer?.scrollToAnnotation) {
          await nextTick()
          await pdfViewer.scrollToAnnotation(highlightData)
          console.log('✅ 已跳转到段落位置并高亮所有区域')
        } else {
          console.warn('❌ PDF查看器未就绪')
        }
      } else {
        // 高亮功能未启用，只跳转不高亮
        pdfData.highlightRects = []
        console.log('✅ 已跳转到页面', pageNum, '(高亮功能已禁用)')
      }
    } else {
      // 单个节点：尝试获取位置信息
      let pageNum, box

      if (node.page !== undefined && node.box) {
        // 格式：node.page + node.box
        pageNum = node.page + 1
        box = node.box
      }

      if (pageNum && box) {
        // 单个节点：跳转并可能高亮
        console.log('📍 单行节点，box:', { pageNum, box })

        pdfData.currentPage = pageNum

        if (enablePdfHighlight.value) {
          const highlightRect = {
            pageNum: pageNum,
            rect: box,
            quadPoints: [box[0], box[1], box[2], box[1], box[2], box[3], box[0], box[3]],
            jump: true,
            needsConversion: true // TOPLEFT 坐标，需要转换为 PDF 坐标
          }

          pdfData.highlightRects = [highlightRect]

          const pdfViewer = contentViewerRef.value?.pdfViewerRef
          if (pdfViewer?.scrollToAnnotation) {
            await nextTick()
            await pdfViewer.scrollToAnnotation(highlightRect)
            console.log('✅ 已跳转到 PDF 位置并高亮')
          }
        } else {
          pdfData.highlightRects = []
          console.log('✅ 已跳转到页面', pageNum, '(高亮功能已禁用)')
        }
      } else if (node.page !== undefined) {
        // 只有页码，没有位置信息：只跳转页面，不高亮
        const pageNum = node.page + 1
        pdfData.currentPage = pageNum
        pdfData.highlightRects = []
        console.log('✅ 已跳转到页面', pageNum, '(无位置信息，不高亮)')
      } else {
        console.warn('⚠️ 节点缺少位置信息:', node)
      }
    }
  } catch (error) {
    console.error('❌ 跳转失败:', error)
  }
}

// 获取段落预览文本
const getParagraphPreview = (paragraphIds: number[]): string => {
  if (!paragraphIds || paragraphIds.length === 0) return ''

  const texts: string[] = []
  for (const id of paragraphIds) {
    const node = nodeMap.value[id]
    if (node && (node.text || node.content)) {
      texts.push(node.text || node.content)
    }
  }

  const fullText = texts.join('')
  return fullText.length > 60 ? fullText.substring(0, 60) + '...' : fullText
}

// 从结构化数据中提取 fields 信息（用于知识图谱）
const extractFieldsFromStructuredData = () => {
  const fieldsMap = new Map<number, any>()

  const traverse = (nodes: any[]) => {
    if (!nodes || !Array.isArray(nodes)) return

    for (const node of nodes) {
      // 如果节点有 fields 属性，记录下来
      if (node.line_id !== undefined && node.fields && typeof node.fields === 'object') {
        fieldsMap.set(node.line_id, node.fields)
        console.log(`📋 找到 fields: line_id=${node.line_id}`, node.fields)
      }

      // 递归处理子节点
      if (node.children && Array.isArray(node.children)) {
        traverse(node.children)
      }
    }
  }

  // 遍历 structuredData（从 _structured_data.json 加载）
  if (structuredData.value && Array.isArray(structuredData.value)) {
    console.log('🔍 开始从 structured_data 提取 fields...')
    traverse(structuredData.value)
    console.log(`✅ 共提取 ${fieldsMap.size} 个节点的 fields 信息`)
  } else {
    console.warn('⚠️ structuredData 为空，无法提取 fields')
  }

  return fieldsMap
}

//生成知识图谱数据（基于 ontology 数据）
const buildGraphData = async () => {
  console.log('🔧 开始生成知识图谱数据')

  // Get concept nodes and edges (with inferred edges from sameAs) from ontology.json
  const { nodes: conceptNodes, edges: conceptEdges } = await getGraphData()

  console.log('📊 原始数据:')
  console.log('  - 概念节点数:', conceptNodes.length)
  console.log('  - 概念边数（含推理）:', conceptEdges.length)
  console.log('  - 前3个节点:', conceptNodes.slice(0, 3))
  console.log('  - 前3条边:', conceptEdges.slice(0, 3))

  // 🎯 过滤逻辑1：只保留有 fields 的节点对应的标签
  const excludedNodeLabels = new Set(['其他关键信息', '招标文件', '文本片段', '文本章节'])

  // 从 ontology 数据中提取有 fields 的节点的 label，并拆分路径
  const allowedLabels = new Set<string>()
  if (nodesWithFields.value && nodesWithFields.value.length > 0) {
    nodesWithFields.value.forEach((node: any) => {
      if (node.label && node.label.trim() !== '') {
        // 拆分路径：'采购项目/采购包' -> ['采购项目', '采购包']
        const pathSegments = node.label.split('/').map((s: string) => s.trim()).filter((s: string) => s !== '')
        pathSegments.forEach((segment: string) => {
          allowedLabels.add(segment)
        })
      }
    })
  }

  console.log(`📊 从 ontology 提取的允许标签数: ${allowedLabels.size}`)
  console.log(`   前10个允许的标签:`, Array.from(allowedLabels).slice(0, 10))
  console.log(`📊 Ontology 字段过滤开关: ${enableOntologyFieldFilter.value ? '开启' : '关闭'}`)

  // 过滤节点：排除指定标签 + (可选) 只保留在允许列表中的标签
  const filteredNodes = conceptNodes.filter((n: any) => {
    if (excludedNodeLabels.has(n.label)) return false
    // 只有在开关开启时才应用 ontology 字段过滤
    if (enableOntologyFieldFilter.value && allowedLabels.size > 0 && !allowedLabels.has(n.label)) return false
    return true
  })

  console.log(`📊 过滤节点后: ${conceptNodes.length} -> ${filteredNodes.length} 个节点`)

  // 获取过滤后的节点ID集合
  const filteredNodeIds = new Set(filteredNodes.map((n: any) => n.id))

  // 🎯 过滤逻辑2：过滤边
  // - 排除 hasAttribute 关系
  // - 只保留两端节点都在过滤后节点集合中的边
  const excludedEdgeTypes = new Set(['hasAttribute'])
  const filteredEdges = conceptEdges.filter((e: any) => {
    return !excludedEdgeTypes.has(e.label) &&
           filteredNodeIds.has(e.source) &&
           filteredNodeIds.has(e.target)
  })

  console.log(`📊 过滤边后: ${conceptEdges.length} -> ${filteredEdges.length} 条边`)

  // 初始化节点和边数组
  const nodes: Array<{ id: string; label: string; type: string }> = []
  const edges: Array<{ id: string; source: string; target: string; label: string }> = []

  // 添加边
  edges.push(...filteredEdges)

  // 🎯 收集涉及的节点ID（从边中）
  const relatedNodeIds = new Set<string>()
  edges.forEach((edge: any) => {
    relatedNodeIds.add(edge.source)
    relatedNodeIds.add(edge.target)
  })

  // 添加节点（只添加有边连接的）
  filteredNodes.forEach((n: any) => {
    if (relatedNodeIds.has(n.id)) {
      nodes.push(n)
    }
  })

  // 🎯 添加要素节点（从 nodesWithFields 中提取 fields）
  let fieldNodeCount = 0
  let fieldEdgeCount = 0

  // 统计每个概念节点的要素节点数量（用于显示标签）
  const nodeFieldCountMap = new Map<string, number>()

  console.log('🏷️ 开始构建要素节点...')
  console.log(`   开关状态: ${enableOntologyFieldFilter.value ? '开启（节点过滤）' : '关闭（显示所有节点）'}`)
  console.log(`   注意: 要素节点始终会创建，开关只控制概念节点的过滤`)

  if (nodesWithFields.value && nodesWithFields.value.length > 0) {
    nodesWithFields.value.forEach((ontologyNode: any, index: number) => {
      if (!ontologyNode.label || ontologyNode.label.trim() === '') return

      // 提取路径：'采购项目/采购包' -> ['采购项目', '采购包']
      const pathSegments = ontologyNode.label.split('/').map((s: string) => s.trim()).filter((s: string) => s !== '')
      const lastLabel = pathSegments[pathSegments.length - 1]

      console.log(`\n📋 处理第 ${index + 1} 个有 fields 的节点:`)
      console.log(`   路径: "${ontologyNode.label}"`)
      console.log(`   路径段: [${pathSegments.join(', ')}]`)
      console.log(`   最后一个标签: "${lastLabel}"`)
      console.log(`   fields 数量: ${Object.keys(ontologyNode.fields || {}).length}`)

      // 查找匹配路径的概念节点
      // 策略：找到所有 label 匹配的节点，然后通过路径验证找到正确的那个
      let conceptNode = null

      if (pathSegments.length === 1) {
        // 只有一层，直接匹配 label
        conceptNode = nodes.find(n => n.label === lastLabel)
      } else {
        // 多层路径，需要验证父节点路径
        // 先找到所有 label 匹配的候选节点
        const candidates = nodes.filter(n => n.label === lastLabel)

        if (candidates.length === 1) {
          // 只有一个候选，直接使用
          conceptNode = candidates[0]
        } else if (candidates.length > 1) {
          // 多个候选，通过路径验证
          console.log(`   ⚠️ 找到 ${candidates.length} 个同名节点: [${candidates.map(c => c.id).join(', ')}]`)
          console.log(`   尝试通过父节点路径验证...`)

          // 向上遍历，验证路径是否匹配
          for (const candidate of candidates) {
            const parentPath: string[] = []
            let currentNodeId = candidate.id

            // 向上查找父节点，构建路径（最多查找 pathSegments.length - 1 层）
            for (let i = 0; i < pathSegments.length - 1; i++) {
              const parentEdge = edges.find(e =>
                e.target === currentNodeId &&
                (e.label === 'hasPart' || e.label === 'hasMember' || e.label === 'attachedTo')
              )

              if (!parentEdge) break

              const parentNode = nodes.find(n => n.id === parentEdge.source)
              if (!parentNode) break

              parentPath.unshift(parentNode.label)
              currentNodeId = parentNode.id
            }

            // 验证路径是否匹配
            const fullPath = [...parentPath, candidate.label]
            console.log(`   候选节点 ${candidate.id}: 路径 = [${fullPath.join('/')}]`)

            // 检查路径是否匹配（从后往前匹配）
            let pathMatches = true
            for (let i = 0; i < Math.min(pathSegments.length, fullPath.length); i++) {
              const segmentIndex = pathSegments.length - 1 - i
              const pathIndex = fullPath.length - 1 - i
              if (pathSegments[segmentIndex] !== fullPath[pathIndex]) {
                pathMatches = false
                break
              }
            }

            if (pathMatches && fullPath.length >= pathSegments.length) {
              conceptNode = candidate
              console.log(`   ✅ 路径匹配成功！使用节点: ${candidate.id}`)
              break
            }
          }

          // 如果没有匹配到，使用第一个候选
          if (!conceptNode) {
            conceptNode = candidates[0]
            console.log(`   ⚠️ 路径验证失败，使用第一个候选节点: ${conceptNode.id}`)
          }
        }
      }

      if (!conceptNode) {
        console.log(`   ⚠️ 未找到概念节点`)
        return
      }

      console.log(`   ✅ 找到概念节点: ${conceptNode.id} (${conceptNode.label})`)
      console.log(`   要挂载的 fields:`, Object.keys(ontologyNode.fields))

      // 统计要素节点数量（需要累加，因为可能多个 ontology 节点映射到同一个概念节点）
      const fieldsCount = ontologyNode.fields && typeof ontologyNode.fields === 'object'
        ? Object.keys(ontologyNode.fields).filter(key => ontologyNode.fields[key]).length
        : 0

      if (fieldsCount > 0) {
        const currentCount = nodeFieldCountMap.get(conceptNode.id) || 0
        nodeFieldCountMap.set(conceptNode.id, currentCount + fieldsCount)
      }

      // 添加要素节点（总是创建，不受开关控制）
      if (ontologyNode.fields && typeof ontologyNode.fields === 'object') {
        Object.entries(ontologyNode.fields).forEach(([fieldKey, fieldValue]) => {
          if (!fieldValue) return

          // 创建要素节点
          const fieldNodeId = `field_${ontologyNode.pid}_${fieldKey}`
          const fieldNode = {
            id: fieldNodeId,
            label: fieldKey,  // label 只显示 key（字段名）
            type: 'element',
            location: ontologyNode.location || [],
            pid: ontologyNode.pid,
            fieldKey: fieldKey,
            fieldValue: fieldValue  // value 存储在 fieldValue 中，用于 tooltip 显示
          }

          nodes.push(fieldNode as any)
          fieldNodeCount++

          // 创建 hasAttribute 边：概念节点 -> 要素节点
          const fieldEdge = {
            id: `edge_field_${edges.length + fieldEdgeCount}`,
            source: conceptNode.id,
            target: fieldNodeId,
            label: 'hasAttribute'
          }

          edges.push(fieldEdge)
          fieldEdgeCount++
        })
      }
    })
  }

  // 为有要素节点的概念节点添加 displayLabel 和 fieldCount
  nodes.forEach((node: any) => {
    if (node.type !== 'element') {
      const fieldCount = nodeFieldCountMap.get(node.id) || 0
      node.fieldCount = fieldCount  // 直接存储数量，供 HTML 标签使用
      if (fieldCount > 0) {
        node.displayLabel = `${node.label} (${fieldCount})`
      } else {
        node.displayLabel = node.label
      }
    } else {
      // 要素节点保持原 label
      node.displayLabel = node.label
      node.fieldCount = 0
    }
  })

  console.log('📊 过滤后数据:')
  console.log('  - 概念节点数:', nodes.length - fieldNodeCount)
  console.log('  - 要素节点数:', fieldNodeCount)
  console.log('  - 总节点数:', nodes.length)
  console.log('  - 概念边数:', edges.length - fieldEdgeCount)
  console.log('  - 要素边数:', fieldEdgeCount)
  console.log('  - 总边数:', edges.length)
  console.log(
    '  - 节点列表:',
    nodes.map(n => `${n.id}:${n.label}`)
  )
  console.log(
    '  - 边列表:',
    edges.map(e => `${e.source}->${e.target}(${e.label})`)
  )

  graphNodes.value = nodes
  graphEdges.value = edges

  // 构建导航树数据
  buildGraphTreeData()
}

// 构建业务实体图谱数据（模拟数据）

// 文件夹模式已改为从后端 API 获取数据，不再需要本地 JSON 加载

// 处理图谱节点点击
const handleNodeClick = (nodeData: { id: string; label: string; type: string }) => {
  console.log('🎯 图谱节点被点击:', nodeData)

  // 处理文档节点 (doc_xxx)
  if (nodeData.type === 'doc' && nodeData.id.startsWith('doc_')) {
    const lineId = parseInt(nodeData.id.replace('doc_', ''))
    if (!isNaN(lineId)) {
      selectTreeNode(lineId)
    }
    return
  }

  // 处理要素节点 (field_pid_fieldKey)
  if (nodeData.type === 'element' && nodeData.id.startsWith('field_')) {
    console.log('🏷️ 要素节点被点击，直接使用节点的 location 信息...')
    console.log('  - nodeData:', nodeData)

    // 直接从节点数据中读取 location（已在 fieldNodesBuilder 中保存）
    const fieldNodeData = nodeData as any // 类型断言，因为要素节点包含额外的字段
    if (fieldNodeData.location && fieldNodeData.location.length > 0) {
      const firstLocation = fieldNodeData.location[0]
      console.log(`  - 找到位置信息:`, firstLocation)

      // 调用 PDF 跳转
      if (pdfReaderRef.value && firstLocation.page) {
        const rect = [firstLocation.l, firstLocation.t, firstLocation.r, firstLocation.b]
        // scrollToAnnotation 期望接收一个对象参数：{pageNum, rect, needsConversion}
        pdfReaderRef.value.scrollToAnnotation({
          pageNum: firstLocation.page,
          rect: rect,
          needsConversion: true
        })
        console.log(`  ✓ 跳转到 PDF 第 ${firstLocation.page} 页`)
      } else {
        console.log(`  ⚠️ location 缺少 page 信息:`, firstLocation)
      }
    } else {
      console.log(`  ⚠️ 节点缺少 location 信息，pid: ${fieldNodeData.pid}`)
    }
    return
  }

  // 处理概念节点：查找连接到它的第一个文档节点
  if (nodeData.type === 'normal') {
    console.log('🏷️ 概念节点，查找关联的文档节点...')

    // 在图谱边中查找以该概念为 target 的 instanceOf 边
    const relatedEdges = graphEdges.value.filter(edge => edge.target === nodeData.id && edge.label === 'instanceOf')

    console.log(`  找到 ${relatedEdges.length} 个关联边`)

    if (relatedEdges.length > 0) {
      // 获取第一个文档节点的 ID
      const firstDocId = relatedEdges[0].source
      console.log(`  跳转到第一个文档节点: ${firstDocId}`)

      // 提取 line_id 并跳转
      if (firstDocId.startsWith('doc_')) {
        const lineId = parseInt(firstDocId.replace('doc_', ''))
        if (!isNaN(lineId)) {
          selectTreeNode(lineId)
          return
        }
      }
    }

    console.log('  ⚠️ 未找到关联的文档节点')
  }
}

// 处理图谱边点击
const handleEdgeClick = (edgeData: { id: string; source: string; target: string; label: string }) => {
  console.log('🔗 图谱边被点击:', edgeData)
}

// 切换导航面板
const toggleNavPanel = () => {
  isNavCollapsed.value = !isNavCollapsed.value
}

// 图谱控制函数
const handleGraphReset = () => {
  cytoscapeRef.value?.resetLayout()
}

const handleGraphFit = () => {
  cytoscapeRef.value?.fitView()
}

const handleGraphZoomIn = () => {
  cytoscapeRef.value?.zoomIn()
}

const handleGraphZoomOut = () => {
  cytoscapeRef.value?.zoomOut()
}

// 业务实体图谱相关方法

// 构建图谱树形导航数据
const buildGraphTreeData = () => {
  console.log('🌲 开始构建图谱树形导航数据')

  const nodes = graphNodes.value
  const edges = graphEdges.value

  if (nodes.length === 0) {
    console.log('⚠️ 没有节点数据')
    graphTreeData.value = []
    return
  }

  // 🎯 过滤掉要素节点，只保留概念节点
  const conceptNodes = nodes.filter(node => node.type !== 'element')

  // 构建父子关系映射
  const childrenMap = new Map<string, string[]>()
  const parentMap = new Map<string, string>()

  // hasPart, hasMember 表示父子关系（排除 hasAttribute）
  edges.forEach(edge => {
    if (edge.label === 'hasPart' || edge.label === 'hasMember') {
      const parent = edge.source
      const child = edge.target

      if (!childrenMap.has(parent)) {
        childrenMap.set(parent, [])
      }
      childrenMap.get(parent)!.push(child)
      parentMap.set(child, parent)
    }
  })

  // 找到根节点（没有父节点的节点，且是概念节点）
  const rootNodeIds = conceptNodes
    .filter(node => !parentMap.has(node.id))
    .map(node => node.id)

  console.log('📌 根节点数:', rootNodeIds.length)
  console.log('📌 根节点列表:', rootNodeIds)

  // 递归构建树（只包含概念节点）
  const buildTree = (nodeId: string): any => {
    const node = conceptNodes.find(n => n.id === nodeId)
    if (!node) return null

    const children = childrenMap.get(nodeId) || []
    const childrenNodes = children.map(childId => buildTree(childId)).filter(Boolean)

    return {
      id: node.id,
      label: node.label,
      nodeType: node.type,
      children: childrenNodes.length > 0 ? childrenNodes : undefined
    }
  }

  const treeData = rootNodeIds.map(id => buildTree(id)).filter(Boolean)

  graphTreeData.value = treeData
  console.log('✅ 图谱树形数据构建完成:', treeData.length, '个根节点')
}

// 处理导航节点选择
const handleNavNodeSelect = (nodeId: string) => {
  console.log('🎯 导航选中节点:', nodeId)

  // 更新选中状态
  selectedGraphNodeId.value = nodeId

  // 高亮图谱节点
  if (cytoscapeRef.value) {
    cytoscapeRef.value.highlightNode?.(nodeId)
    cytoscapeRef.value.centerNode?.(nodeId)
  }

  // 触发图谱节点点击（模拟）
  const node = graphNodes.value.find(n => n.id === nodeId)
  if (node) {
    handleNodeClick(node)
  }
}

// 处理段落点击
const handleParagraphClick = async (paragraphIds: number[]) => {
  console.log('📄 点击段落，line_ids:', paragraphIds)

  if (!paragraphIds || paragraphIds.length === 0) {
    console.warn('❌ 段落 IDs 为空')
    return
  }

  try {
    // 从 nodeMap 中获取所有段落行的信息
    const paragraphNodes = paragraphIds.map(id => nodeMap.value[id]).filter(node => node) // 过滤掉不存在的节点

    if (paragraphNodes.length === 0) {
      console.warn('❌ 未找到段落节点')
      return
    }

    console.log('✅ 找到段落节点:', paragraphNodes)

    // 收集所有的 boxes
    const allBoxes: any[] = []
    paragraphNodes.forEach(node => {
      if (node.box) {
        allBoxes.push({
          page: node.page,
          box: node.box
        })
      }
    })

    if (allBoxes.length === 0) {
      console.warn('❌ 段落没有 box 信息')
      return
    }

    // 跳转到第一个 box 所在的页面
    const firstBox = allBoxes[0]
    const pageNum = firstBox.page + 1
    pdfData.currentPage = pageNum

    // 合并所有的 boxes 并高亮
    const mergedBoxes = mergeBoxesByColumn(allBoxes.map(b => b.box))
    const allQuadPoints = mergedBoxes.flatMap((box: number[]) => boxToQuadPoints(box))

    // 创建高亮对象
    const highlightData = {
      pageNum: pageNum,
      rect: firstBox.box,
      quadPoints: allQuadPoints,
      needsConversion: true, // TOPLEFT 坐标，需要转换为 PDF 坐标
      jump: true
    }

    // 更新 PDF 高亮区域
    pdfData.highlightRects = [highlightData]

    // 跳转并高亮
    const pdfViewer = contentViewerRef.value?.pdfViewerRef
    if (pdfViewer?.scrollToAnnotation) {
      await nextTick()
      await pdfViewer.scrollToAnnotation(highlightData)
      console.log('✅ 已跳转到段落位置并高亮')
    }
  } catch (error) {
    console.error('❌ 段落跳转失败:', error)
  }
}

// 通过ID查找节点（递归查找包括子节点）
const findNodeById = (nodes: any[], id: number): any => {
  for (const node of nodes) {
    if (node.line_id === id) return node

    // 递归查找子节点
    if (node.children && node.children.length > 0) {
      const found = findNodeById(node.children, id)
      if (found) return found
    }
  }
  return null
}

// 处理树节点选择（兼容旧接口）
const handleTreeNodeSelect = (node: any) => {
  if (!node) return
  activeItem.value = node
  handleReviewItemClick(node)
}

// 设置筛选条件
const setActiveFilter = (filterKey: number | null) => {
  state.activeFilter = filterKey
  getData()
}
// 刷新数据的方法
const refreshData = async () => {
  console.log('🔄 开始刷新数据，taskId:', taskId.value)

  // 清空旧数据，防止使用上一个任务的数据
  pdfAnnotationsData.value = null
  pdfAnnotations.value = []
  reviewListData.value = null

  // 加载 ontology 数据
  if (taskId.value) {
    console.log('📦 开始加载 ontology 数据...')
    await loadOntologyData(taskId.value)
    console.log('✅ ontology 数据加载完成')
  }

  await getData()
  await getFile()
  await getMarkList()

  console.log('✅ 数据刷新完成')
}
// 页面离开确认弹窗
const leaveConfirmVisible = ref(false)
const nextRoute = ref<any>(null)
// 确认离开页面
const confirmLeave = () => {
  leaveConfirmVisible.value = false
  if (nextRoute.value) {
    nextRoute.value.next()
  }
}

// 加载标签层级配置
const loadLabelHierarchy = async () => {
  try {
    const hierarchyUrl = `${import.meta.env.BASE_URL}hrdoc/label/label_hierarchy.json`
    const response = await fetch(hierarchyUrl)
    if (response.ok) {
      const data = await response.json()
      if (data.hierarchy && Array.isArray(data.hierarchy)) {
        labelHierarchy.value = data.hierarchy

        // 构建顺序映射表（索引越小，优先级越高）
        const orderMap = new Map<string, number>()
        data.hierarchy.forEach((item: any, index: number) => {
          // 一级标签
          orderMap.set(item.label, index * 1000) // 用1000的倍数，为二级标签留出空间

          // 二级标签
          if (item.children && Array.isArray(item.children)) {
            item.children.forEach((child: string, childIndex: number) => {
              orderMap.set(child, index * 1000 + childIndex + 1)
            })
          }
        })

        labelOrderMap.value = orderMap
        console.log(
          '✅ 标签层级配置加载成功，一级标签数:',
          data.total_first_level,
          '二级标签数:',
          data.total_second_level
        )
        console.log('📋 标签顺序映射表:', Array.from(orderMap.entries()))
      }
    } else {
      console.warn('⚠️ 未找到 label_hierarchy.json，将使用默认排序')
    }
  } catch (error) {
    console.warn('⚠️ 加载标签层级配置失败，将使用默认排序:', error)
  }
}

// 对树节点按照 hierarchy 顺序排序（可用于预构建树和客户端构建树）
const sortTreeByHierarchy = (treeNodes: any[]) => {
  if (!treeNodes || treeNodes.length === 0 || labelOrderMap.value.size === 0) {
    return treeNodes
  }

  // 排序一级标签
  treeNodes.sort((a, b) => {
    const orderA = labelOrderMap.value.get(a.label_level1 || a.text) ?? 999999
    const orderB = labelOrderMap.value.get(b.label_level1 || b.text) ?? 999999
    return orderA - orderB
  })

  // 排序每个一级标签下的二级标签
  treeNodes.forEach(level1Node => {
    if (level1Node.children && level1Node.children.length > 0) {
      // 过滤出二级标签节点
      const level2Nodes = level1Node.children.filter((child: any) => child.class === 'label-group-2')
      const otherChildren = level1Node.children.filter((child: any) => child.class !== 'label-group-2')

      // 排序二级标签
      level2Nodes.sort((a: any, b: any) => {
        const orderA = labelOrderMap.value.get(a.label_level2 || a.text) ?? 999999
        const orderB = labelOrderMap.value.get(b.label_level2 || b.text) ?? 999999
        return orderA - orderB
      })

      // 重新组合：二级标签 + 其他子节点
      level1Node.children = [...level2Nodes, ...otherChildren]
    }
  })

  console.log('📊 已按照 hierarchy 顺序排序树节点')
  return treeNodes
}

// 页面挂载后初始化数据
onMounted(async () => {
  // 加载标签层级配置
  await loadLabelHierarchy()

  // 仅使用地址栏中的 taskId，不再从 taskList.json 回退
  taskId.value = (route.query.taskId as string) || ''
  refreshData()
})

// 监听路由离开
onBeforeRouteLeave((to, from, next) => {
  // 检查是否正在下载
  if (exportState.loading) {
    nextRoute.value = { to, from, next }
    leaveConfirmVisible.value = true
    return
  }
  next()
})
// 页面卸载时清理
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

.content-viewer-wrapper {
  border-right: 1px solid #e5e7eb;
  position: relative;
  flex: 1;
  min-width: 860px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.review-panel {
  position: relative;
  flex: 1;
  // max-width: 632px;
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
    padding: 11px 24px;
    border-bottom: 1px solid var(--line-2);
    background: white;
    font-size: 14px;
    line-height: 22px;
    min-height: 55px;
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

      // 特定tab的颜色样式（适用于正常状态和骨架状态）
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

      // 骨架tab样式
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

        // 骨架状态下保持特定颜色，但降低透明度
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
    &.tree-view {
      padding: 16px;
      display: flex;
      flex-direction: column;
      height: 100%;

      .tree-list {
        display: flex;
        flex-direction: column;
        gap: 4px;
      }
    }

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

// 骨架屏样式
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

// 图谱视图容器
.graph-view-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  flex: 1;
  position: relative;
}

// 文件夹视图容器
.folder-view-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  flex: 1;
  overflow: hidden;
}

// 顶部工具栏
.graph-toolbar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 8px 16px;
  background: #fafafa;
  border-bottom: 1px solid #e5e6eb;
  flex-shrink: 0;

  .toolbar-right {
    display: flex;
    align-items: center;
    gap: 0;

    :deep(.ant-btn) {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 32px;
      height: 32px;

      &.active {
        background: #e6f7ff;
        color: #1890ff;
        border-color: #91d5ff;
      }

      &:hover {
        border-color: #1890ff;
        color: #1890ff;
      }
    }
  }
}

// 导航面板包装器
.graph-nav-panel-wrapper {
  position: absolute;
  top: 48px;
  right: 16px;
  z-index: 10;
  max-width: 400px;
  max-height: 400px;
  background: #ffffff;
  border: 1px solid #e5e6eb;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

// 导航面板
.graph-nav-panel {
  max-height: 400px;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 8px;

  .nav-tree-list {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  // 自定义滚动条
  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 3px;
  }

  &::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 3px;

    &:hover {
      background: #a8a8a8;
    }
  }
}

// 图谱画布
.graph-canvas {
  flex: 1;
  position: relative;
  min-height: 0;
}
</style>

