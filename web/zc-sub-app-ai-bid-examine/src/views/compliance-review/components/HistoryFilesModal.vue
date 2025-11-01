<template>
  <BaseDrawer
    v-model="visible"
    :width="320"
    :loading="loading"
    title="历史文件"
    getContainer=".compliance-review-container"
    rootClassName="customer-history-files-drawer"
    @cancel="handleCancel"
  >

    <div class="history-files-content">
      <div class="files-list">
        <div
          v-for="file in files"
          :key="file.taskId"
          class="file-item"
          :class="{'active': file.taskId === selectedFile.taskId}"
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
  preview: [file: any] 
}>()


const visible = ref(false)
const loading = ref(false)

// 模拟历史文件数据
const files = ref<any[]>([])
// 选中的
const selectedFile = ref<any>({})
const handlePreview = (file: any) => {
  if(file.taskId === selectedFile.value.taskId) return
  selectedFile.value = file
  emit('preview', file)
}

// 监听外部传入的visible状态
watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
  if (newVal) {
    loadanys()
  }
})

// 监听内部visible状态变化
watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})
// 审查结果颜色
const getExamineResult: any = (item: any) => { 
  return item.taskId === selectedFile.value.taskId ? { 
      color: '#133CE8',
      text: '当前文件',
  } : getRiskStyle(item.reviewResult) 
}

// 加载历史文件
const loadanys = async () => {
  // if (!props.taskId) return
    loading.value = true
    try {
      const data = await getLocalTaskList()
      // taskList.json 返回的是数组格式，直接使用
      files.value = data || []
      selectedFile.value = files.value.find(item => item.taskId === props.taskId) ?? {}
    } catch (error) {
      console.error('Failed to load task list:', error)
      files.value = []
    } finally {
      loading.value = false
    }
}


// 取消操作
const handleCancel = () => {
  visible.value = false
}
</script>

<style lang="scss" scoped>
.history-files-content {
  padding: 24px;
  .files-list { 
    overflow-y: auto;
    
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
