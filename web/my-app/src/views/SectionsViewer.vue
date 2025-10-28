<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'

const sections = ref([])
const loading = ref(true)
const error = ref(null)
const currentStep = ref(2)
const availableSteps = ref([])
const fileInfo = ref(null)
const showSidebar = ref(true)
const activeSectionId = ref(null)

// 获取可用的 step 列表
const fetchFilesInfo = async () => {
  try {
    const response = await fetch('/api/files-info')
    if (!response.ok) {
      throw new Error('Failed to load files info')
    }
    const data = await response.json()
    availableSteps.value = data.files.map(f => f.step)
    fileInfo.value = data
  } catch (e) {
    console.error('Error loading files info:', e)
  }
}

// 加载指定 step 的数据
const loadStepData = async (step) => {
  loading.value = true
  error.value = null
  try {
    const response = await fetch(`/api/step-data/${step}`)
    if (!response.ok) {
      throw new Error(`Failed to load step ${step} data`)
    }
    const data = await response.json()
    sections.value = data.sections || []
    currentStep.value = step
    // 重置选中的 section
    activeSectionId.value = null
  } catch (e) {
    error.value = e.message
    console.error('Error loading sections:', e)
  } finally {
    loading.value = false
  }
}

// 切换 step
const switchStep = (step) => {
  if (step !== currentStep.value) {
    loadStepData(step)
  }
}

// 跳转到指定 section
const scrollToSection = (sectionId) => {
  activeSectionId.value = sectionId
  nextTick(() => {
    const element = document.getElementById(sectionId)
    if (element) {
      const offset = 100 // 考虑固定头部的高度
      const elementPosition = element.getBoundingClientRect().top
      const offsetPosition = elementPosition + window.pageYOffset - offset

      window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth'
      })
    }
  })
}

// 切换侧边栏显示
const toggleSidebar = () => {
  showSidebar.value = !showSidebar.value
}

// 计算统计信息
const totalBlocks = computed(() => {
  return sections.value.reduce((sum, section) => {
    return sum + (section.blocks?.length || 0)
  }, 0)
})

const totalTables = computed(() => {
  return sections.value.reduce((sum, section) => {
    const tables = section.blocks?.filter(b => b.type === 'table').length || 0
    return sum + tables
  }, 0)
})

onMounted(async () => {
  await fetchFilesInfo()
  await loadStepData(currentStep.value)
})
</script>

