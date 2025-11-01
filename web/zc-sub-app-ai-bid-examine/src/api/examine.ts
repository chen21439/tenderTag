import { http } from '@/services/http'

/** 单文件上传 */
export const fileUpload = (data: any,config) => http({
  url: '/file/v1/upload',
  data,
  method: 'post',
  headers: {
    'Content-Type': 'multipart/form-data'
  },
  ...config
})

/**
 * 审查点分类接口
 */
export const apiGetReviewItemTypeList = () => http({
  url: '/compliance/v1/reviewItemType/list',
  method: 'post'
})

/**
 * 审查点分类接口
 */
export const apiGetCheckPointPage = (data: any) => http({
  url: '/compliance/v1/checkPoint/page',
  method: 'post',
  data
})

/**
 * 启用审查点
 */
export const apiCheckPointEnable = (data: { pointId: string }) => http({
  url: '/compliance/v1/checkPoint/enable',
  method: 'post',
  data
})

/**
 * 禁用审查点
 */
export const apiCheckPointDisable = (data: { pointId: string }) => http({
  url: '/compliance/v1/checkPoint/disable',
  method: 'post',
  data
})

/**
 * 查看审查点
 */
export const apiCheckPointDetail = (data: { pointId: string }) => http({
  url: '/compliance/v1/checkPoint/detail',
  method: 'post',
  data
})

/**
 * 审查点编辑
 */
export const apiCheckPointEdit = (data: { pointId: string, pointName: string, status: number }) => http({
  url: '/compliance/v1/checkPoint/edit',
  method: 'post',
  data
})

/**
 * 审查任务列表
 */
export const apiTaskList = (
  data: {
    pageNum: number,
    pageSize: number,
    fileName?: string,
    reviewStatus?: number,
    reviewResult?: number
  }
) => http({
  url: '/compliance/v1/task/page',
  method: 'post',
  data
})

/**
 * 删除审查任务
 */
export const apiTaskDelete = (data: { taskId: string }) => http({
  url: '/compliance/v1/task/delete',
  method: 'post',
  data
}) 
/**
 * 开始审查
 */
export const apiTaskCreate = (data: { fileIdList: string[] }) => http({
  url: '/compliance/v1/task/review',
  method: 'post',
  data
})

/**
 * 获取评审结果
 */
export const apiTaskResult = (data: { taskId: string }) => http({
  url: '/compliance/v1/task/review/result',
  method: 'post',
  data
})

/**
 * 审查结果-查看审查点
 */
export const apiReviewCheckPointDetail = (data: { taskId: string }) => http({
  url: '/compliance/v1/task/review/checkPoint/detail',
  method: 'post',
  data
})

/**
 * 获取文件
 */
export const apiGetFile = (fileId: string) => http({
  url: '/file/v1/getById?fileId='.concat(fileId)
})

/**
 * 审查内容批注打标
 */
export const apiReviewResultMark = (data: { resultId: string, markDesc: string,status?:string|number }) => http({
  url: '/compliance/v1/task/review/result/mark',
  method: 'post',
  data
})

/**
 * 审查内容取消忽略
 */
export const apiReviewResultIgnore = (data: { resultId: string }) => http({
  url: '/compliance/v1/task/review/result/ignore',
  method: 'post',
  data
})
/**
 * 查询审查内容的批注打标
 */
export const apiGetMark = (data: { resultId: string }) => http({
  url: '/compliance/v1/task/review/result/getMark',
  method: 'post',
  data
})
/**
 * 获取数据看板统计信息
 */
export const taskDashboard = (data: { startTime: string, endTime: string }) => http({
  url: '/compliance/v1/task/dashboard',
  method: 'post',
  data
})  
/**
 * 撤回审查结果的原文修订接口
 */
export const resultMarkClear = (data: { resultId: string}) => http({
  url: '/compliance/v1/task/review/result/markClear',
  method: 'post',
  data
})  
/**
 * 审查清单接口
 */
export const checkSceneDetail = (data: { taskId: string}) => http({
  url: '/compliance/v1/task/checkScene/detail',
  method: 'post',
  data
})  
/**
 * 审查清单接口
 */
export const reviewAgain = (data: { taskId: string,sceneIdList: string[] }) => http({
  url: '/compliance/v1/task/review/again',
  method: 'post',
  data
})  
/**
 * 历史文件接口
 */
