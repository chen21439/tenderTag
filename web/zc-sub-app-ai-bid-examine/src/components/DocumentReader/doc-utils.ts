/**
 * 文档阅读器工具函数
 *
 * 核心拆分逻辑：
 * 1. 基于position信息进行智能跨页表格拆分
 * 2. 通过分析单元格position的Y坐标判断页面边界
 * 3. 根据页脚position推测页面边界，实现精确切割
 * 4. 支持表格行完整性保护，确保同一行不被分割到不同页面
 */

import type {
  DocumentData,
  ParsedDocumentData,
  DocumentElement
} from './types'
import { ContentType } from './types'

/**
 * 解析文档数据
 */
export function parseDocumentData(data: DocumentData | ParsedDocumentData): ParsedDocumentData {
  // 如果已经是解析后的数据，直接返回
  if ('elements' in data && 'pages' in data && 'totalPages' in data) {
    return data as ParsedDocumentData
  }
  const docData = data as DocumentData
  let elements: DocumentElement[] = []

  // 处理不同格式的数据
  if (typeof docData.markDownDetail === 'string') {
    try {
      elements = JSON.parse(docData.markDownDetail)
    } catch (error) {
      console.error('Failed to parse markDownDetail string:', error)
      elements = []
    }
  } else if (Array.isArray(docData.markDownDetail)) {
    elements = docData.markDownDetail
  }

  // 处理跨页表格拆分
  elements = processTableSplitting(elements)

  // 按页面分组
  const pages = new Map<number, DocumentElement[]>()
  let totalPages = 0

  elements.forEach(element => {
    const pageId = element.page_id
    if (!pages.has(pageId)) {
      pages.set(pageId, [])
    }
    pages.get(pageId)!.push(element)
    totalPages = Math.max(totalPages, pageId)
  })

  // 对每页的元素按paragraph_id排序
  pages.forEach(pageElements => {
    pageElements.sort((a, b) => {
      const aId = typeof a.paragraph_id === 'string' ? parseInt(a.paragraph_id) : a.paragraph_id
      const bId = typeof b.paragraph_id === 'string' ? parseInt(b.paragraph_id) : b.paragraph_id
      return aId - bId
    })
  })

  // 移除空白页，但保留有内容的页面
  const filteredPages = new Map<number, DocumentElement[]>()
  pages.forEach((pageElements, pageId) => {
    // 过滤掉只有页脚的页面
    const contentElements = pageElements.filter(el => el.sub_type !== 'footer')
    if (contentElements.length > 0) {
      filteredPages.set(pageId, pageElements)
    }
  })

  const pageKeys = Array.from(filteredPages.keys())
  const finalTotalPages = pageKeys.length > 0 ? Math.max(...pageKeys) : 0

  return {
    fileId: docData.fileId,
    elements,
    pages: filteredPages,
    totalPages: finalTotalPages
  }
}

/**
 * 处理跨页元素拆分 - 主要处理函数
 */
function processTableSplitting(elements: DocumentElement[]): DocumentElement[] { 
  const processedElements: DocumentElement[] = []

  for (let i = 0; i < elements.length; i++) {
    const element = elements[i]
    
    // 检查是否需要拆分并计算拆分段数
    const splitInfo = analyzeSplitRequirement(elements, i)
    
    if (splitInfo.needsSplit) {
      if (element.type === ContentType.TABLE) {
        // 表格拆分
        const splitElements = splitTableByLogicalStructure(element, elements, i, splitInfo.totalParts)
        processedElements.push(...splitElements)
      } else {
        // 其他类型元素的跨页拆分
        const splitElements = splitElementByPages(element, elements, i, splitInfo.totalParts)
        processedElements.push(...splitElements)
      }
      
      // 跳过已经处理的元素（包括原始元素和后续的拆分段）
      i += splitInfo.totalParts - 1 
    } else {
      // 不需要拆分的元素直接添加
      processedElements.push(element)
    }
  } 
  return processedElements
}

/**
 * 分析元素是否需要拆分并计算拆分段数
 */
