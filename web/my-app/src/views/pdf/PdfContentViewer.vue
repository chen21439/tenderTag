<template>
  <div class="pdf-content-viewer">
    <div class="toolbar">
      <a-space>
        <a-upload
          :before-upload="handleFileUpload"
          :show-upload-list="false"
          accept=".json"
        >
          <a-button type="primary">
            <UploadOutlined /> 加载 Table JSON
          </a-button>
        </a-upload>

        <a-upload
          :before-upload="handleParagraphUpload"
          :show-upload-list="false"
          accept=".json"
        >
          <a-button type="default">
            <FileTextOutlined /> 加载 Paragraph JSON
          </a-button>
        </a-upload>

        <a-divider type="vertical" />

        <a-select
          v-model:value="filterType"
          style="width: 150px"
          placeholder="筛选内容类型"
        >
          <a-select-option value="all">全部内容</a-select-option>
          <a-select-option value="table">仅表格</a-select-option>
          <a-select-option value="paragraph">仅段落</a-select-option>
        </a-select>

        <a-input-search
          v-model:value="searchText"
          placeholder="搜索内容..."
          style="width: 200px"
          @search="handleSearch"
        />

        <a-divider type="vertical" />

        <a-switch
          :checked="useBboxRendering"
          @change="useBboxRendering = $event"
          checked-children="BBox渲染"
          un-checked-children="表格渲染"
        />

        <a-divider type="vertical" />

        <a-switch
          :checked="globalWrapEnabled"
          @change="globalWrapEnabled = $event"
          checked-children="全局换行"
          un-checked-children="全局不换行"
        />

        <a-divider type="vertical" />

        <a-statistic
          title="表格数"
          :value="tableData?.total_tables || 0"
          :value-style="{ fontSize: '14px' }"
          style="display: inline-block; margin: 0 16px;"
        />
        <a-statistic
          title="段落数"
          :value="paragraphData?.total_paragraphs || 0"
          :value-style="{ fontSize: '14px' }"
          style="display: inline-block; margin: 0 16px;"
        />
      </a-space>
    </div>

    <div class="main-content">
      <div class="content-list" ref="contentContainer">
        <a-spin :spinning="loading" tip="加载中...">
          <div v-if="error" class="error-message">
            <a-alert :message="error" type="error" show-icon />
          </div>

          <div v-else-if="!tableData && !paragraphData" class="empty-state">
            <a-empty description="请加载 JSON 文件">
              <template #image>
                <FileOutlined style="font-size: 48px; color: #bfbfbf;" />
              </template>
            </a-empty>
          </div>

          <div v-else>
            <!-- BBox渲染模式 -->
            <div v-if="useBboxRendering" class="bbox-rendering-container">
              <div v-for="pageNum in sortedPageNumbers" :key="`page-${pageNum}`" class="page-container" :id="`page-${pageNum}`">
                <div class="page-header">
                  <h2>第 {{ pageNum }} 页</h2>
                </div>
                <div class="page-content" :style="{ position: 'relative', width: '595px', height: '842px', border: '1px solid #ddd', background: 'white', margin: '0 auto' }">
                  <!-- 渲染该页的表格 -->
                  <div
                    v-for="table in getTablesForPage(pageNum)"
                    :key="table.id"
                    class="bbox-table"
                    :style="getBboxStyle(table.bbox)"
                    :title="`${table.id} - BBox: ${formatBbox(table.bbox)}`"
                  >
                    <div class="bbox-table-label">{{ table.id }}</div>
                    <div class="bbox-table-content">
                      {{ table.rows?.length || 0 }}行 × {{ table.columns?.length || 0 }}列
                    </div>
                  </div>

                  <!-- 渲染该页的段落 -->
                  <div
                    v-for="para in getParagraphsForPage(pageNum)"
                    :key="para.id"
                    class="bbox-paragraph"
                    :style="getBboxStyle(para.bbox)"
                    :title="`${para.id} - BBox: ${formatBbox(para.bbox)}`"
                  >
                    <div class="bbox-paragraph-label">{{ para.id }}</div>
                    <div class="bbox-paragraph-preview">{{ para.content?.substring(0, 30) }}...</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 传统表格渲染模式 -->
            <div v-else class="content-blocks">
              <!-- 渲染表格 -->
              <template v-for="table in filteredTables" :key="table.id">
                <div class="content-block table-block" :id="table.id">
                  <div class="block-header">
                    <a-tag color="blue">表格</a-tag>
                    <span class="block-id">{{ table.id }}</span>
                    <span class="block-page">第 {{ table.page }} 页</span>
                    <a-tag v-if="table.level" :color="table.level === 1 ? 'green' : 'orange'">
                      {{ table.level === 1 ? '主表格' : '嵌套表格' }}
                    </a-tag>
                    <a-switch
                      :checked="tableWrapStates[table.id]"
                      @change="toggleTableWrap(table.id, $event)"
                      checked-children="自动换行"
                      un-checked-children="不换行"
                      size="small"
                      style="margin-left: auto;"
                    />
                  </div>

                <div class="table-wrapper" :class="{ 'wrap-content': shouldWrap(table.id) }">
                  <a-table
                    :columns="formatTableColumns(table)"
                    :data-source="formatTableDataSource(table)"
                    :pagination="false"
                    :bordered="true"
                    size="small"
                    :scroll="{ x: true }"
                  >
                    <template #bodyCell="{ column, record }">
                      <template v-if="record.cells && record.cells[column.dataIndex]">
                        {{ record.cells[column.dataIndex].content }}
                      </template>
                    </template>
                  </a-table>
                </div>

                <div class="table-info">
                  <span>行数: {{ table.rows?.length || 0 }}</span>
                  <span>列数: {{ table.columns?.length || 0 }}</span>
                  <span>BBox: {{ formatBbox(table.bbox) }}</span>
                </div>
              </div>
            </template>

              <!-- 渲染段落 -->
              <template v-for="para in filteredParagraphs" :key="para.id">
                <div class="content-block paragraph-block" :id="para.id">
                  <div class="block-header">
                    <a-tag color="green">段落</a-tag>
                    <span class="block-id">{{ para.id }}</span>
                    <span class="block-page">第 {{ para.page }} 页</span>
                  </div>

                  <div class="paragraph-content" :title="`BBox: ${formatBbox(para.bbox)}`">
                    {{ para.content }}
                  </div>
                </div>
              </template>
            </div>
          </div>
        </a-spin>
      </div>

      <!-- 右侧导航面板 -->
      <div class="navigation-panel" :class="{ collapsed: !showNavPanel }">
        <div class="panel-header">
          <h3>
            <UnorderedListOutlined /> 内容导航
          </h3>
          <a-button type="text" @click="toggleNavPanel">
            <CloseOutlined />
          </a-button>
        </div>

        <div class="panel-content">
          <a-tree
            v-if="navigationTree.length > 0"
            :tree-data="navigationTree"
            :default-expand-all="false"
            @select="handleTreeSelect"
          >
            <template #title="{ title, key, type }">
              <div class="tree-node">
                <a-tag :color="type === 'table' ? 'blue' : 'green'" size="small">
                  {{ type === 'table' ? '表' : '段' }}
                </a-tag>
                <span>{{ title }}</span>
              </div>
            </template>
          </a-tree>
          <a-empty v-else description="暂无内容" />
        </div>

        <div class="panel-footer">
          <a-button type="text" block @click="scrollToTop">
            <UpOutlined /> 回到顶部
          </a-button>
        </div>
      </div>

      <!-- 折叠按钮 -->
      <a-button
        v-if="!showNavPanel"
        class="nav-toggle-btn"
        type="primary"
        @click="toggleNavPanel"
      >
        <MenuOutlined />
      </a-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import {
  UploadOutlined,
  FileTextOutlined,
  FileOutlined,
  UnorderedListOutlined,
  CloseOutlined,
  UpOutlined,
  MenuOutlined
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'

// 响应式数据
const tableData = ref(null)
const paragraphData = ref(null)
const loading = ref(false)
const error = ref(null)
const filterType = ref('all')
const searchText = ref('')
const showNavPanel = ref(true)
const contentContainer = ref(null)
const useBboxRendering = ref(false) // BBox渲染模式开关
const globalWrapEnabled = ref(false) // 全局换行开关
const tableWrapStates = ref({}) // 各表格的换行状态

// 默认加载的 JSON 文件路径（使用自动获取最新时间戳的API）
const DEFAULT_TABLE_URL = 'http://localhost:3000/api/content/table'
const DEFAULT_PARAGRAPH_URL = 'http://localhost:3000/api/content/paragraph'

// 处理表格 JSON 文件上传
const handleFileUpload = async (file) => {
  try {
    loading.value = true
    error.value = null

    const text = await file.text()
    const data = JSON.parse(text)

    // 验证数据结构
    if (!data.tables || !Array.isArray(data.tables)) {
      throw new Error('无效的表格 JSON 格式')
    }

    tableData.value = data
    message.success(`成功加载 ${data.total_tables} 个表格`)

    await nextTick()
    scrollToTop()
  } catch (err) {
    error.value = `加载表格 JSON 失败: ${err.message}`
    message.error(error.value)
    console.error('加载表格错误:', err)
  } finally {
    loading.value = false
  }
  return false
}

// 处理段落 JSON 文件上传
const handleParagraphUpload = async (file) => {
  try {
    loading.value = true
    error.value = null

    const text = await file.text()
    const data = JSON.parse(text)

    // 验证数据结构
    if (!data.paragraphs || !Array.isArray(data.paragraphs)) {
      throw new Error('无效的段落 JSON 格式')
    }

    paragraphData.value = data
    message.success(`成功加载 ${data.total_paragraphs} 个段落`)

    await nextTick()
    scrollToTop()
  } catch (err) {
    error.value = `加载段落 JSON 失败: ${err.message}`
    message.error(error.value)
    console.error('加载段落错误:', err)
  } finally {
    loading.value = false
  }
  return false
}

// 过滤表格
const filteredTables = computed(() => {
  if (!tableData.value || filterType.value === 'paragraph') return []

  let tables = tableData.value.tables || []

  if (searchText.value) {
    tables = tables.filter(table => {
      // 搜索表格内容
      const searchLower = searchText.value.toLowerCase()
      return table.rows?.some(row =>
        row.cells?.some(cell =>
          cell.content?.toLowerCase().includes(searchLower)
        )
      ) || table.columns?.some(col =>
        col.name?.toLowerCase().includes(searchLower)
      )
    })
  }

  return tables.sort((a, b) => {
    if (a.page !== b.page) return a.page - b.page
    return (a.bbox?.[1] || 0) - (b.bbox?.[1] || 0)
  })
})

// 过滤段落
const filteredParagraphs = computed(() => {
  if (!paragraphData.value || filterType.value === 'table') return []

  let paragraphs = paragraphData.value.paragraphs

  if (searchText.value) {
    const searchLower = searchText.value.toLowerCase()
    paragraphs = paragraphs.filter(para =>
      para.content?.toLowerCase().includes(searchLower)
    )
  }

  return paragraphs.sort((a, b) => {
    if (a.page !== b.page) return a.page - b.page
    return (a.bbox?.[1] || 0) - (b.bbox?.[1] || 0)
  })
})

// 构建导航树
const navigationTree = computed(() => {
  const tree = []

  // 按页面分组
  const pageMap = new Map()

  // 添加表格
  filteredTables.value.forEach(table => {
    if (!pageMap.has(table.page)) {
      pageMap.set(table.page, { tables: [], paragraphs: [] })
    }
    pageMap.get(table.page).tables.push(table)
  })

  // 添加段落
  filteredParagraphs.value.forEach(para => {
    if (!pageMap.has(para.page)) {
      pageMap.set(para.page, { tables: [], paragraphs: [] })
    }
    pageMap.get(para.page).paragraphs.push(para)
  })

  // 构建树结构
  Array.from(pageMap.keys()).sort((a, b) => a - b).forEach(page => {
    const pageData = pageMap.get(page)
    const pageNode = {
      title: `第 ${page} 页`,
      key: `page-${page}`,
      children: []
    }

    // 合并表格和段落，按 y 坐标排序
    const allItems = [
      ...pageData.tables.map(t => ({ ...t, type: 'table' })),
      ...pageData.paragraphs.map(p => ({ ...p, type: 'paragraph' }))
    ].sort((a, b) => (a.bbox?.[1] || 0) - (b.bbox?.[1] || 0))

    allItems.forEach(item => {
      const preview = item.type === 'table'
        ? `表格 ${item.id} (${item.rows?.length}行×${item.columns?.length}列)`
        : `段落 ${item.id}: ${item.content?.substring(0, 30)}${item.content?.length > 30 ? '...' : ''}`

      pageNode.children.push({
        title: preview,
        key: item.id,
        type: item.type,
        isLeaf: true
      })
    })

    tree.push(pageNode)
  })

  return tree
})

// 格式化 bbox
const formatBbox = (bbox) => {
  if (!bbox || bbox.length !== 4) return 'N/A'
  return `[${bbox.map(v => Math.round(v)).join(', ')}]`
}

// 获取所有页码（排序）
const sortedPageNumbers = computed(() => {
  const pages = new Set()

  filteredTables.value.forEach(table => {
    if (table.page) pages.add(table.page)
  })

  filteredParagraphs.value.forEach(para => {
    if (para.page) pages.add(para.page)
  })

  return Array.from(pages).sort((a, b) => a - b)
})

// 获取指定页的表格
const getTablesForPage = (pageNum) => {
  return filteredTables.value.filter(table => table.page === pageNum)
}

// 获取指定页的段落
const getParagraphsForPage = (pageNum) => {
  return filteredParagraphs.value.filter(para => para.page === pageNum)
}

// 格式化表格列定义（Ant Design Table格式）
const formatTableColumns = (table) => {
  if (!table.columns) return []

  return table.columns.map(col => ({
    title: col.name,
    dataIndex: col.index,
    key: col.id,
    width: 150,
    ellipsis: true,
    customCell: (record) => {
      // 查找对应的cell来获取colspan/rowspan
      const cell = record.cells?.[col.index]
      if (cell) {
        const result = {}
        if (cell.colspan && cell.colspan > 1) {
          result.colSpan = cell.colspan
        }
        if (cell.rowspan && cell.rowspan > 1) {
          result.rowSpan = cell.rowspan
        }
        // 如果cell被前面的合并单元格覆盖（start_col为null），隐藏它
        if (cell.start_col === null && cell.colspan === 1) {
          result.colSpan = 0
        }
        return result
      }
      return {}
    }
  }))
}

// 格式化表格数据源（Ant Design Table格式）
const formatTableDataSource = (table) => {
  if (!table.rows) return []

  return table.rows.map((row) => {
    const record = {
      key: row.id,
      rowId: row.id,
      cells: {}
    }

    // 将cells数组转换为对象，以列索引为key
    row.cells.forEach((cell, colIndex) => {
      record.cells[colIndex] = cell
    })

    return record
  })
}

// 将 BBox 转换为 CSS 样式
const getBboxStyle = (bbox) => {
  if (!bbox || bbox.length !== 4) {
    return { display: 'none' }
  }

  const [x0, y0, x1, y1] = bbox
  const width = x1 - x0
  const height = y1 - y0

  // PDF坐标系是从左下角开始，需要转换为从左上角
  // 假设页面高度为842（A4纸）
  const pageHeight = 842
  const top = pageHeight - y1

  return {
    position: 'absolute',
    left: `${x0}px`,
    top: `${top}px`,
    width: `${width}px`,
    height: `${height}px`,
    border: '1px solid #1890ff',
    background: 'rgba(24, 144, 255, 0.1)',
    overflow: 'hidden',
    fontSize: '10px',
    padding: '2px'
  }
}

// 搜索处理
const handleSearch = () => {
  // 搜索已通过计算属性自动触发
  message.info(`找到 ${filteredTables.value.length} 个表格和 ${filteredParagraphs.value.length} 个段落`)
}

// 树节点选择
const handleTreeSelect = (selectedKeys) => {
  if (selectedKeys.length > 0) {
    const key = selectedKeys[0]
    const element = document.getElementById(key)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' })
      // 高亮效果
      element.classList.add('highlight')
      setTimeout(() => {
        element.classList.remove('highlight')
      }, 2000)
    }
  }
}

