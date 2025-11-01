<template>
  <div class="library">
    <!-- 审查结果列表 -->
    <div class="result-summary-section">
      <div class="summary-header">审查结果列表</div>
      <div class="summary-stats-bar">
        <div class="stat-group">
          <span class="stat-label">审查总量</span>
          <span class="stat-number total">{{ dashboardData.totalCount }}</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-group">
          <span class="stat-label">未发现风险</span>
          <span class="stat-number safe">{{ dashboardData.noRiskCount }}</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-group">
          <span class="stat-label">发现风险</span>
          <span class="stat-number risk">{{ dashboardData.riskFoundCount }}</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-group">
          <span class="stat-label">处理中</span>
          <span class="stat-number pending">{{ dashboardData.pendingCount }}</span>
        </div>
      </div>
    </div>

    <!-- 筛选和操作区域 -->
    <div class="filter-section">
      <div class="filter-left">
        <a-space :size="12">
          <!-- 文件名搜索 -->
          <div class="search-input">
            <a-input
              v-model:value="searchForm.fileName"
              placeholder="输入名称或编号"
              allow-clear
              :maxLength="100"
              style="width: 200px;"
              @input="onFileNameInput"
            >
              <template #suffix>
                <SearchOutlined class="search-icon" />
              </template>
            </a-input>
          </div>
          <!-- 审查结果筛选 -->
          <a-select
            v-model:value="searchForm.reviewStatus"
            placeholder="审查结果"
            allow-clear
            style="width: 128px;"
            @change="onResultChange"
          >
            <a-select-option v-for="item in statusOptions" :key="item.value" :value="item.value">
              {{ item.label }}
            </a-select-option>
          </a-select>

          <!-- 日期范围选择 -->
          <a-range-picker
            v-model:value="dateRange"
            format="YYYY-MM-DD"
            :placeholder="['开始日期', '结束日期']"
            style="width: 360px;"
            @change="onDateRangeChange"
          />
          <!-- 重置按钮 -->
          <a-button class="reset-button" @click="resetFilters">
            <template #icon>
              <RotateCcw :size="16"/>
            </template> 
          </a-button>
        </a-space>
      </div>

      <div class="filter-right">
        <a-space :size="0">
          <!-- 批量操作 -->
          <div class="batch-operation" :class="{ 'has-selection': state.selectedRowKeys.length > 0 }">
            <div class="batch-info">
              <span class="batch-selected">已选择 {{ state.selectedRowKeys.length }} 项</span>
            </div>
            <a-button
              class="batch-delete-button"
              :disabled="state.selectedRowKeys.length === 0 || dialogOpen"
              type="primary"
              danger
              ghost
              @click="doBatchDelete($event)">
              批量删除
            </a-button>
          </div>

          <!-- 新建审查任务 -->
          <a-button type="primary" @click="router.push({ name: 'HomeIndex' })">
            <template #icon>
              <PlusOutlined />
            </template>
            新建审查
          </a-button>
        </a-space>
      </div>
    </div>

    <a-table
      :data-source="state.dataSource"
      :columns="columns"
      :pagination="pagination"
      :row-selection="rowSelection"
      :row-key="(record: any) => record.taskId"
      :loading="state.loading"
      class="basic-normal-table table "
      @change="onTableChange">
      <template #bodyCell="{ column, index, record, text }">
         <template v-if="column.dataIndex === 'projectInfo'">
            <div class="project-info"> 
              <template v-if="record.projectCode || record.projectName">
                <a-tooltip :title="record.projectName">  
                  <div class="project-title">{{ record.projectName }}</div>
                </a-tooltip>
                <div class="project-code">{{ record.projectCode }}</div>
              </template>
              <template v-else>-</template>
            </div>
          </template>
          <template v-if="column.dataIndex === 'fileName'">
            <a-tooltip :title="record.fileName">  
                {{ record.fileName }} 
            </a-tooltip>
          </template>
        <template v-if="column.dataIndex === 'reviewStatus'">
            <div class="flex items-center">
              <div class="percent-bar" v-if="record.reviewStatus === 1 || record.reviewStatus === 3" >
                <div class="progress-fill"><span class="percent" :style="{ width: `${record.reviewProgress || 0}%` }"></span></div>
                <span class="value">{{record.reviewStatus === 3 ?'解析中：' : '审查中：' }}{{ `${record.reviewProgress || 0}%` }}</span>
              </div>
              <div class="status-badge" v-else>
                <component
                  :is="getExamineResult(record).icon"
                  class="status-icon"
                  :style="{ color: getStatusColor(record) }"
                />
                <span class="status-text">{{ getExamineResult(record).text }}</span>
              </div>
            </div>
          </template>

        <template v-else-if="column.dataIndex === 'reviewResult'">
          <a-tag v-if="typeof text === 'number'" class="result-tag" :color="riskOptions[text].color">{{ riskOptions[text].label}}</a-tag>
          <span v-else>-</span>
        </template>

        <template v-else-if="column.dataIndex === 'handle'">
          <div class="btns">
            <!-- 查看按钮 -->
            <a-button
              v-if="record.reviewStatus === 2"
              type="text"
              @click="goResult(record)">
              <template #icon>
                <a-tooltip title="查看">
                  <FileSearch :size="16" />
                </a-tooltip>
              </template>
            </a-button>

            <!-- 导出报告按钮 -->
            <a-button
              v-if="record.reviewStatus === 2"
              type="text" 
              :loading="exportingIds.has(record.taskId)"
              @click="exportReport(record)">
              <template #icon>
                <a-tooltip title="导出报告">
                  <ArrowDownToLine :size="16" />
                </a-tooltip>
              </template>
            </a-button>

            <!-- 删除按钮 -->
            <a-button
              type="text"
              danger
              @click="doDel(record, $event)">
              <template #icon>
                <a-tooltip title="删除">
                  <Trash :size="16" />
                </a-tooltip>
              </template>
            </a-button>
          </div>
        </template>
      </template>
    </a-table>
  </div>
  <!-- 删除确认Popover -->
  <a-popover
    v-model:open="dialogOpen"
    :placement="batchDeleteMode ? 'bottom':'bottomLeft'"
    trigger="manual"
    :overlay-class-name="'base-delete-confirm-popover'"
  >
    <template #content>
      <div class="delete-confirm-content"> 
        <div class="main-box">
          <CircleAlert class="warning-icon" :size="16" color="var(--error-6)"/> 
          <div class="delete-message">
            <div v-if="batchDeleteMode">
              您确定要删除选中的 {{ state.selectedRowKeys.length }} 个文件吗？<br/>删除后需要重新上传。
            </div>
            <div v-else>
              您确定要删除此文件吗？删除后需要重新上传。
            </div>
          </div>
        </div>
        <div class="delete-dialog-footer">
          <a-button @click="dialogOpen = false" size="small">取消</a-button>
          <a-button type="primary" danger size="small" :loading="deletingLoading"  @click="doDialogOk">确认删除</a-button>
        </div>
      </div>
    </template>
    <!-- 空的触发元素，用于定位 -->
    <div ref="deletePopoverTrigger" style="position: absolute; visibility: hidden;"></div>
  </a-popover>
