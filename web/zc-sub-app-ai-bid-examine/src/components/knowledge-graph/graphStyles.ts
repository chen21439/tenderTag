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

    // === 文档系统图谱节点样式 ===

    // 项目节点（橘色、大号矩形）
    {
      selector: 'node[type="Project"]',
      style: {
        'background-color': '#f39c12',
        color: '#fff',
        shape: 'round-rectangle',
        width: '120px',
        height: '50px',
        'font-size': '14px'
      }
    },

    // 文档节点（蓝色、矩形）
    {
      selector: 'node[type="Document"]',
      style: {
        'background-color': '#3498db',
        color: '#fff',
        shape: 'rectangle',
        width: '100px',
        height: '45px',
        'font-size': '13px'
      }
    },

    // 组织节点（绿色、椭圆）
    {
      selector: 'node[type="Org"]',
      style: {
        'background-color': '#27ae60',
        color: '#fff',
        shape: 'ellipse',
        width: '90px',
        height: '60px',
        'font-size': '13px'
      }
    },

    // 订单节点（紫色、菱形）
    {
      selector: 'node[type="Order"]',
      style: {
        'background-color': '#9b59b6',
        color: '#fff',
        shape: 'diamond',
        width: '80px',
        height: '50px',
        'font-size': '12px'
      }
    },

    // 实体节点（青色、六边形）
    {
      selector: 'node[type="Entity"]',
      style: {
        'background-color': '#16a085',
        color: '#fff',
        shape: 'hexagon',
        width: '80px',
        height: '40px',
        'font-size': '12px'
      }
    },

    // 部门节点（蓝紫色、圆角矩形）
    {
      selector: 'node[type="Dept"]',
      style: {
        'background-color': '#5f27cd',
        color: '#fff',
        shape: 'round-rectangle',
        width: '85px',
        height: '45px',
        'font-size': '12px'
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

    // 选中的供应商节点（红色粗边框、放大）
    {
      selector: 'node.selected-supplier',
      style: {
        'border-width': '4px',
        'border-color': '#e74c3c',
        width: '110px',
        height: '70px'
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

    // === 文档系统图谱边样式 ===

    // BELONGS_TO 关系（文档属于项目，深灰色）
    {
      selector: 'edge[type="BELONGS_TO"]',
      style: {
        'line-color': '#34495e',
        'target-arrow-color': '#34495e',
        width: 2,
        'line-style': 'solid'
      }
    },

    // OWNER 关系（项目所有者，橙色粗线）
    {
      selector: 'edge[type="OWNER"]',
      style: {
        'line-color': '#e67e22',
        'target-arrow-color': '#e67e22',
        width: 3
      }
    },

    // PARTY 关系（合同相对方，紫色粗线）
    {
      selector: 'edge[type="PARTY"]',
      style: {
        'line-color': '#9b59b6',
        'target-arrow-color': '#9b59b6',
        width: 3
      }
    },

    // FRAMEWORK_SUPPLIER 关系（入围供应商，绿色粗线）
    {
      selector: 'edge[type="FRAMEWORK_SUPPLIER"]',
      style: {
        'line-color': '#27ae60',
        'target-arrow-color': '#27ae60',
        width: 3
      }
    },

    // AWARDED_TO 关系（订单中标，橙色粗线）
    {
      selector: 'edge[type="AWARDED_TO"]',
      style: {
        'line-color': '#e67e22',
        'target-arrow-color': '#e67e22',
        width: 3
      }
    },

    // BID_FOR 关系（参与投标，灰色虚线）
    {
      selector: 'edge[type="BID_FOR"]',
      style: {
        'line-color': '#95a5a6',
        'target-arrow-color': '#95a5a6',
        'line-style': 'dashed',
        width: 1
      }
    },

    // BELONGS_TO_FRAMEWORK 关系（订单属于框架，深灰虚线）
    {
      selector: 'edge[type="BELONGS_TO_FRAMEWORK"]',
      style: {
        'line-color': '#34495e',
        'target-arrow-color': '#34495e',
        'line-style': 'dotted',
        width: 1
      }
    },

    // USES_FRAMEWORK 关系（部门使用框架，蓝色虚线）
    {
      selector: 'edge[type="USES_FRAMEWORK"]',
      style: {
        'line-color': '#2980b9',
        'target-arrow-color': '#2980b9',
        'line-style': 'dashed',
        width: 1
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
