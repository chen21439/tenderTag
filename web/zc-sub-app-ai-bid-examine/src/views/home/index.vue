<template>
  <div class="home home-upload-container">
    <!-- 主容器卡片 -->
    <div class="main-card">
      <!-- 标题区域 -->
      <div class="header-section"> 
          <img class="welcome-icon" src="@/assets/images/bid-examine/home-welcome.png" alt="欢迎图标">
          <span class="title-text">您好，欢迎使用采购文件合规性审查</span> 
      </div>

      <!-- 上传区域 -->
      <div class="upload-section">
        <upload-file
          ref="uploadFileRef"
          v-model:files="fileList"
          accept=".docx"
          accept-tip="文件格式不正确，请选择.docx文件"
          :show-upload-list="false"
          @change="doChange">
          <div class="upload-area">
            <img class="upload-icon" src="@/assets/images/bid-examine/upload-circle.png" alt="上传"> 
            <!-- 上传文字 -->
            <div class="upload-text-main">上传采购文件</div>
            <div class="upload-text-sub">仅支持 .docx 格式文档，单个文档大小不超过 20MB</div> 
            <div class="upload-text-hint">或将文件拖拽到此处</div>
          </div>
        </upload-file>
      </div>

      <!-- 文件列表区域 -->
      <div class="file-list-section">
        <!-- 文件列表标题和按钮 -->
        <div class="file-list-header">
          <div class="file-count-text" v-if="fileList.length > 0">已上传文件 ({{ fileList.filter(item=>item.status === 'done').length }}/{{ Math.max(0, fileList.length) }})</div>
          <div class="file-count-text" v-else></div>
          <div class="header-actions"> 
            <div class="tip">
              <svg-icon icon="icon-tishi" class="icon" />
              <span>采用AI辅助审查，最终结果需人工核对</span>
            </div>
            <a-button type="primary" class="start-button" :class="{ disabled: !doneCount }" @click="handleStartReview">
              开始审查
            </a-button>
          </div>
        </div>

        <!-- 文件项列表 -->
        <div class="file-items-container">
          <div v-for="file in fileList" :key="file.uid" class="file-item" :class="`file-item-${file.status}`">
            <div class="file-close-btn" @click="handleRemoveFile(file)">
               <CloseOutlined :style="{'font-size': '8px'}"/>
            </div>
            <div class="file-detail">
              <svg-icon :icon="getFileIcon(file.name)" class="icon-file" /> 
              <div class="file-info">
                <div class="file-name" :title="file.name">{{ file.name }}</div>
                <div class="file-size">{{ file.size }}</div>
              </div>
            </div>
            <div class="file-status">
              <div :class="`status-${file.status}`">
                <component class="status-icon" :is="getStatusIcon(file.status).icon" />
                <span class="status-text">{{ getStatusIcon(file.status).text }}</span>
              </div>
              <a-button v-if="file.status === 'error'" class="retry-btn" type="link" @click="handleRetryUpload(file)">重试</a-button>
            </div>

            <!-- 进度条 -->
            <div  class="progress-bar"> 
              <div class="progress-fill"><span class="percent" :class="file.status" :style="{ width: `${file.percent || 0}%` }"></span></div>
            </div> 
          </div>
        </div>
      </div> 
    </div>
    <!-- 最近添加的审查 -->
    <div class="main-card mt-[24px]" v-if="state.dataSource.length    ">
      <div class="flex justify-between items-center mb-[24px]">
        <span class="font-medium text-[24px]">最近添加的审查</span>
        <a-button  @click="router.push({ name: 'LibraryIndex' })">查看完整列表</a-button>
      </div>
      <a-table
        :data-source="state.dataSource"
        :columns="TABLE_COLUMNS"
        :pagination="false" 
        :loading="state.loading"
        class="basic-normal-table table" >
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
                @click="router.push({name: 'ComplianceReview', query: { taskId: record.taskId }})">
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
      placement="bottomLeft"
      trigger="manual"
      :overlay-class-name="'base-delete-confirm-popover'"
    >
      <template #content>
        <div class="delete-confirm-content"> 
          <div class="main-box">
            <CircleAlert class="warning-icon" :size="16" color="var(--error-6)"/> 
            <div class="delete-message">
              <div>
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
  </div>
</template>

<script setup lang='ts'>
import { computed, ref, onMounted } from 'vue'
import { CloseOutlined } from '@ant-design/icons-vue'
import { Trash,  FileSearch, ArrowDownToLine, CircleAlert } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { useTable } from '@/hooks/use-table'
import {apiTaskCreate, apiTaskList ,apiTaskDelete} from '@/api/examine'
import { customDocumentBundleExport } from '@/api/download'
import { getFileIcon, getStatusIcon } from '@/views/hooks/examine'
import { usePolling } from '@/hooks/use-polling'
import { riskOptions,getStatusStyle,getRiskStyle, TABLE_COLUMNS } from '@/views/hooks/examine'
import UploadFile from '@/components/UploadFile/index.vue'

