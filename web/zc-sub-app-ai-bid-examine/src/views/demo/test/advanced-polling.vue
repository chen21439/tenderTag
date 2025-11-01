<template>
  <div>
    <a-button @click="start" :disabled="isRunning">开始轮询</a-button>
    <a-button @click="stop" :disabled="!isRunning">停止轮询</a-button>
    <div class="status">
      <p>运行状态: {{ isRunning ? '运行中' : '已停止' }}</p>
      <p>执行状态: {{ isExecuting ? '请求中' : '空闲' }}</p>
      <p>待处理请求: {{ pendingRequests }}</p>
      <p>重试次数: {{ retryCount }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { usePolling } from '@/hooks/use-polling'
import { http } from '@/services/http'

const { 
  start, 
  stop, 
  isRunning, 
  retryCount, 
  pendingRequests, 
  isExecuting 
} = usePolling(
  async () => {
    const { data, err } = await http({
      url: '/api/task/status',
      method: 'GET'
    })
    if (err) throw err
    return data
  },
  {
    interval: 3000,
    maxRetries: 5,
    requestTimeout: 10000, // 10秒超时
    skipOnPending: true, // 跳过进行中的请求
    maxConcurrent: 1, // 最大并发数
    onSuccess: (data) => {
      console.log('轮询成功:', data)
    },
    onError: (error, count) => {
      console.error(`轮询失败 (${count}次):`, error)
    }
  }
)
</script>