// 面板控制
const toggleNavPanel = () => {
  showNavPanel.value = !showNavPanel.value
}

const scrollToTop = () => {
  if (contentContainer.value) {
    contentContainer.value.scrollTop = 0
  }
}

// 切换表格换行状态
const toggleTableWrap = (tableId, checked) => {
  tableWrapStates.value[tableId] = checked
}

// 判断表格是否应该换行（局部优先于全局）
const shouldWrap = (tableId) => {
  // 如果设置了局部状态，使用局部状态
  if (tableId in tableWrapStates.value) {
    return tableWrapStates.value[tableId]
  }
  // 否则使用全局状态
  return globalWrapEnabled.value
}

// 从 URL 加载 JSON 文件
const loadJsonFromUrl = async (url, type = 'table') => {
  try {
    // 添加时间戳参数防止缓存
    const timestamp = new Date().getTime()
    const urlWithTimestamp = `${url}?t=${timestamp}`

    const response = await fetch(urlWithTimestamp)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    const data = await response.json()

    if (type === 'table') {
      if (!data.tables || !Array.isArray(data.tables)) {
        throw new Error('无效的表格 JSON 格式')
      }
      tableData.value = data
      console.log(`✅ 成功加载 ${data.total_tables} 个表格`)
    } else if (type === 'paragraph') {
      if (!data.paragraphs || !Array.isArray(data.paragraphs)) {
        throw new Error('无效的段落 JSON 格式')
      }
      paragraphData.value = data
      console.log(`✅ 成功加载 ${data.total_paragraphs} 个段落`)
    }
  } catch (err) {
    console.error(`加载 ${type} JSON 失败:`, err)
    throw err
  }
}

