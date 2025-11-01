<template>
  <div 
    class="virtual-scroll-container"
    :style="containerStyle"
    @scroll="handleScroll"
    ref="containerRef"
  >
    <!-- 占位元素，用于撑开滚动条 -->
    <div 
      class="virtual-scroll-spacer"
      :style="{ height: `${totalHeight}px` }"
    />
    
    <!-- 可见内容区域 -->
    <div 
      class="virtual-scroll-content"
      :style="contentStyle"
    >
      <slot 
        v-for="item in visibleItems"
        :key="getItemKey(item)"
        :item="item"
        :index="item.index"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useThrottleFn } from '@vueuse/core'

interface VirtualScrollItem {
  index: number
  data: any
  height?: number
}

interface Props {
  items: any[]
  itemHeight: number
  height: number | string
  bufferSize?: number
  getItemKey?: (item: any, index: number) => string | number
}

const props = withDefaults(defineProps<Props>(), {
  bufferSize: 5,
  getItemKey: (item: any, index: number) => index
})

// 响应式数据
const containerRef = ref<HTMLElement>()
const scrollTop = ref(0)
const containerHeight = ref(0)

// 计算属性
const containerStyle = computed(() => ({
  height: typeof props.height === 'number' ? `${props.height}px` : props.height,
  overflow: 'auto',
  position: 'relative'
}))

const totalHeight = computed(() => {
  return props.items.length * props.itemHeight
})

const visibleRange = computed(() => {
  const start = Math.floor(scrollTop.value / props.itemHeight)
  const visibleCount = Math.ceil(containerHeight.value / props.itemHeight)
  const end = start + visibleCount
  
  // 添加缓冲区
  const bufferedStart = Math.max(0, start - props.bufferSize)
  const bufferedEnd = Math.min(props.items.length, end + props.bufferSize)
  
  return {
    start: bufferedStart,
    end: bufferedEnd
  }
})

const visibleItems = computed(() => {
  const { start, end } = visibleRange.value
  return props.items.slice(start, end).map((item, index) => ({
    index: start + index,
    data: item
  }))
})

const contentStyle = computed(() => ({
  position: 'absolute',
  top: `${visibleRange.value.start * props.itemHeight}px`,
  left: '0',
  right: '0'
}))

// 方法
const handleScroll = useThrottleFn((event: Event) => {
  const target = event.target as HTMLElement
  scrollTop.value = target.scrollTop
}, 16) // 约60fps

const updateContainerHeight = () => {
  if (containerRef.value) {
    containerHeight.value = containerRef.value.clientHeight
  }
}

const getItemKey = (item: VirtualScrollItem): string | number => {
  return props.getItemKey(item.data, item.index)
}

// 滚动到指定项
const scrollToItem = (index: number, behavior: ScrollBehavior = 'smooth') => {
  if (!containerRef.value) return
  
  const targetScrollTop = index * props.itemHeight
  containerRef.value.scrollTo({
    top: targetScrollTop,
    behavior
  })
}

// 滚动到顶部
const scrollToTop = (behavior: ScrollBehavior = 'smooth') => {
  scrollToItem(0, behavior)
}

// 滚动到底部
const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
  scrollToItem(props.items.length - 1, behavior)
}

// 暴露方法给父组件
defineExpose({
  scrollToItem,
  scrollToTop,
  scrollToBottom
})

// 生命周期
onMounted(() => {
  updateContainerHeight()
  window.addEventListener('resize', updateContainerHeight)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateContainerHeight)
})

// 监听容器变化
watch(() => props.height, () => {
  nextTick(updateContainerHeight)
})
</script>

<style lang="scss" scoped>
.virtual-scroll-container {
  position: relative;
  
  .virtual-scroll-spacer {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    pointer-events: none;
  }
  
  .virtual-scroll-content {
    position: absolute;
    width: 100%;
  }
}
</style>
