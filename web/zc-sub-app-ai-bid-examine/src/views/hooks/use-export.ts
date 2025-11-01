import { reactive, computed } from 'vue'
import { message } from 'ant-design-vue'
import { usePolling } from '@/hooks/use-polling'
import { downloadPackageFiles } from '@/api/download'
import { createPackageFiles, exportTask } from '@/api/examine'
export interface ExportOption {
  key: string
  label: string
  fileType: string
  defaultChecked?: boolean
}
export function useExport(options: ExportOption[], taskId: string, fn?: Function) {
  const state = reactive({
    visible: false,
    loading: false, 
    exportTaskId: '',
    options: options.reduce((acc, option) => {
      acc[option.key] = option.defaultChecked ?? true
      return acc
    }, {} as Record<string, boolean>)
  })
  const { start, stop } = usePolling(
    async () => {
      const { data, err } = await exportTask(state.exportTaskId)
      if (err) return
      return data
    },
    {
      interval: 15*1000,
      requestTimeout: 10000, // 10秒超时
      skipOnPending: true, // 跳过进行中的请求
      maxConcurrent: 1, // 最大并发数
      onSuccess:async (data) => {
        console.log('轮询成功:', data)
        if(!data) {
          stop()
          state.loading = false
          return
        } 
        // 失败或成功停止轮询
        if (data.status === 'success' || data.status === 'failed') { 
          stop()
          state.loading = false
        }
        if(data.status === 'failed') message.error('导出失败') 
        else if(data.status === 'success') {
          await downloadPackageFiles(state.exportTaskId)
          state.visible = false 
        } 
      },
      onError: (error, count) => {
        console.error(`轮询失败 (${count}次):`, error)
      }
    }
  )
  const hasSelectedOptions = computed(() => {
    return Object.values(state.options).some(Boolean)
  })

  const selectedFileTypes = computed(() => {
    return options
      .filter(option => state.options[option.key])
      .map(option => option.fileType)
  })
  const resetOptions = () => {
    options.forEach(option => {
      state.options[option.key] = option.defaultChecked ?? true
    })
  }
  const cancel = () => {
    state.visible = false
  }

  const confirm = async () => {
    if (selectedFileTypes.value.length === 0) {
      message.info('请至少选择一个导出选项')
      return
    }
    state.loading = true 
    const { data, err } = await createPackageFiles({
      fileTypes: selectedFileTypes.value,
      taskId
    })
    if(err) return
    state.exportTaskId = data.taskId ?? ''
    start()
    // state.loading = false 
    // state.visible = false 
  }
  const show = () => {
    resetOptions()
    state.visible = true

  }
  return {
    state,
    show,
    hasSelectedOptions,
    cancel,
    confirm
  }
}