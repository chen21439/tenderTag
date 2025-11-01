# useTable 使用文档

`useTable` 是基于现有 `use-list` 提取的专门针对表格场景的组合式函数，提供了完整的表格数据管理、分页、排序、行选择等功能。

## 特性

- 🚀 **基于 use-list 优化**：继承了 use-list 的优秀设计，专门针对表格场景进行优化
- 📊 **完整的分页支持**：内置分页逻辑，支持页码跳转、页面大小调整
- 🔍 **排序功能**：支持单列排序，自动处理排序参数
- ✅ **行选择**：支持单选、多选、全选功能
- 🔄 **自动加载状态**：内置 loading 状态管理
- 🛠️ **高度可配置**：支持自定义参数处理、数据字段映射等
- 💪 **TypeScript 支持**：完整的类型定义

## 基本用法

```typescript
import { useTable } from '@/hooks/use-table'
import { apiGetTableList } from '@/api/example'

const {
  state,
  pagination,
  rowSelection,
  getTableData,
  onSearch,
  onTableChange
} = useTable({
  params: { status: 1 }, // 初始查询参数
  getList: apiGetTableList, // API 函数
  usePagination: true, // 启用分页
  useRowSelection: true // 启用行选择
})
```

## 配置选项

### UseTableOptions

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `params` | `any` | `{}` | 初始查询参数 |
| `getList` | `Function` | - | 获取数据的 API 函数，必填 |
| `getParams` | `Function` | - | 自定义参数处理函数 |
| `pagination` | `Object \| false` | - | 分页配置，设置为 `false` 禁用分页 |
| `usePagination` | `boolean` | `true` | 是否启用分页 |
| `useRowSelection` | `boolean` | `false` | 是否启用行选择 |
| `useSorter` | `boolean` | `false` | 是否启用排序 |
| `dataFields` | `Object` | - | 数据字段映射 |

### 分页配置

```typescript
// 启用分页（默认）
pagination: {
  current: 1,        // 当前页码
  pageSize: 10,      // 每页条数
  showSizeChanger: true,    // 显示页面大小选择器
  showQuickJumper: true,    // 显示快速跳转
  pageSizeOptions: ['10', '20', '50', '100'] // 页面大小选项
}

// 禁用分页
pagination: false
```

### 数据字段映射

```typescript
dataFields: {
  list: 'dataList',  // 数据列表字段名，默认 'list' 或 'dataList'
  total: 'total'     // 总数字段名，默认 'total'
}
```

## 返回值

| 属性/方法 | 类型 | 说明 |
|-----------|------|------|
| `state` | `Reactive<TableState>` | 表格状态对象 |
| `pagination` | `ComputedRef` | 分页配置对象 |
| `rowSelection` | `ComputedRef` | 行选择配置对象 |
| `getTableData` | `Function` | 获取表格数据 |
| `onSearch` | `Function` | 搜索（从第一页开始） |
| `onReset` | `Function` | 重置查询参数 |
| `onTableChange` | `Function` | 表格变化处理 |
| `refresh` | `Function` | 刷新当前页数据 |
| `clearSelection` | `Function` | 清空选择 |
| `setSelectedRowKeys` | `Function` | 设置选中行 |

### TableState 结构

```typescript
interface TableState {
  dataSource: any[]           // 表格数据
  params: any                 // 查询参数
  pagination: {               // 分页信息
    current: number
    pageSize: number
    total: number
    showSizeChanger: boolean
    showQuickJumper: boolean
    pageSizeOptions: string[]
  }
  loading: boolean            // 加载状态
  selectedRowKeys: any[]      // 选中的行键
  sorter: {                   // 排序信息
    field?: string
    order?: 'ascend' | 'descend'
  }
}
```

## 使用示例

### 1. 基础表格

```vue
<template>
  <a-table
    :data-source="state.dataSource"
    :columns="columns"
    :pagination="pagination"
    :loading="state.loading"
    @change="onTableChange"
  />
</template>

<script setup>
const { state, pagination, onTableChange, getTableData } = useTable({
  getList: apiGetTableList
})

onMounted(() => {
  getTableData()
})
</script>
```

### 2. 带搜索的表格

```vue
<template>
  <div>
    <a-form @submit="handleSearch">
      <a-input v-model:value="searchForm.name" placeholder="项目名称" />
      <a-button type="primary" html-type="submit">搜索</a-button>
    </a-form>
    
    <a-table
      :data-source="state.dataSource"
      :columns="columns"
      :pagination="pagination"
      :loading="state.loading"
      @change="onTableChange"
    />
  </div>
</template>

<script setup>
const searchForm = reactive({ name: '' })

const { state, pagination, onTableChange, onSearch } = useTable({
  params: searchForm,
  getList: apiGetTableList
})

const handleSearch = () => {
  Object.assign(state.params, searchForm)
  onSearch()
}
</script>
```

### 3. 带行选择的表格

```vue
<template>
  <div>
    <div class="actions">
      <a-button 
        :disabled="!state.selectedRowKeys.length"
        @click="handleBatchDelete"
      >
        批量删除 ({{ state.selectedRowKeys.length }})
      </a-button>
    </div>
    
    <a-table
      :data-source="state.dataSource"
      :columns="columns"
      :pagination="pagination"
      :row-selection="rowSelection"
      :loading="state.loading"
      :row-key="record => record.id"
      @change="onTableChange"
    />
  </div>
</template>

<script setup>
const { 
  state, 
  pagination, 
  rowSelection, 
  onTableChange, 
  clearSelection 
} = useTable({
  getList: apiGetTableList,
  useRowSelection: true
})

const handleBatchDelete = () => {
  console.log('删除选中项:', state.selectedRowKeys)
  // 执行删除后清空选择
  clearSelection()
}
</script>
```

### 4. 禁用分页的表格

```vue
<template>
  <a-table
    :data-source="state.dataSource"
    :columns="columns"
    :pagination="pagination"
    :loading="state.loading"
    @change="onTableChange"
  />
</template>

<script setup>
const { state, pagination, onTableChange, getTableData } = useTable({
  getList: apiGetTableList,
  pagination: false // 禁用分页
})

onMounted(() => {
  getTableData()
})
</script>
```

## 与 use-list 的区别

| 特性 | use-list | use-table |
|------|----------|-----------|
| 目标场景 | 通用列表 | 专门针对表格 |
| 分页配置 | 基础分页 | 完整的 Ant Design 分页配置 |
| 行选择 | 不支持 | 内置支持 |
| 排序 | 基础排序 | 完整的表格排序支持 |
| 状态管理 | 简单状态 | 完整的表格状态 |
| API 设计 | 通用 API | 专门为表格优化的 API |

## 最佳实践

1. **参数处理**：使用 `getParams` 函数处理复杂的参数逻辑
2. **错误处理**：在 API 函数中处理错误，use-table 会自动处理 loading 状态
3. **性能优化**：对于大量数据，考虑使用虚拟滚动或服务端分页
4. **状态同步**：搜索表单与 `state.params` 保持同步
5. **分页控制**：
   - 需要分页时使用默认配置或自定义分页参数
   - 不需要分页时设置 `pagination: false`
   - 分页和非分页模式的 API 参数会自动适配

## 迁移指南

从现有的表格代码迁移到 `use-table`：

1. 将分页逻辑替换为 `use-table` 的分页配置
2. 将数据获取逻辑移到 `getList` 函数中
3. 使用 `onTableChange` 替换自定义的表格变化处理
4. 利用内置的行选择功能替换自定义选择逻辑
