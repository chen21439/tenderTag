import { reactive } from 'vue'
interface ListState {
  list: any[]
  params: any
  pages: {
    total: number
    pageNum: number
    pageSize: number
    pageSizes: number[]
  };
  loading: boolean
  useOptimizeRender: boolean
  usePagination: boolean
}

export const useList = (options: any = {}) => {
  const {
    params: optParams,
    getList: optGetList,
    getParams,
    pages,
    usePagination,
    useOptimizeRender
  } = options;

  const state = reactive<ListState>({
    list: [],
    params: {},
    pages: { total: 0, pageNum: 1, pageSize: 10, pageSizes: [10, 20, 30, 40, 50] },
    loading: false,
    useOptimizeRender: useOptimizeRender === true,
    usePagination: usePagination !== false
  });
  // 保存原始params数据
  const cachedParamsJSON = JSON.stringify(optParams || {})
  state.params = JSON.parse(cachedParamsJSON)
  Object.assign(state.pages, pages || {})
  // optimize加载
  const optimize = useOptimize()

  // 通过setList 优化加载
  const setList = (list: any[]) => {
    if (!list || !list.length) {
      state.list = []
      return
    }
    if (state.useOptimizeRender) {
      optimize.doOptimize(list, (_list: any[], i: number) => {
        if (i === 0) state.list = _list
        else state.list.push(..._list)
      });
    } else {
      state.list = list
    }
  };

  // 查询接口
  const getList = async (params?: any) => {
    if (typeof optGetList !== 'function') {
      return Promise.reject('getList is undefined')
    }
    state.loading = true;
    const formattedParamsData = getParamsData(params)
    try {
      const { err, data } = await optGetList(formattedParamsData)
      state.loading = false
      if (err) return
      const items = data.list || data.reviewList || []
      const total = data. total || 0
      setList(items)
      if (state.usePagination) state.pages.total = Number(total)
      return data
    } catch (e) {
      state.loading = false
    }
  }

  // 从第一页开始查询
  const onSearch = () => {
    state.pages.pageNum = 1
    getList()
  }

  // 重置查询参数
  const onReset = () => {
    state.params = JSON.parse(cachedParamsJSON)
  }

  // 分页改变
  const onPageChange = (pg: number) => {
    state.pages.pageNum = pg
    getList()
  };
  // 显示页码变化
  const onSizeChange = (pg:number, size: number) => {
    state.pages.pageNum = pg
    state.pages.pageSize = size
    getList()
  }
  // 获取查询参数
  function getParamsData(inputParams?: any) {
    let fullParams = Object.assign(
      state.usePagination
        ? { pageNum: state.pages.pageNum, pageSize: state.pages.pageSize }
        : {},
      inputParams || state.params
    )
    // 使用定制函数处理参数
    if (typeof getParams === 'function') fullParams = getParams(fullParams)
      const { pageSize, pageNum, sort_field, sort, ...data } = fullParams
      const params = { pageSize, pageNum, sort_field, sort }
      return  {...params,...data }
    }
  return { state, getList, setList, onSearch, onReset, onPageChange, onSizeChange, getParams: getParamsData }
};

// 优化策略
const useOptimize = (opts: any = {}) => {
  const { min: _min, max: _max } = opts
  const initLength = 10
  const min = _min || 10
  const max = _max || 20
  let oid = 0
  const doOptimize = async (sourceList: any[], cb: any) => {
    const nid = (oid = oid + 1)
    let i = 0 // 执行次数, 通常需要判断是否是第一次
    let _source = sourceList || []
    if (_source.length < min) {
      if (typeof cb === 'function') cb(_source, i)
      i++
      return
    }
    let l = initLength;
    do {
      if (nid !== oid) break
      // 第一次不延时
      if (typeof cb === 'function') cb(_source.slice(0, l), i)
      i++
      _source = _source.slice(l)
      if (l < max) l += 2 // 优化加速, 可根据具体情况设置超过多次后 一次加载完
      if (_source.length && nid === oid) await sleep()
    } while (_source.length && nid === oid)
  };

  const sleep = (ms = 60) => new Promise((r) => setTimeout(r, ms));

  return {
    doOptimize
  }
}