interface FileItem {
  uid: string
  name: string
  size: number
  status: 'uploading' | 'done' | 'error'
  percent?: number
  response?: any
}
const router = useRouter()
const fileList = ref<FileItem[]>([])
const uploadFileRef = ref()

function doChange(files:any) { 
  fileList.value = [...files] 
}

// 计算是否可以开始审查
const doneCount = computed(() => {
  return fileList.value.filter(file => file.status === 'done').length
}) 
// 删除文件
function handleRemoveFile(file: FileItem) {
  const index = fileList.value.findIndex(item => item.uid === file.uid)
  if (index !== -1) {
    fileList.value.splice(index, 1)
  }
}

// 重试上传
async function handleRetryUpload(file: FileItem) {
  await uploadFileRef.value?.handleRetry(file) 
}
const isStarting = ref(false)
async function handleStartReview() {
  if (!doneCount.value || isStarting.value) return  
  const fileIdList = fileList.value
    .filter((item: any) => item.status === 'done')
    .map((item: any) => item.response?.fileId)
  isStarting.value = true
  hasOtherRequest.value = true
  const {err,data} = await apiTaskCreate({fileIdList})
  isStarting.value = false
  hasOtherRequest.value = false
  if (err) return
  fileList.value = fileList.value.filter((item: any) => item.status !== 'done')
  restart()
  // if(!data?.taskIdList?.length) {
  //   message.error('审查失败') 
  //   return
  // }
  // router.push({
  //   name: 'ComplianceReview',
  //   query: { taskId:data.taskIdList[0] }
  // })
} 
// 表格 
const { state,getTableData, refresh } = useTable({
  // 初始查询参数
  params: {
    pageNum: 1,
    pageSize: 5
  },

  // API 函数
  getList: apiTaskList, 
  // 启用功能
  usePagination: false,  
  // 数据字段映射
  dataFields: {
    list: 'dataList',
    total: 'total'
  }
})
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
// 审查报告导出
const exportingIds = ref(new Set<string>())
const exportReport = async (record: any) => {
  const { taskId } = record
  if (exportingIds.value.has(taskId)) return // 防止重复点击
  exportingIds.value.add(taskId) 
  hasOtherRequest.value = true
  const params = { taskId,fileTypes:['procurement_revised','risk_report'] }
  await customDocumentBundleExport(params) 
  hasOtherRequest.value = false
  exportingIds.value.delete(taskId) 
}

// 删除
const deletePopoverTrigger = ref<HTMLElement>()
const dialogOpen = ref(false)
const record2Delete = ref<any>(null)
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
  record2Delete.value = record
}
 
// 批量删除 

// 确认删除
const deletingLoading = ref(false)
const doDialogOk = async () => {
  dialogOpen.value = false 
  deletingLoading.value = true 
  hasOtherRequest.value = true
  // 单个删除模式
  const { taskId } = record2Delete.value
  const params = { taskId }
  const { err } = await apiTaskDelete(params)
  deletingLoading.value = false
  hasOtherRequest.value = false
  if (err) return 
  message.success('成功删除')  
  hasOtherRequest.value = true
  await refresh()  
  hasOtherRequest.value = false
}
// getTableData()
// ==================== 轮询 ==================== 
const hasOtherRequest = ref(false)
const { start, stop, restart } = usePolling(
  async () => {
    if (dialogOpen.value || hasOtherRequest.value) {
      console.log('删除确认弹窗显示中或者其他请求进行中，跳过轮询')
      return null
    }
    const res = await getTableData() 
    return res
  },
  {
    interval: 30*1000,
    requestTimeout: 10000, // 10秒超时
    skipOnPending: true, // 跳过进行中的请求
    maxConcurrent: 1, // 最大并发数
    onSuccess:async (data) => {
      console.log('轮询成功:', data) 
      if (data) { 
        state.dataSource = data.dataList ?? [] 
        const allCompleted = data.dataList?.every((item: any) => 
          item.reviewStatus === -1 || item.reviewStatus === 2
        )
        if (allCompleted && data.dataList?.length > 0) { 
          console.log('所有任务已完成，停止轮询')
          stop() 
        } 
      }
    },
    onError: (error, count) => {
      console.error(`轮询失败 (${count}次):`, error)
    }
  }
)
start() 
</script>