<template>
  <div class="sections-viewer">
    <!-- 侧边栏切换按钮 -->
    <button class="sidebar-toggle" @click="toggleSidebar" :class="{ active: showSidebar }">
      <span v-if="showSidebar">✕</span>
      <span v-else>☰</span>
    </button>

    <!-- 侧边栏导航 -->
    <aside class="sidebar" :class="{ show: showSidebar }">
      <div class="sidebar-header">
        <h3>📑 快速导航</h3>
        <span class="section-count">{{ sections.length }} 个章节</span>
      </div>
      <div class="sidebar-content">
        <div
          v-for="section in sections"
          :key="section.id"
          :class="['sidebar-item', `level-${section.level}`, { active: activeSectionId === section.id }]"
          @click="scrollToSection(section.id)"
        >
          <span class="sidebar-item-id">{{ section.id }}</span>
          <span class="sidebar-item-text">{{ section.text }}</span>
        </div>
      </div>
    </aside>

    <!-- 主内容区域 -->
    <div class="main-content" :class="{ 'sidebar-open': showSidebar }">
      <div class="page-header">
        <h1>📄 文档结构分析 - Step {{ currentStep }}</h1>
        <p class="subtitle">Sections 可视化展示</p>
      </div>

      <!-- Step 切换按钮 -->
    <div class="step-selector">
      <div class="step-buttons">
        <button
          v-for="step in availableSteps"
          :key="step"
          :class="['step-btn', { active: step === currentStep }]"
          @click="switchStep(step)"
        >
          Step {{ step }}
        </button>
      </div>
      <div v-if="fileInfo" class="file-info">
        <span class="info-text">文件ID: {{ fileInfo.fileId }}</span>
        <span class="info-text">共 {{ fileInfo.totalSteps }} 个步骤</span>
      </div>
    </div>

    <div v-if="loading" class="loading">
      <div class="loader"></div>
      <p>加载中...</p>
    </div>
    <div v-else-if="error" class="error">
      <span class="error-icon">⚠️</span>
      <p>错误: {{ error }}</p>
    </div>
    <div v-else>
      <!-- 统计信息 -->
      <div class="stats-bar">
        <div class="stat-item">
          <span class="stat-label">总计 Sections</span>
          <span class="stat-value">{{ sections.length }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">总计 Blocks</span>
          <span class="stat-value">{{ totalBlocks }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">总计 Tables</span>
          <span class="stat-value">{{ totalTables }}</span>
        </div>
      </div>

      <!-- Sections 列表 -->
      <div class="sections-container">
        <div v-for="section in sections" :key="section.id" :id="section.id" class="section">
          <!-- Section Header -->
          <div class="section-header" :class="`level-${section.level}`">
            <div class="header-title">
              <span class="section-id">{{ section.id }}</span>
              <h2 :class="`heading-level-${section.level}`">{{ section.text }}</h2>
            </div>
            <div class="section-meta">
              <span class="badge badge-level">L{{ section.level }}</span>
              <span class="badge badge-score">{{ (section.score * 100).toFixed(0) }}%</span>
              <span v-if="section.style" class="badge badge-style">{{ section.style }}</span>
            </div>
          </div>

          <!-- Section Blocks -->
          <div v-if="section.blocks && section.blocks.length > 0" class="section-blocks">
            <div v-for="(block, blockIdx) in section.blocks" :key="blockIdx" class="block">
              <!-- 表格类型 -->
              <div v-if="block.type === 'table'" class="table-block">
                <div class="block-header">
                  <div class="header-left">
                    <span class="block-id">{{ block.id }}</span>
                    <span class="block-type-badge table-badge">📊 Table</span>
                  </div>
                  <span class="block-info">{{ block.rows?.length || 0 }} 行</span>
                </div>
                <div class="table-wrapper">
                  <table class="data-table">
                    <thead>
                      <tr>
                        <th v-for="col in block.columns" :key="col.id">{{ col.label }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="row in block.rows" :key="row.id">
                        <td v-for="cell in row.cells" :key="cell.id" :title="cell.id">
                          {{ cell.text }}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <!-- 段落类型 -->
              <div v-else-if="block.type === 'paragraph'" class="paragraph-block">
                <div class="block-header">
                  <span class="block-id">{{ block.id }}</span>
                  <span class="block-type-badge paragraph-badge">📝 Paragraph</span>
                </div>
                <p class="paragraph-text">{{ block.text }}</p>
              </div>

              <!-- 其他类型 -->
              <div v-else class="other-block">
                <div class="block-header">
                  <span class="block-id">{{ block.id }}</span>
                  <span class="block-type-badge">{{ block.type }}</span>
                </div>
                <pre class="code-block">{{ JSON.stringify(block, null, 2) }}</pre>
              </div>
            </div>
          </div>

          <!-- Children Sections (递归) -->
          <div v-if="section.children && section.children.length > 0" class="children-sections">
            <div class="children-header">
              <span class="children-icon">↳</span>
              <span class="children-label">子章节 ({{ section.children.length }})</span>
            </div>
            <div v-for="child in section.children" :key="child.id" class="child-section">
              <div class="section-header" :class="`level-${child.level}`">
                <span class="section-id">{{ child.id }}</span>
                <h3 :class="`heading-level-${child.level}`">{{ child.text }}</h3>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    </div>
  </div>
</template>

<style scoped>
.sections-viewer {
  position: relative;
  display: flex;
  min-height: 100vh;
}

/* 侧边栏切换按钮 */
.sidebar-toggle {
  position: fixed;
  top: 100px;
  right: 20px;
  z-index: 999;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  border: none;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 1.5rem;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sidebar-toggle:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.6);
}

.sidebar-toggle.active {
  right: 320px;
}

/* 侧边栏 */
.sidebar {
  position: fixed;
  top: 70px;
  right: -320px;
  width: 300px;
  height: calc(100vh - 70px);
  background: white;
  box-shadow: -2px 0 12px rgba(0, 0, 0, 0.1);
  transition: right 0.3s ease;
  z-index: 998;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar.show {
  right: 0;
}

.sidebar-header {
  padding: 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-header h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.2rem;
  font-weight: 700;
}

.section-count {
  font-size: 0.85rem;
  opacity: 0.9;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem 0;
}

.sidebar-item {
  padding: 0.75rem 1.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
  border-left: 3px solid transparent;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.sidebar-item:hover {
  background: #f8f9fa;
  border-left-color: #667eea;
}

.sidebar-item.active {
  background: #e7f3ff;
  border-left-color: #667eea;
}

.sidebar-item.level-2 {
  padding-left: 2rem;
}

.sidebar-item.level-3 {
  padding-left: 3rem;
}

.sidebar-item-id {
  font-family: 'Courier New', monospace;
  font-size: 0.75rem;
  color: #6c757d;
  background: #f0f0f0;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  flex-shrink: 0;
}

.sidebar-item-text {
  font-size: 0.9rem;
  color: #2c3e50;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar-item.active .sidebar-item-text {
  color: #667eea;
  font-weight: 600;
}

/* 主内容区域 */
.main-content {
  flex: 1;
  width: 100%;
  padding: 2rem;
  transition: margin-right 0.3s ease;
}

.main-content.sidebar-open {
  margin-right: 300px;
}

.page-header {
  text-align: center;
  margin-bottom: 2rem;
}

.page-header h1 {
  font-size: 2rem;
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #6c757d;
  font-size: 1rem;
}

/* Step 切换器 */
.step-selector {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.step-buttons {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}

.step-btn {
  padding: 0.75rem 1.5rem;
  border: 2px solid #e9ecef;
  border-radius: 10px;
  background: white;
  color: #495057;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  outline: none;
}

.step-btn:hover {
  border-color: #667eea;
  color: #667eea;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

.step-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: transparent;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.step-btn:active {
  transform: translateY(0);
}

.file-info {
  display: flex;
  gap: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid #e9ecef;
  flex-wrap: wrap;
}

.info-text {
  color: #6c757d;
  font-size: 0.9rem;
  font-weight: 500;
}

/* Loading 状态 */
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

/* Error 状态 */
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

/* 统计栏 */
.stats-bar {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  display: flex;
  gap: 2rem;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.stat-label {
  color: #666;
  font-size: 0.9rem;
  font-weight: 500;
}

.stat-value {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0.5rem 1.2rem;
  border-radius: 20px;
  font-size: 1.2rem;
  font-weight: 700;
}

/* Sections 容器 */
.sections-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.section {
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  padding: 2rem;
  transition: all 0.3s ease;
  border: 1px solid transparent;
}

.section:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
  border-color: #e0e0e0;
}

/* Section Header */
.section-header {
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #f0f0f0;
}

.section-header.level-1 {
  border-left: 5px solid #667eea;
  padding-left: 1.2rem;
}

.section-header.level-2 {
  border-left: 5px solid #764ba2;
  padding-left: 1.2rem;
}

.section-header.level-3 {
  border-left: 5px solid #f093fb;
  padding-left: 1.2rem;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
  flex-wrap: wrap;
}

.section-id {
  display: inline-flex;
  align-items: center;
  background: linear-gradient(135deg, #f5f7fa 0%, #e9ecef 100%);
  color: #495057;
  padding: 0.4rem 0.8rem;
  border-radius: 8px;
  font-size: 0.8rem;
  font-family: 'Courier New', monospace;
  font-weight: 600;
  border: 1px solid #dee2e6;
}

.section-header h2,
.section-header h3 {
  margin: 0;
  color: #2c3e50;
  line-height: 1.3;
}

.heading-level-1 {
  font-size: 1.8rem;
  font-weight: 700;
}

.heading-level-2 {
  font-size: 1.5rem;
  font-weight: 600;
}

.heading-level-3 {
  font-size: 1.3rem;
  font-weight: 600;
}

.section-meta {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: 0.35rem 0.9rem;
  border-radius: 16px;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.3px;
}

.badge-level {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.badge-score {
  background: #d4edda;
  color: #155724;
}

.badge-style {
  background: #fff3cd;
  color: #856404;
}

/* Blocks 容器 */
.section-blocks {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}

.block {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 1.5rem;
  border: 1px solid #e9ecef;
  transition: all 0.2s ease;
}

.block:hover {
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.block-header {
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.block-id {
  background: white;
  border: 1px solid #dee2e6;
  color: #6c757d;
  padding: 0.3rem 0.6rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-family: 'Courier New', monospace;
  font-weight: 600;
}

.block-type-badge {
  padding: 0.3rem 0.8rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
}

.table-badge {
  background: #e7f3ff;
  color: #0066cc;
}

.paragraph-badge {
  background: #fff4e6;
  color: #cc6600;
}

.block-info {
  color: #6c757d;
  font-size: 0.85rem;
  font-weight: 500;
}

/* 表格样式 */
.table-wrapper {
  overflow-x: auto;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  font-size: 0.9rem;
}

.data-table th,
.data-table td {
  padding: 0.9rem 1rem;
  text-align: left;
  border-bottom: 1px solid #e9ecef;
}

.data-table th {
  background: linear-gradient(to bottom, #f8f9fa 0%, #f1f3f5 100%);
  font-weight: 700;
  color: #343a40;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  border-bottom: 2px solid #dee2e6;
}

.data-table tbody tr {
  transition: background 0.2s ease;
}

.data-table tbody tr:hover {
  background: #f8f9fa;
}

.data-table tbody tr:last-child td {
  border-bottom: none;
}

.data-table td {
  color: #495057;
  line-height: 1.5;
}

/* 段落样式 */
.paragraph-text {
  margin: 0;
  padding: 0.75rem 0;
  line-height: 1.8;
  color: #495057;
  font-size: 0.95rem;
}

/* 其他类型块 */
.code-block {
  background: #2d3748;
  color: #e2e8f0;
  padding: 1.2rem;
  border-radius: 8px;
  overflow-x: auto;
  font-size: 0.85rem;
  line-height: 1.6;
  font-family: 'Courier New', monospace;
  margin: 0;
}

/* Children Sections */
.children-sections {
  margin-top: 1.5rem;
  padding: 1.5rem;
  background: #f8f9fa;
  border-radius: 12px;
  border-left: 4px solid #adb5bd;
}

.children-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #dee2e6;
}

.children-icon {
  font-size: 1.2rem;
  color: #6c757d;
}

.children-label {
  font-weight: 600;
  color: #495057;
  font-size: 0.9rem;
}

.child-section {
  margin-top: 0.75rem;
  padding: 1.2rem;
  background: white;
  border-radius: 8px;
  border: 1px solid #e9ecef;
  transition: all 0.2s ease;
}

.child-section:hover {
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  transform: translateX(4px);
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .main-content {
    padding: 1.5rem 1rem;
  }

  .main-content.sidebar-open {
    margin-right: 280px;
  }

  .sidebar {
    width: 280px;
  }

  .sidebar-toggle.active {
    right: 300px;
  }

  .section {
    padding: 1.5rem;
  }
}

@media (max-width: 768px) {
  .sidebar {
    width: 100%;
    right: -100%;
  }

  .sidebar.show {
    right: 0;
  }

  .sidebar-toggle {
    top: 80px;
    right: 10px;
  }

  .sidebar-toggle.active {
    right: calc(100% - 60px);
  }

  .main-content {
    padding: 1rem 0.75rem;
  }

  .main-content.sidebar-open {
    margin-right: 0;
  }

  .page-header h1 {
    font-size: 1.6rem;
  }

  .section {
    padding: 1.25rem;
  }

  .section-header.level-1,
  .section-header.level-2,
  .section-header.level-3 {
    padding-left: 0.75rem;
    border-left-width: 3px;
  }

  .heading-level-1 {
    font-size: 1.4rem;
  }

  .heading-level-2 {
    font-size: 1.2rem;
  }

  .heading-level-3 {
    font-size: 1.1rem;
  }

  .stats-bar {
    padding: 1rem;
  }

  .stat-value {
    font-size: 1rem;
    padding: 0.4rem 1rem;
  }

  .block {
    padding: 1rem;
  }

  .data-table {
    font-size: 0.85rem;
  }

  .data-table th,
  .data-table td {
    padding: 0.6rem 0.8rem;
  }

  .data-table th {
    font-size: 0.75rem;
  }

  .children-sections {
    padding: 1rem;
  }
}

@media (max-width: 480px) {
  .page-header h1 {
    font-size: 1.3rem;
  }

  .section-id,
  .block-id {
    font-size: 0.7rem;
    padding: 0.25rem 0.5rem;
  }

  .badge {
    font-size: 0.7rem;
    padding: 0.25rem 0.7rem;
  }

  .data-table th,
  .data-table td {
    padding: 0.5rem 0.6rem;
    font-size: 0.8rem;
  }
}
</style>
