/**
 * PDF 高亮和跳转工具类
 *
 * 用于处理节点点击后的 PDF 页面跳转和区域高亮
 */

/**
 * Box 信息接口
 */
export interface BoxInfo {
  page: number // 页码（从 0 开始）
  box: [number, number, number, number] // [left, top, right, bottom]
  coord_origin?: string // 坐标原点，默认 'TOPLEFT'
}

/**
 * 高亮数据接口
 */
export interface HighlightData {
  pageNum: number // 页码（从 1 开始）
  rect: [number, number, number, number] // 用于定位的矩形
  quadPoints: number[] // 高亮区域的四边形坐标点数组
  needsConversion: boolean // 是否需要坐标转换（TOPLEFT -> PDF BOTTOMLEFT）
  jump: boolean // 是否跳转
}

/**
 * 将 box 转换为 quadPoints（8个坐标点）
 * quadPoints 格式: [x1,y1, x2,y2, x3,y3, x4,y4]
 * 顺序: 左上 -> 右上 -> 右下 -> 左下
 */
export function boxToQuadPoints(box: number[]): number[] {
  return [
    box[0], box[1], // 左上
    box[2], box[1], // 右上
    box[2], box[3], // 右下
    box[0], box[3]  // 左下
  ]
}

/**
 * 智能合并 boxes：将同一栏的连续行合并成一个大矩形
 *
 * 分栏判断标准：
 * 1. X 坐标显著跳变（超过阈值）→ 换栏
 * 2. Y 坐标向上跳（非连续）→ 换栏
 *
 * @param boxes - box 数组 [left, top, right, bottom]
 * @returns 合并后的 box 数组
 */
export function mergeBoxesByColumn(boxes: BoxInfo[]): number[][] {
  if (!boxes || boxes.length === 0) return []
  if (boxes.length === 1) return [boxes[0].box]

  const mergedBoxes: number[][] = []
  let currentGroup: BoxInfo[] = [boxes[0]]

  // X 轴阈值：横向位移超过 50 像素认为是不同栏
  const X_THRESHOLD = 50
  // Y 轴阈值：纵向间隔超过 20 像素认为不连续
  const Y_GAP_THRESHOLD = 20

  for (let i = 1; i < boxes.length; i++) {
    const prev = boxes[i - 1]
    const curr = boxes[i]

    // 计算 X 轴差异（左边界的差距）
    const xDiff = Math.abs(curr.box[0] - prev.box[0])
    // 计算 Y 轴间隔（当前 box 的上边界 - 前一个 box 的下边界）
    const yGap = curr.box[1] - prev.box[3]

    // 判断是否需要开始新区域
    const shouldStartNewRegion =
      xDiff > X_THRESHOLD || // X 坐标跳变太大
      yGap < 0 || // Y 坐标向上跳
      yGap > Y_GAP_THRESHOLD // Y 坐标间隔太大

    if (shouldStartNewRegion) {
      // 合并当前组
      mergedBoxes.push(mergeGroup(currentGroup))
      // 开始新组
      currentGroup = [curr]
    } else {
      // 添加到当前组
      currentGroup.push(curr)
    }
  }

  // 合并最后一组
  if (currentGroup.length > 0) {
    mergedBoxes.push(mergeGroup(currentGroup))
  }

  return mergedBoxes
}

/**
 * 合并一组 boxes 为单个大矩形
 */
function mergeGroup(group: BoxInfo[]): number[] {
  const left = Math.min(...group.map(b => b.box[0]))
  const top = Math.min(...group.map(b => b.box[1]))
  const right = Math.max(...group.map(b => b.box[2]))
  const bottom = Math.max(...group.map(b => b.box[3]))
  return [left, top, right, bottom]
}

/**
 * 创建 PDF 高亮数据
 *
 * @param boxes - 包含位置信息的 box 数组
 * @param options - 可选配置
 * @returns 高亮数据对象，如果没有有效数据则返回 null
 */
