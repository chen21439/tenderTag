/**
 * DocumentReader 组件入口文件
 */

import DocumentReader from './index.vue'
import type { 
  DocumentReaderProps, 
  DocumentReaderEvents,
  DocumentData,
  ParsedDocumentData,
  DocumentElement,
  TocItem,
  ZoomConfig,
  PaginationConfig,
  RenderOptions
} from './types'

// 导出组件
export default DocumentReader

// 导出类型
export type {
  DocumentReaderProps,
  DocumentReaderEvents,
  DocumentData,
  ParsedDocumentData,
  DocumentElement,
  TocItem,
  ZoomConfig,
  PaginationConfig,
  RenderOptions
}

// 导出工具函数
export {
  parseDocumentData, 
  processTableHtml, 
  searchDocumentContent,
  highlightSearchKeyword,
  getElementClassName, 
} from './doc-utils'
