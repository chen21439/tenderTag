<template>
  <div class="upload-file-container">
    <!-- 主上传区域 -->
    <a-upload-dragger
      v-bind="$attrs"
      :file-list="fileList"
      :before-upload="beforeUpload"
      :custom-request="customRequest"
      :multiple="multiple"
      :accept="accept"
      :disabled="disabled"
      :max-count="maxCount"
      :show-upload-list="showUploadList"
      @remove="handleRemove"
      @drop="handleDrop"
      @change="handleChange"
    >
      <slot>
        <a-button :disabled="disabled" type="primary">
          <upload-outlined />
          {{ buttonText }}
        </a-button>
      </slot>

      <!-- 自定义文件列表项 -->
      <template #itemRender="{ file, actions }">
        <div class="upload-list-item">
          <div class="upload-list-item-info">
            <div class="upload-list-item-name">
              <file-outlined /> {{ file.name }}
            </div>
            <div v-if="file.status === 'uploading'" class="upload-list-item-progress">
              <a-progress :percent="file.percent || 0" size="small" />
            </div>
          </div>
          <div class="upload-list-item-actions">
            <a-button type="link" @click="() => actions.remove()">
              <delete-outlined />
            </a-button>
          </div>
        </div>
      </template>
    </a-upload-dragger>

    <!-- 提示信息 -->
    <div v-if="tip" class="upload-tip">{{ tip }}</div>

    <!-- 全屏拖拽效果遮罩 -->
    <teleport to="body">
      <div
        v-if="enableDragEffect && isDragOver"
        class="drag-overlay"
        @dragover.prevent
        @drop.prevent="handleGlobalDrop"
        @dragleave="handleDragLeave"
      >
        <div class="drag-content">
          <div class="drag-icon"></div>
          <div class="drag-text">在此处释放文件</div>
          <div class="drag-tip">
            仅支持 {{ accept }} 格式文档，单个文档大小不超过 {{ maxSize }}MB
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script lang="ts" setup>
// ==================== 导入模块 ====================
import { ref, onMounted, onUnmounted, computed, h } from 'vue'
import { message } from 'ant-design-vue'
import { UploadOutlined, FileOutlined, DeleteOutlined, InfoCircleOutlined } from '@ant-design/icons-vue'
import type { UploadFile } from 'ant-design-vue'
import { formatFileSize } from '@/utils/tools'
import { fileUpload } from '@/api/examine'

// ==================== 类型定义 ====================
interface Props {
  files?: any[]
  customerFn?: any
  buttonText?: string
  tip?: string
  multiple?: boolean
  accept?: string
  acceptTip?: string
  disabled?: boolean
  maxCount?: number
  maxSize?: number
  showUploadList?: boolean | object
  data?: object
  enableDragEffect?: boolean  // 是否启用全屏拖拽效果
}

interface UploadConfig {
  signal: AbortSignal
  onUploadProgress: (progressEvent: ProgressEvent) => void
}

interface CustomRequestOptions {
  file: File
  onSuccess: (response: any) => void
  onError: (error: any) => void
  onProgress: (event: { percent: number }) => void
}

// ==================== Props 和 Emits ====================
const props = withDefaults(defineProps<Props>(), {
  files: () => [],
  customerFn: () => fileUpload,
  buttonText: '上传文件',
  tip: '',
  multiple: false,
  accept: '',
  acceptTip: '',
  disabled: false,
  maxCount: 10,
  maxSize: 20,
  showUploadList: true,
  data: () => ({}),
  enableDragEffect: true
})

const emit = defineEmits(['update:files', 'change', 'success', 'error'])

// ==================== 响应式数据 ====================
const isDragOver = ref(false)
let dragLeaveTimer: number | null = null

const fileList = computed({
  get: () => props.files,
  set: (val) => {
    emit('update:files', val)
    emit('change', val)
  }
})