export function createHighlightData(
  boxes: BoxInfo[],
  options: {
    enableMerge?: boolean // 是否启用智能合并，默认 true
    filterCurrentPage?: boolean // 是否只高亮第一页的内容，默认 true
  } = {}
): HighlightData | null {
  const { enableMerge = true, filterCurrentPage = true } = options

  if (!boxes || boxes.length === 0) {
    console.warn('❌ boxes 为空，无法创建高亮数据')
    return null
  }

  // 跳转到第一个 box 所在的页面
  const firstBox = boxes[0]
  const pageNum = firstBox.page + 1 // 转换为从 1 开始

  // 如果启用过滤，只保留当前页的 boxes
  const targetBoxes = filterCurrentPage
    ? boxes.filter(b => b.page === firstBox.page)
    : boxes

  console.log('📦 创建高亮数据:', {
    原始boxes数量: boxes.length,
    目标boxes数量: targetBoxes.length,
    当前页码: firstBox.page,
    启用合并: enableMerge
  })

  // 智能合并 boxes（如果启用）
  const mergedBoxes = enableMerge
    ? mergeBoxesByColumn(targetBoxes)
    : targetBoxes.map(b => b.box)

  console.log('📦 合并结果:', {
    原始box数: targetBoxes.length,
    合并后区域数: mergedBoxes.length
  })

  // 将合并后的 boxes 转换为 quadPoints
  const allQuadPoints: number[] = []
  mergedBoxes.forEach((box: number[]) => {
    allQuadPoints.push(...boxToQuadPoints(box))
  })

  console.log('📌 高亮区域:', {
    区域数量: mergedBoxes.length,
    quadPoints长度: allQuadPoints.length,
    页码: pageNum
  })

  // 创建高亮对象
  return {
    pageNum: pageNum,
    rect: mergedBoxes[0], // 使用第一个合并后的 box 用于定位
    quadPoints: allQuadPoints,
    needsConversion: true, // TOPLEFT 坐标，需要转换为 PDF 坐标
    jump: true
  }
}

/**
 * 跳转到 PDF 页面并高亮指定区域
 *
 * @param pdfViewer - PDF 查看器实例（需要有 scrollToAnnotation 方法）
 * @param highlightData - 高亮数据
 * @returns Promise<boolean> - 是否成功跳转和高亮
 */
export async function jumpToHighlight(
  pdfViewer: any,
  highlightData: HighlightData
): Promise<boolean> {
  if (!pdfViewer?.scrollToAnnotation) {
    console.warn('❌ PDF 查看器未就绪或不支持 scrollToAnnotation')
    return false
  }

  try {
    await pdfViewer.scrollToAnnotation(highlightData)
    console.log('✅ 已跳转到页面并高亮区域:', {
      页码: highlightData.pageNum,
      区域数: highlightData.quadPoints.length / 8
    })
    return true
  } catch (error) {
    console.error('❌ PDF 跳转失败:', error)
    return false
  }
}

/**
 * 便捷方法：从节点创建高亮数据并跳转
 *
 * @param node - 节点对象（包含 boxes 或 box + page 信息）
 * @param pdfViewer - PDF 查看器实例
 * @param pdfData - PDF 数据对象（包含 currentPage 和 highlightRects）
 * @param options - 可选配置
 * @returns Promise<boolean> - 是否成功
 */
export async function highlightNodeOnPdf(
  node: any,
  pdfViewer: any,
  pdfData: { currentPage: number; highlightRects: HighlightData[] },
  options: {
    enableMerge?: boolean
    filterCurrentPage?: boolean
    enableHighlight?: boolean // 是否启用高亮，默认 true
  } = {}
): Promise<boolean> {
  const { enableHighlight = true, ...createOptions } = options

  // 提取 boxes 信息
  let boxes: BoxInfo[] = []

  if (node.boxes && Array.isArray(node.boxes) && node.boxes.length > 0) {
    // 节点有 boxes 数组
    boxes = node.boxes
  } else if (node.box && node.page !== undefined) {
    // 节点有单个 box
    boxes = [{ page: node.page, box: node.box }]
  } else {
    console.warn('❌ 节点没有位置信息')
    return false
  }

  // 跳转到页面
  const firstBox = boxes[0]
  pdfData.currentPage = firstBox.page + 1

  // 如果不启用高亮，只跳转
  if (!enableHighlight) {
    pdfData.highlightRects = []
    console.log('✅ 已跳转到页面', pdfData.currentPage, '(高亮功能已禁用)')
    return true
  }

  // 创建高亮数据
  const highlightData = createHighlightData(boxes, createOptions)
  if (!highlightData) {
    return false
  }

  // 更新 PDF 高亮区域
  pdfData.highlightRects = [highlightData]

  // 跳转并高亮
  // 需要等待 DOM 更新
  await new Promise(resolve => setTimeout(resolve, 0))
  return await jumpToHighlight(pdfViewer, highlightData)
}
