/**
 * 知识图谱 Tooltip 管理
 * 为要素节点提供鼠标悬浮提示功能
 */

import type { Core } from 'cytoscape'

export interface TooltipState {
  visible: boolean
  x: number
  y: number
  content: {
    label: string
    fieldValue?: string
  }
}

/**
 * 绑定 tooltip 事件到 Cytoscape 实例
 * @param cy - Cytoscape 实例
 * @param tooltipState - tooltip 状态对象（响应式）
 */
export const bindTooltipEvents = (
  cy: Core | null,
  tooltipState: TooltipState
) => {
  if (!cy) return

  // 鼠标悬浮节点
  cy.on('mouseover', 'node', (event) => {
    const node = event.target
    const nodeData = node.data()

    // 只为要素节点显示 tooltip
    if (nodeData.type === 'element') {
      const renderedPosition = node.renderedPosition()

      tooltipState.visible = true
      tooltipState.x = renderedPosition.x + 10
      tooltipState.y = renderedPosition.y - 10
      tooltipState.content = {
        label: nodeData.label || nodeData.id,
        fieldValue: nodeData.fieldValue
      }
    }
  })

  // 鼠标离开节点
  cy.on('mouseout', 'node', () => {
    tooltipState.visible = false
  })

  console.log('✅ 已绑定 Tooltip 事件')
}

/**
 * 解绑 tooltip 事件
 * @param cy - Cytoscape 实例
 */
export const unbindTooltipEvents = (cy: Core | null) => {
  if (!cy) return

  cy.off('mouseover', 'node')
  cy.off('mouseout', 'node')

  console.log('✅ 已解绑 Tooltip 事件')
}
