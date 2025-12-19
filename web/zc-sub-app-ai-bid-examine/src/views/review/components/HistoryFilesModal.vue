<template>
  <BaseDrawer
    v-model="visible"
    :width="400"
    :loading="loading"
    title="历史文件"
    getContainer=".compliance-review-container"
    rootClassName="customer-history-files-drawer"
    @cancel="handleCancel"
  >

    <div class="history-files-content">
      <!-- Run 选择器 -->
      <div class="run-selector">
        <a-select
          v-model:value="selectedRun"
          placeholder="选择运行批次"
          style="width: 100%; margin-bottom: 16px;"
          @change="handleRunChange"
        >
          <a-select-option value="local">
            本地任务列表
          </a-select-option>
          <a-select-option v-for="run in runsList" :key="run.name" :value="run.name">
            {{ run.date || run.name }}
          </a-select-option>
        </a-select>
      </div>

      <div class="files-list">
        <div
          v-for="file in files"
          :key="file.taskId || file.name"
          class="file-item"
          :class="{'active': file.taskId === selectedFile.taskId || file.name === selectedFile.name}"
          @click="handlePreview(file)"
        >
          <div class="file-header">
            <div class="file-info"> 
              <div class="file-name">{{ file.fileName }}</div> 
              <div class="file-meta">
                <span class="file-date">{{ file.createTime }}</span> 
              </div>
            </div> 
          </div>
          <div class="status-badge" v-if="getExamineResult(file).text">
            <component v-if="getExamineResult(file).icon" :is="getExamineResult(file).icon" class="status-icon"
            :style="{color: getExamineResult(file).color}"/>
            <span class="status-text">{{ getExamineResult(file).text }}</span>
          </div>
        </div>

        <div v-if="files.length === 0" class="empty-state">
          <a-empty description="暂无历史文件" />
        </div>
      </div>
    </div>
  </BaseDrawer>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { getRiskStyle } from '@/views/hooks/examine';
import { getLocalTaskList } from '@/api/examine';
import BaseDrawer from '@/components/BaseDrawer/base-drawer.vue'  

const props = defineProps<{
  modelValue: boolean
  taskId?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  preview: [file: any, autoLoad?: boolean]
}>()


const visible = ref(false)
const loading = ref(false)
const selectedRun = ref('local')

const files = ref<any[]>([])
const selectedFile = ref<any>({})
const runsList = ref<any[]>([])
const handlePreview = (file: any) => {
  const isSame = selectedRun.value === 'local'
    ? file.taskId === selectedFile.value.taskId
    : file.name === selectedFile.value.name
  if(isSame) return
  selectedFile.value = file
  emit('preview', file)
}

// 加载 runs 列表
const loadRunsList = async () => {
  try {
    const response = await fetch('http://localhost:3000/api/runs/list')
    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.error || '加载 runs 列表失败')
    }

    runsList.value = data.folders || []
    console.log('📂 加载了 runs 列表:', runsList.value)
  } catch (error) {
    console.error('Failed to load runs list:', error)
    runsList.value = []
  }
}

watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
  if (newVal) {
    loadRunsList()
    loadanys()
  }
})

watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})
const getExamineResult: any = (item: any) => { 
  return item.taskId === selectedFile.value.taskId ? { 
      color: '#133CE8',
      text: '当前文件',
  } : getRiskStyle(item.reviewResult) 
}

// 加载本地任务列表
const loadLocalTasks = async () => {
    loading.value = true
    try {
      const data = await getLocalTaskList()
      files.value = data || []
      selectedFile.value = files.value.find(item => item.taskId === props.taskId) ?? {}
    } catch (error) {
      console.error('Failed to load task list:', error)
      files.value = []
    } finally {
      loading.value = false
    }
}

// 加载 runs 目录的文件列表
const loadRunsFiles = async (runName: string) => {
    loading.value = true
    try {
      // 读取 enriched 子目录下的文件
      const response = await fetch(`http://localhost:3000/api/runs/${runName}/files?subPath=enriched`)
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || '加载失败')
      }

      console.log('📁 Enriched 目录文件列表:', data)

      // 转换为统一格式
      files.value = data.files
        .filter((file: any) => file.ext === '.json')
        .map((file: any) => ({
          name: file.name,
          fileName: file.name.replace('.json', ''),
          createTime: new Date(file.modified).toLocaleString('zh-CN'),
          size: file.size,
          taskId: null,
          reviewResult: null,
          _runName: runName,
          _isFromRuns: true
        }))
        // 按修改时间降序排序（最新的在前）
        .sort((a: any, b: any) => {
          return new Date(b.createTime).getTime() - new Date(a.createTime).getTime()
        })

      // 默认选中第一个（最新的）
      if (files.value.length > 0) {
        selectedFile.value = files.value[0]
        // 自动触发预览，传递 autoLoad=true 表示自动加载
        emit('preview', files.value[0], true)
      } else {
        selectedFile.value = {}
      }

      console.log(`✅ 加载了 ${files.value.length} 个 JSON 文件，默认选中: ${selectedFile.value.fileName}`)
    } catch (error) {
      console.error('Failed to load runs files:', error)
      files.value = []
    } finally {
      loading.value = false
    }
}

const loadanys = async () => {
    if (selectedRun.value === 'local') {
      await loadLocalTasks()
    } else {
      await loadRunsFiles(selectedRun.value)
    }
}

// 处理 run 切换
const handleRunChange = async () => {
  await loadanys()
}

const handleCancel = () => {
  visible.value = false
}
</script>

<style lang="scss" scoped>
.history-files-content {
  padding: 16px 16px 16px 60px; /* 左侧增加内边距，避免被 AI 图标遮挡 */
  height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;

  .run-selector {
    flex-shrink: 0;
    margin-bottom: 16px;
  }

  .files-list {
    flex: 1;
    overflow-y: auto;
    min-height: 0;

    .file-item {
      cursor: pointer;
      padding: 16px;
      border: 1px solid #D9D9D9;
      border-radius: 8px;
      margin-bottom: 12px;
      transition: all 0.2s;
      &.active,
      &:hover {
        border-color: var(--main-3); 
        background-color: #F0F5FF;
      }
      
      &:last-child {
        margin-bottom: 0;
      }
      &.active {
        .status-badge {
          padding: 0 8px;
          height: 22px;
          line-height: 22px;
          border-radius: 22px;
          background-color: var(--main-1);
          color: var(--main-6);
          font-size: 12px;
          text-align: center;
        }
      }
      .file-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start; 
        
        .file-info {
          flex: 1;
          
          .file-name {
            font-size: 14px;
            font-weight: 500;
            color: #262626;
            margin-bottom: 4px;
            line-height: 1.4;
            word-break: break-all;
          }
          
          .file-meta {
            display: flex;
            gap: 16px;
            font-size: 12px;
            color: #8c8c8c;
            
            .file-date,
            .file-size {
              display: flex;
              align-items: center;
            }
          }
        }  
      }
      .status-badge {
        margin-top: 12px;
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
    
    .empty-state {
      text-align: center;
      padding: 40px 0;
    }
  }
  
}
</style>
<style lang="scss">
.customer-history-files-drawer {
  .ant-drawer-header {
    .ant-drawer-header-title {
      position: relative;
    }
    .ant-drawer-close {
      position: absolute;
      right: 0; 
      top: 50%;
      transform: translateY(-50%);
      z-index: 1;
      margin-right: 0;
    } 
  }
}
</style>