import { reactive, computed, ref } from 'vue'
import type { TableColumnType } from 'ant-design-vue'

// 表格状态接口
interface TableState {
  dataSource: any[]
  params: any
  pagination: {
    current: number
    pageSize: number
    total: number
    showSizeChanger: boolean
    showQuickJumper: boolean
    pageSizeOptions: string[]
  }
  loading: boolean
  selectedRowKeys: any[]
  sorter: {
    field?: string
    order?: 'ascend' | 'descend'
  }
}

// 表格配置选项
interface UseTableOptions {
  // 初始查询参数
  params?: any
  // 获取数据的API函数
  getList: (params: any) => Promise<{ err?: any; data?: any }>
  // 自定义参数处理函数
  getParams?: (params: any) => any
  // 分页配置 - 可以设置为 false 禁用分页
  pagination?: {
    current?: number
    pageSize?: number
    showSizeChanger?: boolean
    showQuickJumper?: boolean
    pageSizeOptions?: string[]
  } | false
  // 是否启用分页
  usePagination?: boolean
  // 是否启用行选择
  useRowSelection?: boolean
  // 是否启用排序
  useSorter?: boolean
  // 数据字段映射
  dataFields?: {
    list?: string // 数据列表字段名，默认 'list' 或 'dataList'
    total?: string // 总数字段名，默认 'total'
  }
}

export const useTable = (options: UseTableOptions) => {
  const {
    params: optParams = {},
    getList: optGetList,
    getParams,
    pagination: paginationOptions = {},
    usePagination = true,
    useRowSelection = false,
    useSorter = false,
    dataFields = {}
  } = options

  // 如果 pagination 设置为 false，则禁用分页
  const enablePagination = paginationOptions !== false && usePagination

  // 表格状态
  const state = reactive<TableState>({
    dataSource: [],
    params: {},
    pagination: {
      current: 1,
      pageSize: 10,
      total: 0,
      showSizeChanger: true,
      showQuickJumper: true,
      pageSizeOptions: ['10', '20', '50', '100'],
      ...(typeof paginationOptions === 'object' ? paginationOptions : {})
    },
    loading: false,
    selectedRowKeys: [],
    sorter: {}
  })

  // 保存原始参数
  const cachedParamsJSON = JSON.stringify(optParams)
  state.params = JSON.parse(cachedParamsJSON)

  // 分页配置计算属性
  const pagination = computed(() => {
    if (!enablePagination) return false
    return {
      current: state.pagination.current,
      pageSize: state.pagination.pageSize,
      total: state.pagination.total,
      showSizeChanger: state.pagination.showSizeChanger,
      showQuickJumper: state.pagination.showQuickJumper,
      pageSizeOptions: state.pagination.pageSizeOptions,
      showTotal: (total: number, range: [number, number]) =>
        `共 ${total} 条记录，第 ${range[0]}-${range[1]} 条`
    }
  })

  // 行选择配置
  const rowSelection = computed(() => {
    if (!useRowSelection) return undefined
    return {
      selectedRowKeys: state.selectedRowKeys,
      onChange: (keys: any[]) => {
        state.selectedRowKeys = keys
      },
      onSelectAll: (_selected: boolean, _selectedRows: any[], _changeRows: any[]) => {
        // 可以在这里添加全选逻辑
      },
      onSelect: (_record: any, _selected: boolean, _selectedRows: any[]) => {
        // 可以在这里添加单选逻辑
      }
    }
  })

  // 获取格式化的查询参数
  const getParamsData = (inputParams?: any) => {
    let fullParams = Object.assign(
      {},
      // 分页参数
      enablePagination ? {
        pageNum: state.pagination.current,
        pageSize: state.pagination.pageSize
      } : {},
      // 排序参数
      useSorter && state.sorter.field ? {
        sort_field: state.sorter.field,
        sort: state.sorter.order === 'ascend' ? 'asc' : 'desc'
      } : {},
      // 查询参数
      inputParams || state.params
    )

    // 使用自定义参数处理函数
    if (typeof getParams === 'function') {
      fullParams = getParams(fullParams)
    }

    return fullParams
  }

  // 获取表格数据
  const getTableData = async (params?: any) => {
    if (typeof optGetList !== 'function') {
      return Promise.reject('getList is undefined')
    }

    state.loading = true
    const formattedParams = getParamsData(params)

    try {
      const { err, data } = await optGetList(formattedParams)
      state.loading = false

      if (err) {
        console.error('获取表格数据失败:', err)
        return
      }

      // 根据配置获取数据列表和总数
      const listField = dataFields.list || 'dataList'
      const totalField = dataFields.total || 'total'
      
      const items = data?.[listField] || data?.list || []
      const total = data?.[totalField] || data?.total || 0

      state.dataSource = items
      if (enablePagination) {
        state.pagination.total = Number(total)
      }

      return data
    } catch (error) {
      state.loading = false
      console.error('获取表格数据异常:', error)
    }
  }

  // 搜索（从第一页开始）
  const onSearch = (params?: any) => {
    if (enablePagination) {
      state.pagination.current = 1
    }
    return getTableData(params)
  }

  // 重置查询参数
  const onReset = () => {
    state.params = JSON.parse(cachedParamsJSON)
    state.selectedRowKeys = []
    state.sorter = {}
    if (enablePagination) {
      state.pagination.current = 1
    }
  }

  // 表格变化处理（分页、排序、筛选）
  const onTableChange = (pag: any, _filters: any, sorter: any) => {
    // 处理分页
    if (enablePagination && pag) {
      state.pagination.current = pag.current
      state.pagination.pageSize = pag.pageSize
    }

    // 处理排序
    if (useSorter && sorter) {
      state.sorter = {
        field: sorter.field,
        order: sorter.order
      }
    }

    // 重新获取数据
    return getTableData()
  }

  // 刷新当前页数据
  const refresh = () => {
    return getTableData()
  }

  // 清空选择
  const clearSelection = () => {
    state.selectedRowKeys = []
  }

  // 设置选中行
  const setSelectedRowKeys = (keys: any[]) => {
    state.selectedRowKeys = keys
  }

  return {
    // 状态
    state,
    
    // 计算属性
    pagination,
    rowSelection,
    
    // 方法
    getTableData,
    onSearch,
    onReset,
    onTableChange,
    refresh,
    clearSelection,
    setSelectedRowKeys,
    getParamsData
  }
}