// ==================== 文件校验模块 ====================
const beforeUpload = (file: File): boolean => {
  const { accept, acceptTip } = props

  // 文件名安全检查
  const unsafeChars = /[\\/:*?"<>|\s]/g
  if (unsafeChars.test(file.name)) {
    message.info('文件名包含非法字符（\\ / : * ? " < > | 或空格），请修改后重试')
    return false
  }

  // 检查文件名长度
  if (file.name.length > 200) {
    message.info('文件名过长，请修改后重试')
    return false
  }

  // 空文件检查
  if (file.size === 0) {
    message.info('不能上传空文件')
    return false
  }

  // 文件大小限制
  const isLtMaxSize = file.size / 1024 / 1024 < props.maxSize
  if (!isLtMaxSize) {
    message.info(`单个文档大小不超过 ${props.maxSize}MB!`)
    return false
  }

  // 文件数量限制
  if (fileList.value.length >= props.maxCount) {
    message.info(`最多只能上传 ${props.maxCount} 份文件!`)
    return false
  }

  // 文件类型限制
  if (accept) {
    const acceptTypes = accept.split(',').map(type => type.trim().toLowerCase())
    const fileType = file.type.toLowerCase()
    const fileName = file.name.toLowerCase()
    const isValidType = acceptTypes.some(type => {
      if (type.startsWith('.')) {
        // 检查文件扩展名
        return fileName.endsWith(type)
      } else {
        // 检查 MIME 类型
        return fileType === type || fileType.startsWith(`${type}/`)
      }
    })

    if (!isValidType) {
      const tip = acceptTip || `只能上传 ${accept} 格式的文件`
      message.info({
        content: tip,
        icon: h(InfoCircleOutlined)
      })
      return false
    }
  }

  return true
}

// ==================== 文件列表管理模块 ====================
const updateFileList = (newList: UploadFile[]) => {
  fileList.value = newList
}

const updateFileStatus = (uid: string, updates: Partial<UploadFile>) => {
  const index = fileList.value.findIndex(item => item.uid === uid)
  if (index !== -1) {
    const newList = [...fileList.value]
    newList[index] = {
      ...newList[index],
      ...updates
    }
    updateFileList(newList)
  }
}
// ==================== 全屏拖拽效果模块 ====================
const handleGlobalDragEnter = (e: DragEvent) => {
  if (!props.enableDragEffect || props.disabled) return

  e.preventDefault()

  // 清除之前的离开定时器
  if (dragLeaveTimer) {
    clearTimeout(dragLeaveTimer)
    dragLeaveTimer = null
  }

  // 检查是否包含文件
  if (e.dataTransfer?.types.includes('Files')) {
    isDragOver.value = true
  }
}

const handleGlobalDragLeave = (e: DragEvent) => {
  if (!props.enableDragEffect) return

  e.preventDefault()

  // 清除之前的定时器
  if (dragLeaveTimer) {
    clearTimeout(dragLeaveTimer)
  }

  // 延迟关闭遮罩，确保在拖拽过程中不会意外关闭
  dragLeaveTimer = setTimeout(() => {
    isDragOver.value = false
    dragLeaveTimer = null
  }, 300)
}

const handleGlobalDragOver = (e: DragEvent) => {
  e.preventDefault()

  // 在 dragover 时保持拖拽状态，避免闪烁
  if (props.enableDragEffect && !props.disabled && e.dataTransfer?.types.includes('Files')) {
    // 清除离开定时器，保持遮罩显示
    if (dragLeaveTimer) {
      clearTimeout(dragLeaveTimer)
      dragLeaveTimer = null
    }

    // 确保遮罩保持显示
    if (!isDragOver.value) {
      isDragOver.value = true
    }
  }
}

const handleGlobalDrop = async (e: DragEvent) => {
  if (!props.enableDragEffect || props.disabled) return

  e.preventDefault()

  // 清除定时器并立即关闭遮罩
  if (dragLeaveTimer) {
    clearTimeout(dragLeaveTimer)
    dragLeaveTimer = null
  }

  isDragOver.value = false

  const files = Array.from(e.dataTransfer?.files || [])
  if (files.length === 0) return

  // 处理每个文件
  for (const file of files) {
    const isValid = beforeUpload(file)
    if (isValid) {
      const options = {
        file,
        onSuccess: (response: any) => {
          console.log('Upload success:', response)
        },
        onError: (error: any) => {
          console.error('Upload error:', error)
        },
        onProgress: (event: { percent: number }) => {
          console.log('Upload progress:', event.percent)
        }
      }

      await customRequest(options)
    }
  }
}

const handleDragLeave = (e: DragEvent) => {
  handleGlobalDragLeave(e)
}



// ==================== 事件处理模块 ====================
const handleDrop = (e: DragEvent) => {
  console.log('拖拽文件:', e)

  const files = Array.from(e.dataTransfer?.files || [])

  // 对每个文件进行预校验
  for (const file of files) {
    const isValid = beforeUpload(file)
    if (!isValid) {
      e.preventDefault()
      e.stopPropagation()
      return false
    }
  }
}

const handleChange = (info: any) => {
  console.log('文件变化:', info)
  const { file, fileList: newFileList } = info

  // 对于拖拽上传的文件，在这里进行校验
  if (file.status === 'uploading' && file.originFileObj) {
    const isValid = beforeUpload(file.originFileObj)
    if (!isValid) {
      // 立即移除无效文件
      const filteredList = newFileList.filter((f: any) => f.uid !== file.uid)
      updateFileList(filteredList)
      return
    }
  }

  // 处理文件状态变化
  if (file.status === 'removed') {
    updateFileList(newFileList)
  }
}

const handleRemove = async (file: UploadFile) => {
  try {
    const index = fileList.value.findIndex(item => item.uid === file.uid)
    if (index === -1) return false

    const newList = [...fileList.value]
    newList.splice(index, 1)
    updateFileList(newList)
    emit('change', newList)
    return true
  } catch (error) {
    console.error('Remove file failed:', error)
    return false
  }
}
// ==================== 上传处理模块 ====================

const customRequest = async (options: CustomRequestOptions) => {
  const { file, onSuccess, onError, onProgress } = options

  // 在上传开始前再次校验（防止拖拽文件跳过 beforeUpload）
  const isValid = beforeUpload(file)
  if (!isValid) {
    onError(new Error('文件校验失败'))
    return
  }

  // 创建上传文件对象
  const uploadFile: UploadFile = {
    uid: String(Date.now()),
    name: file.name,
    type: file.name?.split('.').pop()?.toUpperCase() || '',
    size: formatFileSize(file.size),
    status: 'uploading',
    percent: 0,
    originFileObj: file as any // 保存原始文件对象，用于重试上传
  }

  try {
    // 立即将文件添加到列表
    updateFileList([...fileList.value, uploadFile])
    const formData = new FormData()
    formData.append('file', file)

    // 添加额外参数
    if (props.data) {
      Object.entries(props.data).forEach(([key, value]) => {
        formData.append(key, value as string)
      })
    }

    // 创建上传配置
    const controller = new AbortController()
    const config: UploadConfig = {
      signal: controller.signal,
      onUploadProgress: (progressEvent: ProgressEvent) => {
        const percent = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1))
        updateFileStatus(uploadFile.uid, { percent, status: 'uploading' })
        onProgress({ percent })
      }
    }

    // 执行上传
    const uploadFn = typeof props.customerFn === 'function' ? props.customerFn : fileUpload
    const { err, data = {} } = await uploadFn(formData, config)
    if (err) {
      throw err
    }

    // 更新成功状态
    updateFileStatus(uploadFile.uid, {
      status: 'done',
      response: data,
      percent: 100
    })
    onSuccess(data)
    emit('success', uploadFile)

    return {
      abort: () => controller.abort()
    }

  } catch (error) {
    // 统一错误处理
    updateFileStatus(uploadFile.uid, { status: 'error' })
    emit('error', uploadFile)
    onError(error)
    console.error('Upload failed:', error)
  }
}

