<template>
  <div class="rule-manager">
    <!-- 规则库概览 -->
    <div class="result-summary-section">
      <div class="summary-header">规则管理</div>
      <div class="summary-stats-bar">
        <div class="stat-group">
          <span class="stat-label">总规则数</span>
          <span class="stat-number total">{{ dashboardData.totalRules || 0}}</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-group">
          <span class="stat-label">已启用</span>
          <span class="stat-number safe">{{ dashboardData.activeRules  || 0}}</span>
        </div>
        <div class="stat-divider"></div>
        <!-- <div class="stat-group">
          <span class="stat-label">草稿</span>
          <span class="stat-number pending">{{ dashboardData.draftRules  || 0}}</span>
        </div>
        <div class="stat-divider"></div> -->
        <div class="stat-group">
          <span class="stat-label">已禁用</span>
          <span class="stat-number risk">{{ dashboardData.inactiveRules  || 0}}</span>
        </div>
      </div>
    </div>

    <!-- 筛选和操作区域 -->
    <div class="filter-section">
      <div class="filter-left">
        <a-space :size="12">
          <!-- 规则名称搜索 -->
          <div class="search-input">
            <a-input
              v-model:value="searchForm.keyword"
              placeholder="搜索规则名称"
              allow-clear
              :maxLength="100"
              style="width: 200px;"
              @input="onRuleNameInput"
            >
              <template #suffix>
                <SearchOutlined class="search-icon" />
              </template>
            </a-input>
          </div>

          <!-- 风险级别筛选 -->
          <a-select
            v-model:value="searchForm.violationLevel"
            placeholder="风险级别"
            allow-clear
            style="width: 128px;"
            @change="onRiskLevelChange"
          > 
            <a-select-option v-for="item in dictMap.violationLevel" :key="item.code" :value="item.code">
              {{ item.name }}
            </a-select-option>
          </a-select>

          <!-- 启用状态筛选 -->
          <a-select
            v-model:value="searchForm.status"
            placeholder="启用状态"
            allow-clear
            style="width: 120px;"
            @change="onEnabledChange"
          >
            <a-select-option v-for="item in RULE_STATUS_OPTIONS" :key="item.value" :value="item.value">
                {{ item.label }}
              </a-select-option>
          </a-select>

          <!-- 标签筛选 -->
          <a-select
            v-model:value="searchForm.category"
            placeholder="全部标签"
            allow-clear
            style="width: 200px;"
            @change="onTagsChange"
          > 
            <a-select-option v-for="item in dictMap.label" :key="item.code" :value="item.code">
              {{ item.name }}
            </a-select-option>
          </a-select> 
          <!-- 重置按钮 -->
          <a-button class="reset-button" @click="resetFilters">
            <template #icon>
              <RotateCcw :size="16"/>
            </template>
          </a-button>
        </a-space>
      </div>

      <div class="filter-right">
        <a-space :size="12">
          <!-- 新建规则 -->
          <a-button type="primary" @click="editRule({})">
            <template #icon>
              <PlusOutlined />
            </template>
            新建规则
          </a-button>
        </a-space>
      </div>
    </div>

    <!-- 规则列表表格 -->
    <a-table
      :data-source="state.dataSource"
      :columns="columns"
      :pagination="pagination"
      :row-key="(record: any) => record.id"
      :loading="loading"
      @change="onTableChange"
      class="basic-normal-table table" >
      <template #bodyCell="{ column, record, text }">

        <!-- 标签列 -->
        <template v-if="column.dataIndex === 'lableList'">
          <div class="tags-container">
            <a-tag
              v-for="(tag,index) in record?.lableList"
              :key="tag"
              :color="['processing','success','error','warning','default','lime'][index]"
              size="small"
            > 
              {{ getOptionsMap(dictMap.label, tag).name }}
            </a-tag>
          </div>
        </template> 

        <!-- 启用状态列 -->
        <template v-else-if="column.dataIndex === 'status'">
          <a-switch
            :checked="record.status === 1 ? true : false"
            @change="enabledStatus(record)"
          />
        </template>

        <!-- 操作列 -->
        <template v-else-if="column.dataIndex === 'actions'">
          <div class="btns"> 
            <!-- 编辑按钮 -->
            <a-button type="text" @click="editRule(record)">
              <template #icon>
                <a-tooltip title="编辑">
                  <Edit :size="16" />
                </a-tooltip>
              </template>
            </a-button>

            <!-- 测试按钮 -->
            <a-button type="text" @click="testRule(record)" v-if="record.status === 1">
              <template #icon>
                <a-tooltip title="测试">
                  <BugPlay  :size="16" />
                </a-tooltip>
              </template>
            </a-button>
          </div>
        </template>
      </template>
    </a-table>
  </div>

  <!-- 规则编辑器 -->
  <RuleEditor
    v-model="ruleEditorVisible"
    :riskOptions="dictMap.violationLevel"
    :category="dictMap.label"
    :rule-data="currentRuleData"
    @save="getTableData()"
    @cancel="handleRuleCancel"
  />

  <!-- 规则测试弹框 -->
  <RuleTest
    :ruleId="currentRuleData.id"
    v-model="testDialogVisible" 
    @cancel="handleRuleCancel"
  />
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useDebounceFn } from '@vueuse/core'
import { SearchOutlined, PlusOutlined, PauseCircleOutlined, PlayCircleOutlined } from '@ant-design/icons-vue'
import { RotateCcw, Edit, BugPlay } from 'lucide-vue-next' 
import { RULE_STATUS_OPTIONS,  RULE_TABLE_COLUMNS , getOptionsMap } from '@/views/hooks/examine'
import RuleEditor from './components/RuleEditor.vue'
import RuleTest from './components/RuleTest.vue'
import { useTable } from '@/hooks/use-table'
import { apiRuleList, apiRulesDict, ruleStatistics, updateStatus } from '@/api/examine'
// ==================== 响应式数据 ====================
// 数据看板数据
const dashboardData = ref<any>({ })