</template>

<script setup lang="ts">
import { ref, reactive, onUnmounted } from 'vue'
import { useDebounceFn } from '@vueuse/core'
import { SearchOutlined, PlusOutlined } from '@ant-design/icons-vue'
import { Trash, RotateCcw, FileSearch, ArrowDownToLine, CircleAlert } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import { apiTaskDelete, apiTaskList, taskDashboard } from '@/api/examine'
import { customDocumentBundleExport } from '@/api/download'
import { usePolling } from '@/hooks/use-polling'
import { message } from 'ant-design-vue'
import {
  riskOptions,
  getStatusStyle,
  getRiskStyle,
  statusOptions,
  TABLE_COLUMNS,
  DEFAULT_DASHBOARD_DATA,
  DEFAULT_FORM_DATA
} from '@/views/hooks/examine'
import { useTable } from '@/hooks/use-table'

const router = useRouter()



// 数据看板数据
const dashboardData = ref({ ...DEFAULT_DASHBOARD_DATA })

// 搜索表单数据
const searchForm = reactive({ ...DEFAULT_FORM_DATA })

// 日期范围选择
const dateRange = ref() 

// 使用 use-table 管理表格状态
const {
  state,
  pagination,
  rowSelection,
  getTableData,
  onSearch,
  onReset,
  onTableChange,
  refresh,
  clearSelection
} = useTable({
  // 初始查询参数
  params: searchForm,

  // API 函数
  getList: apiTaskList,

  // 自定义参数处理 - 处理日期范围和特殊状态逻辑
  getParams: (params) => {
    // 处理日期范围
    let startTime = ''
    let endTime = ''
    if (dateRange.value && dateRange.value.length === 2) {
      startTime = dateRange.value[0].format('YYYY-MM-DD')
      endTime = dateRange.value[1].format('YYYY-MM-DD')
    }

    // 处理特殊的审查状态逻辑
    const { reviewStatus, reviewResult, ...otherParams } = params
    const processedParams = {
      ...otherParams,
      reviewStatus: reviewStatus === 10 || reviewStatus === 11 ? undefined : reviewStatus,
      reviewResult,
      startTime,
      endTime
    }

    // 过滤空值
    return Object.fromEntries(
      Object.entries(processedParams).filter(([_, value]) => value !== '' && value != null)
    )
  },

  // 分页配置
  pagination: {
    pageSize: 10,
    showSizeChanger: true,
    showQuickJumper: true,
    pageSizeOptions: ['10', '20', '50', '100']
  },

  // 启用功能
  usePagination: true,
  useRowSelection: true,
  useSorter: false,

  // 数据字段映射
  dataFields: {
    list: 'dataList',
    total: 'total'
  }
})