<style lang="scss" scoped>
.home {
  min-height: 100vh;
  background-color: #F9FAFB;
  color: #000;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px;
  box-sizing: border-box; 
  .main-card {     
    width: 100%;
    background: #FFFFFF;
    border-radius: 16px;
    box-shadow: 0px 1px 2px 0px rgba(0, 0, 0, 0.05);
    padding: 32px; 
  }

  .header-section {
    display: flex; 
    align-items: center; 
    justify-content: center;
    height: 48px;
    .welcome-icon {
      width: 48px;
      height: 48px;
      flex-shrink: 0;
      margin-right: 16px;
    }
    .title-text { 
      font-weight: 600;
      font-size: 30px; 
      color: #111827; 
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
:deep(.ant-upload-wrapper) {
    .ant-upload-select {
      width: 100%;
    }
  }
  .upload-section {
    width: 100%;
    margin-top: 32px;
  }

  .upload-area {
    width: 100%;
    height: 246px;
    background: #F7F8FA;
    border: 1px solid #E5E6EB;
    border-radius: 16px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;     
    cursor: pointer;
    transition: all 0.2s ease;

    &:hover {
      transform: translateY(-10px);
    } 
    .upload-icon {
      width: 64px;
      height: 64px;
      display: block;
    }

    .upload-text-main { 
      font-weight: 400;
      font-size: 20px;
      line-height: 1.4em;
      color: #111827;
      text-align: center;
      margin-top: 16px;
    }
    .upload-text-hint,
    .upload-text-sub{
      font-weight: 400; 
      margin-top: 12px;
    } 
    .upload-text-sub {  
      font-size: 16px; 
      color: #4B5563;
      text-align: center; 
    }

    .upload-text-hint { 
      color: #6B7280;
      font-size: 14px;
      line-height: 20px;
    }
  }

  // 文件列表区域
  .file-list-section {
    display: flex;
    flex-direction: column;  
    .file-list-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin:32px 0 24px;
      .file-count-text { 
        font-weight: 600;
        font-size: 20px;
        line-height: 1.4em;
        color: #000000; 
      }

      .header-actions {
        display: flex;
        align-items: center;
        gap: 16px;
        .tip{
          display: flex;
          align-items: center;
        }
        .icon {
          width: 16px;
          height: 16px;
          margin-right: 4px;
        }
        .tip { 
          color: #4B5563;
        }
        .test-button {
          padding: 8px 16px;
          height: 32px;
          background: #F0F5FF;
          border: 1px solid #8FB0FF;
          border-radius: 4px;
          font-family: 'Inter', sans-serif;
          font-weight: 400;
          font-size: 14px;
          color: #133CE8;
          cursor: pointer;
          transition: all 0.2s ease;

          &:hover {
            background: #E6EFFF;
            border-color: #3B66F5;
          }
        }

        .start-button {
          width: 138px;
          height: 48px;
          background: #133CE8;
          border-radius: 6px;
          border: none;
          font-family: 'Inter', sans-serif;
          font-weight: 600;
          font-size: 16px;
          line-height: 1.5em;
          color: #FFFFFF;
          cursor: pointer;
          transition: all 0.2s ease;

          &:hover {
            background: #3B66F5;
          }

          &:active {
            background: #0625C2;
          }

          &.disabled {
            background: #D1D5DB;
            color: #6B7280;
            cursor: not-allowed;
          }
        }
      }
    }

    .file-items-container { 
      display: grid; 
      gap: 16px; 
      grid-template-columns: repeat(3, 1fr); 
      
      @media (min-width: 1600px) {
        grid-template-columns: repeat(4, 1fr);
      }
      
      @media (min-width: 1920px) {
        grid-template-columns: repeat(5, 1fr); 
      }
    }

    .file-item {
      position: relative;
      width: 100%;
      min-width: 0;
      padding: 16px;
      border-radius: 8px;
      background: #FFFFFF;
      border: 1px solid #E5E6EB; 
      &.file-item-done {
        background: #F6FFED;
        border-color: #B7EB8F;
      }

      &.file-item-error {
        background: #FFF1F0;
        border-color: #FFA39E;
      }

      &.file-item-uploading {
        background: #F0F5FF;
        border-color: #8FB0FF;
      }

      .file-close-btn {
        position: absolute;
        top: 8px;
        right: 8px;
        width: 20px;
        height: 20px;
        background: #FFFFFF;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0px 9px 28px 8px rgba(0, 0, 0, 0.05),
                    0px 3px 6px -4px rgba(0, 0, 0, 0.12),
                    0px 6px 16px 0px rgba(0, 0, 0, 0.08);
        color: #000000; 
      } 
      .file-detail {
        display: flex;
        align-items: center;
        width: 100%;
      }
      .icon-file {
        width: 32px;
        height: 32px;
        flex-shrink: 0;
        margin-right: 4px;
      }
      .file-info {
        flex: 1;
        min-width: 0; 

        .file-name {  
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis; 
          height: 22px;
          line-height: 22px;
          color: rgba(0, 0, 0, 0.88);
        } 
        .file-size { 
          color: rgba(0, 0, 0, 0.45);
        }
      }

      .file-status { 
        margin: 12px 0;
        display: flex;
        align-items: center;  
        justify-content: space-between;
        .status-done,
        .status-error,
        .status-uploading {
          display: flex;
          align-items: center;
          gap: 4px; 
        }
        .status-icon {
          width: 16px;
          height: 16px;
        }

        .status-done {
          color:var(--success-6);
        }

        .status-uploading {
          color: var(--main-6); 
        }

        .status-error {
          color: var(--error-6); 
        }
        .retry-btn {
          padding: 0;
          margin: 0;
          height: 22px;
          &:hover {
            color: #3B66F5;
          }
        }
      }
    }
  }
  .progress-bar,
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
}
</style>
