<template>
  <div class="labeled-data-viewer">
    <!-- 头部信息 -->
    <div class="viewer-header">
      <div class="document-info">
        <h3 class="document-name">{{ documentData?.document_name || '暂无文档' }}</h3>
        <span class="total-count">共 {{ documentData?.total_items || 0 }} 项</span>
      </div>

      <!-- 筛选器 -->
      <div class="filter-controls">
        <el-select
          v-model="selectedLabel"
          placeholder="按标签筛选"
          clearable
          class="label-filter"
          @change="handleFilterChange"
        >
          <el-option label="全部" value="" />
          <el-option
            v-for="label in uniqueLabels"
            :key="label"
            :label="getLabelDisplay(label)"
            :value="label"
          />
        </el-select>

        <el-input
          v-model="searchText"
          placeholder="搜索文本内容"
          clearable
          class="text-search"
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon>🔍</el-icon>
          </template>
        </el-input>
      </div>
    </div>

    <!-- 数据列表 -->
    <div class="data-list">
      <el-empty v-if="!filteredItems.length" description="暂无数据" />

      <div
        v-for="item in paginatedItems"
        :key="item.id"
        class="data-item"
        :class="`label-${item.label}`"
      >
        <div class="item-header">
          <span class="item-id">#{{ item.id }}</span>
          <el-tag :type="getLabelType(item.label)" size="small">
            {{ getLabelDisplay(item.label) }}
          </el-tag>
          <span class="page-info">第 {{ item.page_no }} 页</span>
        </div>

        <div class="item-content">
          <div v-if="item.label === 'table'" class="table-content" v-html="item.text"></div>
          <div v-else class="text-content">{{ item.text }}</div>
        </div>

        <div class="item-bbox">
          <el-tooltip content="边界框坐标信息" placement="top">
            <div class="bbox-info">
              <span>L: {{ item.bbox.l.toFixed(2) }}</span>
              <span>T: {{ item.bbox.t.toFixed(2) }}</span>
              <span>R: {{ item.bbox.r.toFixed(2) }}</span>
              <span>B: {{ item.bbox.b.toFixed(2) }}</span>
            </div>
          </el-tooltip>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="filteredItems.length > pageSize" class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="filteredItems.length"
        layout="total, prev, pager, next, jumper"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
// import { Search } from '@element-plus/icons-vue'

interface BBox {
  l: number
  t: number
  r: number
  b: number
  coord_origin: string
}

interface LabeledItem {
  id: number
  label: string
  text: string
  page_no: number
  bbox: BBox
}

interface DocumentData {
  document_name: string
  total_items: number
  items: LabeledItem[]
}

const props = defineProps<{
  dataUrl?: string
}>()

// 响应式数据
const documentData = ref<DocumentData | null>(null)
const selectedLabel = ref<string>('')
const searchText = ref<string>('')
const currentPage = ref<number>(1)
const pageSize = ref<number>(20)

// 标签类型映射
const labelTypeMap: Record<string, string> = {
  'section_header': 'primary',
  'text': '',
  'table': 'success',
  'list': 'info',
  'title': 'warning'
}

// 标签显示名称映射
const labelDisplayMap: Record<string, string> = {
  'section_header': '章节标题',
  'text': '正文',
  'table': '表格',
  'list': '列表',
  'title': '标题'
}

// 计算属性：获取所有唯一标签
const uniqueLabels = computed(() => {
  if (!documentData.value?.items) return []
  const labels = new Set(documentData.value.items.map(item => item.label))
  return Array.from(labels).sort()
})

// 计算属性：过滤后的数据
const filteredItems = computed(() => {
  if (!documentData.value?.items) return []

  let items = documentData.value.items

  // 按标签筛选
  if (selectedLabel.value) {
    items = items.filter(item => item.label === selectedLabel.value)
  }

  // 按文本搜索
  if (searchText.value) {
    const keyword = searchText.value.toLowerCase()
    items = items.filter(item =>
      item.text.toLowerCase().includes(keyword)
    )
  }

  return items
})

// 计算属性：分页后的数据
const paginatedItems = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredItems.value.slice(start, end)
})

// 获取标签类型
const getLabelType = (label: string): string => {
  return labelTypeMap[label] || ''
}

// 获取标签显示名称
const getLabelDisplay = (label: string): string => {
  return labelDisplayMap[label] || label
}

// 处理筛选变化
const handleFilterChange = () => {
  currentPage.value = 1
}

// 处理搜索
const handleSearch = () => {
  currentPage.value = 1
}

// 处理分页变化
const handlePageChange = (page: number) => {
  currentPage.value = page
}

// 加载数据
const loadData = async () => {
  try {
    const url = props.dataUrl || '/knowledge-graph/output_20251123_144831_labeled.json'
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error('Failed to load data')
    }
    documentData.value = await response.json()
  } catch (error) {
    console.error('Error loading labeled data:', error)
  }
}

onMounted(() => {
  loadData()
})
</script>

<style lang="scss" scoped>
@import './css/labeled-data-viewer.scss';
</style>
