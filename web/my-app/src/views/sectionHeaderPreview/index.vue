<script setup>
import { ref, computed, onMounted } from 'vue'

const loading = ref(true)
const error = ref(null)
const rawData = ref(null) // 原始 JSON 数据
const currentPage = ref(1)
const selectedHeader = ref(null)
const fileInputRef = ref(null)
const showOnlySectionHeaders = ref(true) // 默认只显示 section_header

// 数据适配器 - 从 texts 数组获取数据
const adaptedData = computed(() => {
  if (!rawData.value) return null

  return {
    document_name: rawData.value.name || rawData.value.document_name,
    total_items: rawData.value.texts?.length || 0,
    texts: rawData.value.texts || [],
    pages: rawData.value.pages || {}
  }
})

// 按页码分组的文本项（根据过滤条件）
const itemsByPage = computed(() => {
  if (!adaptedData.value) return {}

  const grouped = {}
  const textsToRender = showOnlySectionHeaders.value
    ? adaptedData.value.texts.filter(item => item.label === 'section_header')
    : adaptedData.value.texts

  textsToRender.forEach(item => {
    if (item.prov && item.prov.length > 0) {
      item.prov.forEach(prov => {
        const pageNo = prov.page_no
        if (!grouped[pageNo]) {
          grouped[pageNo] = []
        }
        grouped[pageNo].push({
          ...item,
          currentProv: prov
        })
      })
    }
  })
  return grouped
})

// 总页数
const totalPages = computed(() => {
  return Object.keys(itemsByPage.value).length
})

// 当前页的项目
const currentPageItems = computed(() => {
  return itemsByPage.value[currentPage.value] || []
})

// 当前页面信息
const currentPageInfo = computed(() => {
  if (!adaptedData.value?.pages) return null
  // pages 的 key 是字符串，需要转换
  return adaptedData.value.pages[String(currentPage.value)]
})

// 加载数据（不再使用 API）
const loadData = async () => {
  loading.value = false
  // 不再从 API 加载，只通过文件上传
}

// 切换页码
const goToPage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
    selectedHeader.value = null
  }
}

// 选中 header
const selectHeader = (header) => {
  selectedHeader.value = header
}

// 获取页码列表（用于分页导航）
const pageNumbers = computed(() => {
  const pages = []
  const total = totalPages.value
  const current = currentPage.value

  // 总是显示第一页
  pages.push(1)

  // 显示当前页附近的页码
  for (let i = Math.max(2, current - 2); i <= Math.min(total - 1, current + 2); i++) {
    if (!pages.includes(i)) {
      pages.push(i)
    }
  }

  // 总是显示最后一页
  if (total > 1 && !pages.includes(total)) {
    pages.push(total)
  }

  return pages.sort((a, b) => a - b)
})

// 触发文件选择
const triggerFileInput = () => {
  fileInputRef.value?.click()
}

// 处理文件上传
const handleFileUpload = (event) => {
  const file = event.target.files?.[0]
  if (!file) return

  if (!file.name.endsWith('.json')) {
    error.value = '请选择 JSON 文件'
    return
  }

  loading.value = true
  error.value = null

  const reader = new FileReader()

  reader.onload = (e) => {
    try {
      const jsonData = JSON.parse(e.target.result)

      rawData.value = jsonData
      currentPage.value = 1
      selectedHeader.value = null
      loading.value = false
    } catch (err) {
      error.value = '无法解析 JSON 文件: ' + err.message
      console.error('Error parsing JSON:', err)
      loading.value = false
    }
  }

  reader.onerror = () => {
    error.value = '读取文件失败'
    loading.value = false
  }

  reader.readAsText(file)
}

// 切换过滤模式
const toggleSectionHeadersOnly = () => {
  showOnlySectionHeaders.value = !showOnlySectionHeaders.value
  currentPage.value = 1
  selectedHeader.value = null
}

// PDF 点到屏幕像素的缩放比例（96 DPI / 72 DPI）
const PDF_TO_SCREEN_SCALE = 96 / 72  // ≈ 1.333