// 表格列配置
const columns = TABLE_COLUMNS

// 审查结果获取
const getExamineResult = (item: any) => {
  return (item.reviewResult === 0 || item.reviewResult === 1)
    ? getRiskStyle(item.reviewResult)
    : getStatusStyle(item.reviewStatus)
}

// 获取状态颜色
const getStatusColor = (item: any) => {
  const result = getExamineResult(item)
  return (result as any).color || (result as any).style?.color || '#000'
}
// 跳转到审查结果页面
const goResult = (record: any) => {
  const { taskId } = record
  router.push({
    name: 'ComplianceReview',
    query: { taskId }
  })
}



// 审查报告导出
const exportingIds = ref(new Set<string>())
const exportReport = async (record: any) => {
  const { taskId } = record
  if (exportingIds.value.has(taskId)) return // 防止重复点击
  exportingIds.value.add(taskId) 
  const params = { taskId,fileTypes:['procurement_revised','risk_report'] }
  await customDocumentBundleExport(params) 
  exportingIds.value.delete(taskId) 
}

// 获取数据看板数据
const getDashboardData = async () => {
  let startTime = ''
  let endTime = ''
  if (dateRange.value && dateRange.value.length === 2) {
    startTime = dateRange.value[0].format('YYYY-MM-DD')
    endTime = dateRange.value[1].format('YYYY-MM-DD')
  }

  try {
    const { data, err } = await taskDashboard({ startTime, endTime })
    if (err) return

    dashboardData.value = {
      totalCount: data.totalCount || 0,
      riskFoundCount: data.riskFoundCount || 0,
      noRiskCount: data.noRiskCount || 0,
      pendingCount: data.pendingCount || 0,
      errorCount: data.errorCount || 0
    }
  } catch (error) {
    console.error('获取仪表板数据失败:', error)
  }
}
// ==================== 轮询 ==================== 
const { start, stop, restart } = usePolling(
  async () => {
    if (dialogOpen.value || state.loading || deletingLoading.value || exportingIds.value.size > 0) {
      console.log('删除确认弹窗显示中或者其他请求进行中，跳过轮询')
      return null
    }
    const res = await getTableData() 
    return res
  },
  {
    interval: 45*1000,
    requestTimeout: 10000, // 10秒超时
    skipOnPending: true, // 跳过进行中的请求
    maxConcurrent: 1, // 最大并发数
    onSuccess:async (data) => {
      console.log('轮询成功:', data)  
    },
    onError: (error, count) => {
      console.error(`轮询失败 (${count}次):`, error)
    }
  }
) 
// ==================== 筛选处理方法 ====================

