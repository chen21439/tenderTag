import { ref, onUnmounted } from 'vue'
import { createPolling, type PollingOptions } from '@/utils/tools'

export function usePolling(pollingFn: () => Promise<any>, options?: PollingOptions) {
  const isRunning = ref(false)
  const retryCount = ref(0)
  const error = ref<any>(null)
  const pendingRequests = ref(0)
  const isExecuting = ref(false)
  
  const polling = createPolling(pollingFn, {
    ...options,
    onSuccess: (data) => {
      error.value = null
      options?.onSuccess?.(data)
      // 更新状态
      updateStatus()
    },
    onError: (err, count) => {
      error.value = err
      retryCount.value = count
      options?.onError?.(err, count)
      // 更新状态
      updateStatus()
    }
  })

  // 更新状态
  const updateStatus = () => {
    const status = polling.status
    isRunning.value = status.isRunning
    retryCount.value = status.retryCount
    pendingRequests.value = status.pendingRequests
    isExecuting.value = status.isExecuting
  }

  const start = () => {
    polling.start()
    updateStatus()
  }

  const stop = () => {
    polling.stop()
    updateStatus()
  }

  const restart = () => {
    polling.restart()
    updateStatus()
  }

  // 组件卸载时自动清理
  onUnmounted(() => { 
    stop()
  })

  return {
    start,
    stop,
    restart,
    isRunning,
    retryCount,
    error,
    pendingRequests,
    isExecuting
  }
}