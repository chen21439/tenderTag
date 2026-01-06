/**
 * 去除 _infer 后缀，获取原始文件名
 */
export const getBaseFileName = (fileName: string): string => {
  return fileName.replace(/_infer\.json$/i, '.json')
}

/**
 * 添加 _infer 后缀
 */
export const getInferFileName = (fileName: string): string => {
  if (fileName.includes('_infer.json')) {
    return fileName
  }
  return fileName.replace(/\.json$/i, '_infer.json')
}

/**
 * 检查文件名是否是推理后版本
 */
export const isInferVersion = (fileName: string): boolean => {
  return fileName.includes('_infer.json')
}
