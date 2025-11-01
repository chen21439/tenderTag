import { Clock2,Clock, CheckCircle2, RefreshCw, CircleAlert, CircleX, Loader, CircleCheck } from 'lucide-vue-next'
import { CloseCircleOutlined, CheckCircleOutlined } from '@ant-design/icons-vue'

// ==================== 审查状态相关配置 ====================

/**
 * 审查状态选项
 */
export const statusOptions = [
  { label: '发现风险', value: 11 },
  { label: '未发现风险', value: 10 },
  { label: '排队中', value: 0 },
  { label: '解析中', value: 3 },
  { label: '审查中', value: 1 },
  { label: '审查失败', value: -1 },
  // {label: '审查完成', value: 2},
]

/**
 * 风险选项配置
 */
export const riskOptions = [
  { label: '未发现风险', value: 0, color: 'default' },
  { label: '发现风险', value: 1, color: 'red' }
]

/**
 * 获取审查状态样式配置
 */
export const getStatusStyle = (status: number) => {
  const statusConfig = {
    0: { // 待审查
      color: '#000000',
      text: '排队中        ',
      icon: Clock
    },
    1: { // 审查中
      color: '#133CE8',
      text: '审查中',
      icon: RefreshCw
    },
    2: { // 审查完成
      style: {
        backgroundColor: 'rgba(78, 171, 12, 0.1)',
        borderColor: 'rgba(78, 171, 12, 0.2)',
        color: '#4EAB0C'
      },
      text: '审查完成',
      icon: CheckCircle2
    },
    3: { // 解析中
      color: '#000000',
      text: '解析中',
      icon: Clock2
    },
    '-1': { // 审查失败
      color: '#EF4444',
      text: '审查失败',             
      icon: CircleX
    }
  }
  return statusConfig[status as keyof typeof statusConfig] || statusConfig[3]
}

/**
 * 获取风险状态样式配置
 */
export const getRiskStyle = (status: number) => {
  const statusConfig = {
    0: { // 无风险
      color: '#52C41A',
      text: '未发现风险',
      icon: CircleCheck,
      className: 'safe'
    },
    1: { // 有风险
      color: '#F5222D',
      text: '发现风险',
      icon: CircleAlert,
      className: 'risk'
    },
    2: { // 不适用
      color: '#374151',
      text: '不适用',
      icon: Loader,
      className: 'not-use'
    },
    '-1': { // 审查中
      color: '#133CE8',
      text: '审查中',
      icon: RefreshCw,
      className: 'processing'
    }
  }
  return statusConfig[status as keyof typeof statusConfig] || {}
}
/**
 * 获取option对象
 */
export const getOptionsMap =(options: any[], key: string)=> {
  return options.find(p=> p.value === key || p.code === key) ?? {}
}
// ==================== 文件相关配置 ====================

/**
 * 获取文件图标
 */
export const getFileIcon = (fileName: string) => {
  const extension = fileName.split('.').pop()?.toLowerCase()
  let fileIcon = 'pdf-fill'
  switch (extension) {
    case 'DOCX':
    case 'DOC':
    case 'doc':
    case 'docx':
      fileIcon = 'docx-fill'
      break
    default:
      break
  }
  return `icon-${fileIcon}`
}

/**
 * 获取上传文件状态图标
 */
export const getStatusIcon = (status: string) => {
  const statusConfig = {
    uploading: {
      icon: RefreshCw,
      text: '上传中'
    },
    done: {
      icon: CheckCircleOutlined,
      text: '上传成功'
    },
    error: {
      icon: CloseCircleOutlined,
      text: '上传失败'
    }
  }
  return statusConfig[status as keyof typeof statusConfig] || statusConfig.done
}

// ==================== 合规审查页面配置 ====================

/**
 * 骨架屏配置
 */
export const SKELETON_CONFIG = {
  categories: [
    { name: '资格公平性检查', itemCount: 3 },
    { name: '需求公平、合理性检查', itemCount: 4 },
    { name: '评审规则公平、合理性检查', itemCount: 2 }
  ]
}

/**
 * 筛选标签配置生成器
 */
export const createFilterTabs = (statsData: any) => [
  { key: null, label: '全部', count: statsData.totalNum },
  { key: 1, label: '发现风险', count: statsData.resultNum },
  { key: 0, label: '未发现风险', count: statsData.passNum  },
  { key: 2, label: '不适用', count: statsData.noUseNum }
]

