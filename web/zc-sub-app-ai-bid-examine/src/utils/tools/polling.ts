export interface PollingOptions {
  interval?: number
  immediate?: boolean
  maxRetries?: number
  onError?: (error: any, retryCount: number) => void
  onSuccess?: (data: any) => void
  stopOnError?: boolean 
  maxConcurrent?: number // 最大并发请求数，默认 1
  requestTimeout?: number // 单个请求超时时间，默认 30s
  skipOnPending?: boolean // 有请求进行中时是否跳过新请求，默认 true
  abortPrevious?: boolean // 是否取消上一个未完成的请求，默认 false
}

export class PollingManager {
  private timerId: number | null = null
  private isRunning = false
  private retryCount = 0
  private readonly options: Required<PollingOptions>
  private readonly pollingFn: () => Promise<any>
  
  // 请求管理
  private pendingRequests = new Set<AbortController>()
  private isExecuting = false
  private lastRequestTime = 0

  constructor(pollingFn: () => Promise<any>, options: PollingOptions = {}) {
    this.pollingFn = pollingFn
    this.options = {
      interval: 3000,
      immediate: true,
      maxRetries: -1,
      onError: () => {},
      onSuccess: () => {},
      stopOnError: false,
      maxConcurrent: 1,
      requestTimeout: 30000,
      skipOnPending: true,
      abortPrevious: false,
      ...options
    }
  }

  start(): void {
    if (this.isRunning) return
    
    this.isRunning = true
    this.retryCount = 0
    
    if (this.options.immediate) {
      this.execute()
    } else {
      this.scheduleNext()
    }
  }

  stop(): void {
    if (this.timerId) {
      clearTimeout(this.timerId)
      this.timerId = null
    }
    
    // 取消所有进行中的请求
    this.abortAllRequests()
    
    this.isRunning = false
    this.retryCount = 0
    this.isExecuting = false
  }

  restart(): void {
    this.stop()
    this.start()
  }

  // 取消所有进行中的请求
  private abortAllRequests(): void {
    this.pendingRequests.forEach(controller => {
      try {
        controller.abort()
      } catch (error) {
        // 忽略已经取消的请求错误
      }
    })
    this.pendingRequests.clear()
  }

  // 检查是否应该跳过当前请求
  private shouldSkipRequest(): boolean {
    // 如果设置了跳过进行中的请求，且当前有请求在执行
    if (this.options.skipOnPending && this.isExecuting) {
      console.log('跳过轮询：上一个请求仍在进行中')
      return true
    }
    
    // 检查并发数限制
    if (this.pendingRequests.size >= this.options.maxConcurrent) {
      console.log('跳过轮询：达到最大并发数限制')
      return true
    }
    
    return false
  }

  private async execute(): Promise<void> {
    if (!this.isRunning) return

    // 检查是否应该跳过
    if (this.shouldSkipRequest()) {
      this.scheduleNext()
      return
    }

    // 如果设置了取消上一个请求
    if (this.options.abortPrevious && this.pendingRequests.size > 0) {
      this.abortAllRequests()
    }

    const controller = new AbortController()
    this.pendingRequests.add(controller)
    this.isExecuting = true
    this.lastRequestTime = Date.now()

    // 设置请求超时
    const timeoutId = setTimeout(() => {
      controller.abort()
    }, this.options.requestTimeout)

    try {
      // 包装原始函数，添加 AbortSignal 支持
      const result = await this.executeWithTimeout(controller.signal)
      
      clearTimeout(timeoutId)
      this.retryCount = 0
      this.options.onSuccess(result)
      this.scheduleNext()
    } catch (error: any) {
      clearTimeout(timeoutId)
      
      // 如果是主动取消的请求，不算作错误
      if (error.name === 'AbortError' || controller.signal.aborted) {
        console.log('请求被取消')
        return
      }
      
      this.retryCount++
      this.options.onError(error, this.retryCount)
      
      if (this.options.stopOnError || 
          (this.options.maxRetries > 0 && this.retryCount >= this.options.maxRetries)) {
        this.stop()
        return
      }
      
      this.scheduleNext()
    } finally {
      this.pendingRequests.delete(controller)
      this.isExecuting = false
    }
  }

  // 执行带超时的请求
  private async executeWithTimeout(signal: AbortSignal): Promise<any> {
    // 如果原始函数支持 AbortSignal，直接传递
    if (this.pollingFn.length > 0) {
      return await this.pollingFn.call(null, signal)
    }
    
    // 否则使用 Promise.race 实现超时
    return await Promise.race([
      this.pollingFn(),
      new Promise((_, reject) => {
        signal.addEventListener('abort', () => {
          reject(new Error('Request aborted'))
        })
      })
    ])
  }

  private scheduleNext(): void {
    if (!this.isRunning) return
    
    // 计算下次执行的延迟时间
    const elapsed = Date.now() - this.lastRequestTime
    const delay = Math.max(0, this.options.interval - elapsed)
    
    this.timerId = window.setTimeout(() => {
      this.execute()
    }, delay)
  }

  get status() {
    return {
      isRunning: this.isRunning,
      retryCount: this.retryCount,
      pendingRequests: this.pendingRequests.size,
      isExecuting: this.isExecuting
    }
  }
}

// 创建轮询实例的工厂函数
export function createPolling(pollingFn: () => Promise<any>, options?: PollingOptions): PollingManager {
  return new PollingManager(pollingFn, options)
}