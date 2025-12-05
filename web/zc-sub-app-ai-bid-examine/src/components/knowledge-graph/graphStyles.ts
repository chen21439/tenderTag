/**
 * 知识图谱样式定义
 * Cytoscape 样式配置
 */

import type { Stylesheet } from 'cytoscape'

/**
 * 获取知识图谱的 Cytoscape 样式
 */
export const getGraphStyles = (): Stylesheet[] => {
  return [
    // 默认节点样式
    {
      selector: 'node',
      style: {
        'background-color': '#2f4554',
        label: 'data(label)',  // 使用原始 label（数量显示在 HTML 徽章中）
        color: '#fff',
        'text-valign': 'center',
        'text-halign': 'center',
        'font-size': '14px',
        width: '70px',
        height: '70px',
        'text-wrap': 'wrap',
        'text-max-width': '90px'
      }
    },

    // 概念节点 - Normal（深蓝灰背景，白色文字）
    {
      selector: 'node[type="normal"]',
      style: {
        'background-color': '#2f4554',
        color: '#fff'
      }
    },

    // 文档节点（较小，浅灰色）
    {
      selector: 'node[type="doc"]',
      style: {
        'background-color': '#95a5a6',
        color: '#fff',
        width: '50px',
        height: '50px',
        'font-size': '12px'
      }
    },

    // 补充节点（最小，粉色）
    {
      selector: 'node[type="supplement"]',
      style: {
        'background-color': '#eb2f96',
        color: '#fff',
        width: '45px',
        height: '45px',
        'font-size': '11px'
      }
    },

    // 要素节点（小型，紫色）
    {
      selector: 'node[type="element"]',
      style: {
        'background-color': '#722ed1',
        color: '#fff',
        width: '60px',
        height: '60px',
        'font-size': '13px',
        shape: 'roundrectangle'
      }
    },

    // 选中的节点
    {
      selector: 'node:selected',
      style: {
        'border-width': '3px',
        'border-color': '#1890ff'
      }
    },

    // 选中的节点（自定义类）
    {
      selector: 'node.selected',
      style: {
        'border-width': '3px',
        'border-color': '#1890ff'
      }
    },

    // 变暗的节点
    {
      selector: 'node.dimmed',
      style: {
        opacity: 0.2
      }
    },

    // 高亮的父节点（橙色边框）
    {
      selector: 'node.highlighted-parent',
      style: {
        'border-width': '3px',
        'border-color': '#fa8c16'
      }
    },

    // 高亮的子节点（绿色边框）
    {
      selector: 'node.highlighted-child',
      style: {
        'border-width': '3px',
        'border-color': '#52c41a'
      }
    },

    // 默认边样式
    {
      selector: 'edge',
      style: {
        width: 2,
        'line-color': '#95a5a6',
        'target-arrow-color': '#95a5a6',
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        label: 'data(label)',
        'font-size': '10px',
        'text-rotation': 'autorotate',
        'text-margin-y': -10
      }
    },

    // 选中的边
    {
      selector: 'edge:selected',
      style: {
        'line-color': '#1890ff',
        'target-arrow-color': '#1890ff',
        width: 3
      }
    },

    // 选中的边（自定义类）
    {
      selector: 'edge.selected',
      style: {
        'line-color': '#1890ff',
        'target-arrow-color': '#1890ff',
        width: 3
      }
    },

    // 变暗的边
    {
      selector: 'edge.dimmed',
      style: {
        opacity: 0.15
      }
    },

    // 高亮的边
    {
      selector: 'edge.highlighted',
      style: {
        'line-color': '#1890ff',
        'target-arrow-color': '#1890ff',
        width: 3
      }
    },

    // attachedTo 边样式（绿色实线）
    {
      selector: 'edge[label="attachedTo"]',
      style: {
        'line-color': '#91cc75',
        'target-arrow-color': '#91cc75',
        width: 2,
        'line-style': 'solid',
        'curve-style': 'bezier'
      }
    },

    // hasPart 边样式（黄色实线）
    {
      selector: 'edge[label="hasPart"]',
      style: {
        'line-color': '#fac858',
        'target-arrow-color': '#fac858',
        width: 2,
        'line-style': 'solid',
        'curve-style': 'bezier'
      }
    },

    // hasMember 边样式（红色实线）
    {
      selector: 'edge[label="hasMember"]',
      style: {
        'line-color': '#ee6666',
        'target-arrow-color': '#ee6666',
        width: 2,
        'line-style': 'solid',
        'curve-style': 'bezier'
      }
    },

    // sameAs 边样式（橙色虚线，双向箭头）
    {
      selector: 'edge[label="sameAs"]',
      style: {
        'line-color': '#fa8c16',
        'target-arrow-color': '#fa8c16',
        'source-arrow-color': '#fa8c16',
        'source-arrow-shape': 'triangle',
        'target-arrow-shape': 'triangle',
        'line-style': 'dashed',
        width: 2,
        'curve-style': 'bezier'
      }
    },

    // hasAttribute 边样式（紫色点线）
    {
      selector: 'edge[label="hasAttribute"]',
      style: {
        'line-color': '#9254de',
        'target-arrow-color': '#9254de',
        width: 2,
        'line-style': 'dotted',
        'curve-style': 'bezier'
      }
    },

    // instanceOf 边样式（蓝色实线）
    {
      selector: 'edge[label="instanceOf"]',
      style: {
        'line-color': '#5470c6',
        'target-arrow-color': '#5470c6',
        width: 2,
        'line-style': 'solid',
        'curve-style': 'bezier'
      }
    },

    // referTo 边样式（青色虚线）
    {
      selector: 'edge[label="referTo"]',
      style: {
        'line-color': '#73c0de',
        'target-arrow-color': '#73c0de',
        width: 2,
        'line-style': 'dashed',
        'curve-style': 'bezier'
      }
    },

    // explainTo 边样式（解释关系）
    {
      selector: 'edge[label="explainTo"]',
      style: {
        'line-color': '#9254de',
        'target-arrow-color': '#9254de',
        width: 2,
        'line-style': 'solid',
        'curve-style': 'bezier'
      }
    },

    // sectionOf 边样式（章节关系）
    {
      selector: 'edge[label="sectionOf"]',
      style: {
        'line-color': '#faad14',
        'target-arrow-color': '#faad14',
        width: 2,
        'line-style': 'solid',
        'curve-style': 'bezier'
      }
    },

    // sameAs 边高亮样式
    {
      selector: 'edge[label="sameAs"].highlighted',
      style: {
        'line-color': '#ff7a45',
        'target-arrow-color': '#ff7a45',
        'source-arrow-color': '#ff7a45',
        width: 3
      }
    },

    // 推理出的边样式（稍微半透明的虚线）
    {
      selector: 'edge[inferred="true"]',
      style: {
        'line-style': 'dotted',
        opacity: 0.7
      }
    },

    // 临时预览边（虚线）
    {
      selector: '.temp-edge',
      style: {
        'line-color': '#1890ff',
        'target-arrow-color': '#1890ff',
        'line-style': 'dashed',
        width: 2,
        opacity: 0.6
      }
    },

    // 临时目标节点（不可见）
    {
      selector: '.temp-node',
      style: {
        width: '1px',
        height: '1px',
        'background-color': 'transparent',
        'border-width': 0
      }
    },

    // 临时预览节点（虚线边框，半透明）
    {
      selector: '.temp-preview-node',
      style: {
        'background-color': '#2f4554',
        width: '60px',
        height: '60px',
        'border-width': '2px',
        'border-color': '#1890ff',
        'border-style': 'dashed',
        opacity: 0.6,
        label: ''
      }
    }
  ]
}