function analyzeSplitRequirement(elements: DocumentElement[], currentIndex: number): {needsSplit: boolean; totalParts: number} {
  const element = elements[currentIndex]
  const originalPageId = element.page_id
  const pageIds = new Set<number>([originalPageId])
  let foundSplitElements = false

  // 短文本长度阈值 - 小于此长度的文本不进行拆分
  const SHORT_TEXT_THRESHOLD = 50
  
  // 检查当前元素是否为短文本
  const isShortText = element.text && element.text.trim().length < SHORT_TEXT_THRESHOLD
  
  // 如果是短文本且不是表格，直接返回不拆分
  if (isShortText && element.type !== ContentType.TABLE) { 
    return { needsSplit: false, totalParts: 1 }
  }

  // 检查后续元素来判断是否需要拆分
  for (let i = currentIndex + 1; i < elements.length; i++) {
    const nextElement = elements[i]
    
    // 专门查找具有 sub_type==='footer' 属性的元素
    if (nextElement.sub_type==='footer') {
      // 获取前一个元素和后一个元素
      const prevElement = i > 0 ? elements[i - 1] : null
      const afterElement = i < elements.length - 1 ? elements[i + 1] : null
      
      // 条件1：前一个元素没有 sub_type==='footer' 且 page_id 与原始元素相同
      const condition1 = prevElement && 
                        !prevElement.sub_type && 
                        prevElement.page_id === originalPageId
      
      // 条件2：后一个元素有 sub_type 且 page_id 与原始元素不同
      const condition2 = afterElement && 
                        afterElement.sub_type==='footer' && 
                        afterElement.page_id !== originalPageId 
      
      // 只有同时满足两个条件且是表格或长文本才判定需要拆分
      if (condition1 && condition2 && 
          (prevElement?.type === ContentType.TABLE || 
           (prevElement?.type === ContentType.PARAGRAPH && !isShortText))) {
        foundSplitElements = true
        pageIds.add(nextElement.page_id)
        pageIds.add(afterElement.page_id)
        continue
      }
    }
    
    // 保持原有逻辑：如果遇到有sub_type==='footer'或者text为空的元素，说明是跨页元素的一部分
    if (nextElement.sub_type==='footer' || !nextElement.text?.trim()) {
      foundSplitElements = true
      pageIds.add(nextElement.page_id)
      continue
    }
    
    // 遇到没有sub_type且content不为空的元素，跨页元素结束
    break
  }

  // 判断是否需要拆分：有找到拆分元素且页面ID不唯一
  const needsSplit = foundSplitElements && pageIds.size > 1
  const totalParts = pageIds.size

  if (needsSplit) {
    console.log(`📊 需要拆分${element.type}元素，涉及页面: [${Array.from(pageIds).sort().join(', ')}]，总共${totalParts}个段`)
  }

  return { needsSplit, totalParts }
}

/**
 * 基于逻辑结构进行表格拆分
 */
function splitTableByLogicalStructure(
  element: DocumentElement, 
  elements: DocumentElement[], 
  currentIndex: number,
  totalParts: number
): DocumentElement[] { 
  console.log(`📊 开始基于position信息拆分表格，预期${totalParts}段`)

  // 收集所有相关的表格元素，按页面ID分组
  const tableElementsByPage = new Map<number, DocumentElement>()
  tableElementsByPage.set(element.page_id, element)
  
  for (let i = currentIndex + 1; i < elements.length; i++) {
    const nextElement = elements[i]
    if (nextElement.sub_type || !nextElement.text?.trim()) {
      tableElementsByPage.set(nextElement.page_id, nextElement)
      continue
    }
    break
  }

  const originalCells = element.cells || []
  if (originalCells.length === 0) {
    return [element]
  }

  // 获取所有涉及的页面ID并排序
  const pageIds = Array.from(tableElementsByPage.keys()).sort((a, b) => a - b)
  
  // 基于position和页面分布计算每个段的行数分配
  const rowDistribution = calculateRowDistributionByPagePosition(pageIds, tableElementsByPage, originalCells)
  
  const splitElements: DocumentElement[] = []
  let currentRowStart = 0

  pageIds.forEach((pageId, index) => {
    const tableElement = tableElementsByPage.get(pageId)!
    const rowCount = rowDistribution[index] || 0
    const rowEnd = currentRowStart + rowCount - 1

    // 获取该段的单元格
    const segmentCells = originalCells.filter(cell => 
      cell.row >= currentRowStart && cell.row <= rowEnd
    ).map(cell => ({
      ...cell,
      row: cell.row - currentRowStart, // 重新映射行号从0开始
      page_id: pageId
    }))

    // 构建表格HTML，第一段包含表头
    const segmentTableHtml = buildTableFromCells(segmentCells, index === 0)

    const splitElement: DocumentElement = {
      ...element,
      page_id: pageId,
      paragraph_id: `${element.paragraph_id}_segment_${index + 1}`,
      text: segmentTableHtml,
      position: tableElement.position || element.position,
      cells: segmentCells,
      split_info: {
        total_parts: totalParts,
        current_part: index + 1,
        original_page: element.page_id,
        is_table_split: true,
        page_row_range: [currentRowStart, rowEnd], 
        has_header: index === 0
      }
    }

    splitElements.push(splitElement)
    console.log(`📄 创建第${index + 1}段，页面${pageId}，行范围: ${currentRowStart}-${rowEnd}，单元格数: ${segmentCells.length}`)
    
    currentRowStart = rowEnd + 1
  })

  return splitElements
}