// ==================== 重试上传模块 ====================
const handleRetry = async (file: UploadFile) => {
  try {
    // 检查是否有原始文件对象
    if (!file.originFileObj) {
      console.error('无法重试上传：缺少原始文件对象')
      return false
    }

    // 更新文件状态为上传中
    updateFileStatus(file.uid, {
      status: 'uploading',
      percent: 0
    })

    // 创建FormData
    const formData = new FormData()
    formData.append('file', file.originFileObj as File)

    // 添加额外参数
    if (props.data) {
      Object.entries(props.data).forEach(([key, value]) => {
        formData.append(key, value as string)
      })
    }

    // 创建上传配置
    const controller = new AbortController()
    const config: UploadConfig = {
      signal: controller.signal,
      onUploadProgress: (progressEvent: ProgressEvent) => {
        const percent = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1))
        updateFileStatus(file.uid, { percent, status: 'uploading' })
      }
    }

    // 执行上传
    const uploadFn = typeof props.customerFn === 'function' ? props.customerFn : fileUpload
    const { err, data = {} } = await uploadFn(formData, config)

    if (err) {
      throw err
    }

    // 更新成功状态
    updateFileStatus(file.uid, {
      status: 'done',
      response: data,
      percent: 100
    })

    emit('success', file)
    return true

  } catch (error) {
    // 重试失败，恢复错误状态
    updateFileStatus(file.uid, { status: 'error' })
    emit('error', file)
    console.error('Retry upload failed:', error)
    return false
  }
}
// ==================== 生命周期管理模块 ====================
onMounted(() => {
  if (props.enableDragEffect) {
    document.addEventListener('dragenter', handleGlobalDragEnter)
    document.addEventListener('dragleave', handleGlobalDragLeave)
    document.addEventListener('dragover', handleGlobalDragOver)
    document.addEventListener('drop', (e) => e.preventDefault())
  }
})

