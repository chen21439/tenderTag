<template>
  <div class="virtual-table-container" :style="containerStyle">
    <div class="table-header" v-if="showHeader">
      <table class="header-table">
        <thead>
          <tr>
            <th 
              v-for="(col, index) in columns"
              :key="index"
              :style="{ width: col.width || 'auto' }"
            >
              {{ col.title }}
            </th>
          </tr>
        </thead>
      </table>
    </div>
    
    <div class="table-body" :style="bodyStyle" @scroll="handleScroll" ref="bodyRef">
      <div class="table-spacer" :style="{ height: `${totalHeight}px` }" />
      
      <div class="table-content" :style="contentStyle">
        <table class="content-table">
          <tbody>
            <tr 
              v-for="(row, rowIndex) in visibleRows"
              :key="getRowKey(row, rowIndex)"
              :class="getRowClass(row, rowIndex)"
            >
              <td 
                v-for="(col, colIndex) in columns"
                :key="colIndex"
                :style="{ width: col.width || 'auto' }"
              >
                <slot 
                  name="cell"
                  :row="row"
                  :column="col"
                  :rowIndex="rowIndex"
                  :colIndex="colIndex"
                  :value="getCellValue(row, col)"
                >
                  {{ getCellValue(row, col) }}
                </slot>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useThrottleFn } from '@vueuse/core'

interface TableColumn {
  key: string
  title: string
  width?: string
  render?: (value: any, row: any, index: number) => any
}

interface Props {
  data: any[]
  columns: TableColumn[]
  rowHeight?: number
  height?: number | string
  showHeader?: boolean
  bufferSize?: number
  getRowKey?: (row: any, index: number) => string | number
  getRowClass?: (row: any, index: number) => string | object
}

const props = withDefaults(defineProps<Props>(), {
  rowHeight: 40,
  height: 400,
  showHeader: true,
  bufferSize: 10,
  getRowKey: (row: any, index: number) => index,
  getRowClass: () => ''
})

// 响应式数据
const bodyRef = ref<HTMLElement>()
const scrollTop = ref(0)
const bodyHeight = ref(0)

// 计算属性
const containerStyle = computed(() => ({
  height: typeof props.height === 'number' ? `${props.height}px` : props.height,
  border: '1px solid #f0f0f0',
  borderRadius: '4px',
  overflow: 'hidden'
}))

const bodyStyle = computed(() => ({
  height: props.showHeader ? 'calc(100% - 40px)' : '100%',
  overflow: 'auto',
  position: 'relative'
}))

const totalHeight = computed(() => {
  return props.data.length * props.rowHeight
})

const visibleRange = computed(() => {
  const start = Math.floor(scrollTop.value / props.rowHeight)
  const visibleCount = Math.ceil(bodyHeight.value / props.rowHeight)
  const end = start + visibleCount
  
  // 添加缓冲区
  const bufferedStart = Math.max(0, start - props.bufferSize)
  const bufferedEnd = Math.min(props.data.length, end + props.bufferSize)
  
  return {
    start: bufferedStart,
    end: bufferedEnd
  }
})

const visibleRows = computed(() => {
  const { start, end } = visibleRange.value
  return props.data.slice(start, end)
})

const contentStyle = computed(() => ({
  position: 'absolute',
  top: `${visibleRange.value.start * props.rowHeight}px`,
  left: '0',
  right: '0'
}))

// 方法
const handleScroll = useThrottleFn((event: Event) => {
  const target = event.target as HTMLElement
  scrollTop.value = target.scrollTop
}, 16)

const getCellValue = (row: any, column: TableColumn) => {
  if (column.render) {
    return column.render(row[column.key], row, 0)
  }
  return row[column.key]
}

const updateBodyHeight = () => {
  if (bodyRef.value) {
    bodyHeight.value = bodyRef.value.clientHeight
  }
}

// 滚动到指定行
const scrollToRow = (index: number, behavior: ScrollBehavior = 'smooth') => {
  if (!bodyRef.value) return
  
  const targetScrollTop = index * props.rowHeight
  bodyRef.value.scrollTo({
    top: targetScrollTop,
    behavior
  })
}

// 暴露方法
defineExpose({
  scrollToRow
})

// 生命周期
onMounted(() => {
  updateBodyHeight()
  window.addEventListener('resize', updateBodyHeight)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateBodyHeight)
})
</script>

<style lang="scss" scoped>
.virtual-table-container {
  display: flex;
  flex-direction: column;
  background: #fff;
  
  .table-header {
    border-bottom: 1px solid #f0f0f0;
    background: #fafafa;
    
    .header-table {
      width: 100%;
      border-collapse: collapse;
      
      th {
        padding: 12px 16px;
        text-align: left;
        font-weight: 600;
        color: #262626;
        border-right: 1px solid #f0f0f0;
        
        &:last-child {
          border-right: none;
        }
      }
    }
  }
  
  .table-body {
    flex: 1;
    position: relative;
    
    .table-spacer {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      pointer-events: none;
    }
    
    .table-content {
      position: absolute;
      width: 100%;
      
      .content-table {
        width: 100%;
        border-collapse: collapse;
        
        td {
          padding: 8px 16px;
          border-right: 1px solid #f0f0f0;
          border-bottom: 1px solid #f0f0f0;
          vertical-align: top;
          
          &:last-child {
            border-right: none;
          }
        }
        
        tr {
          &:hover {
            background-color: #f5f5f5;
          }
          
          &:nth-child(even) {
            background-color: #fafafa;
            
            &:hover {
              background-color: #f0f0f0;
            }
          }
        }
      }
    }
  }
}
</style>