export const taskHistory = (data: { pageNum: number,pageSize: number }) => http({
  url: '/compliance/v1/task/history',
  method: 'post',
  data
})  
/**
 * 点赞或点踩接口
 */
export const reviewResultLike = (data: { uniqueId: string,taskId: string,actionType: number | undefined,isRisk:number, feedbackReason?: string | undefined,
  otherOpinion?: string | undefined}) => http({
  url: '/compliance/v1/task/review/result/like',
  method: 'post',
  data
})  
/**
 * 点赞或点踩详情接口
 */
export const reviewResultLikeDetail = (data: { uniqueId: string,taskId: string}) => http({
  url: '/compliance/v1/task/review/result/likeDetail',
  method: 'post',
  data
})  
/**
 * 审查结果接口
 */
export const getTaskReview = (data: { taskId: string,reviewResult: number | null }) => http({
  url: '/compliance/v1/task/review/list',
  method: 'post',
  data
})   
/**
 * 修订风险点的修订建议接口
 */
export const updateSuggestion = (data: { resultId: string,revisionSuggestion: string }) => http({
  url: '/compliance/v1/task/review/result/updateSuggestion',
  method: 'post',
  data
}) 
/**
 * 获取审查任务简单数据
 */
export const complianceTaskGetOne = (data: { taskId: string}) => http({
  url: '/compliance/v1/task/getOne',
  method: 'post',
  data
})

// ==================== 规则管理相关接口 ====================

/**
 * 获取规则列表
 */
export const apiRuleList = (data: {
  pageNum: number
  pageSize: number
  keyword?: string
  category?: string
  violationLevel?: string
  status?: number 
}) => http({
  url: '/compliance/v1/rules/page',
  method: 'post',
  data
})

/**
 * 创建规则
 */
export const apiRuleSaveOrUpdate = (data: {
  id?:string,
  name: string 
  violationLevel: string
  threshold:string
  categoryList: string[]
  status: number 
}) => http({
  url: '/compliance/v1/rules/saveOrUpdate',
  method: 'post',
  data
}) 
 
/**
 * 启用/停用规则
 */
export const updateStatus = (data: { ruleId: string, status: number }) => http({
  url: '/compliance/v1/rules/updateStatus',
  method: 'post',
  data
})

/**
 * 规则测试
 */
export const apiRuleTest = (data: {
  ruleId: string
  testText?: string 
}) => http({
  url: '/compliance/v1/rules/test',
  method: 'post',
  data
})

/**
 * 获取规则相关字典数据
 */
export const apiRulesDict = () => http({
  url: '/compliance/v1/rules/dict',
  method: 'post'
})

/**
 * 获取规则统计概览
 */
export const ruleStatistics = () => http({
  url: '/compliance/v1/rules/statistics',
  method: 'post'
})

/**
 * 根据任务ID获取md信息
 */
export const taskMarkDownDetail = (data: { taskId: string }) => http({
  url: '/compliance/v1/task/markDownDetail',
  method: 'post',
  data
})

/**
 * 审查提示列表接口
 */
export const reviewTipList = (data: { taskId: string }) => http({
  url: '/compliance/v1/task/review/tipList',
  method: 'post',
  data
})

/**
 * 创建打包任务
 */
export const createPackageFiles = (data: { fileTypes: string[], taskId:string }) => http({
  url: '/compliance/v1/task/review/createPackageFiles',
  method: 'post',
  data
})

/**
 * 创建打包任务
 */
export const exportTask = (dexportTaskId: string) => http({
  url: `/compliance/v1/task/review/exportTask/${dexportTaskId}`,
  method: 'get'
})

/**
 * 获取本地任务列表
 * 开发模式：从本地 server 读取
 * 生产模式：从 public 目录读取
 */
export const getLocalTaskList = async () => {
  try {
    // 判断是否为开发环境
    const isDev = import.meta.env.VITE_ENV === 'dev'
    const baseUrl = import.meta.env.VITE_APP_PUBLIC_URL || ''
    const url = isDev
      ? 'http://localhost:3000/api/task-list'
      : `${baseUrl}/task/taskList.json`

    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    return await response.json()
  } catch (error) {
    console.error('Failed to load local task list:', error)
    throw error
  }
}