/**
 * 默认审查结果数据结构
 */
export const DEFAULT_REVIEW_RESULT = {
  fileId: '',
  finalFileId: '', // 显示文件ID
  fileName: '', // 文件名称
  reviewTime: '', // 审核时间
  dataList: [], // 数据列表
  stats: [], // 统计信息
  resultFinishNum: 0,
  reviewResult: undefined,
}
/**
 * 导出选项配置
 */ 
export const exportOptionsList = [
  { key: 'original', label: '采购文件(原始)', fileType: 'procurement_original' },
  { key: 'annotated', label: '采购文件(批注版)', fileType: 'procurement_revised' },
  { key: 'report', label: '审查风险报告', fileType: 'risk_report' }
]

// ==================== 文档库页面配置 ====================

/**
 * 表格列配置
 */
export const TABLE_COLUMNS = [
  // {
  //   title: '序号',
  //   dataIndex: 'index',
  //   fixed: 'left',
  //   width: 80,
  //   customRender: (row: any) => row.index + 1
  // },
  {
    title: '采购项目名称/编号',
    dataIndex: 'projectInfo',
    ellipsis: true
  },
  { title: '文件名称', dataIndex: 'fileName', ellipsis: true },
  { title: '审查结果', dataIndex: 'reviewStatus', width: '20%'},
  { title: '创建人', dataIndex: 'createUserName', width: '10%' ,minWidth: 130},
  { title: '创建时间', dataIndex: 'createTime', width: 200},
  { title: '操作', dataIndex: 'handle', width: '10%', minWidth: 100, fixed: 'right' }
]

/**
 * 默认分页配置
 */
export const DEFAULT_PAGINATION = {
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number, range: [number, number]) =>
    `共 ${total} 条记录，显示 ${range[0]}-${range[1]} 条`,
  pageSizeOptions: ['10', '20', '50', '100'],
  showLessItems: true
}

/**
 * 默认仪表板数据
 */
export const DEFAULT_DASHBOARD_DATA = {
  totalCount: 0,        // 审查文件总量
  riskFoundCount: 0,    // 发现风险文件数量
  noRiskCount: 0,       // 未发现风险文件数量
  pendingCount: 0,      // 处理中任务数量
  errorCount: 0         // 审查失败任务数量
}

/**
 * 默认表单数据
 */
export const DEFAULT_FORM_DATA = {
  fileName: '',
  reviewStatus: undefined as number | undefined,
  reviewResult: undefined as number | undefined
}

// ==================== 规则管理页面配置 ====================

/**
 * 规则状态选项
 */
export const RULE_STATUS_OPTIONS = [ 
  { label: '已启用', value: 1 },
  { label: '已禁用', value: 0},
  // { label: '草稿', value: 2}
]

/**
 * 规则管理表格列配置
 */
export const RULE_TABLE_COLUMNS = [
  {
    title: '规则名称',
    dataIndex: 'name',
    ellipsis: true
  },
  {
    title: '标签',
    dataIndex: 'lableList'
  },
  {
    title: '风险级别',
    dataIndex: 'violationLevelName',
    width: '12%'
  },
  {
    title: '启用状态',
    dataIndex: 'status',
    width: '10%'
  },
  {
    title: '最近修改',
    dataIndex: 'lastModified',
    width: '12%'
  },
  {
    title: '操作',
    dataIndex: 'actions',
    width: '15%',
    fixed: 'right'
  }
]


/**
 * 阈值标记
 */
export const thresholdMarks = {
  0: '0%',
  60: {
    style: {
      color: 'var(--error-6)' 
    } ,
    label: '60%'
  },
  75: {
    style: {
      color: 'var(--main-6)' 
    },
    label: '75%(推荐)'
  },
  100: '100%'
} 

export const getLevel = (status: string) => {
  const statusConfig = {
    low: {
      color: 'processing',
      text: '低'
    },
    medium: {
      color: 'warning',
      text: '中'
    },
    high: {
      color: 'error',
      text: '高'
    }
  }
  return statusConfig[status as keyof typeof statusConfig] || {
    color: 'default',
    text: '未知'
  }
}