// 加载默认 JSON 文件
const loadDefaultJsonFiles = async () => {
  try {
    loading.value = true
    error.value = null

    console.log('开始加载默认 JSON 文件...')

    // 并行加载表格和段落 JSON
    await Promise.all([
      loadJsonFromUrl(DEFAULT_TABLE_URL, 'table'),
      loadJsonFromUrl(DEFAULT_PARAGRAPH_URL, 'paragraph')
    ])

    message.success('成功加载默认文件')

    await nextTick()
    scrollToTop()
  } catch (err) {
    error.value = `加载默认文件失败: ${err.message}`
    message.warning('加载默认文件失败，请手动上传 JSON 文件')
    console.error('加载默认文件错误:', err)
  } finally {
    loading.value = false
  }
}

// 组件挂载时加载默认文件
onMounted(() => {
  loadDefaultJsonFiles()
})
</script>

<style scoped>
.pdf-content-viewer {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f0f2f5;
}

.toolbar {
  padding: 16px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 10;
}

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
  position: relative;
}

.content-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.empty-state,
.error-message {
  padding: 60px 20px;
  text-align: center;
}

.content-blocks {
  max-width: 1400px;
  margin: 0 auto;
}

/* 内容块样式 */
.content-block {
  background: white;
  border-radius: 8px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  transition: all 0.3s ease;
}