// 基于页面position计算行数分配
function calculateRowDistributionByPagePosition(
  pageIds: number[], 
  tableElementsByPage: Map<number, DocumentElement>, 
  originalCells: any[]
): number[] {
  const totalRows = Math.max(...originalCells.map(cell => cell.row)) + 1
  console.log(`📊 开始分析表格行分布，总行数: ${totalRows}，涉及页面: [${pageIds.join(', ')}]`)
  
  // 按行号分组，获取每行的Y坐标
  const rowYCoords = new Map<number, number>()
  
  originalCells.forEach(cell => {
    const y = cell.position[1] // 左上角Y坐标
    if (!rowYCoords.has(cell.row)) {
      rowYCoords.set(cell.row, y)
    }
  })
  
  // 按行号排序，分析Y坐标变化
  const sortedRows = Array.from(rowYCoords.entries()).sort(([a], [b]) => a - b)
  
  console.log('行Y坐标分析:')
  sortedRows.forEach(([row, y]) => {
    console.log(`  行${row}: Y=${y}`)
  })
  
  // 检测页面边界：基于Y坐标的突变
  const pageBreaks: number[] = [0] // 第一页从第0行开始
  
  for (let i = 1; i < sortedRows.length; i++) {
    const [currentRow, currentY] = sortedRows[i]
    const [prevRow, prevY] = sortedRows[i - 1]
    
    // 检测跨页：Y坐标从高值跳到低值（页面切换）
    // 或者Y坐标有大幅度跳跃
    const yDiff = prevY - currentY
    const isPageJump = yDiff > 1000 || (prevY > 2000 && currentY < 1000)
    
    if (isPageJump) {
      console.log(`📄 检测到页面跳跃：行${prevRow}(Y=${prevY}) -> 行${currentRow}(Y=${currentY})`)
      pageBreaks.push(currentRow)
    }
  }
  
  // 如果检测到的边界数量少于页面数，需要补充边界
  if (pageBreaks.length < pageIds.length) {
    console.log(`⚠️ 检测到${pageBreaks.length}个边界，但有${pageIds.length}个页面，需要补充边界`)
    
    // 寻找次级跳跃点
    const remainingRows = sortedRows.filter(([row]) => !pageBreaks.includes(row))
    
    for (let i = 1; i < remainingRows.length && pageBreaks.length < pageIds.length; i++) {
      const [currentRow, currentY] = remainingRows[i]
      const [prevRow, prevY] = remainingRows[i - 1]
      
      const yDiff = Math.abs(prevY - currentY)
      if (yDiff > 200) { // 降低阈值寻找次级边界
        console.log(`📄 添加次级边界：行${currentRow}，Y跳跃=${yDiff}`)
        pageBreaks.push(currentRow)
      }
    }
  }
  
  // 按行号排序边界点
  pageBreaks.sort((a, b) => a - b)
  
  // 确保边界数量正确
  while (pageBreaks.length > pageIds.length) {
    pageBreaks.pop()
  }
  
  // 计算每页的行数分配
  const distribution: number[] = []
  
  for (let i = 0; i < pageIds.length; i++) {
    const startRow = pageBreaks[i] || 0
    const endRow = pageBreaks[i + 1] || totalRows
    const rowCount = endRow - startRow
    distribution[i] = rowCount
    
    console.log(`📄 页面${pageIds[i]}：第${startRow}-${endRow-1}行，共${rowCount}行`)
  }
  
  console.log(`📊 最终行数分配: [${distribution.join(', ')}]`)
  
  // 如果分配结果明显不合理，使用基于实际数据的分配
  const totalAssigned = distribution.reduce((sum, count) => sum + count, 0)
  if (totalAssigned !== totalRows || distribution.some(count => count <= 0)) {
    console.warn(`⚠️ 分配结果异常，使用基于单元格分布的重新计算`)
    return calculateByActualCellDistribution(pageIds, originalCells, totalRows)
  }
  
  return distribution
}

