import { downLoadHttp  as http } from '@/services/http'


/**
* 切片文件下载
*/
export const apiDownRefs = (fileId: string) => http({
  url: '/file/v1/downRefsDocument?fileId='.concat(fileId),
  timeout: 600000
})

/**
 * 文件下载
 */
export const apiDownload = (fileId: string) => http({
  url: '/file/v1/download?fileId='.concat(fileId),
  timeout: 60 * 1000
})

/**
 * 导出审查报告
 */
export const apiReviewImport = (data: { taskId: string }) => http({
  url: '/compliance/v1/task/review/import',
  method: 'post',
  data
})

/** 修订文件导出接口 */
export const commentedFile = (data: { taskId: string }) => http({
  url: '/compliance/v1/task/review/commentedFile',
  method: 'post',
  data
}) 
/** 多个招标文件上传接口(复用) */
export const uploadMulti = (data: { files: string[] }) => http({
  url: '/file/v1/uploadMulti',
  method: 'post',
  data
}) 

/** 导出打包后的文件 */
export const customDocumentBundleExport = (data: { fileTypes: string[], taskId:string }) => http({
  url: '/compliance/v1/task/review/customDocumentBundleExport',
  method: 'post',
  data,
  timeout: 180000
}) 

/** 下载打包文件 */
export const downloadPackageFiles = (exportTaskId:string) => http({
  url: `/compliance/v1/task/review/downloadPackageFiles/${exportTaskId}`,
  method: 'get'
}) 