// 搜索表单数据
const searchForm = reactive({
  keyword: '',
  category: undefined,
  violationLevel: undefined,
  status: undefined
})
const dictMap = ref<Record<string, any>>({
  label: [], 
  violationLevel: []
})
// 表格数据
const loading = ref(false)

// 规则编辑器相关
const ruleEditorVisible = ref(false)
const currentRuleData = ref<any>({})

// 规则测试相关
const testDialogVisible = ref(false) 

// 表格列配置
const columns = RULE_TABLE_COLUMNS 
const { state,  getTableData ,pagination,onTableChange, onSearch, onReset} = useTable({
  params: searchForm,
  getList: apiRuleList 
})
// ==================== 筛选处理方法 ====================
// 搜索处理
const handleSearch = () => {
  Object.assign(state.params, searchForm) 
  onSearch()
}
// 重置筛选条件
const resetFilters = () => {
  Object.assign(searchForm, {
    keyword: '',
    category: undefined,
    violationLevel: undefined,
    status: undefined
  }) 
  onReset() 
  getTableData()
}
// 防抖查询函数
const debouncedSearch = useDebounceFn(() => {
  handleSearch()
}, 500)

// 规则名称输入处理
const onRuleNameInput = () => {
  debouncedSearch()
}

// 风险级别变化处理
const onRiskLevelChange = () => {
  handleSearch()
}

// 启用状态变化处理
const onEnabledChange = () => {
  handleSearch()
}

// 标签变化处理
const onTagsChange = () => {
  handleSearch()
} 

// ==================== 规则操作方法 ==================== 

// 编辑规则
const editRule = (record: any) => {
  currentRuleData.value = { ...record }
  ruleEditorVisible.value = true
}

// 测试规则
const testRule = (record: any) => { 
  currentRuleData.value = { ...record }
  testDialogVisible.value = true
} 
// 处理规则取消
const handleRuleCancel = () => {
  currentRuleData.value = {}
}

// 更新仪表板数据
const updateDashboardData = async() => {
  const {data,err} = await ruleStatistics()
  if(err) return
  dashboardData.value =  data ?? {}
}
// 字典
const getDict = async ()=> {
  const defaultDict = { label:[], violationLevel:[] }
  dictMap.value = defaultDict
  const {data,err} = await apiRulesDict()
  if(err) return
  dictMap.value = data ?? defaultDict
}
// 启动、禁用
const enableLoading = ref(false)
const enabledStatus = async (record: Record<string,any>)=> {
  const { id,status }  = record
  if(enableLoading.value) return
  enableLoading.value = true 
  const {data,err} = await updateStatus({
    ruleId: id,
    status: status === 1 ? 0 : 1
  })
  enableLoading.value = false
  if(err) return 
  getTableData()
}
const init = async ()=> {
  Promise.all([getDict(),updateDashboardData()]) 
  await getTableData()
}
init()
</script>

<style lang="scss" scoped>
.rule-manager { 
  padding:24px;

  // 规则库概览样式
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

    // 规则信息样式
    .rule-info {
      .rule-title {
        font-size: 14px;
        color: #000;
        font-weight: 500;
        white-space: nowrap;
        text-overflow: ellipsis;
        overflow: hidden;
        margin-bottom: 4px;
      }
      .rule-description {
        font-size: 12px;
        color: rgba(0, 0, 0, 0.45);
        white-space: nowrap;
        text-overflow: ellipsis;
        overflow: hidden;
      }
    }

    // 标签容器样式
    .tags-container {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;

      .ant-tag {
        margin: 0;
        font-size: 12px;
        line-height: 18px;
        padding: 0 6px;
        border-radius: 3px;
      }
    }

    // 操作按钮样式
    .btns {
      display: flex;
      gap: 4px;

      .ant-btn {
        padding: 4px;
        width: 28px;
        height: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
      }
    }
  }
} 

</style>