// 基于实际单元格分布重新计算
function calculateByActualCellDistribution(pageIds: number[], originalCells: any[], totalRows: number): number[] {
  // 根据Y坐标范围将行分配到页面
  const pageRowMap = new Map<number, Set<number>>()
  
  pageIds.forEach(pageId => {
    pageRowMap.set(pageId, new Set())
  })
  
  originalCells.forEach(cell => {
    const y = cell.position[1]
    const row = cell.row
    
    // 根据Y坐标范围判断页面归属
    let targetPageIndex = 0
    
    if (y >= 2000) {
      targetPageIndex = 0 // 第一页
    } else if (y >= 1500) {
      targetPageIndex = Math.min(1, pageIds.length - 1)
    } else if (y >= 1000) {
      targetPageIndex = Math.min(2, pageIds.length - 1)
    } else if (y >= 500) {
      targetPageIndex = Math.min(Math.floor(pageIds.length / 2), pageIds.length - 1)
    } else {
      targetPageIndex = pageIds.length - 1 // 最后一页
    }
    
    const targetPageId = pageIds[targetPageIndex]
    pageRowMap.get(targetPageId)?.add(row)
  })
  
  const distribution = pageIds.map(pageId => {
    const rows = pageRowMap.get(pageId) || new Set()
    return rows.size
  })
  
  console.log(`📊 基于单元格分布的分配: [${distribution.join(', ')}]`)
  return distribution
}

/**
 * 基于单元格数据重建表格HTML
 */
export function buildTableFromCells(cells: any[], includeHeader: boolean = true): string {
  if (cells.length === 0) return ''

  // 按行分组单元格
  const rowMap = new Map<number, any[]>()
  cells.forEach(cell => {
    if (!rowMap.has(cell.row)) {
      rowMap.set(cell.row, [])
    }
    rowMap.get(cell.row)!.push(cell)
  })

  // 按行号排序
  const sortedRows = Array.from(rowMap.keys()).sort((a, b) => a - b)
  let tableHtml = '<table border="1">'

  sortedRows.forEach((rowIndex, index) => {
    const rowCells = rowMap.get(rowIndex)!
    // 按列号排序
    rowCells.sort((a, b) => a.col - b.col)

    // 第一行且包含表头时使用th标签
    const isHeaderRow = includeHeader && index === 0
    const cellTag = isHeaderRow ? 'th' : 'td'

    tableHtml += '<tr>'
    rowCells.forEach(cell => {
      const colspanAttr = cell.col_span > 1 ? ` colspan="${cell.col_span}"` : ''
      const rowspanAttr = cell.row_span > 1 ? ` rowspan="${cell.row_span}"` : ''

      const cellText = ensureCellTextIntegrity(cell.text)
      tableHtml += `<${cellTag}${colspanAttr}${rowspanAttr}>${cellText}</${cellTag}>`
    })
    tableHtml += '</tr>'
  })

  tableHtml += '</table>'
  return tableHtml
}

/**
 * 确保单元格文本的完整性
 */
function ensureCellTextIntegrity(text: string): string {
  if (!text) return ''

  // 清理和规范化文本
  return text.trim()
    .replace(/\s+/g, ' ') // 规范化空白字符
    .replace(/\n+/g, '<br>') // 保留换行
}
 

/**
 * 处理表格HTML内容
 */
