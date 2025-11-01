/**
 * 文档阅读器相关类型定义
 */

// 内容类型枚举
export enum ContentType {
  PARAGRAPH = 'paragraph',
  TABLE = 'table',
  IMAGE = 'image'
}

// 段落子类型枚举
export enum ParagraphSubType {
  CATALOG = 'catalog',
  HEADER = 'header',
  FOOTER = 'footer',
  SIDEBAR = 'sidebar',
  TEXT = 'text',
  TEXT_TITLE = 'text_title',
  IMAGE_TITLE = 'image_title',
  TABLE_TITLE = 'table_title'
}

// 图片子类型枚举
export enum ImageSubType {
  STAMP = 'stamp',
  CHART = 'chart',
  QRCODE = 'qrcode',
  BARCODE = 'barcode'
}

// 表格子类型枚举
export enum TableSubType {
  BORDERED = 'bordered',
  BORDERLESS = 'borderless'
}

// 标题级别枚举
export enum OutlineLevel {
  CONTENT = -1,  // 正文
  LEVEL_1 = 0,   // 一级标题
  LEVEL_2 = 1,   // 二级标题
  LEVEL_3 = 2,   // 三级标题
  LEVEL_4 = 3,   // 四级标题
  LEVEL_5 = 4    // 五级标题
}

// 位置坐标类型 [左上x, 左上y, 右上x, 右上y, 右下x, 右下y, 左下x, 左下y]
export type Position = [number, number, number, number, number, number, number, number]



// 表格单元格接口
export interface TableCell {
  col: number
  col_span: number
  position: Position
  row: number
  row_span: number
  text: string
  type: 'cell'
  page_id: number  // 添加页面ID字段
}

// 印章识别结果接口
export interface StampInfo {
  value: string
  stamp_shape: string
  type: string
  color: string
}

// 标题ID接口
export interface CaptionId {
  [key: string]: any
}

// 拆分信息接口
export interface SplitInfo {
  total_parts: number
  current_part: number
  original_page: number
  is_table_split?: boolean
  original_row_count?: number
  page_row_range?: [number, number] 
  has_header?: boolean
}

// 文档元素基础接口
export interface DocumentElement {
  page_id: number
  paragraph_id: number | string
  outline_level: OutlineLevel
  text: string
  type: ContentType
  position: Position
  tags: string[]
  content?: number
  origin_position?: Position
  sub_type?: ParagraphSubType | ImageSubType | TableSubType
  image_url?: string
  caption_id?: CaptionId
  cells?: TableCell[]
  split_section_page_ids?: number[]
  split_section_positions?: Position[]
  stamp?: StampInfo
  split_info?: SplitInfo
}

// 文档数据接口
export interface DocumentData {
  fileId: string
  markDownDetail: string | DocumentElement[]
}

// 解析后的文档数据接口
export interface ParsedDocumentData {
  fileId: string
  elements: DocumentElement[]
  pages: Map<number, DocumentElement[]>
  totalPages: number
}

// 目录项接口
export interface TocItem {
  id: string
  title: string
  level: OutlineLevel
  pageId: number
  paragraphId: number | string
  children?: TocItem[]
}

// 缩放配置接口
export interface ZoomConfig {
  current: number
  min: number
  max: number
  step: number
  fitWidth: boolean
  fitHeight: boolean
}

// 分页配置接口
export interface PaginationConfig {
  current: number
  total: number
  pageSize: number
  showSizeChanger: boolean
  showQuickJumper: boolean
}

// 组件Props接口
export interface DocumentReaderProps {
  data: DocumentData | ParsedDocumentData
  height?: string | number
  width?: string | number
  showToc?: boolean
  showToolbar?: boolean
  showPagination?: boolean
  initialZoom?: number
  enableVirtualScroll?: boolean
  pageSize?: number
  tocWidth?: number
  toolbarHeight?: number
}

// 组件事件接口
export interface DocumentReaderEvents {
  'page-change': [page: number]
  'zoom-change': [zoom: number]
  'toc-item-click': [item: TocItem]
  'element-click': [element: DocumentElement]
}

// 渲染选项接口
export interface RenderOptions {
  enableSelection: boolean
  enableCopy: boolean
  highlightSearch: boolean
  searchKeyword?: string
}

// 虚拟滚动配置接口
export interface VirtualScrollConfig {
  enabled: boolean
  itemHeight: number
  bufferSize: number
  threshold: number
}

// 性能配置接口
export interface PerformanceConfig {
  lazyLoad: boolean
  virtualScroll: VirtualScrollConfig
  cacheSize: number
  preloadPages: number
}