// 搜索处理
const handleSearch = () => {
  Object.assign(state.params, searchForm)
  getDashboardData() // 同时更新看板数据
  onSearch()
}

// 防抖查询函数
const debouncedSearch = useDebounceFn(() => {
  handleSearch()
}, 500)

// 文件名输入处理
const onFileNameInput = () => {
  debouncedSearch()
}

// 结果变化处理
const onResultChange = (val: number) => {
  searchForm.reviewResult = undefined
  if (val === 10) searchForm.reviewResult = 0
  else if (val === 11) searchForm.reviewResult = 1
  handleSearch()
}

// 日期范围变化处理
const onDateRangeChange = () => {
  debouncedSearch()
}

// 重置筛选条件
const resetFilters = () => {
  Object.assign(searchForm, DEFAULT_FORM_DATA)
  dateRange.value = undefined
  onReset()
  getDashboardData() // 重置时也更新看板数据
  getTableData()
}


// ==================== 删除相关方法 ====================
// 删除相关
const record2Delete = ref<any>(null)
const batchDeleteMode = ref(false)
const deletePopoverTrigger = ref<HTMLElement>()
const dialogOpen = ref(false)

// 单个删除 
const doDel = (record: any, event?: Event) => {
  // 定位Popover到触发按钮的位置
  if (event && deletePopoverTrigger.value) {
    const target = event.currentTarget as HTMLElement
    const rect = target.getBoundingClientRect()
    // 计算按钮中心位置
    const centerX = rect.left + rect.width / 2
    const centerY = rect.top + rect.height / 2
    deletePopoverTrigger.value.style.position = 'fixed'
    deletePopoverTrigger.value.style.left = `${centerX + 20}px`
    deletePopoverTrigger.value.style.top = `${centerY}px`
    deletePopoverTrigger.value.style.visibility = 'visible'
  }

  dialogOpen.value = true
  batchDeleteMode.value = false
  record2Delete.value = record
}

// 批量删除
const doBatchDelete = (event?: Event) => {
  if (state.selectedRowKeys.length === 0) {
    message.info('请先选择要删除的项目')
    return
  }

  // 定位Popover到批量删除按钮的位置
  if (event && deletePopoverTrigger.value) {
    const target = event.currentTarget as HTMLElement
    const rect = target.getBoundingClientRect()
    // 计算按钮中心位置
    const centerX = rect.left + rect.width / 2
    const centerY = rect.top + rect.height / 2
    deletePopoverTrigger.value.style.position = 'fixed'
    deletePopoverTrigger.value.style.left = `${centerX}px`
    deletePopoverTrigger.value.style.top = `${centerY + 20}px`
    deletePopoverTrigger.value.style.visibility = 'visible'
  }

  batchDeleteMode.value = true
  dialogOpen.value = true
}

// 确认删除
const deletingLoading = ref(false)
const doDialogOk = async () => {
  dialogOpen.value = false 
  deletingLoading.value = true
  if (batchDeleteMode.value) {
    // 批量删除模式
    const taskIds = state.selectedRowKeys.join(',')
    const params = { taskId: taskIds } 
    const { err } = await apiTaskDelete(params)
    deletingLoading.value = false
    if (err) return 
    message.success(`成功删除 ${state.selectedRowKeys.length} 个任务`)
    clearSelection()
    batchDeleteMode.value = false
  } else {
    // 单个删除模式
    const { taskId } = record2Delete.value
    const params = { taskId }
    const { err } = await apiTaskDelete(params)
    deletingLoading.value = false
    if (err) return 
    message.success('成功删除')
  }

  await refresh() // 使用 use-table 的 refresh 方法
}