onUnmounted(() => {
  if (props.enableDragEffect) {
    document.removeEventListener('dragenter', handleGlobalDragEnter)
    document.removeEventListener('dragleave', handleGlobalDragLeave)
    document.removeEventListener('dragover', handleGlobalDragOver)
    document.removeEventListener('drop', (e) => e.preventDefault())
  }

  // 清理定时器
  if (dragLeaveTimer) {
    clearTimeout(dragLeaveTimer)
    dragLeaveTimer = null
  }
})
// ==================== 组件暴露 ====================
defineExpose({
  handleRemove,
  handleRetry
})
</script>

<style scoped lang="scss">
// ==================== 基础样式 ====================
.upload-file-container {
  width: 100%;
}

.upload-tip {
  margin-top: 8px;
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
}

// ==================== 上传列表样式 ====================
.upload-list-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.upload-list-item-info {
  flex: 1;
  overflow: hidden;
}

.upload-list-item-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.upload-list-item-progress {
  margin-top: 4px;
}

.upload-list-item-actions {
  margin-left: 8px;
}

// ==================== 上传组件样式覆盖 ====================
:deep(.ant-upload-wrapper) {
  .ant-upload-drag {
    border: none;
    background-color: transparent;
    .ant-upload {
      padding: 0;
    }
  }
}

// ==================== 全屏拖拽效果样式 ====================
.drag-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(247, 250, 252, 0.8);
  backdrop-filter: blur(8px);
  z-index: 9999;
  display: flex;
  justify-content: center;
  animation: fadeIn 0.3s ease-in-out;
}

.drag-content {
  margin-top: 80px;
  text-align: center; 
  animation: scaleIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative;
}

.drag-icon {
  margin-bottom: 10px;
  width: 307px;
  height: 257px;
  background: url('@/assets/images/bid-examine/drag-info.png') no-repeat center top;
  animation: float 3s ease-in-out infinite;
}

.drag-text {
  font-size: 20px;
  font-weight: 600;
  color: #262626;
  margin-bottom: 16px;
  letter-spacing: 0.5px;
}

.drag-tip {
  font-size: 13px;
  color: #8c8c8c;
  line-height: 1.6;
  max-width: 320px;
  margin: 0 auto;
}

.drag-close {
  position: absolute;
  top: 24px;
  right: 24px;
  width: 32px;
  height: 32px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 16px;
  color: #666;
  transition: all 0.2s ease;

  &:hover {
    background: #fff;
    color: #333;
    transform: scale(1.1);
  }
}

// ==================== 动画效果 ====================
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.9) translateY(20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-10px);
  }
}
</style>

