/**
 * 格式化文件大小
 * @param bytes 文件大小，单位为字节
 * @returns 格式化后的文件大小字符串
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'

  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  if (i === 0) {
    // 字节数直接显示，不带小数
    return bytes + ' B'
  }

  const size = bytes / Math.pow(k, i)

  // 根据大小决定小数位数
  if (size >= 100) {
    // 大于等于100时，不显示小数位
    return Math.round(size) + ' ' + sizes[i]
  } else if (size >= 10) {
    // 10-99之间，显示1位小数
    return size.toFixed(1) + ' ' + sizes[i]
  } else {
    // 小于10时，显示2位小数
    return size.toFixed(2) + ' ' + sizes[i]
  }
}