.content-block:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.content-block.highlight {
  animation: highlight-pulse 1s ease-in-out;
  box-shadow: 0 0 0 4px rgba(24, 144, 255, 0.3);
}

@keyframes highlight-pulse {
  0%, 100% { box-shadow: 0 0 0 4px rgba(24, 144, 255, 0.3); }
  50% { box-shadow: 0 0 0 8px rgba(24, 144, 255, 0.5); }
}

.block-header {
  padding: 12px 16px;
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.block-id {
  font-weight: 600;
  color: #262626;
  font-family: 'Courier New', monospace;
}

.block-page {
  color: #8c8c8c;
  font-size: 13px;
}

/* 表格样式 */
.table-block {
  border-left: 4px solid #1890ff;
}

.table-wrapper {
  overflow-x: auto;
  padding: 16px;
}

/* Ant Design Table 美化样式 */
.table-wrapper :deep(.ant-table) {
  border: none;
}

.table-wrapper :deep(.ant-table-container) {
  border: none;
}

.table-wrapper :deep(.ant-table-thead > tr > th) {
  background: linear-gradient(to bottom, #f8fafc, #f1f5f9);
  font-weight: 600;
  color: #334155;
  border: 1px solid #5dade2 !important;
}

.table-wrapper :deep(.ant-table-tbody > tr > td) {
  border: 1px solid #5dade2 !important;
  color: #475569;
  vertical-align: top;
  background: #ffffff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 换行模式样式 */
.table-wrapper.wrap-content :deep(.ant-table-tbody > tr > td) {
  white-space: normal;
  word-break: break-word;
  overflow: visible;
}

.table-wrapper :deep(.ant-table-tbody > tr:hover > td) {
  background: #f8fafc !important;
}

.table-wrapper :deep(.ant-table-cell) {
  padding: 10px 8px;
}

/* 合并单元格样式 - 淡紫色主题 */
.table-wrapper :deep(.ant-table-tbody > tr > td[colspan]) {
  background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%) !important;
  font-weight: 500;
  border: 1px solid #c084fc !important;
  box-shadow: inset 0 0 0 1px rgba(192, 132, 252, 0.3);
}

/* 旧的原生table样式（保留以防回退） */
.content-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.content-table th {
  background: #fafafa;
  padding: 12px 8px;
  border: 2px solid #d9d9d9;
  font-weight: 600;
  color: #262626;
  text-align: left;
}

.content-table td {
  padding: 10px 8px;
  border: 2px solid #d9d9d9;
  color: #595959;
  vertical-align: top;
}

.content-table td.has-nested {
  background: #f6ffed;
}

.content-table td.merged-cell {
  background: #fff7e6;
  font-weight: 500;
  border: 2px solid #ff7a45;
}

.cell-content {
  min-height: 20px;
}

/* 嵌套表格样式 */
.nested-tables {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 2px dashed #d9d9d9;
}

.nested-table-wrapper {
  margin-top: 8px;
}

.nested-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 8px;
  font-size: 12px;
}

.nested-table th {
  background: #fff7e6;
  padding: 6px 4px;
  border: 1px solid #ffd591;
  font-weight: 600;
  font-size: 11px;
}

.nested-table td {
  padding: 6px 4px;
  border: 1px solid #ffd591;
  background: white;
}

.table-info {
  padding: 8px 16px;
  background: #f9f9f9;
  border-top: 1px solid #f0f0f0;
  font-size: 12px;
  color: #8c8c8c;
  display: flex;
  gap: 16px;
}

/* 段落样式 */
.paragraph-block {
  border-left: 4px solid #52c41a;
}

.paragraph-content {
  padding: 16px 20px;
  line-height: 1.8;
  color: #262626;
  font-size: 14px;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 导航面板样式 */
.navigation-panel {
  width: 320px;
  background: white;
  border-left: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
}

.navigation-panel.collapsed {
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

.panel-footer {
  padding: 12px;
  border-top: 1px solid #f0f0f0;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 导航切换按钮 */
.nav-toggle-btn {
  position: fixed;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 100;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

/* 滚动条美化 */
.content-list::-webkit-scrollbar,
.panel-content::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.content-list::-webkit-scrollbar-track,
.panel-content::-webkit-scrollbar-track {
  background: #f0f0f0;
  border-radius: 4px;
}

.content-list::-webkit-scrollbar-thumb,
.panel-content::-webkit-scrollbar-thumb {
  background: #bfbfbf;
  border-radius: 4px;
}

.content-list::-webkit-scrollbar-thumb:hover,
.panel-content::-webkit-scrollbar-thumb:hover {
  background: #8c8c8c;
}

.table-wrapper::-webkit-scrollbar {
  height: 6px;
}

.table-wrapper::-webkit-scrollbar-track {
  background: #fafafa;
}

.table-wrapper::-webkit-scrollbar-thumb {
  background: #d9d9d9;
  border-radius: 3px;
}

/* BBox渲染模式样式 */
.bbox-rendering-container {
  max-width: 650px;
  margin: 0 auto;
  padding: 20px;
}

.page-container {
  margin-bottom: 40px;
  background: #f5f5f5;
  padding: 20px;
  border-radius: 8px;
}

.page-header {
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #262626;
}

.page-content {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.bbox-table {
  cursor: pointer;
  transition: all 0.2s ease;
}

.bbox-table:hover {
  background: rgba(24, 144, 255, 0.2) !important;
  border: 2px solid #1890ff !important;
  z-index: 10;
}

.bbox-table-label {
  font-weight: 600;
  color: #1890ff;
  font-size: 11px;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bbox-table-content {
  font-size: 9px;
  color: #595959;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bbox-paragraph {
  cursor: pointer;
  border: 1px solid #52c41a;
  background: rgba(82, 196, 26, 0.05);
  transition: all 0.2s ease;
}

.bbox-paragraph:hover {
  background: rgba(82, 196, 26, 0.15) !important;
  border: 2px solid #52c41a !important;
  z-index: 10;
}

.bbox-paragraph-label {
  font-weight: 600;
  color: #52c41a;
  font-size: 10px;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bbox-paragraph-preview {
  font-size: 8px;
  color: #595959;
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
</style>
