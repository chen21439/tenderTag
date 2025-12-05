/**
 * 知识图谱 HTML 标签配置
 * 使用 cytoscape-node-html-label 插件为节点添加 HTML 标签
 */

import type { Core } from 'cytoscape'
// @ts-ignore - cytoscape-node-html-label 没有类型定义
import nodeHtmlLabel from 'cytoscape-node-html-label'

/**
 * 注册 HTML 标签插件
 * @param cytoscape - Cytoscape 构造函数
 */
export const registerHtmlLabelPlugin = (cytoscape: any) => {
  if (typeof nodeHtmlLabel === 'function') {
    nodeHtmlLabel(cytoscape)
  }
}

/**
 * 解析要素节点的 label，分离 key 和 value
 * @param label - 原始 label，格式如 "评标方法名称: 综合评分法"
 * @returns { key, value } 或 { key: label, value: '' }
 */
export const parseFieldLabel = (label: string): { key: string; value: string } => {
  if (!label || typeof label !== 'string') {
    return { key: '', value: '' }
  }

  const colonIndex = label.indexOf(':')
  if (colonIndex === -1) {
    // 没有冒号，整个字符串作为 key
    return { key: label.trim(), value: '' }
  }

  const key = label.substring(0, colonIndex).trim()
  const value = label.substring(colonIndex + 1).trim()

  return { key, value }
}

/**
 * 应用 HTML 标签配置到 Cytoscape 实例
 * @param cy - Cytoscape 实例
 */
export const applyHtmlLabels = (cy: Core | null) => {
  if (!cy) return

  // @ts-ignore - nodeHtmlLabel 扩展了 cy 实例
  if (typeof cy.nodeHtmlLabel !== 'function') {
    console.warn('⚠️ nodeHtmlLabel 插件未注册')
    return
  }

  // @ts-ignore
  cy.nodeHtmlLabel([
    {
      // 为有要素节点的概念节点添加徽章
      query: 'node[type!="element"]',
      tpl: function(data: any) {
        // 直接使用节点的 fieldCount 字段（更可靠，避免字符串解析）
        const count = data.fieldCount || 0

        if (count > 0) {
          return `
            <div class="node-badge-container">
              <div class="node-badge">${count}</div>
            </div>
          `
        }
        return ''
      },
      halign: 'right',
      valign: 'top',
      cssClass: 'node-html-label'
    }
  ])

  console.log('✅ 已应用 HTML 标签配置')
}

/**
 * 获取 HTML 标签的样式
 * @returns CSS 样式字符串
 */
export const getHtmlLabelStyles = () => {
  return `
    .node-html-label {
      pointer-events: none;
    }

    .node-badge-container {
      position: relative;
      width: 0;
      height: 0;
    }

    .node-badge {
      position: absolute;
      top: -35px;
      right: -35px;
      min-width: 20px;
      height: 20px;
      padding: 0 6px;
      background: #ff4d4f;
      color: #fff;
      border-radius: 10px;
      font-size: 12px;
      font-weight: bold;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
      border: 2px solid #fff;
    }
  `
}