// 获取文本框样式（坐标转换）
const getTextBoxStyle = (item) => {
  const bbox = item.currentProv.bbox
  const pageHeight = currentPageInfo.value?.size.height || 842

  // PDF 坐标系：BOTTOMLEFT（左下角为原点，Y轴向上）
  // Web 坐标系：TOPLEFT（左上角为原点，Y轴向下）
  //
  // PDF 使用 points (1pt = 1/72 inch)
  // 屏幕使用 pixels，通常 96 DPI
  // 缩放比例 = 96/72 ≈ 1.333

  const left = bbox.l * PDF_TO_SCREEN_SCALE
  let width = (bbox.r - bbox.l) * PDF_TO_SCREEN_SCALE
  let height = (bbox.t - bbox.b) * PDF_TO_SCREEN_SCALE

  // SectionHeaderOnly 模式下，宽高调整为 1.5 倍
  if (showOnlySectionHeaders.value && item.label === 'section_header') {
    width = width * 1.5
    height = height * 1.5
  }

  // Web 坐标的 top = (pageHeight - bbox.t) * scale
  const top = (pageHeight - bbox.t) * PDF_TO_SCREEN_SCALE

  return {
    left: `${left}px`,
    top: `${top}px`,
    width: `${width}px`,
    height: `${height}px`
  }
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="section-header-preview">
    <div class="page-container">
      <div class="page-header">
        <h1>📑 Section Headers 预览</h1>
        <p class="subtitle">按页面浏览文档的章节标题及位置信息</p>
      </div>

      <!-- 控制区域 - 始终显示 -->
      <div class="control-section">
        <!-- Section Headers Only 过滤按钮 -->
        <button
          v-if="rawData"
          :class="['filter-btn', { active: showOnlySectionHeaders }]"
          @click="toggleSectionHeadersOnly"
        >
          Section Headers Only
        </button>

        <!-- 上传按钮 -->
        <button class="upload-btn" @click="triggerFileInput">
          📂 读取 JSON 文件
        </button>
        <input
          ref="fileInputRef"
          type="file"
          accept=".json"
          style="display: none"
          @change="handleFileUpload"
        />
      </div>

      <div v-if="loading" class="loading">
        <div class="loader"></div>
        <p>加载中...</p>
      </div>

      <div v-else-if="error" class="error">
        <span class="error-icon">⚠️</span>
        <p>错误: {{ error }}</p>
      </div>

      <div v-else-if="adaptedData" class="content-area">
        <!-- 文档信息 -->
        <div class="document-info">
          <div class="info-item">
            <span class="info-label">文档名称:</span>
            <span class="info-value">{{ adaptedData.document_name }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">{{ viewMode === 'sectionHeaderOnly' ? '总标题数' : '总文本数' }}:</span>
            <span class="info-value">{{ adaptedData.total_items }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">总页数:</span>
            <span class="info-value">{{ totalPages }}</span>
          </div>
          <div class="info-item" v-if="currentPageInfo">
            <span class="info-label">页面尺寸:</span>
            <span class="info-value">{{ currentPageInfo.size.width.toFixed(1) }} × {{ currentPageInfo.size.height.toFixed(1) }}</span>
          </div>
        </div>

        <!-- 分页导航 -->
        <div class="pagination-bar">
          <button
            class="page-btn"
            :disabled="currentPage === 1"
            @click="goToPage(currentPage - 1)"
          >
            ← 上一页
          </button>

          <div class="page-numbers">
            <template v-for="(page, idx) in pageNumbers" :key="page">
              <span v-if="idx > 0 && page - pageNumbers[idx - 1] > 1" class="page-ellipsis">...</span>
              <button
                :class="['page-number', { active: page === currentPage }]"
                @click="goToPage(page)"
              >
                {{ page }}
              </button>
            </template>
          </div>

          <button
            class="page-btn"
            :disabled="currentPage === totalPages"
            @click="goToPage(currentPage + 1)"
          >
            下一页 →
          </button>
        </div>

        <!-- 当前页面内容 -->
        <div class="page-content">
          <div class="page-title">
            <h2>第 {{ currentPage }} 页</h2>
            <span class="header-count">{{ currentPageItems.length }} 个{{ showOnlySectionHeaders ? '标题' : '文本' }}</span>
          </div>

          <!-- 页面可视化容器 -->
          <div class="page-visualization">
            <!-- 页面画布包装器 -->
            <div class="page-canvas-wrapper">
              <!-- 页面画布 -->
              <div
                class="page-canvas"
                :style="{
                  width: currentPageInfo ? `${currentPageInfo.size.width * PDF_TO_SCREEN_SCALE}px` : `${595 * PDF_TO_SCREEN_SCALE}px`,
                  height: currentPageInfo ? `${currentPageInfo.size.height * PDF_TO_SCREEN_SCALE}px` : `${842 * PDF_TO_SCREEN_SCALE}px`
                }"
              >
              <!-- 渲染每个文本框 -->
              <div
                v-for="(item, idx) in currentPageItems"
                :key="idx"
                :class="[
                  'text-box',
                  { selected: selectedHeader === item },
                  { 'is-section-header': item.label === 'section_header' }
                ]"
                :style="getTextBoxStyle(item)"
                @click="selectHeader(item)"
                :title="`${item.label || ''} ${item.level ? 'Level ' + item.level : ''}`"
              >
                <div class="text-box-content">
                  {{ item.text }}
                </div>
              </div>
            </div>
            </div>
          </div>
        </div>

        <!-- 底部分页 -->
        <div class="pagination-bar bottom">
          <button
            class="page-btn"
            :disabled="currentPage === 1"
            @click="goToPage(currentPage - 1)"
          >
            ← 上一页
          </button>

          <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页</span>

          <button
            class="page-btn"
            :disabled="currentPage === totalPages"
            @click="goToPage(currentPage + 1)"
          >
            下一页 →
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.section-header-preview {
  min-height: 100vh;
  padding: 2rem;
  background: linear-gradient(to bottom, #f8f9fa 0%, #e9ecef 100%);
}

.page-container {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  text-align: center;
  margin-bottom: 2rem;
}

.page-header h1 {
  font-size: 2.5rem;
  color: #2c3e50;
  margin-bottom: 0.5rem;
  font-weight: 700;
}

.subtitle {
  color: #6c757d;
  font-size: 1.1rem;
  margin: 0;
}

/* 控制区域 */
.control-section {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}

/* 过滤按钮 */
.filter-btn {
  padding: 0.75rem 1.5rem;
  border: 2px solid #667eea;
  border-radius: 10px;
  background: white;
  color: #667eea;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.filter-btn:hover {
  background: #f8f9fa;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.filter-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: transparent;
}

/* 上传按钮 */
.upload-btn {
  padding: 0.75rem 1.5rem;
  border: 2px solid #28a745;
  border-radius: 10px;
  background: white;
  color: #28a745;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.upload-btn:hover {
  background: #28a745;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
}

/* Loading & Error */
.loading {
  text-align: center;
  padding: 4rem;
}

.loader {
  width: 50px;
  height: 50px;
  border: 5px solid #f3f3f3;
  border-top: 5px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem auto;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading p {
  color: #666;
  font-size: 1.1rem;
}

.error {
  background: white;
  border: 2px solid #e74c3c;
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
  max-width: 600px;
  margin: 2rem auto;
}

.error-icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 1rem;
}

.error p {
  color: #e74c3c;
  margin: 0;
  font-size: 1.1rem;
}

.content-area {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* 文档信息 */
.document-info {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  display: flex;
  gap: 2rem;
  flex-wrap: wrap;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.info-label {
  color: #6c757d;
  font-size: 0.9rem;
  font-weight: 500;
}

.info-value {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0.4rem 1rem;
  border-radius: 16px;
  font-size: 0.95rem;
  font-weight: 600;
}

/* 分页导航 */
.pagination-bar {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.pagination-bar.bottom {
  margin-top: 0;
}

.page-btn {
  padding: 0.75rem 1.5rem;
  border: 2px solid #667eea;
  border-radius: 10px;
  background: white;
  color: #667eea;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.page-btn:hover:not(:disabled) {
  background: #667eea;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  border-color: #dee2e6;
  color: #6c757d;
}

.page-numbers {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
}

.page-number {
  min-width: 40px;
  height: 40px;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  background: white;
  color: #495057;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.page-number:hover {
  border-color: #667eea;
  color: #667eea;
}

.page-number.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: transparent;
}

.page-ellipsis {
  color: #6c757d;
  padding: 0 0.5rem;
}

.page-info {
  color: #495057;
  font-size: 0.95rem;
  font-weight: 600;
}

/* 页面内容 */
.page-content {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.page-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #f0f0f0;
}

.page-title h2 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.8rem;
  font-weight: 700;
}

.header-count {
  background: #e7f3ff;
  color: #0066cc;
  padding: 0.5rem 1rem;
  border-radius: 16px;
  font-size: 0.9rem;
  font-weight: 600;
}

/* 页面可视化 */
.page-visualization {
  background: #f8f9fa;
  border-radius: 8px;
  overflow: auto;
  max-height: 1200px;
  padding: 2rem;
}

.page-canvas-wrapper {
  display: flex;
  justify-content: center;
  min-width: min-content;
}

.page-canvas {
  position: relative;
  background: white;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  border: 1px solid #dee2e6;
  /* 保持原始尺寸，不缩放 */
}

.text-box {
  position: absolute;
  cursor: pointer;
  transition: all 0.2s ease;
  overflow: hidden;
  display: flex;
  align-items: center;
  /* 调试用：显示 bbox 矩形边框 */
  border: 1px solid rgba(255, 0, 0, 0.5);
  background: rgba(255, 0, 0, 0.1);
}

.text-box:hover {
  background: rgba(102, 126, 234, 0.1);
  z-index: 10;
  outline: 2px solid rgba(102, 126, 234, 0.5);
}

.text-box.selected {
  background: rgba(255, 235, 59, 0.3);
  z-index: 20;
  outline: 2px solid #ffc107;
}

/* Section Header 字体为蓝色 */
.text-box.is-section-header .text-box-content {
  color: #2196f3;
  font-weight: 600;
}

.text-box-content {
  padding: 2px 4px;
  font-size: 12px;
  line-height: 1.4;
  color: #000000;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif;
  word-break: break-all;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100%;
}

/* Headers 列表 */
.headers-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.header-item {
  background: #f8f9fa;
  border: 2px solid #e9ecef;
  border-radius: 12px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.header-item:hover {
  background: white;
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
  transform: translateY(-2px);
}

.header-item.selected {
  background: #e7f3ff;
  border-color: #667eea;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
}

.header-main {
  margin-bottom: 1rem;
}

.header-title-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.level-badge {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0.3rem 0.8rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 700;
  flex-shrink: 0;
}

.label-badge {
  background: #fff3cd;
  color: #856404;
  padding: 0.3rem 0.8rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 700;
  flex-shrink: 0;
}

.header-text {
  color: #2c3e50;
  font-size: 1.1rem;
  font-weight: 600;
  line-height: 1.4;
  flex: 1;
}

.header-meta {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.ref-id {
  background: white;
  border: 1px solid #dee2e6;
  color: #6c757d;
  padding: 0.25rem 0.6rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-family: 'Courier New', monospace;
  font-weight: 600;
}

/* BBox 信息 */
.bbox-info {
  background: white;
  border-radius: 8px;
  padding: 1rem;
  border: 1px solid #dee2e6;
}

.bbox-label {
  color: #495057;
  font-size: 0.85rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
}

.bbox-details {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.bbox-item {
  background: #f8f9fa;
  color: #495057;
  padding: 0.4rem 0.8rem;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 500;
  font-family: 'Courier New', monospace;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .section-header-preview {
    padding: 1rem;
  }

  .page-header h1 {
    font-size: 1.8rem;
  }

  .document-info {
    flex-direction: column;
    gap: 1rem;
  }

  .pagination-bar {
    flex-direction: column;
  }

  .page-numbers {
    order: -1;
    width: 100%;
    justify-content: center;
  }

  .page-content {
    padding: 1.5rem;
  }

  .page-title {
    flex-direction: column;
    gap: 0.75rem;
    align-items: flex-start;
  }

  .page-title h2 {
    font-size: 1.5rem;
  }

  .header-item {
    padding: 1rem;
  }

  .bbox-details {
    gap: 0.5rem;
  }
}
</style>