// ==================== 生命周期 ====================
// 初始化数据
const initData = async () => {
  await getDashboardData()
  start()
}

initData() 
</script>

<style lang="scss" scoped>
.library {
  height: calc(100vh - 48px);
  display: flex;
  flex-direction: column;
  padding:24px;

  // 审查结果列表样式
  .result-summary-section {
    display: flex;
    align-items: center;
    margin-bottom: 16px;
    .summary-header {
      font-size: 24px;
      margin-right: 30px;
    }

    .summary-stats-bar {
      display: flex;
      align-items: center;
      background: #F9FAFB;
      border: 1px solid #E5E7EB;
      box-sizing: border-box;
      border-radius: 8px;
      padding: 0 21px;
      height: 46px;

      .stat-group {
        display: flex;
        align-items: center;
        gap: 8px;  
        .stat-label {  
          color: #4B5563; 
        }

        .stat-number { 
          font-size: 18px; 

          &.total {
            color: var(--main-6);
          }

          &.safe {
            color: #52C41A;
          }

          &.risk {
            color: #F5222D;
          }

          &.pending {
            color: #FA8C16;
          }
        }
      }

      .stat-divider {
        width: 1px;
        height: 16px;
        background: #D1D5DB;
        margin: 0 24px;
      }
    }
  }
  // 筛选区域样式
  .filter-section {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;

    .filter-left {
      flex: 1;
    }

    .filter-right {
      flex-shrink: 0;
    }

    .batch-operation {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 8px 12px;
      border-radius: 8px; 

      .batch-info {
        display: flex;
        align-items: center;
        gap: 8px;

        .batch-selected {
          font-size: 14px;
          color: #6B7280;
          white-space: nowrap;
          min-width: 80px;
          font-weight: 500;
        }

        .batch-hint {
          display: flex;
          align-items: center;

          .batch-icon {
            width: 16px;
            height: 16px;
            animation: fadeIn 0.3s ease;
          }
        }
      }
    }
    .search-input {
      .search-icon {
        color: #9CA3AF;
      }
    }
  } 
  .percent-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      width: 100%;
     .progress-fill {
        flex: 1;
        min-width: 0; 
        background-color: #E5E7EB;
        height: 8px;
        display: flex;
        border-radius: 8px;
        .percent {
          border-radius: 8px;
          background-color: var(--main-6);
          &.done {
            width: 100%;
            background-color:var(--success-6);
          }

          &.uploading {
             background-color: var(--main-6); 
          }

          &.error {
             background-color: var(--error-6); 
          }
        }
     }
      .value {
        width: 100px;
        flex-shrink: 0;
        margin-left: 8px;
        color: #000000E0;
      }
    }
    .percent-bar {
      max-width: 260px;
    }
  :deep(.ant-btn-dangerous.batch-delete-button){
    border-color:#D9D9D9 ;
  }
  :deep(.ant-btn) {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  :deep(.ant-modal-body) {
    max-height: 75vh;
    margin-top: 32px;
  }
  :deep(.ant-pagination) {
    position: relative;
    .ant-pagination-total-text {
      position: absolute;
      z-index: 1;
      left: 0;
    }
    .ant-pagination-item-active {
      background-color: var(--main-6);
      color: var(--text-0);
      a {
        color: var(--text-0);
      }
    }
  }
  :deep(.ant-table) {
    flex: 1; 

    // 项目信息样式
    .project-info {
      .project-title { 
        font-size: 14px;
        color: #000; 
        white-space: nowrap;
        text-overflow: ellipsis;
        overflow: hidden;
      }
      .project-code { 
        color: #6B7280;
      }
    }

    // 状态Badge样式
    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      width: fit-content;

      .status-icon {
        width: 16px;
        height: 16px;
      }
    }
  }
} 

</style>