export function processTableHtml(htmlContent: string): string {
  // 清理HTML内容，确保表格正确显示
  return htmlContent
    .replace(/\\"/g, '"')
    .replace(/\n/g, '')
    .trim()
}


 

/**
 * 搜索文档内容
 */
export function searchDocumentContent(elements: DocumentElement[], keyword: string): DocumentElement[] {
  if (!keyword.trim()) return []

  const searchTerm = keyword.toLowerCase()
  return elements.filter(element =>
    element.text.toLowerCase().includes(searchTerm)
  )
}

/**
 * 高亮搜索关键词
 */
export function highlightSearchKeyword(text: string, keyword: string): string {
  if (!keyword.trim()) return text

  const regex = new RegExp(`(${keyword})`, 'gi')
  return text.replace(regex, '<mark>$1</mark>')
}

/**
 * 获取元素的样式类名
 */
export function getElementClassName(element: DocumentElement): string {
  const classes = ['document-element', `element-${element.type}`]

  if (element.sub_type) {
    classes.push(`sub-type-${element.sub_type}`)
  }

  if (element.outline_level >= 0) {
    classes.push(`heading-level-${element.outline_level}`)
  }

  if (element.tags && element.tags.length > 0) {
    element.tags.forEach(tag => {
      classes.push(`tag-${tag}`)
    })
  }

  return classes.join(' ')
}

/**
 * 解析位置字符串为数组
 */
export function parsePosition(position: any): number[] {
  if (Array.isArray(position)) {
    return position
  }

  if (typeof position === 'string') {
    try {
      // 解析字符串格式的位置信息 "[191, 2044, 1609, 2044, 1609, 2327, 191, 2327]"
      const parsed = JSON.parse(position)
      return Array.isArray(parsed) ? parsed : []
    } catch (e) {
      console.warn('无法解析位置信息:', position)
      return []
    }
  }

  return []
}

/**
 * 通用的跨页元素拆分函数
 */
function splitElementByPages(
  element: DocumentElement,
  elements: DocumentElement[],
  currentIndex: number,
  totalParts: number
): DocumentElement[] {
  console.log(`📊 开始拆分${element.type}元素，预期${totalParts}段`)

  // 收集所有相关的元素，按页面ID分组
  const elementsByPage = new Map<number, DocumentElement>()
  elementsByPage.set(element.page_id, element)
  
  for (let i = currentIndex + 1; i < elements.length; i++) {
    const nextElement = elements[i]
    if (nextElement.sub_type === 'footer' || !nextElement.text?.trim()) {
      elementsByPage.set(nextElement.page_id, nextElement)
      continue
    }
    break
  }

  // 获取所有涉及的页面ID并排序
  const pageIds = Array.from(elementsByPage.keys()).sort((a, b) => a - b)
  const splitElements: DocumentElement[] = []

  // 如果只有一个页面，直接返回原元素
  if (pageIds.length === 1) {
    return [element]
  }

  // 智能文本拆分：基于句号、分号等标点符号进行拆分
  const originalText = element.text || ''
  const textParts = smartTextSplit(originalText, totalParts)

  pageIds.forEach((pageId, index) => {
    const pageElement = elementsByPage.get(pageId)!
    
    // 使用拆分后的文本内容，如果没有则使用原始文本
    const segmentText = textParts[index] || originalText
    
    const splitElement: DocumentElement = {
      ...element,
      page_id: pageId,
      paragraph_id: `${element.paragraph_id}_segment_${index + 1}`,
      text: segmentText,
      position: pageElement.position || element.position,
      split_info: {
        total_parts: totalParts,
        current_part: index + 1,
        original_page: element.page_id,
        is_table_split: false,
        text_segment: true
      }
    }

    splitElements.push(splitElement)
    console.log(`📄 创建第${index + 1}段，页面${pageId}，类型: ${element.type}，文本长度: ${segmentText.length}`)
  })

  return splitElements
}

/**
 * 智能文本拆分函数
 */
function smartTextSplit(text: string, parts: number): string[] {
  if (parts <= 1) return [text]
  
  // 优先按句号拆分
  let sentences = text.split(/[。！？；]/g).filter(s => s.trim())
  
  // 如果句子数量不够，按逗号拆分
  if (sentences.length < parts) {
    sentences = text.split(/[，、]/g).filter(s => s.trim())
  }
  
  // 如果还是不够，按字符长度平均拆分
  if (sentences.length < parts) {
    const avgLength = Math.ceil(text.length / parts)
    const result: string[] = []
    for (let i = 0; i < parts; i++) {
      const start = i * avgLength
      const end = Math.min((i + 1) * avgLength, text.length)
      if (start < text.length) {
        result.push(text.substring(start, end))
      }
    }
    return result
  }
  
  // 将句子分组到指定数量的段落中
  const result: string[] = []
  const sentencesPerPart = Math.ceil(sentences.length / parts)
  
  for (let i = 0; i < parts; i++) {
    const startIdx = i * sentencesPerPart
    const endIdx = Math.min((i + 1) * sentencesPerPart, sentences.length)
    
    if (startIdx < sentences.length) {
      const partSentences = sentences.slice(startIdx, endIdx)
      // 重新添加标点符号
      const partText = partSentences.map((s, idx) => {
        if (idx === partSentences.length - 1 && i === parts - 1) {
          // 最后一段的最后一句，保持原样
          return s
        }
        // 其他句子添加句号
        return s + (s.match(/[。！？；]$/) ? '' : '。')
      }).join('')
      
      result.push(partText)
    }
  }
  
  return result
}





























